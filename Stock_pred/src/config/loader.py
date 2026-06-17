from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BacktestConfig:
    universe: List[str]
    horizon_days: int = 1
    delta_threshold: float = 0.002
    entry_p_threshold: float = 0.65
    stop_loss_pct: float = 0.015
    take_profit_pct: float = 0.03
    risk_per_trade_pct: float = 0.005
    max_positions: int = 10
    commission_per_trade: float = 20.0
    slippage_model: Dict = None
    backtest_period: Dict = None


def load_config(path: str) -> BacktestConfig:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return BacktestConfig(**cfg)


