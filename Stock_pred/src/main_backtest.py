import argparse
import os
from datetime import datetime

import numpy as np
import pandas as pd

from src.backtesting.engine import EntryRules, RiskRules, backtest_daily
from src.backtesting.execution import CommissionModel, SlippageModel
from src.config.loader import load_config
from src.data.fetch import fetch_ohlcv
from src.features.engineering import add_core_features
from src.training.train_classification import (
    ClassifierTrainConfig,
    build_xy,
    prepare_dataset,
    train_xgb_walkforward,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Train and backtest daily signal generator")
    parser.add_argument("--config", type=str, required=True, help="Path to JSON config")
    parser.add_argument("--artifacts", type=str, default="artifacts", help="Artifacts directory")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg = load_config(args.config)

    start = pd.Timestamp(cfg.backtest_period["start"])  # type: ignore[index]
    end = pd.Timestamp(cfg.backtest_period["end"])  # type: ignore[index]

    # Prepare combined dataset across universe
    frames = []
    for t in cfg.universe:
        feats = prepare_dataset(t, start, end)
        frames.append(feats)
    df_all = pd.concat(frames, axis=0).sort_index()

    X, y = build_xy(df_all, horizon_days=cfg.horizon_days, delta_threshold=cfg.delta_threshold)
    metrics = train_xgb_walkforward(X, y, save_dir=args.artifacts, cfg=ClassifierTrainConfig(
        horizon_days=cfg.horizon_days,
        delta_threshold=cfg.delta_threshold,
    ))
    print("CV Metrics:", metrics)

    # Predict probabilities for backtest period
    import joblib

    scaler = joblib.load(os.path.join(args.artifacts, "xgb_scaler.joblib"))
    feature_columns = scaler["columns"]
    model = joblib.load(os.path.join(args.artifacts, "xgb_model.joblib"))

    # Build per-date, per-ticker feature rows
    proba_rows = []
    for t in cfg.universe:
        feats = prepare_dataset(t, start, end)
        feats = feats.assign(ticker_code=float(pd.Series([t]).astype("category").cat.codes.iloc[0]))
        feats = feats.drop(columns=["ticker"], errors="ignore")
        # Align columns to training schema
        feats = feats.reindex(columns=feature_columns, fill_value=0.0)
        X_mat = scaler["scaler"].transform(feats.values)
        p = model.predict_proba(X_mat)[:, 1]
        s = pd.Series(p, index=feats.index, name="p_up")
        s.index = pd.MultiIndex.from_product([s.index, [t]])
        proba_rows.append(s)

    proba = pd.concat(proba_rows).sort_index()

    # Load prices for backtest
    prices = {t: prepare_dataset(t, start, end) for t in cfg.universe}

    tm = backtest_daily(
        prices=prices,
        proba=proba,
        entry_rules=EntryRules(
            p_entry_threshold=cfg.entry_p_threshold,
            stop_loss_pct=cfg.stop_loss_pct,
            take_profit_pct=cfg.take_profit_pct,
            max_hold_days=5,
        ),
        risk_rules=RiskRules(max_positions=cfg.max_positions, max_alloc_single=0.05, risk_per_trade_pct=cfg.risk_per_trade_pct),
        commission=CommissionModel(fixed=cfg.commission_per_trade, percent=0.0003),
        slippage=SlippageModel(base_slip_pct=cfg.slippage_model.get("base_slip_pct", 0.0002), k=cfg.slippage_model.get("k", 0.5)),
        initial_equity=200_000.0,
    )
    print("Backtest Trading Metrics:", tm)


if __name__ == "__main__":
    main()


