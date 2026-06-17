"""
Fyers DataSocket & OrderSocket — Real-Time WebSocket Feeds
----------------------------------------------------------
DataSocket  → streams live OHLCV ticks for all universe symbols
OrderSocket → streams real-time order/position updates

Both push events into thread-safe queues that the signal engine
and order manager read from.

Usage:
    from src.data.fyers_stream import DataFeed, OrderFeed
    feed = DataFeed(symbols=["RELIANCE", "TCS"])
    feed.start()
    while True:
        tick = feed.get_tick()   # blocks until next tick arrives
"""

from __future__ import annotations

import os
import queue
import threading
from typing import Any, Callable

from dotenv import load_dotenv
from fyers_apiv3.FyersWebsocket import data_ws, order_ws  # type: ignore

load_dotenv()
_CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "")


def _nse_sym(ticker: str) -> str:
    ticker = ticker.upper().strip()
    if ":" in ticker:
        return ticker
    return f"NSE:{ticker}-EQ"


# ──────────────────────────────────────────────────────────────────────────────
# DataFeed: live OHLCV tick streaming
# ──────────────────────────────────────────────────────────────────────────────

class DataFeed:
    """
    Streams live market data ticks for a list of NSE symbols.
    Internally uses Fyers DataSocket (FyersDataSocket v2.0).
    """

    def __init__(
        self,
        symbols: list[str],
        access_token: str,
        on_tick: Callable[[dict], None] | None = None,
        data_type: str = "SymbolUpdate",   # 'SymbolUpdate' = OHLCV, 'Ltp' = LTP only
    ) -> None:
        self.symbols      = [_nse_sym(s) for s in symbols]
        self._tick_queue: queue.Queue[dict] = queue.Queue()
        self._on_tick     = on_tick or self._default_on_tick
        self._access_token = access_token
        self._data_type   = data_type
        self._ws: data_ws.FyersDataSocket | None = None
        self._thread: threading.Thread | None = None

    def _default_on_tick(self, tick: dict) -> None:
        self._tick_queue.put(tick)

    def _on_error(self, err: Any) -> None:
        print(f"[DataFeed] WebSocket error: {err}")

    def _on_close(self) -> None:
        print("[DataFeed] WebSocket closed. Reconnecting...")
        self.start()  # auto-reconnect

    def _on_open(self) -> None:
        print(f"[DataFeed] ✅ Connected. Subscribing to {len(self.symbols)} symbols...")
        self._ws.subscribe(symbols=self.symbols, data_type=self._data_type)
        self._ws.keep_running()

    def start(self) -> None:
        """Start the WebSocket in a background daemon thread."""
        self._ws = data_ws.FyersDataSocket(
            access_token=f"{_CLIENT_ID}:{self._access_token}",
            log_path="artifacts/fyers_logs",
            litemode=False,
            write_to_file=False,
            reconnect=True,
            on_connect=self._on_open,
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_tick,
        )
        self._thread = threading.Thread(target=self._ws.connect, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._ws:
            self._ws.close_connection()

    def get_tick(self, timeout: float = 30.0) -> dict | None:
        """Block until a tick arrives or timeout. Returns None on timeout."""
        try:
            return self._tick_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_all_ticks(self) -> list[dict]:
        """Drain all pending ticks from the queue without blocking."""
        ticks: list[dict] = []
        while not self._tick_queue.empty():
            try:
                ticks.append(self._tick_queue.get_nowait())
            except queue.Empty:
                break
        return ticks


# ──────────────────────────────────────────────────────────────────────────────
# OrderFeed: live order/position/trade updates
# ──────────────────────────────────────────────────────────────────────────────

class OrderFeed:
    """
    Streams real-time order status, position, and trade updates from Fyers.
    """

    def __init__(
        self,
        access_token: str,
        on_order_update: Callable[[dict], None] | None = None,
    ) -> None:
        self._access_token = access_token
        self._event_queue: queue.Queue[dict] = queue.Queue()
        self._on_order_update = on_order_update or self._default_handler
        self._ws: order_ws.FyersOrderSocket | None = None

    def _default_handler(self, msg: dict) -> None:
        self._event_queue.put(msg)

    def _on_error(self, err: Any) -> None:
        print(f"[OrderFeed] Error: {err}")

    def _on_close(self) -> None:
        print("[OrderFeed] Closed. Reconnecting...")
        self.start()

    def _on_open(self) -> None:
        print("[OrderFeed] ✅ Connected to Order Socket.")

    def start(self) -> None:
        self._ws = order_ws.FyersOrderSocket(
            access_token=f"{_CLIENT_ID}:{self._access_token}",
            write_to_file=False,
            log_path="artifacts/fyers_logs",
            on_connect=self._on_open,
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_order_update,
        )
        thread = threading.Thread(target=self._ws.connect, daemon=True)
        thread.start()

    def stop(self) -> None:
        if self._ws:
            self._ws.close_connection()

    def get_event(self, timeout: float = 5.0) -> dict | None:
        try:
            return self._event_queue.get(timeout=timeout)
        except queue.Empty:
            return None
