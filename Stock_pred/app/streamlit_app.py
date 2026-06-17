"""
Fyers AI Trading — Live Streamlit Dashboard
--------------------------------------------
Run with: streamlit run app/streamlit_app.py
"""

import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fyers AI Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e1a; }

.metric-card {
    background: linear-gradient(135deg, #1a1f35 0%, #141829 100%);
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}
.metric-value { font-size: 2rem; font-weight: 700; color: #63b3ed; }
.metric-label { font-size: 0.8rem; color: #718096; text-transform: uppercase; letter-spacing: 1px; }

.signal-card {
    background: linear-gradient(135deg, #1a2e1a 0%, #122012 100%);
    border: 1px solid rgba(72,187,120,0.3);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.signal-ticker { font-size: 1.1rem; font-weight: 700; color: #48bb78; }
.signal-meta   { font-size: 0.8rem; color: #a0aec0; }

.pos-card {
    background: linear-gradient(135deg, #1a1f35 0%, #141829 100%);
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
}

.status-open  { color: #48bb78; font-weight: 700; }
.status-closed{ color: #fc8181; font-weight: 700; }
.pnl-pos { color: #48bb78; }
.pnl-neg { color: #fc8181; }

/* Header bar */
.header-bar {
    background: linear-gradient(90deg, #1a1f35, #0d1117);
    border-bottom: 1px solid rgba(99,179,237,0.2);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 12px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

ARTIFACTS = "artifacts"
TRADE_LOG = os.path.join(ARTIFACTS, "trade_log.csv")
CONFIG    = "config/nse_intraday.json"


# ── Data Loaders ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def load_trade_log() -> pd.DataFrame:
    if not os.path.exists(TRADE_LOG):
        return pd.DataFrame()
    df = pd.read_csv(TRADE_LOG, parse_dates=["timestamp"])
    return df.sort_values("timestamp", ascending=False)


def load_config() -> dict:
    if os.path.exists(CONFIG):
        with open(CONFIG) as f:
            return json.load(f)
    return {}


def market_status() -> tuple[str, str]:
    now = datetime.now()
    wd  = now.weekday()
    hm  = now.hour * 60 + now.minute
    if wd >= 5:
        return "CLOSED", "#fc8181"
    if 555 <= hm < 915:    # 9:15 – 15:15
        return "OPEN", "#48bb78"
    return "CLOSED", "#fc8181"


def time_to_event() -> str:
    now = datetime.now()
    hm  = now.hour * 60 + now.minute
    if hm < 555:
        mins = 555 - hm
        return f"Opens in {mins // 60}h {mins % 60}m"
    if hm < 915:
        mins = 915 - hm
        return f"Closes in {mins // 60}h {mins % 60}m"
    return "Market closed"


# ── Header ────────────────────────────────────────────────────────────────────

status, status_color = market_status()

st.markdown(f"""
<div class="header-bar">
    <div style="display:flex;align-items:center;gap:14px">
        <span style="font-size:1.8rem">📈</span>
        <div>
            <div style="font-size:1.3rem;font-weight:700;color:#e2e8f0">Fyers AI Trader</div>
            <div style="font-size:0.8rem;color:#718096">NSE Intraday • Dual-AI (XGBoost + LSTM) • Supertrend + VWAP</div>
        </div>
    </div>
    <div style="text-align:right">
        <div style="font-size:1.1rem;font-weight:700;color:{status_color}">● {status}</div>
        <div style="font-size:0.8rem;color:#718096">{time_to_event()} &nbsp;|&nbsp; {datetime.now().strftime('%d %b %Y %H:%M:%S')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Live Metrics Row ──────────────────────────────────────────────────────────

df_log = load_trade_log()
cfg    = load_config()
paper_cap = cfg.get("paper_capital", 200_000)

completed = df_log[df_log["action"] == "EXIT"] if not df_log.empty else pd.DataFrame()
total_pnl  = completed["pnl"].sum() if not completed.empty else 0.0
trade_cnt  = len(completed)
win_rate   = (
    f"{(completed['pnl'] > 0).mean() * 100:.1f}%"
    if not completed.empty else "—"
)
open_cnt   = len(df_log[df_log["action"] == "ENTER"]) - len(completed) if not df_log.empty else 0

pnl_color  = "#48bb78" if total_pnl >= 0 else "#fc8181"
pnl_sign   = "+" if total_pnl >= 0 else ""

c1, c2, c3, c4, c5, c6 = st.columns(6)
# High-Integrity Sharpe Calculation (Full-Horizon)
if not completed.empty and len(completed) > 1:
    returns = completed["pnl"] / paper_cap
    full_sharpe = (returns.mean() / (returns.std() + 1e-12)) * (252 ** 0.5)
    max_dd = (completed["drawdown_pct"].max()) if "drawdown_pct" in completed.columns else 0.0
else:
    full_sharpe = 0.0
    max_dd = 0.0

metrics = [
    (c1, f"₹{paper_cap + total_pnl:,.0f}", "Total Equity"),
    (c2, f"{pnl_sign}₹{total_pnl:,.0f}", "Realised P&L"),
    (c3, win_rate, "Win Rate"),
    (c4, f"{full_sharpe:.2f}", "Full Sharpe"),
    (c5, f"{max_dd:.1f}%", "Max DD"),
    (c6, str(max(open_cnt, 0)), "Open"),
]
for col, val, label in metrics:
    with col:
        color = pnl_color if "P&L" in label else "#63b3ed"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{color}">{val}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Layout: 2 columns ─────────────────────────────────────────────────────────

left, right = st.columns([1.3, 1])

# ── Left: Equity Curve ────────────────────────────────────────────────────────

with left:
    st.markdown("#### 📊 Equity Curve (Today)")
    if not completed.empty:
        eq_df = completed.copy().sort_values("timestamp")
        eq_df["cumulative_pnl"] = eq_df["pnl"].cumsum()
        eq_df["equity"]         = paper_cap + eq_df["cumulative_pnl"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=eq_df["timestamp"], y=eq_df["equity"],
            mode="lines+markers",
            line=dict(color="#63b3ed", width=2.5),
            marker=dict(size=6, color="#63b3ed"),
            fill="tonexty",
            fillcolor="rgba(99,179,237,0.08)",
            name="Equity",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
            xaxis=dict(showgrid=False, color="#718096"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#718096"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completed trades yet. Equity curve will appear after first exit.")

    # ── Trade Journal ─────────────────────────────────────────────────────────
    st.markdown("#### 📋 Trade Journal")
    if not df_log.empty:
        show_cols = ["timestamp", "action", "ticker", "qty", "price", "pnl", "reason", "mode"]
        display_df = df_log[show_cols].head(30).copy()
        display_df["pnl"] = display_df["pnl"].apply(
            lambda x: f"+₹{x:.2f}" if x > 0 else f"₹{x:.2f}"
        )
        st.dataframe(
            display_df,
            use_container_width=True,
            height=280,
        )
    else:
        st.info("No trades logged yet.")

# ── Right: Signals + Mode ─────────────────────────────────────────────────────

with right:
    # Mode indicator
    live_mode = os.getenv("LIVE_TRADING", "false").lower() == "true"
    mode_str  = "🔴 LIVE TRADING" if live_mode else "📄 PAPER MODE"
    mode_col  = "#fc8181" if live_mode else "#f6ad55"
    st.markdown(f"""
    <div style="background:rgba(0,0,0,0.3);border:1px solid {mode_col}44;
    border-radius:10px;padding:12px 18px;margin-bottom:16px;text-align:center">
        <span style="color:{mode_col};font-size:1rem;font-weight:700">{mode_str}</span><br>
        <span style="color:#718096;font-size:0.78rem">
            {'Real orders placed on Fyers account' if live_mode else 'No real orders — simulated fills only'}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── AI Signal Feed ────────────────────────────────────────────────────────
    st.markdown("#### 🤖 AI Signal Feed")
    buy_signals = df_log[df_log["action"] == "ENTER"] if not df_log.empty else pd.DataFrame()
    if not buy_signals.empty:
        for _, row in buy_signals.head(8).iterrows():
            ts  = pd.to_datetime(row["timestamp"]).strftime("%H:%M:%S")
            st.markdown(f"""
            <div class="signal-card">
                <div class="signal-ticker">✅ BUY {row['ticker']}</div>
                <div class="signal-meta">
                    Qty: {row['qty']} &nbsp;|&nbsp; Entry: ₹{row['price']:.2f}
                    &nbsp;|&nbsp; {ts} &nbsp;|&nbsp; {row.get('mode','PAPER')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="color:#718096;padding:30px;text-align:center;
        border:1px dashed rgba(255,255,255,0.1);border-radius:10px">
            🔍 Scanning for signals...<br>
            <span style="font-size:0.8rem">Signals appear here during market hours</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Universe being watched ────────────────────────────────────────────────
    st.markdown("#### 👁 Watching Universe")
    universe = cfg.get("universe", [])
    if universe:
        cols_uni = st.columns(3)
        for i, tick in enumerate(universe):
            with cols_uni[i % 3]:
                st.markdown(f"""
                <div style="background:rgba(99,179,237,0.08);border:1px solid rgba(99,179,237,0.2);
                border-radius:8px;padding:8px;text-align:center;margin-bottom:8px;
                font-size:0.85rem;color:#63b3ed;font-weight:600">{tick}</div>
                """, unsafe_allow_html=True)

    # ── Risk Params ───────────────────────────────────────────────────────────
    st.markdown("#### 🛡 Risk Config")
    st.markdown(f"""
    <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.07);
    border-radius:10px;padding:14px 18px;font-size:0.85rem;color:#a0aec0">
        Max Positions: <b style="color:#e2e8f0">{cfg.get('max_positions',5)}</b> &nbsp;|&nbsp;
        Daily Loss Limit: <b style="color:#fc8181">{cfg.get('max_daily_loss_pct',0.02)*100:.0f}%</b><br>
        Signal Expectancy: <b style="color:#63b3ed">{cfg.get('expectancy_threshold',0.5):.2f}x Ratio</b> &nbsp;|&nbsp;
        Risk/Trade: <b style="color:#e2e8f0">{cfg.get('risk_per_trade_pct',0.01)*100:.0f}%</b>
    </div>
    """, unsafe_allow_html=True)

# ── Auto-refresh every 10 seconds ────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#4a5568;font-size:0.75rem'>"
    "🔄 Auto-refreshes every 10 seconds during market hours</div>",
    unsafe_allow_html=True,
)
time.sleep(10)
st.rerun()
