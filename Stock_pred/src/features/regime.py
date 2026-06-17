"""
Market Regime Detection Module
------------------------------
Classifies the current market phase to allow the Meta-Model to contextualize signals.
Institutional systems know that a breakout signal in a 'Volatility Compression' 
regime is highly valuable, whereas the same signal in 'Ranging' is likely a trap.

Regimes Identified:
1. TREND_UP:       Strong positive direction.
2. TREND_DOWN:     Strong negative direction.
3. RANGING:        Low directional momentum, normal volatility.
4. VOL_EXPANSION:  Sudden increase in price variance (chaotic/news).
5. VOL_COMPRESSION: Tight consolidation, low variance (often precedes breakouts).
"""

from typing import Literal

import numpy as np
import pandas as pd
import ta


RegimeType = Literal[
    "TREND_UP", "TREND_DOWN", "RANGING", "VOL_EXPANSION", "VOL_COMPRESSION"
]


def add_regime_features(df: pd.DataFrame, adx_window: int = 14, atr_window: int = 14) -> pd.DataFrame:
    """
    Computes Advanced Directional Index (ADX) and Average True Range (ATR) ratios
    to classify each candle into a distinct Market Regime.
    """
    df = df.copy()

    # 1. ADX for Trend Strength
    try:
        adx_ind = ta.trend.ADXIndicator(
            high=df["High"], low=df["Low"], close=df["Close"], window=adx_window, fillna=True
        )
        df["adx"] = adx_ind.adx()
        df["plus_di"] = adx_ind.adx_pos()
        df["minus_di"] = adx_ind.adx_neg()
    except Exception:
        df["adx"] = 0.0
        df["plus_di"] = 0.0
        df["minus_di"] = 0.0

    # 2. ATR for Volatility States
    try:
        atr_ind = ta.volatility.AverageTrueRange(
            high=df["High"], low=df["Low"], close=df["Close"], window=atr_window, fillna=True
        )
        df["atr"] = atr_ind.average_true_range()
    except Exception:
        df["atr"] = df["Close"] * 0.005  # fallback

    # Volatility Ratio: Current ATR vs 50-period SMA of ATR
    df["atr_sma_50"] = df["atr"].rolling(window=50, min_periods=1).mean()
    df["vol_ratio"] = np.where(df["atr_sma_50"] > 0, df["atr"] / df["atr_sma_50"], 1.0)

    # 3. Regime Classification Logic
    def classify(row: pd.Series) -> str:
        vol_ratio = row["vol_ratio"]
        adx       = row["adx"]
        p_di      = row["plus_di"]
        m_di      = row["minus_di"]

        # Volatility overrides trend if extreme (chaos or extreme compression)
        if vol_ratio > 1.5:
            return "VOL_EXPANSION"
        
        if vol_ratio < 0.6:
            return "VOL_COMPRESSION"

        # Trend Logic
        if adx > 25:
            if p_di > m_di:
                return "TREND_UP"
            else:
                return "TREND_DOWN"
                
        # If neither extreme volatility nor strong trend:
        return "RANGING"

    df["regime"] = df.apply(classify, axis=1)

    # One-hot encode the regimes so ML models can use them structurally
    regimes = ["TREND_UP", "TREND_DOWN", "RANGING", "VOL_EXPANSION", "VOL_COMPRESSION"]
    for r in regimes:
        df[f"regime_{r}"] = (df["regime"] == r).astype(int)

    return df
