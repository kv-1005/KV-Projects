"""
Intraday Feature Engineering for NSE 5-Minute Candles
-------------------------------------------------------
Adds VWAP, Supertrend, session features, and candle patterns
on top of existing core indicators.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands

from src.features.regime import add_regime_features


# ── Helpers ───────────────────────────────────────────────────────────────────

def _s(df: pd.DataFrame, col: str) -> pd.Series:
    """Safe 1-D Series extractor (avoids 2-D MultiIndex columns)."""
    if col not in df.columns:
        return pd.Series(dtype=float, index=df.index)
    obj = df[col]
    if isinstance(obj, pd.DataFrame):
        return obj.iloc[:, 0].astype(float)
    return pd.Series(obj, index=df.index).astype(float)


# ── VWAP ─────────────────────────────────────────────────────────────────────

def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Volume Weighted Average Price, reset every trading session (9:15 AM).
    Requires DatetimeIndex with timezone info (Asia/Kolkata).
    """
    close  = _s(df, "Close")
    high   = _s(df, "High")
    low    = _s(df, "Low")
    volume = _s(df, "Volume")

    typical = (high + low + close) / 3.0
    tpv     = typical * volume

    # Group by trading date to reset VWAP each session
    idx = df.index
    if hasattr(idx, "date"):
        date_key = pd.Series(idx.date, index=idx)
    else:
        date_key = pd.Series(idx.normalize(), index=idx)

    cum_tpv = tpv.groupby(date_key).cumsum()
    cum_vol = volume.groupby(date_key).cumsum()
    df = df.copy()
    df["vwap"] = cum_tpv / (cum_vol + 1e-12)
    df["above_vwap"] = (close > df["vwap"]).astype(int)
    df["vwap_dist_pct"] = (close - df["vwap"]) / (df["vwap"] + 1e-12)
    return df


# ── Supertrend ────────────────────────────────────────────────────────────────

def add_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """
    Supertrend indicator — bullish (1) / bearish (-1) trend direction.
    """
    close = _s(df, "Close")
    high  = _s(df, "High")
    low   = _s(df, "Low")
    atr   = AverageTrueRange(high=high, low=low, close=close, window=period).average_true_range()
    hl2   = (high + low) / 2.0

    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    supertrend = pd.Series(np.nan, index=df.index)
    direction  = pd.Series(1, index=df.index)

    for i in range(1, len(df)):
        prev_upper = upper_band.iloc[i - 1]
        prev_lower = lower_band.iloc[i - 1]
        prev_close = close.iloc[i - 1]
        prev_dir   = direction.iloc[i - 1]

        # Adjust bands
        cur_upper = upper_band.iloc[i]
        cur_lower = lower_band.iloc[i]
        if cur_upper > prev_upper or prev_close < prev_upper:
            upper_band.iloc[i] = cur_upper
        else:
            upper_band.iloc[i] = prev_upper

        if cur_lower < prev_lower or prev_close > prev_lower:
            lower_band.iloc[i] = cur_lower
        else:
            lower_band.iloc[i] = prev_lower

        # Direction
        if prev_dir == -1 and close.iloc[i] > upper_band.iloc[i]:
            direction.iloc[i] = 1
        elif prev_dir == 1 and close.iloc[i] < lower_band.iloc[i]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = prev_dir

        supertrend.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]

    df = df.copy()
    df["supertrend"]     = supertrend
    df["supertrend_dir"] = direction   # 1 = bullish, -1 = bearish
    return df


# ── Session / Time Features ───────────────────────────────────────────────────

def add_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Time-of-day features relevant for intraday trading.
    Columns: minutes_since_open, first_30min_high, first_30min_low, session_phase
    """
    df = df.copy()
    idx = df.index

    # Minutes since market open (9:15 IST)
    open_minutes = 9 * 60 + 15
    if hasattr(idx, "hour"):
        df["min_since_open"] = (idx.hour * 60 + idx.minute) - open_minutes
    else:
        df["min_since_open"] = 0

    # Session phase: 0=opening(0-30min), 1=mid(30-180min), 2=closing(>180min)
    df["session_phase"] = pd.cut(
        df["min_since_open"],
        bins=[-1, 30, 180, 400],
        labels=[0, 1, 2],
    ).astype(float)

    # Rolling first-30-min high/low (anchored to each date)
    close = _s(df, "Close")
    if hasattr(idx, "date"):
        date_key = pd.Series(idx.date, index=idx)
        # Only include candles in first 30 minutes
        is_first_30 = df["min_since_open"] <= 30
        df["first30_high"] = close.where(is_first_30).groupby(date_key).transform("max")
        df["first30_low"]  = close.where(is_first_30).groupby(date_key).transform("min")
        df["above_first30_high"] = (close > df["first30_high"]).astype(int)
        df["below_first30_low"]  = (close < df["first30_low"]).astype(int)

    return df


# ── Candle Pattern Flags ──────────────────────────────────────────────────────

def add_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Simple candle pattern binary flags."""
    df = df.copy()
    o = _s(df, "Open")
    h = _s(df, "High")
    l = _s(df, "Low")
    c = _s(df, "Close")

    body   = (c - o).abs()
    candle = h - l
    upper_wick = h - c.where(c > o, other=o)
    lower_wick = c.where(c < o, other=o) - l

    # Doji: tiny body relative to candle range
    df["is_doji"] = (body < 0.1 * candle).astype(int)

    # Hammer: small body at top, long lower wick
    df["is_hammer"] = (
        (body < 0.3 * candle) &
        (lower_wick > 2 * body) &
        (upper_wick < body)
    ).astype(int)

    # Bullish engulfing
    prev_c = c.shift(1)
    prev_o = o.shift(1)
    df["is_bull_engulf"] = (
        (prev_c < prev_o) &   # previous was bearish
        (c > o) &             # current is bullish
        (o < prev_c) &
        (c > prev_o)
    ).astype(int)

    # Bearish engulfing
    df["is_bear_engulf"] = (
        (prev_c > prev_o) &   # previous was bullish
        (c < o) &             # current is bearish
        (o > prev_c) &
        (c < prev_o)
    ).astype(int)

    return df


