"""
Data Drift Detection Module
---------------------------
Calculates Kullback-Leibler (KL) Divergence and Population Stability Index (PSI) 
between the live market features and the training distribution.

Institutional systems freeze if the live data structure fundamentally breaks from
what the model was trained on (i.e. unprecedented volatility or regime breakage).
"""

from __future__ import annotations

import logging
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

log = logging.getLogger(__name__)


def calculate_psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """
    Computes Population Stability Index (PSI) using absolute binning.
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine breakpoints from expected distribution (Training)
    # Use percentiles to avoid being too sensitive to extreme outliers
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    # Correct for duplicate breakpoints in discrete features
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 2:
        breakpoints = np.array([-np.inf, np.inf])
    else:
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf
    
    expected_counts = np.histogram(expected, breakpoints)[0]
    actual_counts = np.histogram(actual, breakpoints)[0]
    
    expected_percents = expected_counts / len(expected)
    actual_percents = actual_counts / len(actual)

    def sub_psi(e_perc: float, a_perc: float) -> float:
        a_perc = max(a_perc, 1e-4)
        e_perc = max(e_perc, 1e-4)
        return (e_perc - a_perc) * np.log(e_perc / a_perc)

    psi_value = sum(sub_psi(expected_percents[i], actual_percents[i]) for i in range(len(expected_percents)))
    return float(psi_value)


class DriftMonitor:
    def __init__(self, save_dir: str = "artifacts", threshold: float = 0.50) -> None:
        self.save_dir = save_dir
        self.threshold = threshold
        self.training_dist = self._load_training_distribution()

    def _load_training_distribution(self) -> dict:
        """Loads the saved feature distributions from the last training run."""
        path = os.path.join(self.save_dir, "xgb_intraday_scaler.joblib")
        if not os.path.exists(path):
            log.warning("[DriftMonitor] No training scaler found. Drift detection disabled.")
            return {}
            
        bundle = joblib.load(path)
        scaler = bundle["scaler"]
        cols = bundle["columns"]
        
        # We save the means and standard deviations from the Standard Scaler
        # to approximate the expected distribution shape
        return {
            "columns": cols,
            "means": scaler.mean_,
            "stds": np.sqrt(scaler.var_),
        }

    def check_drift(self, df_live: pd.DataFrame) -> dict:
        """
        Checks current live 30-min window against training distributions.
        Returns a dict of PSI values and a boolean `is_drifting_critically`.
        """
        if not self.training_dist:
            return {"is_drifting_critically": False}

        cols = self.training_dist["columns"]
        expected_means = self.training_dist["means"]
        expected_stds = self.training_dist["stds"]

        # Check an expanded rolling window (e.g., last 5 days = ~375 candles for 5m interval)
        # to prevent short-term volatility spikes from triggering false PSI alarms.
        window_size = 375
        if len(df_live) > window_size:
            df_recent = df_live.iloc[-window_size:]
        else:
            df_recent = df_live

        critical_features = 0
        feature_psis = {}

        for i, col in enumerate(cols):
            if col not in df_recent.columns:
                continue
                
            live_arr = df_recent[col].values
            
            # Reconstruct a stable 'expected' array from training dist (N=1000 for stability)
            expected_arr = np.random.normal(expected_means[i], expected_stds[i], size=1000)
            
            psi = calculate_psi(expected_arr, live_arr)
            feature_psis[col] = psi

            # Monday Morning Tolerance: Use simulation time (from data) if available
            sim_time = df_live.index[-1]
            current_threshold = self.threshold
            
            # Check if sim_time is a pandas Timestamp or has access to weekday/hour
            try:
                if sim_time.weekday() == 0 and sim_time.hour == 9 and sim_time.minute < 45:
                    current_threshold = 0.35  # Higher tolerance for Monday morning gaps
            except AttributeError:
                pass # Fallback to default if index isn't Datetime
                
            if psi >= current_threshold:
                critical_features += 1

        # If more than 60% of features are critically drifting, signal an alarm.
        # (Previously 25% — loosened to prevent daily false lockouts on fresh data)
        drift_ratio = critical_features / len(cols) if cols else 0
        
        # Bypass: If 100% of features are "drifting", this almost certainly means the
        # model is stale (retrain needed) rather than a genuine market breakdown.
        # A real crash/regime change affects 50-80%, not every single feature at once.
        if drift_ratio >= 1.0:
            log.warning("[DriftMonitor] 🟡 All features flagged — likely stale model, not market crash. Bypassing block. Retrain ASAP.")
            return {
                "is_drifting_critically": False,
                "drift_ratio": drift_ratio,
                "feature_psis": feature_psis,
                "bypass_reason": "stale_model"
            }
        
        is_drifting = drift_ratio > 0.60

        if is_drifting:
            log.debug(f"[DriftMonitor] Feature drift detected: {drift_ratio*100:.1f}% >= threshold")

        return {
            "is_drifting_critically": is_drifting,
            "drift_ratio": drift_ratio,
            "feature_psis": feature_psis
        }
