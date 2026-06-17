"""
Risk Guard — Pre-trade and intra-session risk checks.
Blocks new orders if hard limits are breached.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, time

log = logging.getLogger(__name__)

# Market session: 9:15 AM – 3:15 PM IST (last 15 min no new entries)
_MARKET_OPEN  = time(9, 15)
_NEW_ENTRY_CUTOFF = time(15, 5)   # No NEW entries after 3:05 PM
_MARKET_CLOSE = time(15, 30)


class RiskGuard:
    """
    Stateful risk checker. Call `allow_entry()` before every order.
    """

    def __init__(
        self,
        max_daily_loss_pct: float | None = None,
        max_positions: int = 5,
    ) -> None:
        self.max_daily_loss_pct = max_daily_loss_pct or float(
            os.getenv("MAX_DAILY_LOSS_PCT", "0.02")
        )
        self.max_positions   = max_positions
        self._trading_halted = False
        self._halt_reason    = ""
        self._start_equity   = 0.0
        self._initialized    = False

    def init_session(self, equity: float) -> None:
        """Call at market open with starting equity to anchor daily loss calculation."""
        self._start_equity  = equity
        self._initialized   = True
        self._trading_halted = False
        self._halt_reason   = ""
        log.info(f"[RiskGuard] Session started. Starting equity: ₹{equity:,.0f}")

    def allow_entry(
        self,
        current_equity: float,
        open_positions: int,
    ) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        allowed=False means the order should NOT be placed.
        """
        now = datetime.now().time()

        # 1. Outside market hours
        if not (_MARKET_OPEN <= now <= _NEW_ENTRY_CUTOFF):
            return False, f"Outside entry window ({now} not in [{_MARKET_OPEN}–{_NEW_ENTRY_CUTOFF}])"

        # 2. Manual halt
        if self._trading_halted:
            return False, f"Trading halted: {self._halt_reason}"

        # 3. Max positions
        if open_positions >= self.max_positions:
            return False, f"Max positions ({self.max_positions}) reached"

        # 4. Daily loss limit
        if self._initialized and self._start_equity > 0:
            loss_pct = (self._start_equity - current_equity) / self._start_equity
            if loss_pct >= self.max_daily_loss_pct:
                reason = f"Daily loss {loss_pct:.2%} ≥ limit {self.max_daily_loss_pct:.2%}"
                self.halt(reason)
                return False, reason

        return True, "OK"

    def is_squareoff_time(self) -> bool:
        """Returns True at 3:15 PM → trigger mandatory EOD square-off."""
        now = datetime.now().time()
        return now >= _NEW_ENTRY_CUTOFF

    def is_market_open(self) -> bool:
        now = datetime.now().time()
        today = datetime.now().weekday()
        if today >= 5:   # Saturday / Sunday
            return False
        return _MARKET_OPEN <= now <= _MARKET_CLOSE

    def halt(self, reason: str) -> None:
        self._trading_halted = True
        self._halt_reason    = reason
        log.warning(f"[RiskGuard] 🛑 TRADING HALTED — {reason}")

    def resume(self) -> None:
        self._trading_halted = False
        self._halt_reason    = ""
        log.info("[RiskGuard] ✅ Trading resumed.")