# ── Core Indicators (existing pipeline-compatible) ────────────────────────────

def add_core_features(df: pd.DataFrame) -> pd.DataFrame:
    """Standard indicators matching the original pipeline + intraday additions."""
    data = df.copy()
    # Use Wavelet Denoised Close for all secondary calculations
    close  = _s(data, "Close_clean") if "Close_clean" in data.columns else _s(data, "Close")
    raw_close = _s(data, "Close")
    high   = _s(data, "High")
    low    = _s(data, "Low")
    volume = _s(data, "Volume")

    # Returns (Always use RAW Close for PnL-based features)
    data["r_1"]  = raw_close.pct_change().fillna(0.0)
    data["lr_1"] = np.log(raw_close).diff().fillna(0.0)

    # Moving averages
    for w in [5, 10, 20, 50]:
        data[f"ma_{w}"] = SMAIndicator(close=close, window=w).sma_indicator()
    for w in [9, 21, 200]:
        data[f"ema_{w}"] = EMAIndicator(close=close, window=w).ema_indicator()

    # Momentum
    for n in [3, 5, 10]:
        data[f"mom_{n}"] = close.diff(n)

    # Volatility
    for w in [5, 10, 20]:
        data[f"vol_{w}"] = close.pct_change().rolling(w).std()

    # Bollinger Bands & Width
    bb = BollingerBands(close=close, window=20, window_dev=2)
    data["bb_upper"] = bb.bollinger_hband()
    data["bb_lower"] = bb.bollinger_lband()
    data["bb_mid"]   = bb.bollinger_mavg()
    data["bb_pct"]   = bb.bollinger_pband()
    data["bb_width"] = (data["bb_upper"] - data["bb_lower"]) / (data["bb_mid"] + 1e-12)

    # RSI, MACD, Stochastic, ATR
    data["rsi14"] = RSIIndicator(close=close, window=14).rsi()
    macd = MACD(close=close, window_fast=12, window_slow=26, window_sign=9)
    data["macd"]        = macd.macd()
    data["macd_signal"] = macd.macd_signal()
    data["macd_hist"]   = macd.macd_diff()
    stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
    data["stoch_k"] = stoch.stoch()
    data["stoch_d"] = stoch.stoch_signal()
    atr = AverageTrueRange(high=high, low=low, close=close, window=14)
    data["atr14"] = atr.average_true_range()

    # Volume & OI
    data["vol_ma_5"]  = volume.rolling(5).mean()
    data["vol_ratio"] = volume / (data["vol_ma_5"] + 1e-12)
    
    if "OI" in data.columns:
        data["oi_delta"] = data["OI"].diff().fillna(0.0)
        data["oi_ma_5"]  = data["OI"].rolling(5).mean()
    else:
        data["oi_delta"] = 0.0
        data["oi_ma_5"]  = 0.0

    # Institutional Volatility Kernel (Parkinson)
    # Parkinson = sqrt(1/(4*n*ln(2)) * sum(ln(High/Low)^2))
    hl_ratio_sq = np.log(high / (low + 1e-12))**2
    data["vol_parkinson"] = np.sqrt((1 / (4 * np.log(2))) * hl_ratio_sq.rolling(20).mean())

    # Lagged returns
    for k in range(1, 6):
        data[f"r_lag_{k}"] = data["r_1"].shift(k)

    return data


def denoise_series(series: pd.Series, wavelet: str = "haar", level: int = 1) -> pd.Series:
    """Wavelet Denoising: Filters high-frequency noise from price series."""
    import pywt
    coeffs = pywt.wavedec(series, wavelet, mode="per")
    # Soft thresholding on detail coefficients
    sigma  = np.median(np.abs(coeffs[-level])) / 0.6745
    uthresh = sigma * np.sqrt(2 * np.log(len(series)))
    coeffs[1:] = [pywt.threshold(c, value=uthresh, mode="soft") for c in coeffs[1:]]
    return pd.Series(pywt.waverec(coeffs, wavelet, mode="per")[:len(series)], index=series.index)


# ── Master Pipeline ───────────────────────────────────────────────────────────

def build_intraday_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full feature engineering pipeline for intraday NSE data.
    Runs all feature additions in order and returns a clean DataFrame.
    """
    data = df.copy()
    # Apply Research-Grade Wavelet Denoising to 'Close'
    data["Close_clean"] = denoise_series(data["Close"])
    
    # Run pipelines with denoised base
    data = add_core_features(data)
    data = add_vwap(data)
    data = add_supertrend(data)
    data = add_session_features(data)
    data = add_candle_patterns(data)
    data = add_regime_features(data)
    return data.dropna().copy()
