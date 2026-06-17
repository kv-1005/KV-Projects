import pandas as pd
import numpy as np

def debug_losses():
    try:
        df = pd.read_csv("artifacts/trade_log.csv")
    except Exception as e:
        print(f"Error reading log: {e}")
        return

    exits = df[df['action'] == 'EXIT'].copy()
    
    if exits.empty:
        print("No exits found.")
        return

    # Convert timestamp to datetime
    exits['ts'] = pd.to_datetime(exits['timestamp'])
    exits['hour'] = exits['ts'].dt.hour
    
    print(f"Total Exits: {len(exits)}")
    print("\nPnL by Reason:")
    print(exits.groupby('reason')['pnl'].sum())
    
    print("\nPnL by Hour of Entry/Exit (Exit Logic):")
    print(exits.groupby('hour')['pnl'].sum())
    
    # Calculate Profit Factor
    gross_profits = exits[exits['pnl'] > 0]['pnl'].sum()
    gross_losses = abs(exits[exits['pnl'] < 0]['pnl'].sum())
    pf = gross_profits / (gross_losses + 1e-12)
    print(f"\nProfit Factor: {pf:.2f}")
    
    # Check Average Return per Trade
    avg_return = exits['pnl'].mean()
    print(f"Avg PnL per Trade: ₹{avg_return:.2f}")

if __name__ == "__main__":
    debug_losses()
