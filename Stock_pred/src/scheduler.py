"""
Market Session Scheduler
---------------------------
Uses APScheduler to orchestrate the trading day:
  09:00 → Daily login + model warmup
  09:15 → Start scanning
  Every 5 min → Run signal scan
  15:05 → Square off all open positions
  15:30 → Generate daily P&L report
"""

from __future__ import annotations

import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

# Injected from run.py
_signal_generator = None
_order_manager    = None
_risk_guard       = None
_access_token     = None


def setup(signal_generator, order_manager, risk_guard, access_token: str) -> None:
    global _signal_generator, _order_manager, _risk_guard, _access_token
    _signal_generator = signal_generator
    _order_manager    = order_manager
    _risk_guard       = risk_guard
    _access_token     = access_token


# ─── Jobs ─────────────────────────────────────────────────────────────────────

def _job_market_open() -> None:
    """9:15 AM: Initialize risk guard with current equity."""
    log.info("[Scheduler] 🔔 Market opened — initialising session")
    summary = _order_manager.portfolio_summary()
    _risk_guard.init_session(equity=summary["total_equity"])


def _job_scan() -> None:
    """Every 5 minutes during market hours: run signal scan."""
    if not _risk_guard.is_market_open():
        return

    summary = _order_manager.portfolio_summary()
    allowed, reason = _risk_guard.allow_entry(
        current_equity=summary["total_equity"],
        open_positions=summary["open_trades"],
    )

    # Check SL/TP exits using latest LTPs from Fyers
    try:
        from src.data.fyers_fetch import fetch_live_quote_fyers
        tickers = list(_order_manager.positions.keys())
        if tickers:
            ltps = fetch_live_quote_fyers(tickers)
            _order_manager.check_exits(ltps)
            for ticker in tickers:
                if ticker in ltps:
                    _order_manager.update_trailing_sl(ticker, ltps[ticker])
    except Exception as exc:
        log.error(f"[Scheduler] LTP check failed: {exc}")

    # Generate new signals if entry is allowed
    if allowed:
        signals = _signal_generator.scan()
        for sig in signals:
            _order_manager.enter(sig)
    else:
        log.info(f"[Scheduler] ⏸ Entry blocked: {reason}")


def _job_squareoff() -> None:
    """3:05 PM: Square off all open intraday positions."""
    log.info("[Scheduler] 🔔 3:05 PM — mandatory square-off")
    try:
        from src.data.fyers_fetch import fetch_live_quote_fyers
        tickers = list(_order_manager.positions.keys())
        ltps = fetch_live_quote_fyers(tickers) if tickers else {}
        _order_manager.exit_all(ltps, reason="EOD_SQUAREOFF")
    except Exception as exc:
        log.error(f"[Scheduler] Square-off error: {exc}")
        _order_manager.exit_all({})


def _job_daily_report() -> None:
    """3:30 PM: Print end-of-day P&L summary."""
    summary = _order_manager.portfolio_summary()
    log.info(f"[Report] 📊 End of Day Summary: {summary}")
    print(f"\n{'='*50}")
    print(f"  📊 END OF DAY REPORT")
    print(f"  Cash:         ₹{summary['cash']:,.2f}")
    print(f"  Total Equity: ₹{summary['total_equity']:,.2f}")
    print(f"  Unrealised:   ₹{summary['unrealised_pnl']:,.2f}")
    print(f"{'='*50}\n")


# ─── Scheduler Builder ────────────────────────────────────────────────────────

def build_scheduler() -> BackgroundScheduler:
    """Build and return the configured APScheduler instance (not yet started)."""
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    # 9:15 AM — Market open initialisation
    scheduler.add_job(
        _job_market_open,
        CronTrigger(hour=9, minute=15, day_of_week="mon-fri", timezone="Asia/Kolkata"),
        id="market_open",
    )

    # Every 5 minutes, 9:15–15:05, Mon–Fri
    scheduler.add_job(
        _job_scan,
        CronTrigger(
            minute="*/5",
            hour="9-15",
            day_of_week="mon-fri",
            timezone="Asia/Kolkata",
        ),
        id="scan_job",
    )

    # 3:05 PM — Square off
    scheduler.add_job(
        _job_squareoff,
        CronTrigger(hour=15, minute=5, day_of_week="mon-fri", timezone="Asia/Kolkata"),
        id="squareoff",
    )

    # 3:30 PM — Daily report
    scheduler.add_job(
        _job_daily_report,
        CronTrigger(hour=15, minute=30, day_of_week="mon-fri", timezone="Asia/Kolkata"),
        id="daily_report",
    )

    return scheduler
