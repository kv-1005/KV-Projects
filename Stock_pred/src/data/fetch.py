from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf


def fetch_ohlcv(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1d",
) -> pd.DataFrame:
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval, auto_adjust=True, progress=False)
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError(f"No data returned for ticker {ticker}")
    data = data.rename(columns=str.title)  # Ensure standardized columns
    data = data[[c for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in data.columns]]
    data = data.dropna().copy()
    data.index = pd.to_datetime(data.index)
    return data


