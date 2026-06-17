# Stock Prediction AI (CNN-LSTM + Indicators + Sentiment)

End-to-end stock prediction pipeline implementing a high-accuracy CNN-LSTM model with technical indicators and sentiment integration, plus backtesting metrics. Includes optional ensemble stacking skeleton.

## Quickstart

1. Create a Python 3.10+ virtual environment
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run an end-to-end training + evaluation on a ticker (e.g., AAPL):
```bash
python -m src.main --ticker AAPL --start 2015-01-01 --end 2025-10-01
```

## Features

- CNN-LSTM hybrid model with tuned hyperparameters (sequence length=60, Adam lr=1e-3, dropout=0.2-0.3)
- Technical indicators: RSI, MACD, Bollinger Bands, moving averages
- Sentiment via VADER on recent headlines (normalized to [-1, 1])
- Backtesting metrics: Directional Accuracy, MAPE, RMSE, Sharpe, Max Drawdown, Win Rate, Profit Factor
- Early stopping and model checkpointing
- Optional ensemble stacking (LSTM, CNN-LSTM, GRU, Transformer -> XGBoost)

## Notes

- Data fetched via yfinance; news headlines use simple public endpoints or can be supplied via CSV.
- GPU is optional; CPU should work for small experiments.


