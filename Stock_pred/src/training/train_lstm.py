"""
Deep Learning LSTM Trainer (Regression / Institutional)
-------------------------------------------------------
Trains a recurrent neural network (LSTM) on sequences of 5-minute candles to
predict Expected Net Return (R-multiple).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.training.train_intraday import get_feature_cols, make_labels

import tensorflow as tf
from tensorflow.keras.layers import (
    LSTM, Dense, Dropout, BatchNormalization, GaussianNoise, 
    MultiHeadAttention, LayerNormalization, Input
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau


@dataclass
class LSTMTrainConfig:
    seq_length: int          = 15         # 15 candles = 75 minutes of market memory
    horizon_candles: int     = 3
    transaction_cost: float  = 0.0013     # 0.13% estimated slippage + fees
    val_split: float         = 0.15       # last 15% of data used for validation
    batch_size: int          = 64
    epochs: int              = 30
    lstm_units_1: int        = 64
    lstm_units_2: int        = 32
    dropout_rate: float      = 0.3
    noise_std: float         = 0.005      # Anti-overfitting noise injection


def _create_sequences(
    X: np.ndarray, y: np.ndarray, seq_length: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Converts 2D tabular data into 3D (samples, time_steps, features) for LSTM."""
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_length):
        X_seq.append(X[i : i + seq_length])
        y_seq.append(y[i + seq_length - 1])
    return np.array(X_seq), np.array(y_seq)


def build_lstm_model(input_shape: Tuple[int, int], cfg: LSTMTrainConfig) -> tf.keras.Model:
    """Constructs the Attention-Enhanced Hybrid Architecture."""
    inputs = Input(shape=input_shape)
    x = GaussianNoise(cfg.noise_std)(inputs)
    
    # 1. Sequential Encoding
    x = LSTM(cfg.lstm_units_1, return_sequences=True)(x)
    x = Dropout(cfg.dropout_rate)(x)
    x = BatchNormalization()(x)
    
    # 2. Multi-Head Attention (The 'Transformer' Block)
    attn_output = MultiHeadAttention(num_heads=4, key_dim=cfg.lstm_units_1 // 4)(x, x)
    x = LayerNormalization(epsilon=1e-6)(x + attn_output)
    
    # 3. Final Compression
    x = LSTM(cfg.lstm_units_2, return_sequences=False)(x)
    x = Dropout(cfg.dropout_rate)(x)
    x = BatchNormalization()(x)
    
    x = Dense(32, activation="relu")(x)
    x = Dropout(cfg.dropout_rate / 2)(x)
    outputs = Dense(1, activation="linear")(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",
        metrics=["mae"]
    )
    return model


def train_lstm_model(
    df: pd.DataFrame,
    cfg: LSTMTrainConfig = LSTMTrainConfig(),
    save_dir: str = "artifacts",
) -> Dict[str, float]:
    """
    Trains the LSTM Regressor.
    """
    os.makedirs(save_dir, exist_ok=True)
    
    print("[LSTM] 🧠 Preparing sequences for Deep Learning (Regression)...")

    # Create targets (Net Expected Return)
    labels = make_labels(df, cfg.horizon_candles, cfg.transaction_cost)
    df = df.copy()
    df["label"] = labels
    df = df.dropna(subset=["label"])

    feature_cols = get_feature_cols(df)
    
    # Treat each ticker independently
    X_all, y_all = [], []
    
    from rich.progress import track
    
    grouped = df.groupby("ticker") if "ticker" in df.columns else [("ALL", df)]
    for _, group in track(grouped, description="[green]Creating LSTM sequences..."):
        X_group = group[feature_cols].values
        y_group = group["label"].values
        X_seq, y_seq = _create_sequences(X_group, y_group, cfg.seq_length)
        if len(X_seq) > 0:
            X_all.append(X_seq)
            y_all.append(y_seq)
            
    if not X_all:
        raise ValueError("No sequences could be created. Not enough data.")
        
    X_3d = np.vstack(X_all)
    y_1d = np.concatenate(y_all)
    
    # Scale data
    samples, steps, features = X_3d.shape
    X_flat = X_3d.reshape(-1, features)
    
    scaler = StandardScaler()
    X_flat_sc = scaler.fit_transform(X_flat)
    X_3d_sc = X_flat_sc.reshape(samples, steps, features)
    
    # Temporal train/val split
    split_idx = int(len(X_3d_sc) * (1 - cfg.val_split))
    X_train, y_train = X_3d_sc[:split_idx], y_1d[:split_idx]
    X_val, y_val     = X_3d_sc[split_idx:], y_1d[split_idx:]
    
    # Callbacks
    early_stop = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
    reduce_lr  = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-5)
    
    print(f"[LSTM] 🚀 Training LSTM Regressor ({len(X_train)} train seqs, {len(X_val)} val seqs)...")
    
    model = build_lstm_model((cfg.seq_length, len(feature_cols)), cfg)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        batch_size=cfg.batch_size,
        epochs=cfg.epochs,
        callbacks=[early_stop, reduce_lr],
        verbose=0
    )
    
    # Evaluate
    val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
    
    # Save artifacts
    model_path = os.path.join(save_dir, "lstm_intraday.keras")
    model.save(model_path)
    
    joblib.dump(
        {"scaler": scaler, "columns": feature_cols, "seq_length": cfg.seq_length},
        os.path.join(save_dir, "lstm_intraday_scaler.joblib"),
    )
    print(f"[LSTM] ✅ Model saved to {model_path}")
    
    return {
        "val_rmse": float(np.sqrt(val_loss)),
        "val_mae": float(val_mae)
    }
