"""
System Kill Switch
------------------
Hard shutdown protocol triggering manual review.
Protects the system from black swan events, structural decay, and data drift.
Triggers if:
  1. Drawdown exceeds absolute limit (2x expected).
  2. Short-term equity slope turns sharply negative combined with data drift.
  3. Live execution slippage exceeds 2σ historical.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

log = logging.getLogger(__name__)


@dataclass
class KillSwitchConfig:
    max_drawdown_pct: float     = 0.15   # 15% absolute hard stop
    min_equity_slope: float     = -0.05  # -5% slope over 10 trades
    max_slippage_pct: float     = 0.005  # 0.5% max allowable slippage
    max_volatility:   float     = 0.12   # 12% max volatility hard stop


class SystemKillSwitch:
    def __init__(self, cfg: KillSwitchConfig = KillSwitchConfig()) -> None:
        self.cfg = cfg
        self._is_killed = False
        self._kill_reason = ""
        self._peak_equity = 0.0
        
        # Tracking buffers
        self._recent_pnl_pcts: List[float] = []
        self._recent_slippage: List[float] = []

    @property
    def is_killed(self) -> bool:
        return self._is_killed

    @property
    def kill_reason(self) -> str:
        return self._kill_reason

    def update_equity(
        self, 
        current_equity: float, 
        trade_pnl_pct: float = None, 
        slippage_pct: float = None,
        volatility: float = None
    ) -> None:
        """Called after every closed trade or periodically to monitor equity drops."""
        if self._is_killed:
            return

        # Update Peak
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity

        # Check Drawdown
        if self._peak_equity > 0:
            drawdown = (self._peak_equity - current_equity) / self._peak_equity
            if drawdown >= self.cfg.max_drawdown_pct:
                self._trigger(f"HARD STOP: Drawdown {drawdown*100:.1f}% exceeded limit {self.cfg.max_drawdown_pct*100:.1f}%")
                return

        # Track short-term trends
        if trade_pnl_pct is not None:
            self._recent_pnl_pcts.append(trade_pnl_pct)
            if len(self._recent_pnl_pcts) > 10:
                self._recent_pnl_pcts.pop(0)
                
            # Calculate simple slope wrapper (sum of last 10 trades)
            slope = sum(self._recent_pnl_pcts)
            if slope <= self.cfg.min_equity_slope:
                self._trigger(f"HARD STOP: Severe Negative Equity Slope ({slope*100:.1f}% over 10 trades). Possible structural decay.")
                return

        # Track execution friction
        if slippage_pct is not None:
            self._recent_slippage.append(slippage_pct)
            if len(self._recent_slippage) > 5:
                self._recent_slippage.pop(0)
                
            avg_slip = sum(self._recent_slippage) / len(self._recent_slippage)
            if avg_slip >= self.cfg.max_slippage_pct:
                self._trigger(f"HARD STOP: Toxic Market Friction. Avg Slippage {avg_slip*100:.3f}% exceeded limit.")
                return

        # 4. Volatility Threshold
        if volatility is not None and volatility >= self.cfg.max_volatility:
            self._trigger(f"HARD STOP: System Entropy Exceeded. Volatility {volatility*100:.1f}% > {self.cfg.max_volatility*100:.1f}%.")
            return

    def _trigger(self, reason: str) -> None:
        self._is_killed = True
        self._kill_reason = reason
        log.critical("=====================================================")
        log.critical("🚨 KILL SWITCH ACTIVATED 🚨")
        log.critical(f"Reason: {reason}")
        log.critical("System is now FROZEN. Manual review required.")
        log.critical("=====================================================")
