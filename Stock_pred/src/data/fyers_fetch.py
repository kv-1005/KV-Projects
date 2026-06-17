"""
Fyers Historical & Live Data Fetcher
-------------------------------------
Replaces yfinance for NSE intraday data.
- Fetches OHLCV candles via Fyers History API (up to 366 days of 1min data)
- Fetches live quotes via fyersModel.quotes()
- Normalises columns to match the rest of the pipeline: Open/High/Low/Close/Volume
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Literal

import pandas as pd

from src.data.fyers_client import get_fyers_client


# Fyers interval strings → minutes mapping
INTERVAL_MAP: dict[str, str] = {
    "1minute":   "1",
    "2minute":   "2",
    "3minute":   "3",
    "5minute":   "5",
    "10minute":  "10",
    "15minute":  "15",
    "20minute":  "20",
    "30minute":  "30",
    "60minute":  "60",
    "1day":      "D",
}

# Max days Fyers allows per interval
MAX_DAYS: dict[str, int] = {
    "1":  30,   # 1-minute  → 30 days max per request
    "2":  60,
    "3":  60,
    "5":  100,
    "10": 100,
    "15": 180,
    "20": 180,
    "30": 366,
    "60": 366,
    "D":  3650,
}


def _nse_symbol(ticker: str) -> str:
    """Convert bare ticker (e.g. 'RELIANCE') to Fyers format 'NSE:RELIANCE-EQ'."""
    ticker = ticker.upper().strip()
    if ":" in ticker:
        return ticker          # already formatted
    return f"NSE:{ticker}-EQ"


def fetch_intraday_fyers(
    ticker: str,
    interval: str = "5minute",
    days_back: int = 365,
) -> pd.DataFrame:
    """
    Fetch OHLCV intraday/daily candles from Fyers History API.

    Parameters
    ----------
    ticker    : NSE symbol, e.g. 'RELIANCE' or 'NSE:RELIANCE-EQ'
    interval  : One of INTERVAL_MAP keys ('1minute', '5minute', '1day', ...)
    days_back : How many calendar days of history to fetch (≤ MAX_DAYS[interval])

    Returns
    -------
    pd.DataFrame with DatetimeIndex (IST) and columns: Open, High, Low, Close, Volume
    """
    fyers = get_fyers_client()
    sym = _nse_symbol(ticker)
    iv_code = INTERVAL_MAP.get(interval, "5")
    max_per_req = MAX_DAYS.get(iv_code, 30)

    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=days_back)

    # Chunk requests to respect per-request day limits
    frames: list[pd.DataFrame] = []
    chunk_end = end_dt

    while chunk_end > start_dt:
        chunk_start = max(chunk_end - timedelta(days=max_per_req), start_dt)
        data_params = {
            "symbol":      sym,
            "resolution":  iv_code,
            "date_format": "1",   # Unix timestamp
            "range_from":  chunk_start.strftime("%Y-%m-%d"),
            "range_to":    chunk_end.strftime("%Y-%m-%d"),
            "cont_flag":   "1",
        }
        response = fyers.history(data=data_params)
        if response.get("code") == 200 and response.get("candles"):
            df = pd.DataFrame(
                response["candles"],
                columns=["timestamp", "Open", "High", "Low", "Close", "Volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            df["timestamp"] = df["timestamp"].dt.tz_convert("Asia/Kolkata")
            df = df.set_index("timestamp")
            frames.append(df)
        else:
            # Add explicit logging for debugging
            from src.utils.logging_config import get_logger
            log = get_logger("fyers_fetch")
            log.error(f"[Fyers] API Error for {ticker}: Code={response.get('code')} Msg={response.get('message') or 'No candles'}")

        chunk_end = chunk_start - timedelta(days=1)
        time.sleep(0.35)   # respect rate limit: 3 req/sec

    if not frames:
        raise ValueError(f"No data returned for {ticker} ({interval})")

    result = (
        pd.concat(frames)
        .sort_index()
        .drop_duplicates()
        [["Open", "High", "Low", "Close", "Volume"]]
    )
    result.index.name = "datetime"
    return result


def fetch_live_quote_fyers(tickers: list[str]) -> dict[str, float]:
    """
    Fetch last traded price (LTP) for a list of tickers.

    Returns
    -------
    dict mapping ticker → LTP (float)
    """
    fyers = get_fyers_client()
    symbols = ",".join(_nse_symbol(t) for t in tickers)
    response = fyers.quotes(data={"symbols": symbols})
    ltp_map: dict[str, float] = {}
    if response.get("code") == 200:
        for item in response.get("d", []):
            sym_raw = item.get("n", "")              # e.g. 'NSE:RELIANCE-EQ'
            ltp = item.get("v", {}).get("lp", 0.0)  # last price
            # extract bare ticker
            bare = sym_raw.split(":")[1].replace("-EQ", "")
            ltp_map[bare] = float(ltp)
    return ltp_map
