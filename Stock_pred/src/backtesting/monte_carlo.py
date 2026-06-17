"""
Monte Carlo Risk Stress Tester
------------------------------
Run this module independently to stress-test your strategy's Trade Log.
Institutional robustness requires simulating:
  1. Trade sequence reshaping (10,000 paths of randomized winning/losing sequences).
  2. Severe slippage shocks (+30% to historical avg).
  3. Consecutive drawdowns (Calculating Risk-of-Ruin (RoR)).
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class MonteCarloConfig:
    simulations: int        = 10_000
    starting_capital: float = 200_000
    risk_of_ruin_pct: float = 0.50     # Account considered "ruined" if 50% drawdown
    slippage_shock: float   = 0.30     # +30% worse slippage than backtest
    spread_widening: float  = 2.0      # 2x spread applied to randomly selected toxic trades


class MonteCarloTester:
    def __init__(self, cfg: MonteCarloConfig = MonteCarloConfig()) -> None:
        self.cfg = cfg

    def run(self, trade_log_csv: str) -> dict:
        """
        Reads a historical trade log (containing 'pnl' or 'action' rows) 
        and simulates thousands of alternative futures.
        """
        try:
            df = pd.read_csv(trade_log_csv)
            # Filter to only exits to get realized PnL per trade
            exits = df[df["action"] == "EXIT"]
            if exits.empty:
                return {"error": "No completed trades to simulate."}
            
            pnl_series = exits["pnl"].values
        except Exception as e:
            return {"error": f"Failed reading log: {e}"}

        print(f"\n[Monte Carlo]  Running {self.cfg.simulations} Simulations...")
        print(f"[Monte Carlo]  Applying {self.cfg.slippage_shock*100}% Slippage Shock")

        ruin_events = 0
        max_drawdowns = []
        final_equities = []

        total_trades = len(pnl_series)
        ruin_barrier = self.cfg.starting_capital * (1.0 - self.cfg.risk_of_ruin_pct)

        for _ in range(self.cfg.simulations):
            # Reshuffle trade sequence (Block Bootstrapping to preserve losing streak clusters)
            block_size = min(5, total_trades)
            sim_pnl = []
            while len(sim_pnl) < total_trades:
                start_idx = random.randint(0, total_trades - block_size)
                sim_pnl.extend(pnl_series[start_idx:start_idx+block_size])
            sim_pnl = np.array(sim_pnl[:total_trades])
            
            # Apply toxic shocks
            for i in range(total_trades):
                # Apply base slippage shock to ALL winners
                if sim_pnl[i] > 0:
                    sim_pnl[i] *= (1.0 - self.cfg.slippage_shock)
                # Apply spread widening randomly to 10% of trades (black swans)
                if random.random() < 0.10:
                    if sim_pnl[i] < 0:
                        sim_pnl[i] *= self.cfg.spread_widening # Make losers 2x worse

            # Calculate simulated equity curve
            equity_curve = self.cfg.starting_capital + np.cumsum(sim_pnl)
            
            # Record metrics
            final_equity = equity_curve[-1]
            final_equities.append(final_equity)
            
            peak = np.maximum.accumulate(equity_curve)
            drawdown = (peak - equity_curve) / peak
            max_drawdowns.append(np.max(drawdown))

            if np.any(equity_curve <= ruin_barrier):
                ruin_events += 1

        ror = ruin_events / self.cfg.simulations
        median_dd = np.median(max_drawdowns)
        worst_dd = np.max(max_drawdowns)
        median_equity = np.median(final_equities)

        print("-" * 50)
        print(f"[{'FAIL' if ror > 0.01 else 'PASS'}] Risk of Ruin: {ror*100:.2f}%")
        print(f"Median Drawdown: {median_dd*100:.2f}%")
        print(f"Worst Case Drawdown (99th %): {np.percentile(max_drawdowns, 99)*100:.2f}%")
        print(f"Median Final Equity: INR{median_equity:,.2f}")
        print("-" * 50)

        return {
            "risk_of_ruin": ror,
            "median_drawdown": median_dd,
            "worst_drawdown": worst_dd,
            "median_equity": median_equity
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        tester = MonteCarloTester()
        tester.run(log_file)
    else:
        print("Usage: python src/backtesting/monte_carlo.py artifacts/trade_log.csv")
