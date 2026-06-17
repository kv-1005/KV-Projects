from __future__ import annotations

import os
from dataclasses import asdict
from datetime import datetime
from typing import Dict

import numpy as np
from rich.console import Console

from src.data.fetch import fetch_ohlcv
from src.data.preprocess import Scalers, build_feature_frame, scale_and_sequence, train_val_test_split
from src.evaluation.backtest import evaluate_predictions
from src.models.cnn_lstm import build_cnn_lstm_model, default_callbacks
from src.utils.config import FeatureConfig, ModelConfig, TrainConfig
from src.utils.metrics import compute_core_regression_metrics
from src.utils.seed import set_global_seed


def run_training_pipeline(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    sequence_length: int = ModelConfig.sequence_length,
    max_epochs: int = ModelConfig.max_epochs,
    batch_size: int = ModelConfig.batch_size,
    learning_rate: float = ModelConfig.learning_rate,
    save_dir: str = "artifacts",
) -> Dict[str, float]:
    console = Console()
    set_global_seed(TrainConfig.random_seed)

    os.makedirs(save_dir, exist_ok=True)

    console.log("Fetching OHLCV data…")
    raw = fetch_ohlcv(ticker=ticker, start_date=start_date, end_date=end_date)

    feature_cfg = FeatureConfig()
    train_cfg = TrainConfig()
    model_cfg = ModelConfig(
        sequence_length=sequence_length,
        learning_rate=learning_rate,
        batch_size=batch_size,
        max_epochs=max_epochs,
    )

    console.log("Building features (indicators + sentiment)…")
    df = build_feature_frame(raw=raw, ticker=ticker, feature_cfg=feature_cfg)

    console.log("Splitting train/val/test…")
    train_df, val_df, test_df = train_val_test_split(
        df, test_ratio=train_cfg.test_size_ratio, val_ratio=train_cfg.validation_size_ratio
    )

    console.log("Scaling and building sequences…")
    X_tr, y_tr, X_v, y_v, X_te, y_te, scalers, feature_cols = scale_and_sequence(
        train=train_df,
        val=val_df,
        test=test_df,
        target_col=train_cfg.target_column,
        sequence_length=model_cfg.sequence_length,
    )

    console.log(f"Input shape: {X_tr.shape}, Features: {len(feature_cols)}")

    console.log("Constructing CNN-LSTM model…")
    model = build_cnn_lstm_model(
        input_shape=(X_tr.shape[1], X_tr.shape[2]),
        lstm_units_1=model_cfg.lstm_units_layer1,
        lstm_units_2=model_cfg.lstm_units_layer2,
        dropout_rate=model_cfg.dropout_rate,
        learning_rate=model_cfg.learning_rate,
    )

    ckpt_path = os.path.join(save_dir, f"{ticker}_cnn_lstm.keras")
    cbs = default_callbacks(save_path=ckpt_path, patience=model_cfg.early_stopping_patience)

    console.log("Training…")
    history = model.fit(
        X_tr,
        y_tr,
        validation_data=(X_v, y_v),
        epochs=model_cfg.max_epochs,
        batch_size=model_cfg.batch_size,
        verbose=1,
        callbacks=cbs,
    )

    console.log("Evaluating on test set…")
    y_pred_scaled = model.predict(X_te, verbose=0)

    y_true = scalers.target_scaler.inverse_transform(y_te).flatten()
    y_pred = scalers.target_scaler.inverse_transform(y_pred_scaled).flatten()

    metrics = evaluate_predictions(y_true=y_true, y_pred=y_pred)
    console.log(f"Metrics: {metrics}")

    return metrics


