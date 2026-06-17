"""
Real-Time Signal Generator
---------------------------
Runs every 5 minutes on candle-close and:
  1. Fetches latest candles for each ticker in the universe
  2. Engineers features
  3. Applies model prediction + filter rules
  4. Emits SignalEvent objects for the order manager to consume
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List

import pandas as pd

from src.data.fyers_fetch import fetch_intraday_fyers
from src.features.engineering import build_intraday_features
from src.features.drift_monitor import DriftMonitor
from src.models.intraday_predictor import IntradayPredictor, SignalResult

log = logging.getLogger(__name__)


@dataclass
class ScanConfig:
    universe:        List[str]   = field(default_factory=list)
    interval:        str         = "5minute"
    lookback_days:   int         = 30
    expectancy_threshold: float  = 0.5
    min_supertrend:  int         = 1    # 1 = only trade bullish Supertrend candles
    require_above_vwap: bool     = True
    sl_atr_mult:     float       = 1.5
    tp_atr_mult:     float       = 3.0
    execution_delay_seconds: int = 5     # Wait for spreads to settle post-close
    save_dir:        str         = "artifacts"


class SignalGenerator:
    """
    Scans the universe every 5-minute candle close and yields BUY signals.
    """

    def __init__(self, cfg: ScanConfig) -> None:
        self.cfg       = cfg
        self.predictor = IntradayPredictor(save_dir=cfg.save_dir)
        self.drift_mon = DriftMonitor(save_dir=cfg.save_dir)
        self._callbacks: List[Callable[[SignalResult], None]] = []

    def on_signal(self, callback: Callable[[SignalResult], None]) -> None:
        """Register a callback invoked whenever a BUY signal is generated."""
        self._callbacks.append(callback)

    def _emit(self, signal: SignalResult) -> None:
        for cb in self._callbacks:
            try:
                cb(signal)
            except Exception as exc:
                log.error(f"[Signal] Callback error: {exc}")

    def scan(self) -> List[SignalResult]:
        """
        Run one full scan of all tickers. Returns list of BUY signals.
        Called every 5 minutes by the scheduler.
        """
        import time
        if getattr(self.cfg, 'execution_delay_seconds', 0) > 0:
            log.info(f"[Scanner] ⏳ Waiting {self.cfg.execution_delay_seconds}s for post-close liquidity trap to clear...")
            time.sleep(self.cfg.execution_delay_seconds)

        signals: List[SignalResult] = []
        now = datetime.now().strftime("%H:%M:%S")
        log.info(f"[Scanner] Scanning {len(self.cfg.universe)} tickers at {now}")

        for ticker in self.cfg.universe:
            try:
                df_raw = fetch_intraday_fyers(
                    ticker,
                    interval=self.cfg.interval,
                    days_back=self.cfg.lookback_days,
                )
                if len(df_raw) < 60:
                    log.warning(f"[Scanner] {ticker}: insufficient data ({len(df_raw)} rows)")
                    continue

                df = build_intraday_features(df_raw)
                if df.empty:
                    continue

                # ── Filter rules before model ─────────────────────────────
                latest = df.iloc[-1]

                # 2. Data Drift Check (FM-2) — WARNING ONLY, never blocks live trades
                # Full block re-enabled after weekend retrain.
                drift_status = self.drift_mon.check_drift(df)
                drift_ratio = drift_status.get("drift_ratio", 0)
                if drift_status.get("is_drifting_critically"):
                    log.warning(f"[Scanner] {ticker} drift ratio={drift_ratio:.0%} — trading anyway (retrain needed)")

                # 3. AI Meta-Model Prediction (FM-3 if rejected)
                result = self.predictor.predict(
                    ticker,
                    df,
                    expectancy_threshold=self.cfg.expectancy_threshold,
                    sl_atr_mult=self.cfg.sl_atr_mult,
                    tp_atr_mult=self.cfg.tp_atr_mult,
                )

                if result.signal in ["BUY", "SELL"]:
                    # Symmetric Regime Filters: Ensure we trade WITH the trend
                    if result.signal == "BUY":
                        if self.cfg.min_supertrend > 0 and latest.get("supertrend_dir", 0) != 1:
                            log.debug(f"[Scanner] {ticker} BUY rejected: Bearish Supertrend")
                            continue
                        if self.cfg.require_above_vwap and latest.get("above_vwap", 0) != 1:
                            log.debug(f"[Scanner] {ticker} BUY rejected: Below VWAP")
                            continue
                    
                    elif result.signal == "SELL":
                        if self.cfg.min_supertrend > 0 and latest.get("supertrend_dir", 0) != -1:
                            log.debug(f"[Scanner] {ticker} SELL rejected: Bullish Supertrend")
                            continue
                        if self.cfg.require_above_vwap and latest.get("above_vwap", 0) != -1: # -1 means below VWAP
                            log.debug(f"[Scanner] {ticker} SELL rejected: Above VWAP")
                            continue

                    log.info(
                        f"[Signal] ✅ {result.signal} {ticker} | exp_net_r={result.expected_net_r:.4f} ratio={result.expectancy_ratio:.2f} "
                        f"entry={result.entry} SL={result.stop_loss} TP={result.take_profit}"
                    )
                    signals.append(result)
                    self._emit(result)
                else:
                    log.debug(f"[Scanner] {ticker} rejected: Low Expectancy/Ratio (FM-3)")

            except Exception as exc:
                log.error(f"[Scanner] Error scanning {ticker}: {exc}")

        return signals
