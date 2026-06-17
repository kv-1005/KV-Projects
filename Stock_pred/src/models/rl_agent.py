import os
import pandas as pd
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from src.models.rl_env import TradingEnv

def train_rl_agent(df: pd.DataFrame, save_path: str = "artifacts/rl_ppo_agent.zip"):
    """
    Train a PPO (Proximal Policy Optimization) agent for the Trading System.
    """
    # Create Env (Env handles its own feature selection)
    env = DummyVecEnv([lambda: TradingEnv(df)])
    
    # Policy architecture: 256x256 MlpPolicy
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1, 
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01
    )
    
    print(f"[RL] Training PPO Agent for {len(df)} steps...")
    model.learn(total_timesteps=50000) # Quick research cycle
    
    model.save(save_path)
    print(f"[RL] ✅ Model saved to {save_path}")
    return model

def load_rl_agent(path: str = "artifacts/rl_ppo_agent.zip"):
    """Load the trained RL model."""
    if os.path.exists(path):
        return PPO.load(path)
    return None
