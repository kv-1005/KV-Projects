from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, List, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class WalkForwardConfig:
    train_years: int = 5
    val_years: int = 1
    step_years: int = 1


def generate_walkforward_splits(index: pd.DatetimeIndex, cfg: WalkForwardConfig) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
    years = sorted(set(index.year))
    if len(years) < cfg.train_years + cfg.val_years:
        yield (np.arange(len(index)), np.array([], dtype=int))
        return
    start_idx_year = years[0]
    end_idx_year = years[-1]
    start_train_year = start_idx_year

    while start_train_year + cfg.train_years + cfg.val_years - 1 <= end_idx_year:
        train_start = pd.Timestamp(year=start_train_year, month=1, day=1)
        train_end = pd.Timestamp(year=start_train_year + cfg.train_years - 1, month=12, day=31)
        val_start = pd.Timestamp(year=start_train_year + cfg.train_years, month=1, day=1)
        val_end = pd.Timestamp(year=start_train_year + cfg.train_years + cfg.val_years - 1, month=12, day=31)

        tr_idx = np.where((index >= train_start) & (index <= train_end))[0]
        va_idx = np.where((index >= val_start) & (index <= val_end))[0]
        if tr_idx.size and va_idx.size:
            yield tr_idx, va_idx

        start_train_year += cfg.step_years


