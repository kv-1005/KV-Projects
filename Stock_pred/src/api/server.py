from __future__ import annotations

from datetime import datetime
from typing import List

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from src.data.fetch import fetch_ohlcv
from src.features.engineering import add_core_features
from src.signal.generator import SignalConfig, generate_signals

app = FastAPI(title="Stock Prediction API")


def _load_model_artifacts(artifacts_dir: str):
    try:
        scaler = joblib.load(f"{artifacts_dir}/xgb_scaler.joblib")
        model = joblib.load(f"{artifacts_dir}/xgb_model.joblib")
        return scaler, model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model artifacts not found: {e}")


@app.get("/predict")
def predict(
    date: str = Query(..., description="ISO date, e.g., 2025-10-31"),
    universe: List[str] = Query(..., description="Tickers"),
    artifacts_dir: str = Query("artifacts", description="Path to saved model"),
):
    target_date = pd.Timestamp(datetime.fromisoformat(date))
    scaler, model = _load_model_artifacts(artifacts_dir)

    frames = {}
    for t in universe:
        df = fetch_ohlcv(t, start_date=target_date - pd.Timedelta(days=400), end_date=target_date + pd.Timedelta(days=1))
        feats = add_core_features(df)
        frames[t] = feats

    # Build feature vector per ticker for the target date
    X_rows = []
    order = []
    feature_columns = scaler["columns"]
    for t, feats in frames.items():
        if target_date not in feats.index:
            continue
        x = feats.loc[target_date].copy()
        # Encode ticker
        x = x.copy()
        x["ticker_code"] = float(pd.Series([t]).astype("category").cat.codes.iloc[0])
        x = x.drop(labels=["ticker"], errors="ignore")
        # Align to training columns
        x = x.reindex(index=feature_columns, fill_value=0.0)
        X_rows.append(x.values)
        order.append(t)

    if not X_rows:
        raise HTTPException(status_code=400, detail="No features for the requested date")

    X_mat = scaler["scaler"].transform(np.vstack(X_rows))
    p_up = model.predict_proba(X_mat)[:, 1]
    proba = pd.Series(p_up, index=order, name="p_up")

    signals = generate_signals(
        date=target_date,
        universe_prices=frames,
        probabilities=proba,
        equity=200_000.0,
        cfg=SignalConfig(),
    )
    return signals


