"""
Order Manager — Place / Modify / Exit MIS Orders via Fyers API v3
------------------------------------------------------------------
Supports both PAPER mode (simulated fills) and LIVE mode (real API calls).
All trades are logged to artifacts/trade_log.csv.
"""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Literal

from dotenv import load_dotenv

from src.models.intraday_predictor import SignalResult
from src.orders.performance_monitor import PerformanceMonitor

load_dotenv()

LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"
log = logging.getLogger(__name__)


@dataclass
class Position:
    ticker:      str
    shares:      int
    entry_price: float
    stop_loss:   float
    take_profit: float
    side:        Literal["BUY", "SELL"] = "BUY"
    entry_time:  datetime = field(default_factory=datetime.now)
    order_id:    str = ""
    margin_blocked: float = 0.0

    @property
    def unrealised_pnl(self) -> float:
        return 0.0   # updated live from OrderFeed ticks / LTP

    def current_pnl(self, ltp: float) -> float:
        if self.side == "SELL":
            return round((self.entry_price - ltp) * self.shares, 2)
        return round((ltp - self.entry_price) * self.shares, 2)


class OrderManager:
    """
    Routes signals → orders (paper or live).
    Tracks open positions and handles exits (SL / TP / EOD square-off).
    """

    def __init__(
        self,
        capital: float,
        max_positions: int = 5,
        risk_per_trade_pct: float = 0.01,
        save_dir: str = "artifacts",
    ) -> None:
        self.capital             = capital
        self.cash                = capital
        self.max_positions       = max_positions
        self.risk_per_trade_pct  = risk_per_trade_pct
        self.realised_pnl        = 0.0
        self.positions: Dict[str, Position] = {}
        self._trade_log: List[dict] = []
        self._log_path = os.path.join(save_dir, "trade_log.csv")
        os.makedirs(save_dir, exist_ok=True)
        
        self.consecutive_losses = 0
        from src.orders.capital_manager import CapitalAllocator, CapitalAllocationConfig
        self.allocator = CapitalAllocator(cfg=CapitalAllocationConfig(
            max_correlated_trades=max_positions,
            max_trades_per_sector=max(2, max_positions // 2)
        ))
        self.perf_monitor = PerformanceMonitor()

    # ─── Sizing ──────────────────────────────────────────────────────────────

    def _calc_shares(self, entry: float, stop: float, adjusted_risk: float, expectancy_ratio: float, volatility_kernel: float = 0.0) -> int:
        """Dynamic Sizing: Scale adjusted risk based on Expectancy + Volatility Kernel."""
        # 1. Expectancy Scaling
        ratio_abs = abs(expectancy_ratio)
        if ratio_abs < 0.5:
            multiplier = 0.5
        elif ratio_abs < 1.0:
            multiplier = 1.0
        elif ratio_abs < 1.5:
            multiplier = 1.5
        else:
            multiplier = 2.0

        # 2. Volatility De-risking (Institutional Kernel)
        # If volatility is > 1% (Parkinson), scale down the position
        if volatility_kernel > 0.01:
            vol_reduction = 0.5
            log.info(f"[Orders] 🛡️ High Volatility Detected ({volatility_kernel:.4f}): Scaling down risk.")
            multiplier *= vol_reduction

        final_risk_pct = adjusted_risk * multiplier
        risk_amount    = self.cash * final_risk_pct
        risk_per_sh    = max(abs(entry - stop), entry * 0.001)
        shares         = int(risk_amount / (risk_per_sh + 1e-12))
        
        # Small Account Optimization: Allow 5x Intraday (MIS) Leverage for buying power
        leverage = 5.0 if self.cash <= 50000 else 1.0
        max_shares = int((self.cash * leverage) / entry)
        return max(0, min(shares, max_shares))

    # ─── Entry ───────────────────────────────────────────────────────────────

    def enter(self, signal: SignalResult) -> bool:
        """
        Enter a position from a SignalResult.
        Returns True if order placed/simulated, False if skipped.
        """
        ticker = signal.ticker
        if ticker in self.positions:
            log.info(f"[Orders] Already in {ticker}, skip.")
            return False
        if len(self.positions) >= self.max_positions:
            log.info(f"[Orders] Max positions ({self.max_positions}) reached.")
            return False

        current_regime = getattr(signal, "regime", "TREND_UP")
        base_risk = self.risk_per_trade_pct
        
        # 3-Loss Rule: Halve risk if consecutive losses >= 3
        if self.consecutive_losses >= 3:
            base_risk *= 0.5
            log.warning(f"[Orders] 🛡️ 3-Loss Rule active: Reducing risk to {base_risk*100:.2f}%")

        adjusted_risk = self.allocator.allocate(
            ticker=ticker,
            base_risk_pct=base_risk,
            current_regime=current_regime,
            open_positions=list(self.positions.keys())
        )
        
        if adjusted_risk <= 0.0:
            return False

        vol_kernel = getattr(signal, "vol_parkinson", 0.0)
        shares = self._calc_shares(signal.entry, signal.stop_loss, adjusted_risk, signal.expectancy_ratio, volatility_kernel=vol_kernel)
        
        if shares <= 0:
            log.info(f"[Orders] {ticker} skipped: shares=0 (Risk too high or cash low)")
            return False

        # --- Atomic Margin Accounting (Institutional Spec) ---
        leverage = 5.0 if self.cash <= 50000 else 1.0
        notional = shares * signal.entry
        brokerage = 20.0 
        
        margin_required = notional / leverage
        total_initial_outlay = margin_required + brokerage
        
        if total_initial_outlay > self.cash:
            log.warning(f"[Orders] {ticker}: Insufficient Cash (Need {total_initial_outlay:.0f}, Available Cash {self.cash:.0f})")
            return False

        pos = Position(
            ticker      = ticker,
            shares      = shares,
            entry_price = signal.entry,
            stop_loss   = signal.stop_loss,
            take_profit = signal.take_profit,
            side        = signal.signal,
            entry_time  = getattr(signal, "timestamp", datetime.now()),
            order_id    = f"PAPER-{ticker}-{datetime.now().strftime('%H%M%S')}" if not LIVE_TRADING else "",
            margin_blocked = margin_required
        )

        self.cash -= total_initial_outlay
        self.positions[ticker] = pos

        if LIVE_TRADING:
            pos.order_id = self._place_fyers_order(ticker, shares, signal.entry, signal.signal)
        else:
            action_text = "BUY" if signal.signal == "BUY" else "SELL (SHORT)"
            log.info(f"[Orders] 📄 PAPER {action_text} {shares}×{ticker} @ {signal.entry} | id={pos.order_id}")

        self._log_trade("ENTER", ticker, shares, signal.entry, pos.order_id, reason=current_regime, timestamp=pos.entry_time)
        return True

    # ─── Exit ────────────────────────────────────────────────────────────────

    def exit(self, ticker: str, exit_price: float, reason: str = "MANUAL", timestamp: Optional[datetime] = None) -> bool:
        if ticker not in self.positions:
            return False
        pos = self.positions.pop(ticker)
        
        if pos.side == "SELL":
            # SHORT: Profit if exit < entry
            pnl_raw = (pos.entry_price - exit_price) * pos.shares
        else:
            # LONG: Profit if exit > entry
            pnl_raw = (exit_price - pos.entry_price) * pos.shares
            
        # Release Margin + add PnL - Exit Fee (20)
        proceeds = pos.margin_blocked + pnl_raw - 20
        self.cash += proceeds
        
        # Net PnL = (Proceeds - Outlay) = (Margin + PnL - 20) - (Margin + 20) = PnL - 40
        net_pnl = round(pnl_raw - 40, 2)
        self.realised_pnl += net_pnl

        if LIVE_TRADING:
            side_text = "SELL" if pos.side == "BUY" else "BUY" 
            self._place_fyers_order(ticker, pos.shares, exit_price, side_text)
        else:
            exit_type = "SELL" if pos.side == "BUY" else "BUYBACK (COVER)"
            log.info(f"[Orders] 📄 PAPER {exit_type} {pos.shares}×{ticker} @ {exit_price} | PnL={net_pnl} | {reason}")

        if net_pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        # Update Performance
        self.perf_monitor.add_trade(net_pnl, self.cash + sum(p.current_pnl(exit_price) for p in self.positions.values()))
        metrics = self.perf_monitor.get_metrics()

        ts = timestamp or datetime.now()
        self._log_trade("EXIT", ticker, pos.shares, exit_price, pos.order_id, 
                        pnl=net_pnl, reason=reason, sharpe=metrics["sharpe"], 
                        drawdown=metrics["drawdown_pct"], timestamp=ts)
        return True

    def exit_all(self, ltps: Dict[str, float], reason: str = "EOD_SQUAREOFF", timestamp: Optional[datetime] = None) -> None:
        """Square off all open positions (e.g. 3:15 PM mandatory exit)."""
        for ticker in list(self.positions.keys()):
            price = ltps.get(ticker, self.positions[ticker].entry_price)
            self.exit(ticker, price, reason, timestamp=timestamp)

    # ─── SL / TP Check ───────────────────────────────────────────────────────

    def check_exits(self, ltps: Dict[str, float], timestamp: Optional[datetime] = None) -> None:
        """Check all open positions against SL/TP and exit if triggered."""
        for ticker in list(self.positions.keys()):
            ltp = ltps.get(ticker)
            if ltp is None: continue
            pos = self.positions[ticker]
            
            if pos.side == "SELL":
                if ltp >= pos.stop_loss:
                    self.exit(ticker, ltp, reason="STOP_LOSS", timestamp=timestamp)
                elif ltp <= pos.take_profit:
                    self.exit(ticker, ltp, reason="TAKE_PROFIT", timestamp=timestamp)
            else:
                if ltp <= pos.stop_loss:
                    self.exit(ticker, ltp, reason="STOP_LOSS", timestamp=timestamp)
                elif ltp >= pos.take_profit:
                    self.exit(ticker, ltp, reason="TAKE_PROFIT", timestamp=timestamp)

    # ─── Trailing SL ─────────────────────────────────────────────────────────

    def update_trailing_sl(self, ticker: str, ltp: float, trail_pct: float = 0.005) -> None:
        """Raise stop-loss as price moves up (trail by trail_pct)."""
        if ticker not in self.positions: return
        pos = self.positions[ticker]
        if pos.side == "SELL":
            new_sl = round(ltp * (1.0 + trail_pct), 2)
            if pos.stop_loss == 0 or new_sl < pos.stop_loss:
                pos.stop_loss = new_sl
        else:
            new_sl = round(ltp * (1.0 - trail_pct), 2)
            if new_sl > pos.stop_loss:
                pos.stop_loss = new_sl

    # ─── Status ──────────────────────────────────────────────────────────────

    def portfolio_summary(self, ltps: Dict[str, float] = {}) -> dict:
        total_unrealised = sum(pos.current_pnl(ltps.get(t, pos.entry_price)) for t, pos in self.positions.items())
        return {
            "cash":           round(self.cash, 2),
            "open_trades":    len(self.positions),
            "unrealised_pnl": round(total_unrealised, 2),
            "realised_pnl":   round(self.realised_pnl, 2),
            "total_equity":   round(self.cash + total_unrealised, 2),
            "positions":      {
                t: {
                    "shares": p.shares,
                    "entry":  p.entry_price,
                    "sl":     p.stop_loss,
                    "tp":     p.take_profit,
                    "pnl":    p.current_pnl(ltps.get(t, p.entry_price)),
                }
                for t, p in self.positions.items()
            },
        }

    # ─── Fyers Live Order Placement ───────────────────────────────────────────

    def _place_fyers_order(self, ticker: str, qty: int, price: float, side: str) -> str:
        from src.data.fyers_client import get_fyers_client
        fyers = get_fyers_client()
        data = {
            "symbol":        f"NSE:{ticker}-EQ",
            "qty":           qty,
            "type":          2,    # 2 = Market order
            "side":          1 if side == "BUY" else -1,
            "productType":   "INTRADAY",
            "limitPrice":    0,
            "stopPrice":     0,
            "validity":      "DAY",
            "disclosedQty":  0,
            "offlineOrder":  False,
        }
        response = fyers.place_order(data=data)
        order_id = response.get("id", "")
        log.info(f"[Orders] LIVE {side} {qty}×{ticker} | Fyers response: {response}")
        return str(order_id)

    # ─── Logging ─────────────────────────────────────────────────────────────

    def _log_trade(self, action, ticker, qty, price, order_id, pnl=0.0, reason="", sharpe=0.0, drawdown=0.0, timestamp=None):
        ts = timestamp.isoformat() if timestamp else datetime.now().isoformat()
        row = {
            "timestamp": ts,
            "action":    action,
            "ticker":    ticker,
            "qty":       qty,
            "price":     price,
            "pnl":       pnl,
            "reason":    reason,
            "order_id":  order_id,
            "mode":      "LIVE" if LIVE_TRADING else "PAPER",
            "sharpe":    sharpe,
            "drawdown_pct": drawdown,
        }
        self._trade_log.append(row)
        write_header = not os.path.exists(self._log_path)
        with open(self._log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(row)
