from __future__ import annotations

import numpy as np

from src.utils.metrics import (
    compute_core_regression_metrics,
    compute_trading_metrics,
    generate_trading_returns_from_predictions,
)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    core = compute_core_regression_metrics(y_true, y_pred)
    strat_returns = generate_trading_returns_from_predictions(y_true, y_pred)
    trading = compute_trading_metrics(strat_returns)
    return {**core, **trading}


