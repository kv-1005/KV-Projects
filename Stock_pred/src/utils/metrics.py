from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error


def compute_directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    direction_true = np.sign(np.diff(y_true, prepend=y_true[0]))
    direction_pred = np.sign(np.diff(y_pred, prepend=y_pred[0]))
    correct = (direction_true == direction_pred).astype(np.float32)
    return float(np.mean(correct))


def compute_core_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    mape = float(mean_absolute_percentage_error(y_true, y_pred) * 100.0)
    da = compute_directional_accuracy(y_true, y_pred) * 100.0
    return {"MSE": mse, "RMSE": rmse, "MAPE%": mape, "DirectionalAccuracy%": da}


def compute_trading_metrics(returns: np.ndarray, risk_free_rate_daily: float = 0.0) -> Dict[str, float]:
    # Annualization assumes ~252 trading days
    if returns.size == 0:
        return {"Sharpe": 0.0, "MaxDrawdown%": 0.0, "WinRate%": 0.0, "ProfitFactor": 0.0}

    mean_daily = np.mean(returns)
    std_daily = np.std(returns) + 1e-12
    sharpe = (mean_daily - risk_free_rate_daily) / std_daily * np.sqrt(252)

    equity_curve = np.cumprod(1 + returns)
    rolling_max = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve - rolling_max) / (rolling_max + 1e-12)
    max_drawdown = float(np.min(drawdowns)) * 100.0

    wins = (returns > 0).sum()
    win_rate = float(wins) / returns.size * 100.0

    gross_profit = np.sum(returns[returns > 0])
    gross_loss = -np.sum(returns[returns < 0]) + 1e-12
    profit_factor = float(gross_profit / gross_loss)

    return {
        "Sharpe": float(sharpe),
        "MaxDrawdown%": float(max_drawdown),
        "WinRate%": float(win_rate),
        "ProfitFactor": float(profit_factor),
    }


def generate_trading_returns_from_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    transaction_cost_bps: float = 5.0,
) -> np.ndarray:
    # Simple strategy: go long if next-day predicted return positive, short if negative
    # Build returns from next-day percentage changes
    pct_change = np.diff(y_true) / (y_true[:-1] + 1e-12)
    pct_change = np.concatenate([[0.0], pct_change])

    pred_change = np.diff(y_pred) / (y_pred[:-1] + 1e-12)
    pred_change = np.concatenate([[0.0], pred_change])

    positions = np.sign(pred_change)
    raw_returns = positions * pct_change

    # Apply transaction cost on position changes
    position_change = np.abs(np.diff(positions, prepend=0.0))
    transaction_cost = position_change * (transaction_cost_bps / 10000.0)
    strategy_returns = raw_returns - transaction_cost
    return strategy_returns


