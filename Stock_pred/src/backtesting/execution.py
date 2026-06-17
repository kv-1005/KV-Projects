from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommissionModel:
    fixed: float = 20.0  # per trade
    percent: float = 0.0003  # 0.03%


@dataclass(frozen=True)
class SlippageModel:
    base_slip_pct: float = 0.0002  # 0.02%
    k: float = 0.5  # linear factor on size/volume


def estimate_slippage(price: float, shares: int, avg_volume: float, model: SlippageModel) -> float:
    impact = model.base_slip_pct + model.k * (abs(shares) / (avg_volume + 1e-12))
    return price * impact


def estimate_commission(price: float, shares: int, model: CommissionModel) -> float:
    notional = price * abs(shares)
    return model.fixed + notional * model.percent


