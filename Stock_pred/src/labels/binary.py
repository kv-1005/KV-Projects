from __future__ import annotations

import numpy as np
import pandas as pd


def make_binary_label(df: pd.DataFrame, horizon_days: int = 1, delta_threshold: float = 0.002) -> pd.Series:
    """
    y_t = 1 if (close_{t+H} / close_t - 1) >= Δ else 0
    Preserve NaN where future price is unknown (last H rows).
    """
    close = df["Close"].astype(float)
    future = close.shift(-horizon_days)
    ret = (future / (close + 1e-12)) - 1.0
    y = (ret >= float(delta_threshold)).astype(float)
    y[ret.isna()] = np.nan
    y.name = f"y_bin_h{horizon_days}_d{delta_threshold}"
    return y


