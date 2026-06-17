"""
Portfolio Capital Allocation Controller
---------------------------------------
Governs portfolio-level exposure to prevent correlated wipeouts.
1. Implements Sector Caps (e.g., max 2 bank trades at once).
2. Scales down capital in Volatility Compression regimes (chop).
3. Hard limits maximum correlated active trades.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

log = logging.getLogger(__name__)

# Basic NSE sector map for correlation prevention
SECTOR_MAP = {
    "HDFCBANK": "BANK",
    "ICICIBANK": "BANK",
    "KOTAKBANK": "BANK",
    "SBIN": "BANK",
    "AXISBANK": "BANK",
    "TCS": "IT",
    "INFY": "IT",
    "WIPRO": "IT",
    "RELIANCE": "ENERGY",
    "LT": "INFRA",
    "BAJFINANCE": "FINANCE",
}

@dataclass
class CapitalAllocationConfig:
    max_trades_per_sector: int     = 2  # Max 2 banks at the same time
    max_correlated_trades: int     = 3  # Max 3 of anything highly correlated
    regime_exposure_scales: dict   = None


class CapitalAllocator:
    def __init__(self, cfg: CapitalAllocationConfig = None) -> None:
        self.cfg = cfg or CapitalAllocationConfig()
        
        # Scaling total exposure based on market regime
        if self.cfg.regime_exposure_scales is None:
            self.cfg.regime_exposure_scales = {
                "TREND_UP":        1.0,   # Full allocation
                "TREND_DOWN":      1.0,   # Full allocation
                "VOL_EXPANSION":   0.5,   # Half-size in chaos
                "RANGING":         0.25,  # Quarter-size in chop
                "VOL_COMPRESSION": 0.0    # No trading during dead consolidation
            }

    def allocate(
        self, 
        ticker: str, 
        base_risk_pct: float, 
        current_regime: str, 
        open_positions: List[str]
    ) -> float:
        """
        Takes the base risk % and scales it down according to portfolio limits.
        Returns 0.0 if the trade is banned due to correlation or regime limits.
        """
        # 1. Regime Scaling
        scale = self.cfg.regime_exposure_scales.get(current_regime, 0.0)
        if scale == 0.0:
            log.warning(f"[CapitalAllocator] Blocked {ticker}: {current_regime} regime.")
            return 0.0
            
        final_risk = base_risk_pct * scale

        # 2. Sector Cap Check
        sector = SECTOR_MAP.get(ticker, "OTHER")
        active_in_sector = sum(1 for p in open_positions if SECTOR_MAP.get(p, "OTHER") == sector)
        
        if active_in_sector >= self.cfg.max_trades_per_sector:
            log.warning(f"[CapitalAllocator] Blocked {ticker}: Sector cap ({sector}) reached.")
            return 0.0

        # 3. Overall Correlation (Total open positions)
        # Assuming our universe is already highly correlated (Nifty 50 staples)
        if len(open_positions) >= self.cfg.max_correlated_trades:
            log.warning(f"[CapitalAllocator] Blocked {ticker}: Global correlation limit reached.")
            return 0.0

        return final_risk
