"""
Intraday XGBoost Walk-Forward Trainer (Regression / Institutional)
------------------------------------------------------------------
Trains an XGBoost Regressor to predict the Expected Net Return (R-multiple) 
over the next N candles. The target label structurally penalizes the transaction 
and slippage costs directly during cost-aware training.

Walk-forward (anchored) cross-validation:
    30-day train → 5-day validate → step 5 days → repeat
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR


@dataclass
class IntradayTrainConfig:
    horizon_candles: int      = 3          
    transaction_cost: float   = 0.0013     
    train_days: int           = 30
    val_days: int             = 5
    step_days: int            = 5
    n_estimators: int         = 300
    max_depth: int            = 5
    learning_rate: float      = 0.05
    subsample: float          = 0.8
    colsample_bytree: float   = 0.8
    reg_alpha: float          = 0.1
    random_state: int         = 42


# Non-feature columns to exclude from X
_EXCLUDE_COLS = {"Open", "High", "Low", "Close", "Volume", "ticker", "Close_clean"}


def make_labels(df: pd.DataFrame, horizon: int, transaction_cost: float) -> pd.Series:
    """
    Cost-Aware Continuous Label: 
    Expected Net Return = (Future Price / Current Price) - 1.0 - Transaction_Cost
    """
    future_return = df["Close"].shift(-horizon) / df["Close"] - 1.0
    net_return = future_return - transaction_cost
    return net_return.rename("label")


def get_feature_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c not in _EXCLUDE_COLS and c != "label" and c != "regime"]


def train_intraday_model(
    df: pd.DataFrame,
    cfg: IntradayTrainConfig = IntradayTrainConfig(),
    save_dir: str = "artifacts",
) -> Dict[str, float]:
    """
    Walk-forward train an Ensemble (XGB, RF, SVR) on intraday features.
    """
    os.makedirs(save_dir, exist_ok=True)

    labels = make_labels(df, cfg.horizon_candles, cfg.transaction_cost)
    df = df.copy()
    df["label"] = labels
    df = df.dropna(subset=["label"])

    feature_cols = get_feature_cols(df)
    dates = df.index.normalize().unique().sort_values()

    from rich.progress import track
    
    cv_results: List[Dict[str, float]] = []
    all_X_train, all_y_train = [], []

    # Calculate total steps for the progress bar
    total_steps = 0
    temp_i = 0
    while temp_i + cfg.train_days + cfg.val_days <= len(dates):
        total_steps += 1
        temp_i += cfg.step_days

    i = 0
    for _ in track(range(total_steps), description="[green]Research Ensemble (XGB+RF+SVR) CV..."):
        train_dates = dates[i : i + cfg.train_days]
        val_dates   = dates[i + cfg.train_days : i + cfg.train_days + cfg.val_days]

        train_mask = df.index.normalize().isin(train_dates)
        val_mask   = df.index.normalize().isin(val_dates)

        if not train_mask.any() or not val_mask.any():
            i += cfg.step_days
            continue

        X_train = df.loc[train_mask, feature_cols].values
        y_train = df.loc[train_mask, "label"].values
        X_val   = df.loc[val_mask, feature_cols].values
        y_val   = df.loc[val_mask, "label"].values
        
        if len(y_train) < 100:
            i += cfg.step_days
            continue

        scaler  = StandardScaler()
        X_tr_sc = scaler.fit_transform(X_train)
        X_vl_sc = scaler.transform(X_val)
        
        # XGBoost Fold
        xgb = XGBRegressor(n_estimators=100, max_depth=cfg.max_depth, learning_rate=cfg.learning_rate, random_state=cfg.random_state, tree_method="hist")
        xgb.fit(X_tr_sc, y_train, eval_set=[(X_vl_sc, y_val)], verbose=False)
        
        # RandomForest Fold (Parallelised)
        rf = RandomForestRegressor(n_estimators=50, max_depth=cfg.max_depth, random_state=cfg.random_state, n_jobs=-1)
        rf.fit(X_tr_sc, y_train)
        
        # SVR Fold (Optimised for large datasets)
        svr = SVR(kernel="rbf", C=1.0, epsilon=0.01, max_iter=5000)
        svr.fit(X_tr_sc, y_train)

        # Ensemble Score (Averaged RMSE)
        p_xgb = xgb.predict(X_vl_sc)
        p_rf  = rf.predict(X_vl_sc)
        p_svr = svr.predict(X_vl_sc)
        p_ens = (p_xgb + p_rf + p_svr) / 3.0
        
        rmse = float(np.sqrt(mean_squared_error(y_val, p_ens)))
        cv_results.append({"rmse": rmse})
        
        all_X_train.append(X_train)
        all_y_train.append(y_train)
        i += cfg.step_days

    if not all_X_train:
        raise RuntimeError("No walk-forward folds were completed. Check data length.")

    all_X = np.vstack(all_X_train)
    all_y = np.concatenate(all_y_train)
    final_scaler = StandardScaler().fit(all_X)
    all_X_sc     = final_scaler.transform(all_X)

    # Final Training
    print("[Train] Finalizing Research Ensemble (XGB, RF, SVR)...")
    # 1. XGBoost (Fast)
    final_xgb = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42, tree_method="hist")
    final_xgb.fit(all_X_sc, all_y)
    
    # 2. RandomForest (Multi-core)
    print("  -> Fitting RandomForest (N_JOBS=-1)...")
    final_rf = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    final_rf.fit(all_X_sc, all_y)
    
    # 3. SVR (Kernel cap to prevent hang)
    print("  -> Fitting SVR (RBF Kernel, max_iter=20000)...")
    final_svr = SVR(kernel="rbf", C=1.0, epsilon=0.01, cache_size=2000, max_iter=20000)
    final_svr.fit(all_X_sc, all_y)

    # Save all models
    joblib.dump(final_xgb, os.path.join(save_dir, "xgb_intraday.joblib"))
    joblib.dump(final_rf, os.path.join(save_dir, "rf_intraday.joblib"))
    joblib.dump(final_svr, os.path.join(save_dir, "svr_intraday.joblib"))
    
    joblib.dump(
        {"scaler": final_scaler, "columns": feature_cols},
        os.path.join(save_dir, "xgb_intraday_scaler.joblib"),
    )
    print(f"[Train] ✅ Research Ensemble (3 Models) saved to {save_dir}/")

    metrics = {
        "cv_rmse": float(np.mean([r["rmse"] for r in cv_results])),
        "n_folds": len(cv_results),
    }
    return metrics
