import os
import json
import pandas as pd
from src.data.fyers_fetch import fetch_intraday_fyers
from src.features.engineering import build_intraday_features
from src.models.intraday_predictor import IntradayPredictor
import numpy as np

def run_debug():
    with open("config/nse_intraday.json") as f:
        cfg = json.load(f)

    ticker = "TCS"
    print(f"Fetching 2 days data for {ticker}...")
    df = fetch_intraday_fyers(ticker, interval=cfg["interval"], days_back=2)
    df = build_intraday_features(df)
    
    data_map = {ticker: df}
    predictor = IntradayPredictor(save_dir="artifacts")
    print(f"Data rows: {len(df)}")
    
    results = predictor.batch_predict(data_map, expectancy_threshold=1.2)
    
    holds = 0
    buys = 0
    sells = 0
    max_exp = 0
    min_exp = 0
    
    for (ts, t), res in results.items():
        if res.signal == "HOLD": holds += 1
        elif res.signal == "BUY": buys += 1
        elif res.signal == "SELL": sells += 1
        max_exp = max(max_exp, res.expectancy_ratio)
        min_exp = min(min_exp, res.expectancy_ratio)
    
    print(f"HOLDs: {holds}, BUYs: {buys}, SELLs: {sells}")
    print(f"Max Exp: {max_exp}, Min Exp: {min_exp}")
    
    X_lstm_base = df.reindex(columns=predictor._lstm_cols, fill_value=0.0).values
    X_lstm_sc   = predictor._lstm_scaler.transform(X_lstm_base)
    
    sequences = [X_lstm_sc[i - predictor._seq_length : i] for i in range(predictor._seq_length, len(df) + 1)]
    lstm_p_raw = predictor._lstm_model(np.array(sequences, dtype=np.float32), training=False).numpy().flatten()
    print(f"Max LSTM pred: {lstm_p_raw.max():.6f}, Min LSTM pred: {lstm_p_raw.min():.6f}")

if __name__ == "__main__":
    run_debug()
