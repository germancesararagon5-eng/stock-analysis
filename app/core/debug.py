import functools
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

MAX_LOG = 500


def _clean(val: Any) -> Any:
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, dict):
        return {k: _clean(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_clean(v) for v in val]
    if isinstance(val, tuple):
        return tuple(_clean(v) for v in val)
    return val


class DebugTracker:
    _instance: Optional["DebugTracker"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self):
        self.enabled = True
        self.requests: list[dict] = []
        self.broker_events: list[dict] = []
        self.strategy_evals: list[dict] = []
        self.errors: list[dict] = []

    # ── Request tracing ──────────────────────────────────────────────

    def track_request(
        self,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        request_body: Any = None,
        response_body: Any = None,
    ):
        if not self.enabled:
            return
        entry = dict(
            id=len(self.requests) + 1,
            method=method,
            path=path,
            status=status,
            duration_ms=round(duration_ms, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        if request_body is not None:
            entry["request"] = str(request_body)[:500]
        if response_body is not None:
            entry["response"] = str(response_body)[:500]
        self.requests.append(entry)
        if len(self.requests) > MAX_LOG:
            self.requests.pop(0)

    # ── Broker events ───────────────────────────────────────────────

    def track_broker_event(self, event: str, broker: str, details: Optional[dict] = None):
        if not self.enabled:
            return
        entry = dict(
            event=event,
            broker=broker,
            details=details or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.broker_events.append(entry)
        if len(self.broker_events) > MAX_LOG:
            self.broker_events.pop(0)

    # ── Strategy evaluations ────────────────────────────────────────

    def track_strategy(
        self,
        ticker: str,
        strategy: str,
        signal: str,
        confidence: float,
        indicators: dict,
        reasons: list,
        raw_data_shape: tuple = None,
    ):
        if not self.enabled:
            return
        entry = dict(
            ticker=ticker,
            strategy=strategy,
            signal=signal,
            confidence=confidence,
            indicators=indicators,
            reasons=reasons,
            raw_data_shape=raw_data_shape,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.strategy_evals.append(entry)
        if len(self.strategy_evals) > MAX_LOG:
            self.strategy_evals.pop(0)

    # ── Error capture ───────────────────────────────────────────────

    def track_error(self, source: str, error: str, trace: Optional[str] = None):
        if not self.enabled:
            return
        entry = dict(
            source=source,
            error=error,
            trace=trace,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.errors.append(entry)
        if len(self.errors) > MAX_LOG:
            self.errors.pop(0)

    # ── Snapshot ────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        broker_switches = [e for e in self.broker_events if e["event"] == "switch"]
        return _clean(dict(
            enabled=self.enabled,
            stats=dict(
                total_requests=len(self.requests),
                total_errors=len(self.errors),
                broker_switches=len(broker_switches),
                strategy_runs=len(self.strategy_evals),
            ),
            recent_requests=self.requests[-20:],
            recent_errors=self.errors[-10:],
            recent_broker_events=self.broker_events[-10:],
            recent_strategy_evals=self.strategy_evals[-5:],
        ))

    def clear(self):
        self._reset()


debug = DebugTracker()


# ── Decorator: time + error tracking ─────────────────────────────

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            ms = (time.perf_counter() - start) * 1000
            logger.debug("  %s  %.2fms", func.__name__, ms)
            return result
        except Exception as e:
            ms = (time.perf_counter() - start) * 1000
            debug.track_error(func.__name__, str(e), traceback.format_exc())
            logger.error("  %s  %.2fms  %s", func.__name__, ms, e)
            raise

    return wrapper


# ── ASGI middleware ──────────────────────────────────────────────

class DebugMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        method = scope["method"]
        path = scope["path"]

        async def _send(message):
            if message["type"] == "http.response.start":
                status = message["status"]
                ms = (time.perf_counter() - start) * 1000
                debug.track_request(method, path, status, ms)
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception as e:
            ms = (time.perf_counter() - start) * 1000
            debug.track_request(method, path, 500, ms)
            debug.track_error(f"{method} {path}", str(e), traceback.format_exc())
            raise
