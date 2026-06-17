from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def fetch_headline_sentiment_series(
    ticker: str,
    index_dates: pd.DatetimeIndex,
    lookback_days: int = 7,
) -> pd.Series:
    """
    Fetch recent headlines using yfinance's news endpoint (if available), compute VADER compound scores,
    and aggregate into a daily sentiment series aligned with provided index_dates. Values are clipped to [-1, 1].
    """
    try:
        news = yf.Ticker(ticker).news or []
    except Exception:
        news = []

    analyzer = SentimentIntensityAnalyzer()

    # Build a DataFrame of headlines and dates
    rows = []
    for item in news:
        try:
            title = item.get("title") or ""
            provider_publish_time = item.get("providerPublishTime")
            if not title or provider_publish_time is None:
                continue
            dt = pd.to_datetime(provider_publish_time, unit="s").normalize()
            score = analyzer.polarity_scores(title).get("compound", 0.0)
            rows.append((dt, float(np.clip(score, -1.0, 1.0))))
        except Exception:
            continue

    if not rows:
        # Return neutral series if no headlines
        return pd.Series(0.0, index=index_dates, name="sentiment")

    df = pd.DataFrame(rows, columns=["date", "score"]).groupby("date").mean().sort_index()

    # Create daily series aligned to index_dates, fill 7-day rolling mean to smooth
    daily = df.reindex(pd.DatetimeIndex(index_dates).normalize()).fillna(0.0)
    daily["score"] = daily["score"].rolling(window=lookback_days, min_periods=1).mean()
    daily = daily["score"].clip(-1.0, 1.0)
    daily.name = "sentiment"
    return daily


