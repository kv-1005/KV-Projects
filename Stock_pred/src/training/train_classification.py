from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from src.data.fetch import fetch_ohlcv
from src.features.engineering import add_core_features
from src.labels.binary import make_binary_label
from src.models.xgb_classifier import build_xgb_classifier, compute_scale_pos_weight, fit_calibrated
from src.validation.walkforward import WalkForwardConfig, generate_walkforward_splits


@dataclass
class ClassifierTrainConfig:
    horizon_days: int = 1
    delta_threshold: float = 0.002
    walk_train_years: int = 5
    walk_val_years: int = 1
    walk_step_years: int = 1


def prepare_dataset(ticker: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    raw = fetch_ohlcv(ticker, start, end)
    feats = add_core_features(raw)
    feats["ticker"] = ticker
    return feats


def build_xy(df: pd.DataFrame, horizon_days: int, delta_threshold: float) -> Tuple[pd.DataFrame, pd.Series]:
    # Compute labels within each ticker to avoid cross-ticker leakage
    df_local = df.copy()
    if "ticker" not in df_local.columns:
        raise ValueError("Expected 'ticker' column in features DataFrame")

    parts = []
    for _, g in df_local.groupby("ticker", sort=False):
        parts.append(make_binary_label(g, horizon_days=horizon_days, delta_threshold=delta_threshold))
    y = pd.concat(parts).sort_index()

    # Valid mask (drop last H rows per ticker where future is unknown). Use positional mask to avoid index shape issues.
    valid_mask = y.notna().reindex(df_local.index).fillna(False).to_numpy()
    # Positional selection to avoid label alignment surprises
    X = df_local.iloc[valid_mask].copy()
    y_full = y.reindex(df_local.index)
    y_vals = y_full.to_numpy()[valid_mask]
    y = pd.Series(y_vals, index=X.index, name="y")
    # Ensure binary {0,1}
    y = pd.Series(np.where(y > 0, 1, 0), index=y.index, name="y")

    # Remove leakage columns
    drop_cols = ["Adj Close"]
    X = X.drop(columns=[c for c in drop_cols if c in X.columns], errors="ignore")
    return X, y


def train_xgb_walkforward(
    X: pd.DataFrame,
    y: pd.Series,
    save_dir: str,
    cfg: ClassifierTrainConfig,
) -> Dict[str, float]:
    os.makedirs(save_dir, exist_ok=True)
    index = X.index

    # Prepare feature matrix; scale numeric features except categorical like ticker (encode as category codes)
    X_proc = X.copy()
    if "ticker" in X_proc.columns:
        X_proc["ticker_code"] = X_proc["ticker"].astype("category").cat.codes.astype(float)
        X_proc = X_proc.drop(columns=["ticker"])

    numeric_cols = X_proc.columns
    scaler = StandardScaler()
    X_values = scaler.fit_transform(X_proc.values)

    wf_cfg = WalkForwardConfig(
        train_years=cfg.walk_train_years, val_years=cfg.walk_val_years, step_years=cfg.walk_step_years
    )

    aucs: List[float] = []
    pr_aps: List[float] = []
    briers: List[float] = []

    # For simplicity, fit one model on the final combined train; still report CV metrics
    for tr_idx, va_idx in generate_walkforward_splits(index, wf_cfg):
        X_tr, y_tr = X_values[tr_idx], y.values[tr_idx]
        X_va, y_va = X_values[va_idx], y.values[va_idx]

        spw = compute_scale_pos_weight(y_tr)
        base = build_xgb_classifier(scale_pos_weight=spw)
        model = fit_calibrated(base, X_tr, y_tr, cv=3)

        p_va = model.predict_proba(X_va)[:, 1]
        try:
            auc = roc_auc_score(y_va, p_va)
        except Exception:
            auc = float("nan")
        aucs.append(auc)
        pr_aps.append(average_precision_score(y_va, p_va))
        briers.append(brier_score_loss(y_va, p_va))

    # Final fit on all data
    spw_all = compute_scale_pos_weight(y.values)
    final_base = build_xgb_classifier(scale_pos_weight=spw_all)
    final_model = fit_calibrated(final_base, X_values, y.values, cv=5)

    # Persist scaler and model
    import joblib

    joblib.dump({"scaler": scaler, "columns": list(numeric_cols)}, os.path.join(save_dir, "xgb_scaler.joblib"))
    joblib.dump(final_model, os.path.join(save_dir, "xgb_model.joblib"))

    return {
        "ROC_AUC_mean": float(np.nanmean(aucs)) if len(aucs) else float("nan"),
        "PR_AUC_mean": float(np.mean(pr_aps)) if len(pr_aps) else float("nan"),
        "Brier_mean": float(np.mean(briers)) if len(briers) else float("nan"),
    }


