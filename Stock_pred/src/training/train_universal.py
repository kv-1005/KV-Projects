import os
import pandas as pd
import numpy as np
import joblib
import torch
from rich.console import Console

# Import all Phase 19 architectures
from src.training.train_intraday import train_intraday_model, IntradayTrainConfig
from src.training.train_lstm import train_lstm_model, LSTMTrainConfig
from src.models.rl_agent import train_rl_agent
from src.models.forecasting_darts import train_darts_models
from src.models.forecasting_tft import train_tft_model
from src.models.graph_net import train_graph_net
from src.models.autoencoder import train_autoencoder
from src.training.train_intraday import train_intraday_model, IntradayTrainConfig, get_feature_cols
from src.features.denoising_eemd import add_eemd_features

console = Console()

def train_universal_ensemble(df: pd.DataFrame, cfg: dict, artifacts: str = "artifacts"):
    """
    Orchestrates the training of the "Singularity V2" Universal Hyper-Ensemble.
    Models: XGB, RF, SVR, LSTM, PPO, N-BEATS, N-HiTS, TFT, GNN, Autoencoder.
    """
    os.makedirs(artifacts, exist_ok=True)
    
    # 1. High-Precision Denoising (EEMD)
    console.rule("[bold cyan] Step 1: EEMD Deep Denoising")
    df = add_eemd_features(df)
    
    # 2. Sequential/Latent Training (LSTM + Autoencoder)
    console.rule("[bold cyan] Step 2: Sequential & Latent Extraction")
    exclude = ["Open", "High", "Low", "Close", "Volume", "ticker", "Close_clean", "Close_eemd", "regime", "label", "target"]
    
    ae_path = os.path.join(artifacts, "feature_encoder.joblib")
    if not os.path.exists(ae_path):
        X_ae = df.drop(columns=[c for c in exclude if c in df.columns]).select_dtypes(include=[np.number]).fillna(0.0).values.astype(np.float32)
        encoder = train_autoencoder(X_ae, encoding_dim=16)
        joblib.dump(encoder, ae_path)
    else:
        console.print("[yellow]Skipping Autoencoder: Artifact exists.")
    
    lstm_path = os.path.join(artifacts, "lstm_intraday.keras")
    if not os.path.exists(lstm_path):
        lstm_cfg = LSTMTrainConfig(horizon_candles=cfg.get("horizon_candles", 6))
        train_lstm_model(df, cfg=lstm_cfg, save_dir=artifacts)
    else:
        console.print("[yellow]Skipping LSTM: Artifact exists.")

    # 3. Decision Optimization (Reinforcement Learning)
    console.rule("[bold cyan] Step 3: Reinforcement Learning (PPO)")
    rl_path = os.path.join(artifacts, "rl_ppo_agent.zip")
    if not os.path.exists(rl_path):
        train_rl_agent(df, save_path=rl_path)
    else:
        console.print("[yellow]Skipping RL Agent: Artifact exists.")

    # 4. Multi-Horizon Forecasting (Darts: N-BEATS, N-HiTS, TFT) - [LIGHTWEIGHT CALIBRATION]
    console.rule("[bold cyan] Step 4: Multi-Horizon Forecasts (Darts)")
    for ticker in cfg["universe"]:
        train_darts_models(df, ticker, save_dir=artifacts)
        train_tft_model(df, ticker, save_dir=artifacts)

    # 5. Relational Intelligence (Graph Neural Network)
    console.rule("[bold cyan] Step 5: Systemic Correlation (GNN)")
    # Group by timestamp to provide cross-ticker snapshots to GNN
    # For now, we train on the latest snapshot (Simplified for research-scale)
    tickers = cfg["universe"]
    ticker_feats = {}
    ticker_targets = {}
    gnn_cols = get_feature_cols(df)
    for t in tickers:
        t_df = df[df["ticker"] == t].tail(100) # Last 100 candles
        feats = t_df[gnn_cols].fillna(0.0).values
        ticker_feats[t] = feats
        ticker_targets[t] = t_df["r_1"].values.reshape(-1, 1) # Simple target for GNN
        
    gnn_model, edge_index = train_graph_net(ticker_feats, ticker_targets)
    torch.save(gnn_model.state_dict(), os.path.join(artifacts, "gnn_model.pth"))
    joblib.dump(edge_index, os.path.join(artifacts, "gnn_edges.joblib"))

    # 6. Primary Ensemble (XGB, RF, SVR)
    console.rule("[bold cyan] Step 6: Primary Institutional Ensemble")
    ml_cfg = IntradayTrainConfig(horizon_candles=cfg.get("horizon_candles", 6))
    train_intraday_model(df, cfg=ml_cfg, save_dir=artifacts)

    console.rule("[bold green] Universal Hyper-Ensemble Training Complete")
    return {"status": "Universal Singularity V2 Operational"}
