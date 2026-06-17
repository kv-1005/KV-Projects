import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces

class TradingEnv(gym.Env):
    """
    Institutional Trading Environment for Reinforcement Learning (PPO).
    """
    def __init__(self, df: pd.DataFrame, initial_balance: float = 200000, transaction_cost: float = 0.0013):
        super(TradingEnv, self).__init__()
        # Internal Data (Full DF for PnL/Price)
        self.full_df = df.copy()
        
        # Observation Data (Numeric Features only, exclude targets/meta)
        exclude = ["Open", "High", "Low", "Volume", "ticker", "target", "date", "Close_clean", "label", "regime"]
        self.obs_df = df.drop(columns=[c for c in exclude if c in df.columns]).select_dtypes(include=[np.number]).fillna(0.0)
        
        self.reward_range = (-np.inf, np.inf)
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        
        # Actions: 0=HOLD, 1=BUY, 2=SELL
        self.action_space = spaces.Discrete(3)
        
        # State: Features + Account Status (Current PnL, Position Side)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.obs_df.shape[1] + 2,), dtype=np.float32
        )
        
        self.reset()
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.current_step = 30 # Skip priming
        self.pos_side = 0 # 0=NONE, 1=LONG, -1=SHORT
        self.entry_price = 0.0
        self.total_pnl = 0.0
        return self._get_obs(), {}
        
    def _get_obs(self):
        obs = self.obs_df.iloc[self.current_step].values.astype(np.float32)
        # Append meta-state: [pos_side, pnl_pct]
        pnl_pct = 0.0
        if self.pos_side != 0:
            cur_price = float(self.full_df.iloc[self.current_step]["Close"])
            pnl_pct = (cur_price - self.entry_price) / (self.entry_price + 1e-12) * self.pos_side
            
        return np.append(obs, [float(self.pos_side), float(pnl_pct)]).astype(np.float32)
        
    def step(self, action):
        done = False
        truncated = False
        reward = 0.0
        
        # Current state
        cur_price = float(self.full_df.iloc[self.current_step]["Close"])
        
        # Logic: 0=HOLD, 1=BUY, 2=SELL
        if action == 1: # BUY
            if self.pos_side == -1: # Close Short
                pnl = (self.entry_price - cur_price) / self.entry_price - self.transaction_cost
                reward += pnl * 10 # Scale reward
                self.balance *= (1 + pnl)
                self.pos_side = 0
            if self.pos_side == 0: # Open Long
                self.pos_side = 1
                self.entry_price = cur_price
                reward -= self.transaction_cost # Entry cost penalty
                
        elif action == 2: # SELL
            if self.pos_side == 1: # Close Long
                pnl = (cur_price - self.entry_price) / self.entry_price - self.transaction_cost
                reward += pnl * 10
                self.balance *= (1 + pnl)
                self.pos_side = 0
            if self.pos_side == 0: # Open Short
                self.pos_side = -1
                self.entry_price = cur_price
                reward -= self.transaction_cost
                
        # Time progression
        self.current_step += 1
        if self.current_step >= len(self.obs_df) - 1:
            done = True
            # Mandatory square-off
            if self.pos_side != 0:
                pnl = (cur_price - self.entry_price) / (self.entry_price + 1e-12) * self.pos_side - self.transaction_cost
                reward += pnl * 10
            
        return self._get_obs(), reward, done, truncated, {}
