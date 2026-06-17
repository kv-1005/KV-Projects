import pandas as pd
import os
from datetime import datetime

def deep_research():
    path = "artifacts/trade_log.csv"
    if not os.path.exists(path): 
        print("Log not found")
        return
    
    # 0,action,ticker,qty,price,pnl,reason,order_id,mode,sharpe,dd
    df = pd.read_csv(path, header=None)
    
    # Filter for EXITS
    exits = df[df[1] == 'EXIT'].copy()
    exits[5] = pd.to_numeric(exits[5], errors='coerce')
    exits[0] = pd.to_datetime(exits[0])
    
    # 1. Temporal Analysis (Hour of Day)
    exits['hour'] = exits[0].dt.hour
    hourly_pnl = exits.groupby('hour')[5].agg(['sum', 'count'])
    
    # 2. Daily Analysis (Weekdays)
    exits['weekday'] = exits[0].dt.day_name()
    daily_pnl = exits.groupby('weekday')[5].agg(['sum', 'count'])
    
    # 3. Ticker Efficiency (PnL per Trade)
    ticker_efficiency = exits.groupby(2)[5].mean().sort_values()
    
    # 4. Successive Losses
    exits['is_win'] = exits[5] > 0
    # streak calculation
    streaks = (exits['is_win'] != exits['is_win'].shift()).cumsum()
    streak_counts = exits.groupby(streaks)['is_win'].count()
    max_loss_streak = streak_counts[exits.groupby(streaks)['is_win'].first() == False].max()

    print("=== DEEP RESEARCH: TEMPORAL ALPHA ===")
    print("\n[HOURLY PNL]")
    print(hourly_pnl)
    
    print("\n[DAILY PNL]")
    print(daily_pnl)
    
    print("\n[TICKER AVG PNL (EFFICIENCY)]")
    print(ticker_efficiency)
    
    print(f"\n[MAX LOSS STREAK]: {max_loss_streak}")
    
    # Threshold for Alpha Filter: 
    # If 9:00 AM - 10:00 AM is toxic (high vol noise), we should block it.
    # If 3:00 PM+ is toxic (EOD liquidate), we should block it.

if __name__ == "__main__":
    deep_research()
