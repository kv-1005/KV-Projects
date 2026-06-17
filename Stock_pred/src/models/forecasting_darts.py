import os
import pandas as pd
import numpy as np
from darts import TimeSeries
import joblib
from darts.models import NBEATSModel, NHiTSModel, TFTModel, AutoARIMA
from darts.dataprocessing.transformers import Scaler

def train_darts_models(df: pd.DataFrame, ticker: str, save_dir: str = "artifacts"):
    """
    Train Darts-based forecasting models (N-BEATS, N-HiTS).
    """
    # Filter for single ticker
    ticker_df = df[df["ticker"] == ticker].copy()
    if len(ticker_df) < 500: return {}
    
    # Target: Future returns (r_1)
    # Use RangeIndex to avoid frequency issues with market gaps
    ticker_df = ticker_df.reset_index(drop=True)
    series = TimeSeries.from_dataframe(
        ticker_df, 
        value_cols="r_1"
    )
    
    # Scale the series to prevent NaN loss in neural networks
    scaler = Scaler()
    series_sc = scaler.fit_transform(series)
    joblib.dump(scaler, os.path.join(save_dir, f"scaler_{ticker}.joblib"))
    
    # N-BEATS Model
    nbeats = NBEATSModel(
        input_chunk_length=30,
        output_chunk_length=5,
        n_epochs=5,
        random_state=42,
        pl_trainer_kwargs={"accelerator": "cpu"}
    )
    print(f"[Darts] Training N-BEATS for {ticker}...")
    nbeats.fit(series_sc)
    nbeats.save(os.path.join(save_dir, f"nbeats_{ticker}.pkl"))
    
    # N-HiTS Model
    nhits = NHiTSModel(
        input_chunk_length=30,
        output_chunk_length=5,
        n_epochs=5,
        random_state=42,
        pl_trainer_kwargs={"accelerator": "cpu"}
    )
    print(f"[Darts] Training N-HiTS for {ticker}...")
    nhits.fit(series_sc)
    nhits.save(os.path.join(save_dir, f"nhits_{ticker}.pkl"))
    
    # 3. Classical Baseline (AutoARIMA)
    try:
        print(f"[Darts] Training AutoARIMA for {ticker}...")
        arima = AutoARIMA()
        arima.fit(series_sc)
        arima.save(os.path.join(save_dir, f"arima_{ticker}.pkl"))
    except Exception as e:
        print(f"[Darts] AutoARIMA failed for {ticker}: {e}")

    return {"nbeats_status": "done", "nhits_status": "done", "arima_status": "done"}
