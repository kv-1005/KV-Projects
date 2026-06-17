from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.backtesting.execution import CommissionModel, SlippageModel, estimate_commission, estimate_slippage


@dataclass
class RiskRules:
    max_positions: int = 10
    max_alloc_single: float = 0.05  # 5% of equity
    risk_per_trade_pct: float = 0.005  # 0.5%


@dataclass
class EntryRules:
    p_entry_threshold: float = 0.65
    stop_loss_pct: float = 0.015
    take_profit_pct: float = 0.03
    max_hold_days: int = 5


class Portfolio:
    def __init__(self, initial_equity: float):
        self.equity = float(initial_equity)
        self.cash = float(initial_equity)
        self.positions: Dict[str, Dict] = {}
        self.history: List[Dict] = []

    def update_equity(self, date: pd.Timestamp, prices: Dict[str, float]) -> None:
        mtm = self.cash
        for sym, pos in self.positions.items():
            qty = pos["shares"]
            price = prices.get(sym, pos["entry_price"])  # fallback
            mtm += qty * price
        self.equity = mtm
        self.history.append({"date": date, "equity": self.equity})


def position_size_by_risk(
    equity: float, entry_price: float, stop_price: float, max_alloc_single: float, risk_per_trade_pct: float
) -> int:
    risk_amount = equity * risk_per_trade_pct
    dollar_risk_per_share = max(entry_price - stop_price, 1e-6)
    shares = int(np.floor(risk_amount / dollar_risk_per_share))
    cap_shares = int(np.floor((equity * max_alloc_single) / entry_price))
    return max(0, min(shares, cap_shares))


def backtest_daily(
    prices: Dict[str, pd.DataFrame],
    proba: pd.DataFrame,
    entry_rules: EntryRules,
    risk_rules: RiskRules,
    commission: CommissionModel,
    slippage: SlippageModel,
    initial_equity: float = 200_000.0,
) -> Dict[str, float]:
    # prices dict: ticker -> DataFrame with columns [Open, High, Low, Close, Volume]
    # proba: MultiIndex (date, ticker) with column p_up
    dates = sorted({d for d, _ in proba.index})
    portfolio = Portfolio(initial_equity=initial_equity)

    for i, dt in enumerate(dates[:-1]):  # use next day open for execution
        today_slice = proba.loc[dt]
        # today_slice can be a Series (index=ticker, values=p_up) or a DataFrame with column 'p_up'
        if isinstance(today_slice, pd.Series):
            p_series = today_slice
        else:
            p_series = today_slice["p_up"]
        candidates = p_series[p_series >= entry_rules.p_entry_threshold]

        # Rank by probability/volatility proxy (ATR or Close*vol)
        def rank_score(sym: str) -> float:
            df = prices[sym]
            # Use rolling ATR14 if available; fallback to daily range
            if "atr14" in df.columns:
                return float(p_series.loc[sym]) / (float(df.loc[dt, "atr14"]) + 1e-6)
            return float(p_series.loc[sym]) / (
                (float(df.loc[dt, "High"]) - float(df.loc[dt, "Low"])) + 1e-6
            )

        ranked_syms = sorted(candidates.index.tolist(), key=rank_score, reverse=True)

        # Update equity with mark-to-market using close
        today_prices = {sym: float(prices[sym].loc[dt, "Close"]) for sym in prices}
        portfolio.update_equity(dt, today_prices)

        # Manage existing positions for exits
        to_close: List[str] = []
        for sym, pos in list(portfolio.positions.items()):
            df = prices[sym]
            if dt not in df.index:
                continue
            high = float(df.loc[dt, "High"])
            low = float(df.loc[dt, "Low"]) 
            close = float(df.loc[dt, "Close"]) 
            # Check TP/SL
            if high >= pos["take_profit"] or low <= pos["stop_loss"] or (i - pos["entry_day"]) >= entry_rules.max_hold_days:
                exit_price = close
                shares = pos["shares"]
                comm = estimate_commission(exit_price, -shares, commission)
                portfolio.cash += shares * exit_price - comm
                to_close.append(sym)

        for sym in to_close:
            portfolio.positions.pop(sym, None)

        # Open new positions at next open
        next_dt = dates[i + 1]
        for sym in ranked_syms:
            if len(portfolio.positions) >= risk_rules.max_positions:
                break
            # Skip if already in position
            if sym in portfolio.positions:
                continue
            df = prices[sym]
            if next_dt not in df.index or dt not in df.index:
                continue
            next_open = float(df.loc[next_dt, "Open"])  # execution
            stop = float(df.loc[dt, "Close"]) * (1.0 - entry_rules.stop_loss_pct)
            take = float(df.loc[dt, "Close"]) * (1.0 + entry_rules.take_profit_pct)
            shares = position_size_by_risk(
                portfolio.equity, next_open, stop, risk_rules.max_alloc_single, risk_rules.risk_per_trade_pct
            )
            if shares <= 0:
                continue

            avg_vol = float(df["Volume"].rolling(20).mean().loc[dt]) if "Volume" in df.columns else 1e6
            slip = estimate_slippage(next_open, shares, avg_vol, slippage)
            exec_price = next_open + slip
            comm = estimate_commission(exec_price, shares, commission)
            cost = shares * exec_price + comm
            if portfolio.cash < cost:
                continue
            portfolio.cash -= cost
            portfolio.positions[sym] = {
                "shares": shares,
                "entry_price": exec_price,
                "entry_day": i,
                "stop_loss": stop,
                "take_profit": take,
            }

    # Final mark-to-market on last date close
    last_dt = dates[-1]
    last_prices = {sym: float(prices[sym].loc[last_dt, "Close"]) for sym in prices if last_dt in prices[sym].index}
    portfolio.update_equity(last_dt, last_prices)

    # Build equity curve and compute basic metrics
    equity_df = pd.DataFrame(portfolio.history).set_index("date").sort_index()
    returns = equity_df["equity"].pct_change().fillna(0.0).values
    from src.utils.metrics import compute_trading_metrics

    tm = compute_trading_metrics(returns)
    tm["equity_curve"] = equity_df
    return tm


