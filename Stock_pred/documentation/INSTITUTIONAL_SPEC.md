# Institutional Quantitative Specification: Fyers AI Engine

This document defines the rigorous operational and mathematical framework for the Fyers AI Intraday Engine. It serves as the primary "Institutional Whitepaper" for the system.

---

## 1. Explicit Operational Assumptions
The system’s performance and safety rely on the following environment constants:

| Assumption | Specification | Rationale |
| :--- | :--- | :--- |
| **Slippage Model** | 20 INR flat + 0.10% variable buffer | Captures round-trip brokerage and typical bid-ask spread friction in NSE Large-Caps. |
| **Execution Latency** | 5.0 Seconds Post-Close | Bypasses the high-volatility "liquidity vacuum" often found exactly at 5-minute candle closes. |
| **Capital Range** | 2L – 50L INR | Optimized for liquid execution. Deployments >50L require multi-leg execution filters to avoid market impact. |
| **Asset Universe** | Top 10 High-LTP Stocks | Limits the universe to stocks with deep order books and high institutional participation (e.g., RELIANCE, TCS). |
| **Timeframe** | 5-Minute Epochs | Balances signal signal-to-noise ratio; prevents high-frequency churn and excessive brokerage erosion. |

---

## 2. Risk Matrix & Failure Modes
Institutional robustness assumes the system WILL fail under certain conditions. Potential failure vectors include:

*   **Cost Model Drift**: Real-world execution friction (STT, taxes, slippage) consistently exceeding the 0.0013 (13bps) modeled cost.
*   **Liquidity Shocks**: Price gapping through stop-loss levels during black-swan events (e.g., index-rebalancing or major news).
*   **Regime Misclassification**: The ADX/ATR logic incorrectly identifying a "ranging" market as "trending," leading to "Stop-Loss Churn."
*   **Model Decay (Non-Stationarity)**: The underlying structural relationships between features (VWAP/OI) shifting faster than the weekend retraining cycle can adapt.
*   **Execution Mismatch**: Significant divergence between Paper Trading fills and Live Market fills due to order-book depth.

---

## 3. Mathematical Variance Definition
In this system, **Variance** is not a simple historical residual. It is defined as an **Ensemble Uncertainty Proxy**:

$$Variance = \text{Abs}(Pred_{XGB} - Pred_{LSTM}) + \sigma_{Live}$$

*   **Model Disagreement**: The difference between the point-in-time XGBoost regressor and the temporal-memory LSTM regressor represents the "Structural Uncertainty" of the current signal.
*   **Volatility Adjustment**: Normalized ATR is added to the denominator to punish setups occurring during high-noise/high-volatility spikes.
*   **Expectancy Ratio**: Signals are only valid if $(Normalized Expected Return) / Variance \ge Threshold$.

---

## 4. Institutional Performance Targets
Target bands used to monitor system health. Breaches of these bands trigger mandatory model review or Kill Switch activation.

| Metric | Target Band | Recovery/Governance Action |
| :--- | :--- | :--- |
| **Annualized Sharpe** | 1.8 – 2.4 | If < 1.2, tighten Expectancy Threshold (+0.2). |
| **Win Rate (Net)** | 42% – 55% | If < 40%, audit model for feature-bias overfitting. |
| **Monthly Volatility** | 4.0% – 8.0% | If > 12.0%, activate Capital Allocator "Ranging" mode (0.25x). |
| **Target Drawdown** | 8.0% – 12.0% | Kill Switch triggers at 15.0% absolute peak-to-trough. |
| **Recovery Period** | 10 – 25 Days | If recovery > 45 days, halt live trading for regime audit. |

---

## 5. Governance & Compliance
- **Retraining Governance**: Banned ad-hoc training. Weights are locked Monday–Friday.
- **Exposure Control**: Maximum 2 correlated sector trades (Sector Cap); Scaled risk in ranging regimes.
- **Monte Carlo Protocol**: Weekly stress-testing of trade logs with 30% slippage shocks and block bootstrapping.
