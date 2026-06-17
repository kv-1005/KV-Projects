import pandas as pd
import os

def collect():
    path = "artifacts/trade_log.csv"
    if not os.path.exists(path):
        print("No log file")
        return
        
    df = pd.read_csv(path, header=None)
    exits = df[df[1] == 'EXIT']
    
    # Force numeric conversion for PnL column (Index 5)
    exits[5] = pd.to_numeric(exits[5], errors='coerce')
    
    tp_total = exits[exits[6] == 'TAKE_PROFIT'][5].sum()
    sl_total = exits[exits[6] == 'STOP_LOSS'][5].sum()
    eo_total = exits[exits[6] == 'EOD_SQUAREOFF'][5].sum()
    total_pnl = exits[5].sum()
    
    win_count = len(exits[exits[5] > 0])
    total_trades = len(exits)
    
    print(f"TP_TOTAL: {tp_total:.2f}")
    print(f"SL_TOTAL: {sl_total:.2f}")
    print(f"EOD_TOTAL: {eo_total:.2f}")
    print(f"GRAND_TOTAL: {total_pnl:.2f}")
    print(f"WIN_COUNT: {win_count}")
    print(f"TOTAL_TRADES: {total_trades}")

if __name__ == "__main__":
    collect()
