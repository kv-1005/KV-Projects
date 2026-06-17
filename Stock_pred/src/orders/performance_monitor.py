"""
Performance Monitor — Real-time tracking of Sharpe, Drawdown, and Equity Slope.
-----------------------------------------------------------------------------
Tracks institutional metrics to trigger adaptive thresholds or kill switches.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, lookback_trades: int = 50):
        self.lookback_trades = lookback_trades
        self.trades = []
        self.peak_equity = 0.0
        self.current_drawdown = 0.0
        
    def add_trade(self, pnl: float, equity: float):
        """Record a closed trade."""
        self.trades.append({
            "timestamp": datetime.now(),
            "pnl": pnl,
            "equity": equity
        })
        if len(self.trades) > self.lookback_trades:
            self.trades.pop(0)
            
        # Update peak and drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        if self.peak_equity > 0:
            self.current_drawdown = (self.peak_equity - equity) / self.peak_equity
            
    def get_metrics(self) -> dict:
        if not self.trades:
            return {
                "sharpe": 0.0,
                "drawdown_pct": 0.0,
                "equity_slope": 0.0,
                "win_rate": 0.0
            }
            
        df = pd.DataFrame(self.trades)
        pnls = df["pnl"]
        
        # Win Rate
        win_rate = (pnls > 0).mean()
        
        # Sharpe Ratio (Simplified for intraday)
        std = pnls.std()
        sharpe = pnls.mean() / std if std > 0 else 0.0
        
        # Equity Slope (Linear Regression)
        # Using simple index for time axis since trades are sequential
        y = df["equity"].values
        x = np.arange(len(y))
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            normalized_slope = slope / y[0] if y[0] > 0 else 0.0
        else:
            normalized_slope = 0.0
            
        # Volatility (Std of daily-equivalent returns)
        # Simplified: Std of PNLS normalized by equity
        if len(pnls) > 5:
            volatility = pnls.std() / y[0] if y[0] > 0 else 0.0
        else:
            volatility = 0.0
            
        return {
            "sharpe": round(sharpe, 3),
            "drawdown_pct": round(self.current_drawdown * 100, 2),
            "equity_slope": round(normalized_slope, 5),
            "volatility": round(volatility, 4),
            "win_rate": round(win_rate * 100, 1),
            "trade_count": len(self.trades)
        }
