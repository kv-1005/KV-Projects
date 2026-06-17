"""
run.py — Main entry point for the Fyers AI Trading System
----------------------------------------------------------
Usage:
    python run.py --config config/nse_intraday.json --paper   # Safe paper mode
    python run.py --config config/nse_intraday.json --live    # Real money (be careful!)
    python run.py --train                                      # Retrain the AI model
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log     = logging.getLogger("trading_system")
console = Console()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fyers AI Short-Term Trading System")
    p.add_argument("--config", type=str, default="config/nse_intraday.json")
    p.add_argument("--paper",  action="store_true", help="Paper trading mode (default)")
    p.add_argument("--live",   action="store_true", help="Live trading (USE WITH CARE)")
    p.add_argument("--train",  action="store_true", help="Retrain AI model then exit")
    p.add_argument("--backtest", action="store_true", help="Run historical backtest")
    p.add_argument("--lookback", type=int, default=30, help="Days to backtest (default 30)")
    p.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard")
    p.add_argument("--artifacts", type=str, default="artifacts")
    return p.parse_args()


def load_config(path: str) -> dict:
    import json
    with open(path) as f:
        return json.load(f)


def run_training(cfg: dict, artifacts: str) -> None:
    """Fetch historical data and train the Universal Hyper-Ensemble (10+ Models)."""
    from src.data.fyers_fetch import fetch_intraday_fyers
    from src.features.engineering import build_intraday_features
    from src.training.train_universal import train_universal_ensemble
    import pandas as pd

    console.rule("[bold green] Training Universal Hyper-Ensemble (Singularity V2)")
    frames = []
    
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[green]Fetching Universe Data...", total=len(cfg["universe"]))
        
        for ticker in cfg["universe"]:
            progress.update(task, description=f"[cyan]Fetching {ticker}...")
            try:
                df = fetch_intraday_fyers(ticker, interval=cfg["interval"], days_back=90)
                df = build_intraday_features(df)
                df["ticker"] = ticker
                frames.append(df)
            except Exception as exc:
                console.log(f"[red]Failed {ticker}: {exc}")
            progress.advance(task)

    if not frames:
        console.log("[red]No data fetched. Exiting.")
        sys.exit(1)

    combined = pd.concat(frames).sort_index()
    train_universal_ensemble(combined, cfg, artifacts=artifacts)
    console.rule("[bold green] Universal Singularity V2 Training Complete")


def run_dashboard() -> None:
    """Launch the Streamlit dashboard in a subprocess."""
    import subprocess
    subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py",
         "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    console.log("[green]📊 Dashboard running at http://localhost:8501")


def run_backtest(cfg: dict, lookback: int, artifacts: str) -> None:
    """Historical intraday backtest using the same components as live trading."""
    from src.data.fyers_fetch import fetch_intraday_fyers
    from src.features.engineering import build_intraday_features
    from src.signal.generator import ScanConfig, SignalGenerator
    from src.orders.manager import OrderManager
    from src.models.intraday_predictor import SignalResult
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    console.rule(f"[bold blue] Starting {lookback}-Day Historical Backtest")
    
    # 0. Pre-authenticate (ensure login happens outside Progress bars)
    from src.data.fyers_client import get_fyers_client
    get_fyers_client()
    
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    
    # 1. Fetch data for all tickers
    data_map = {}
    all_timestamps = set()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[green]Fetching Backtest Data...", total=len(cfg["universe"]))
        for ticker in cfg["universe"]:
            progress.update(task, description=f"[cyan]Fetching {ticker}...")
            try:
                df = fetch_intraday_fyers(ticker, interval=cfg["interval"], days_back=lookback)
                df = build_intraday_features(df)
                data_map[ticker] = df
                all_timestamps.update(df.index)
            except Exception as e:
                console.log(f"[red]Error fetching {ticker}: {e}")
            progress.advance(task)
            
    sorted_ts = sorted(list(all_timestamps))
    if not sorted_ts:
        console.log("[red]No data found for backtest.")
        return

    # 2. Setup Components
    scan_cfg = ScanConfig(
        universe=cfg["universe"],
        interval=cfg["interval"],
        expectancy_threshold=cfg.get("expectancy_threshold", 0.5),
        sl_atr_mult=cfg.get("stop_loss_atr_mult", 1.5),
        tp_atr_mult=cfg.get("take_profit_atr_mult", 3.0),
        save_dir=artifacts,
    )
    
    signal_gen = SignalGenerator(cfg=scan_cfg)
    order_mgr = OrderManager(
        capital=float(cfg.get("paper_capital", 200_000)),
        max_positions=cfg.get("max_positions", 5),
        risk_per_trade_pct=cfg.get("risk_per_trade_pct", 0.01),
        save_dir=artifacts
    )

    # 3. Batch Pre-calculate Signals (The Optimization)
    with console.status("[yellow]Batching AI predictions...") as status:
        signal_map = signal_gen.predictor.batch_predict(
            data_map,
            expectancy_threshold=scan_cfg.expectancy_threshold,
            sl_atr_mult=scan_cfg.sl_atr_mult,
            tp_atr_mult=scan_cfg.tp_atr_mult
        )

    # 4. Replay Loop
    # We skip the first 60 candles to ensure indicators are primed
    from rich.progress import track
    
    console.log(f"[yellow]Priming indicators (skipping first 60 mins)...")
    
    for ts in track(sorted_ts[60:], description="Simulating Market..."):
        # Update Order Manager on every step
        for ticker in list(order_mgr.positions.keys()):
            df = data_map.get(ticker)
            if df is None or ts not in df.index:
                continue
            
            row = df.loc[ts]
            pos = order_mgr.positions[ticker]
            # Precise SL/TP logic for both Long (BUY) and Short (SELL)
            low, high, close = float(row['Low']), float(row['High']), float(row['Close'])
            
            if pos.side == "SELL":
                # SHORT EXIT RULES
                if high >= pos.stop_loss:
                    order_mgr.exit(ticker, pos.stop_loss, reason="STOP_LOSS", timestamp=ts)
                elif low <= pos.take_profit:
                    order_mgr.exit(ticker, pos.take_profit, reason="TAKE_PROFIT", timestamp=ts)
                elif ts.hour == 15 and ts.minute >= 5: # EOM Squareoff
                    order_mgr.exit(ticker, close, reason="EOD_SQUAREOFF", timestamp=ts)
            else:
                # LONG EXIT RULES
                if low <= pos.stop_loss:
                    order_mgr.exit(ticker, pos.stop_loss, reason="STOP_LOSS", timestamp=ts)
                elif high >= pos.take_profit:
                    order_mgr.exit(ticker, pos.take_profit, reason="TAKE_PROFIT", timestamp=ts)
                elif ts.hour == 15 and ts.minute >= 5: # EOM Squareoff
                    order_mgr.exit(ticker, close, reason="EOD_SQUAREOFF", timestamp=ts)

        # Scan for new signals (Optimization: Simple lookup from pre-calculated map)
        # Institutional Time-Fencing: No new entries after 14:30 IST
        is_entry_window = ts.hour < 14 or (ts.hour == 14 and ts.minute < 30)
        
        if is_entry_window and len(order_mgr.positions) < order_mgr.max_positions:
            for ticker in cfg["universe"]:
                if ticker in order_mgr.positions: continue
                
                # Instant lookup instead of expensive .predict() call
                result = signal_map.get((ts, ticker))
                if result and result.signal in ["BUY", "SELL"]:
                    order_mgr.enter(result)

    # 5. Final Square-off (Close any remaining positions at the last known price)
    last_ts = sorted_ts[-1]
    final_ltps = {ticker: float(data_map[ticker].loc[last_ts, "Close"]) for ticker in cfg["universe"] if ticker in data_map and last_ts in data_map[ticker].index}
    order_mgr.exit_all(final_ltps, reason="BACKTEST_END_SQUAREOFF", timestamp=last_ts)

    console.rule("[bold blue] Backtest Complete")
    summary = order_mgr.portfolio_summary()
    console.print(f"  [bold]Final Equity[/]: ₹{summary['total_equity']:,.2f}")
    console.print(f"  [bold]Realised PnL[/]: ₹{summary['realised_pnl']:,.2f}")
    console.print(f"  [bold]Open Positions[/]: {summary['open_trades']}")
    console.print(f"\n[green]Check {os.path.join(artifacts, 'trade_log.csv')} for full history.")


def main() -> None:
    args = parse_args()
    cfg  = load_config(args.config)

    # ── Backtest Mode ────────────────────────────────────────────────────────
    if args.backtest:
        run_backtest(cfg, args.lookback, args.artifacts)
        return

    # Override live/paper via flag
    if args.live:
        os.environ["LIVE_TRADING"] = "true"
        console.print("[bold red]⚠ LIVE TRADING ENABLED — REAL MONEY MODE[/]")
    else:
        os.environ["LIVE_TRADING"] = "false"
        console.print("[bold yellow]📄 Paper Trading Mode (safe)[/]")

    # ── Login ────────────────────────────────────────────────────────────────
    from src.data.fyers_client import get_fyers_client
    fyers = get_fyers_client()

    # Read the cached access token for WebSocket
    access_token = open(".fyers_token").read().strip()

    # ── Train-only mode ──────────────────────────────────────────────────────
    if args.train:
        run_training(cfg, args.artifacts)
        return

    # ── Check model exists ───────────────────────────────────────────────────
    model_path = os.path.join(args.artifacts, "xgb_intraday.joblib")
    if not os.path.exists(model_path):
        console.print("[yellow]No model found. Running training first...[/]")
        run_training(cfg, args.artifacts)

    # ── Build components ─────────────────────────────────────────────────────
    from src.signal.generator import ScanConfig, SignalGenerator
    from src.orders.manager   import OrderManager
    from src.orders.risk_guard import RiskGuard
    from src.orders.kill_switch import SystemKillSwitch
    from src.scheduler        import setup as scheduler_setup, build_scheduler

    capital = float(cfg.get("paper_capital", 200_000))

    # Calculate Adaptive Expectancy Threshold using Institutional Governance Bands
    # As per INSTITUTIONAL_SPEC.md: If Sharpe < 1.2, tighten Expectancy Threshold (+0.2)
    dynamic_threshold = cfg.get("expectancy_threshold", 0.5)
    try:
        trade_log_path = os.path.join(args.artifacts, "trade_log.csv")
        if os.path.exists(trade_log_path):
            import pandas as pd
            log_df = pd.read_csv(trade_log_path)
            exits = log_df[log_df["action"] == "EXIT"]
            if len(exits) >= 5:
                # Use the 'sharpe' column directly from our logs
                current_sharpe = exits["sharpe"].iloc[-1]
                if current_sharpe < 1.2:
                    log.info(f"[Governance] 🛡️ Sharpe {current_sharpe:.2f} < 1.2. Tightening Expectancy Threshold (+0.2)")
                    dynamic_threshold += 0.2
                elif current_sharpe > 2.4:
                    log.info(f"[Governance] 🟢 Sharpe {current_sharpe:.2f} > 2.4. Loosening threshold (-0.1)")
                    dynamic_threshold -= 0.1
                
                dynamic_threshold = max(0.4, min(1.2, dynamic_threshold)) 
    except Exception as e:
        log.error(f"[Governance] Error calculating adaptive bands: {e}")
        pass

    scan_cfg = ScanConfig(
        universe         = cfg["universe"],
        interval         = cfg.get("interval", "5minute"),
        lookback_days    = cfg.get("lookback_days", 30),
        expectancy_threshold = dynamic_threshold,
        require_above_vwap = cfg.get("require_above_vwap", True),
        sl_atr_mult      = cfg.get("stop_loss_atr_mult", 1.5),
        tp_atr_mult      = cfg.get("take_profit_atr_mult", 3.0),
        save_dir         = args.artifacts,
    )

    signal_gen = SignalGenerator(cfg=scan_cfg)
    order_mgr  = OrderManager(
        capital            = capital,
        max_positions      = cfg.get("max_positions", 5),
        risk_per_trade_pct = cfg.get("risk_per_trade_pct", 0.01),
        save_dir           = args.artifacts,
    )
    risk_guard = RiskGuard(
        max_daily_loss_pct = cfg.get("max_daily_loss_pct", 0.02),
        max_positions      = cfg.get("max_positions", 5),
    )
    kill_switch = SystemKillSwitch()

    # Wire signal → order / alarms
    def handle_signal(sig: SignalResult) -> None:
        metrics = order_mgr.perf_monitor.get_metrics()
        current_vol = metrics.get("volatility", 0.0)
        
        # Periodic update of Kill Switch with latest equity and metrics
        kill_switch.update_equity(
            current_equity=order_mgr.portfolio_summary()["total_equity"],
            volatility=current_vol
        )

        if getattr(sig, "is_drifting", False):
            log.warning(f"[Safety] ⚡ Data Drift signal received. Skipping entry to prevent structural risk.")
            return
            
        if not kill_switch.is_killed and risk_guard.allow_entry(
            order_mgr.portfolio_summary()["total_equity"],
            len(order_mgr.positions)
        )[0]:
            order_mgr.enter(sig)

    signal_gen.on_signal(handle_signal)

    # Note: A background task should idealistically update the kill_switch on every PNL change.
    # For now, we update it post-exit inside the scheduler's EOD or during live updates.

    # ── Scheduler ────────────────────────────────────────────────────────────
    scheduler_setup(signal_gen, order_mgr, risk_guard, access_token)
    scheduler = build_scheduler()
    scheduler.start()

    # ── Dashboard ────────────────────────────────────────────────────────────
    if args.dashboard:
        run_dashboard()

    console.rule("[bold green] System Started")
    console.print("[green]✅ AI Trading System is running.[/]")
    console.print("   Signals scan every 5 minutes during market hours.")
    console.print("   Mandatory square-off at 3:05 PM IST.")
    console.print("   Press [bold]Ctrl+C[/] to stop.\n")

    try:
        threading.Event().wait()   # block main thread
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/]")
        scheduler.shutdown()
        console.print("[green]Goodbye![/]")


if __name__ == "__main__":
    main()
