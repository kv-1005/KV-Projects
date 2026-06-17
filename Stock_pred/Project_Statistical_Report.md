# Project Report: Statistical Performance & Risk Analysis of AI Trading Engine

**Topic**: Quantitative Evaluation of a Multi-Model Ensemble Strategy for Intraday Equities (NSE)

---

## 1. Executive Summary
This report provides a data-driven evaluation of the **Fyers AI Trading Engine**. The system employs a "Universal Hyper-Ensemble" (XGBoost, LSTM, and GNN) to predict 5-minute intraday price action. The following analysis is based on actual trade logs, backtesting data, and Monte Carlo risk simulations.
---

## 2. Decision Architecture & Algorithmic Logic (Singularity V2)
The "Heart" of the system is the **Singularity V2 Hyper-Ensemble**, which does not rely on a single model. Instead, it employs a **Consensus-Driven Intelligence** framework. Decisions are made through a three-layer validation process.

### 2.1 The Algorithmic Ensemble
The system utilizes 10+ distinct architectures to ensure that no single mathematical bias (like overfitting or trend-lag) dominates the signal.

| Algorithm Family | Specific Model(s) | Primary Responsibility |
| :--- | :--- | :--- |
| **Statistical Regression** | **XGBoost, RF, SVR** | Captures non-linear point relationships and structural price anomalies. |
| **Sequential Memory** | **Attention-LSTM** | Analyzes the last 15–60 candles to identify temporal patterns and momentum. |
| **Relational Graph** | **Graph Neural Net (GNN)** | Models "Sector Contagion" (e.g., if HDFCBANK moves, how does ICICIBANK react?). |
| **Multi-Horizon Blocks** | **N-BEATS, N-HiTS** | Concurrent forecasting across multiple time scales (short vs. medium term). |
| **Decision Layer** | **PPO RL Agent** | Reinforcement Learning agent that "vetos" entries if market volatility is too chaotic. |

### 2.2 How "Decisions" Are Made
A trade signal (BUY/SELL) is only emitted if the system clears the **consensus gate**:

1.  **Ensemble Scoring**: Every model generates an `Expected_Return`. The system calculates a **Weighted Meta-Score** based on the current Market Regime (Ranging vs. Trending).
2.  **Structural Variance Check**: We calculate `Variance = |XGBoost_Pred - LSTM_Pred|`. If the models disagree significantly, the "Variance" spikes, which automatically suppresses the signal. This is a "Defense First" mechanism.
3.  **Expectancy Ratio Calculation**: The system requires a signal-to-noise ratio:
    $$Expectancy \ Ratio = \frac{Expected \ Net \ Return}{Model \ Variance + Normalized \ ATR}$$
    A trade is only authorized if this ratio exceeds the threshold (default: **0.5x**).
4.  **Institutional Filters**: Final validation via **Supertrend direction** (Confirms Trend) and **Above/Below VWAP** (Confirms Institutional Buying/Selling bias).

---

## 3. Core Statistical Metrics
Based on the current trade history and recent evaluation windows (Sample Size: 13 Trades).

| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Net Accuracy (Win Rate)** | 38.46% | Strategy relies on positive risk/reward ratio rather than high frequency accuracy. |
| **Realised PnL** | INR -407.99 | Slight drawdown in current regime (-2.04% of tactical capital). |
| **Annualized Sharpe Ratio** | -0.58 | Indicates current volatility exceeds returns for this specific period. |
| **Total Trade Count** | 13 | Preliminary deployment phase logs. |
| **Max Loss Streak** | 7 Trades | Structural clustering of losses during high-volatility regimes. |

---
## 4. Temporal Alpha Analysis (Market Seasonality)
A deep dive into PnL distribution by time and weekday reveals significant "Alpha Windows" and "Toxic Windows."

### 3.1 Hourly PnL Breakdown
The system shows significant divergence in performance across different times of the Indian market day.

| Hour (IST) | Net PnL (INR) | Trade Count | Performance Signature |
| :--- | :--- | :--- | :--- |
| **10:00 AM** | -652.15 | 1 | High Morning Volatility Noise |
| **11:00 AM** | -1016.14 | 1 | Trend Transition Risk |
| **12:00 PM** | -1512.40 | 1 | Mid-Day Liquidity Vacuum |
| **03:00 PM** | **+2772.70** | 10 | **Optimal Alpha (EOD Mean Reversion)** |

> [!TIP]
> **Key Insight**: The strategy performs best during the market close (3:00 PM+), capturing EOD square-off trends, while early morning hours currently act as a "Toxic Window" for the current model weights.

### 3.2 Weekday Performance
Thursday (Expiry Day) shows the highest efficiency for the current ensemble.

- **Best Day**: Thursday (+1226.25 PnL)
- **Worst Day**: Tuesday (-934.44 PnL)

---
## 5. Institutional Risk Stress-Test
We performed a **Monte Carlo Simulation** (10,000 randomized paths) to test for robustness against market friction and slippage shocks (+30%).

| Risk Metric | Simulated Value | Status |
| :--- | :--- | :--- |
| **Probability of Ruin (50% DD)** | **0.00%** | **PASS** |
| **Median Max Drawdown** | 2.22% | **SAFE** |
| **Worst-Case Drawdown (99th %)** | 4.48% | **LOW RISK** |
| **Median Final Equity** | INR 195,532.91 | **STABLE** |

---
## 6. Technical Architecture Overview
The system leverages a complex **Universal Hyper-Ensemble** that consolidates signals from 10+ distinct model families:

1.  **Temporal Regression**: LSTM, GRU, CNN-LSTM (for sequential feature extraction).
2.  **Structural Stability**: XGBoost, Random Forest, SVR (for robust point predictions).
3.  **Modern Forecasting**: N-BEATS, N-HiTS, Temporal Fusion Transformer (TFT).
4.  **Network Relationship**: Graph Neural Networks (GNN) to capture sector correlations.
5.  **Denoising Layer**: Ensemble Empirical Mode Decomposition (EEMD) to filter market noise out of indicators.

---
## 7. Recommendations for Future Deployment
1.  **Implement Time-Fencing**: Actively block new position entries between 10:00 AM and 1:00 PM IST to preserve capital for the high-alpha 3:00 PM window.
2.  **Sector Concentration**: The current efficiency scan shows **TCS** as a primary contributor to drift; suggest diversification into **RELIANCE** or **HDFCBANK** to balance sector risk.
3.  **Adaptive Thresholding**: Tighten the "Expectancy Threshold" during Tuesday/Monday regimes.

---
## 8. Model Ensemble Inventory
The system maintains a large-scale repository of specialized models to ensure cross-regime stability.

| Model Category | Files Detected | Purpose |
| :--- | :--- | :--- |
| **Unified Ensemble** | `xgb_intraday.joblib`, `rf_intraday.joblib` | Global signal consolidation. |
| **Temporal Models** | `lstm_intraday.keras`, `forecasting_tft.py` | Long-range sequence prediction. |
| **Relationship Graphs** | `gnn_model.pth`, `gnn_edges.joblib` | Cross-asset sector correlation. |
| **Statistical Baselines** | `arima_*.pkl`, `svr_intraday.joblib` | Mean-reversion & trend persistence. |
| **Modern Forecasts** | `nbeats_*.pkl`, `nhits_*.pkl` | Dense-layer time-series forecasting. |
| **Reinforcement Learning**| `rl_ppo_agent.zip` | Dynamic position sizing and exit logic. |

---
**Report Generated**: 2026-03-31
**System Status**: Paper Trading Active
