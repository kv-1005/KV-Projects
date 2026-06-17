import os
import pandas as pd
import numpy as np
from darts import TimeSeries
import joblib
from darts.models import TFTModel
from darts.dataprocessing.transformers import Scaler

def train_tft_model(df: pd.DataFrame, ticker: str, save_dir: str = "artifacts"):
    """
    Train Temporal Fusion Transformer (TFT) with multi-variate covariates.
    """
    ticker_df = df[df["ticker"] == ticker].copy()
    if len(ticker_df) < 500: return {}
    
    # Target: Future returns (r_1)
    # Use RangeIndex to avoid frequency issues with market gaps
    ticker_df = ticker_df.reset_index(drop=True)
    series = TimeSeries.from_dataframe(
        ticker_df, 
        value_cols="r_1"
    )
    
    # Past Covariates: Volume, RSI, EMA, ATR
    cov_cols = ["Volume", "rsi_14", "ema_50", "atr14"]
    cov_cols = [c for c in cov_cols if c in ticker_df.columns]
    
    past_covariates = None
    if cov_cols:
        past_covariates = TimeSeries.from_dataframe(
            ticker_df,
            value_cols=cov_cols
        )
    
    # Scale both target and covariates
    scaler = Scaler()
    series_sc = scaler.fit_transform(series)
    
    past_cov_sc = None
    if past_covariates:
        cov_scaler = Scaler()
        past_cov_sc = cov_scaler.fit_transform(past_covariates)
        joblib.dump(cov_scaler, os.path.join(save_dir, f"cov_scaler_{ticker}.joblib"))
    
    joblib.dump(scaler, os.path.join(save_dir, f"scaler_{ticker}.joblib"))
    
    tft = TFTModel(
        input_chunk_length=60,
        output_chunk_length=12,
        hidden_size=32,
        lstm_layers=1,
        num_attention_heads=4,
        dropout=0.1,
        batch_size=32,
        n_epochs=5,
        add_relative_index=True,
        random_state=42,
        pl_trainer_kwargs={"accelerator": "cpu"}
    )
    
    print(f"[TFT] Training Temporal Fusion Transformer (Multi-Variate) for {ticker}...")
    tft.fit(series_sc, past_covariates=past_cov_sc)
    tft.save(os.path.join(save_dir, f"tft_{ticker}.pkl"))
    
    return {"tft_status": "done"}

