from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

from src.data.sentiment import fetch_headline_sentiment_series
from src.utils.config import FeatureConfig


@dataclass
class Scalers:
    feature_scaler: StandardScaler
    target_scaler: MinMaxScaler


def add_technical_indicators(df: pd.DataFrame, cfg: FeatureConfig) -> pd.DataFrame:
    data = df.copy()

    # Ensure 1-D Series inputs
    def s(col: str) -> pd.Series:
        if col not in data.columns:
            return pd.Series(dtype=float, index=data.index)
        obj = data[col]
        if isinstance(obj, pd.DataFrame):
            if obj.shape[1] == 1:
                return obj.iloc[:, 0].astype(float)
            return obj.iloc[:, 0].astype(float)
        return pd.Series(obj, index=data.index, name=col).astype(float)

    close = s("Close")
    high = s("High")
    low = s("Low")

    if cfg.use_technical_indicators:
        rsi = RSIIndicator(close=close, window=cfg.rsi_period).rsi()
        macd = MACD(close=close, window_fast=cfg.macd_fast, window_slow=cfg.macd_slow, window_sign=cfg.macd_signal)
        bb = BollingerBands(close=close, window=cfg.bb_window, window_dev=cfg.bb_std)

        data["rsi"] = rsi
        data["macd"] = macd.macd()
        data["macd_signal"] = macd.macd_signal()
        data["macd_hist"] = macd.macd_diff()
        data["bb_high"] = bb.bollinger_hband()
        data["bb_low"] = bb.bollinger_lband()
        data["bb_width"] = (data["bb_high"] - data["bb_low"]) / (close + 1e-12)

        data["sma_5"] = SMAIndicator(close=close, window=cfg.sma_short).sma_indicator()
        data["sma_20"] = SMAIndicator(close=close, window=cfg.sma_medium).sma_indicator()
        data["sma_50"] = SMAIndicator(close=close, window=cfg.sma_long).sma_indicator()
        data["sma_200"] = SMAIndicator(close=close, window=cfg.sma_very_long).sma_indicator()

        # Normalize moving averages by price to stabilize scale
        for col in ["sma_5", "sma_20", "sma_50", "sma_200"]:
            data[f"{col}_pct"] = (data[col] - close) / (close + 1e-12)

    data = data.dropna().copy()
    return data


def build_feature_frame(
    raw: pd.DataFrame,
    ticker: str,
    feature_cfg: FeatureConfig,
) -> pd.DataFrame:
    df = add_technical_indicators(raw, feature_cfg)

    if feature_cfg.use_sentiment:
        sent = fetch_headline_sentiment_series(ticker=ticker, index_dates=df.index)
        df = df.join(sent, how="left").fillna(0.0)

    # Core price-derived features
    df["return_1d"] = close.pct_change().fillna(0.0)
    df["range_ratio"] = (high - low) / (close + 1e-12)
    df = df.dropna().copy()
    return df


def train_val_test_split(
    df: pd.DataFrame,
    test_ratio: float,
    val_ratio: float,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    n = len(df)
    n_test = int(n * test_ratio)
    n_val = int((n - n_test) * val_ratio)
    train = df.iloc[: n - n_test - n_val]
    val = df.iloc[n - n_test - n_val : n - n_test]
    test = df.iloc[n - n_test :]
    return train, val, test


def scale_and_sequence(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    target_col: str,
    sequence_length: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, Scalers, list[str]]:
    feature_cols = [c for c in train.columns if c not in ["Adj Close"]]

    feature_scaler = StandardScaler()
    target_scaler = MinMaxScaler()

    X_train_raw = train[feature_cols].values
    X_val_raw = val[feature_cols].values
    X_test_raw = test[feature_cols].values

    y_train_raw = train[[target_col]].values
    y_val_raw = val[[target_col]].values
    y_test_raw = test[[target_col]].values

    X_train = feature_scaler.fit_transform(X_train_raw)
    X_val = feature_scaler.transform(X_val_raw)
    X_test = feature_scaler.transform(X_test_raw)

    y_train = target_scaler.fit_transform(y_train_raw)
    y_val = target_scaler.transform(y_val_raw)
    y_test = target_scaler.transform(y_test_raw)

    def make_sequences(X: np.ndarray, y: np.ndarray, seq_len: int) -> Tuple[np.ndarray, np.ndarray]:
        X_seq, y_seq = [], []
        for i in range(seq_len, len(X)):
            X_seq.append(X[i - seq_len : i])
            y_seq.append(y[i])
        return np.array(X_seq, dtype=np.float32), np.array(y_seq, dtype=np.float32)

    X_tr, y_tr = make_sequences(X_train, y_train, sequence_length)
    X_v, y_v = make_sequences(X_val, y_val, sequence_length)
    X_te, y_te = make_sequences(X_test, y_test, sequence_length)

    scalers = Scalers(feature_scaler=feature_scaler, target_scaler=target_scaler)
    return X_tr, y_tr, X_v, y_v, X_te, y_te, scalers, feature_cols


