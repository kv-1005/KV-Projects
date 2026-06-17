import pandas as pd
import os

def analyze():
    log_path = "artifacts/trade_log.csv"
    if not os.path.exists(log_path):
        print("Log not found")
        return

    try:
        # Load CSV with header
        df = pd.read_csv(log_path)
        
        # Mapping by name
        exits = df[df['action'] == 'EXIT']
        
        if exits.empty:
            print("No exits found in trade_log.csv")
            return

        import json
        with open("config/nse_intraday.json") as f:
            cfg = json.load(f)
        initial_capital = cfg.get("paper_capital", 200000)
        
        total_pnl = exits['pnl'].sum()
        final_equity = initial_capital + total_pnl
        
        wins = exits[exits['pnl'] > 0]
        win_rate = (len(wins) / len(exits)) * 100
        
        reason_stats = exits.groupby('reason')['pnl'].sum()
        
        # Total Stats
        returns = exits['pnl'] / initial_capital
        sharpe = (returns.mean() / (returns.std() + 1e-12)) * (252 ** 0.5) if len(returns) > 1 else 0.0
        
        print("-" * 40)
        print("      INSTITUTIONAL PERFORMANCE REPORT      ")
        print("-" * 40)
        print(f"Accuracy (Win Rate): {win_rate:.2f}%")
        print(f"Sharpe Ratio:        {sharpe:.2f}")
        print(f"Total Trades:        {len(exits)}")
        print(f"Total PnL:           INR {total_pnl:,.2f}")
        print(f"Final Equity:        INR {final_equity:,.2f}")
        print("-" * 40)
        print("Model Convergence Summary:")
        print(reason_stats)
        print("-" * 40)
    except Exception as e:
        print(f"Error analyzing: {e}")

if __name__ == "__main__":
    analyze()
