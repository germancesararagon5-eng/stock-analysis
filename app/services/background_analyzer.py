import asyncio
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.debug import debug
from app.database import SessionLocal
from app.models import BackgroundResult
from app.services.analysis_service import run_analysis
from app.services.prediction_service import resolve_predictions, store_prediction

logger = logging.getLogger(__name__)


class BackgroundAnalyzer:
    def __init__(self):
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._config: dict[str, Any] = self._default_config()
        self._results: list[dict] = []

    def _default_config(self) -> dict:
        return {
            "enabled": False,
            "tickers": [],
            "strategy": "scalping",
            "interval": "5m",
            "periods": 100,
            "min_confidence": 0.2,
            "alert_whatsapp": False,
            "run_every_seconds": 300,
            "last_run": None,
            "max_results": 50,
        }

    def get_config(self) -> dict:
        with self._lock:
            cfg = dict(self._config)
            cfg.pop("max_results", None)
            return cfg

    def update_config(self, updates: dict) -> dict:
        allowed = {"tickers", "strategy", "interval", "periods",
                   "min_confidence", "alert_whatsapp", "run_every_seconds"}
        with self._lock:
            for k, v in updates.items():
                if k in allowed:
                    self._config[k] = v
            if self._config["enabled"]:
                self._stop_event.set()
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=5)
                self._stop_event.clear()
                self._thread = threading.Thread(target=self._loop, daemon=True)
                self._thread.start()
        return self.get_config()

    def start(self) -> dict:
        with self._lock:
            if self._config["enabled"]:
                return {"status": "already_running"}
            self._config["enabled"] = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            logger.info("Background analyzer started")
        return {"status": "started"}

    def stop(self) -> dict:
        with self._lock:
            if not self._config["enabled"]:
                return {"status": "already_stopped"}
            self._config["enabled"] = False
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
            logger.info("Background analyzer stopped")
        return {"status": "stopped"}

    def get_results(self, limit: int = 20) -> list[dict]:
        try:
            db = SessionLocal()
            try:
                rows = (
                    db.query(BackgroundResult)
                    .order_by(BackgroundResult.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [
                    {
                        "ticker": r.ticker,
                        "signal": r.signal,
                        "confidence": r.confidence,
                        "price": r.price,
                        "strategy": r.strategy,
                        "interval": r.interval,
                        "periods": r.periods,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in rows
                    if r.error is None
                ]
            finally:
                db.close()
        except Exception:
            logger.exception("Error reading background results from DB")
            with self._lock:
                return list(self._results[-limit:])

    def _loop(self):
        logger.info("Background analyzer loop started")
        while not self._stop_event.is_set():
            try:
                self._run_cycle()
            except Exception as e:
                logger.exception("Background analyzer cycle error: %s", e)
                debug.track_error("background_analyzer", str(e))
            for _ in range(int(self._config["run_every_seconds"])):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def _run_cycle(self):
        with self._lock:
            tickers = list(self._config["tickers"])
            strategy = self._config["strategy"]
            interval = self._config["interval"]
            periods = self._config["periods"]
            min_conf = self._config["min_confidence"]
            alert_wa = self._config["alert_whatsapp"]

        if not tickers:
            tickers = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META",
                "TSLA", "JPM", "V", "JNJ", "WMT", "PG",
                "SPY", "QQQ", "BTC-USD", "ETH-USD",
            ]

        batch_results = []
        for ticker in tickers:
            if self._stop_event.is_set():
                break
            try:
                result = run_analysis(
                    ticker=ticker,
                    strategy=strategy,
                    interval=interval,
                    periods=periods,
                    store_prediction=False,  # BG analyzer stores manually
                )
                entry = {
                    "ticker": ticker,
                    "signal": result.get("signal", "NEUTRAL"),
                    "confidence": result.get("confidence", 0.0),
                    "price": result.get("indicators", {}).get("price"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                batch_results.append(entry)

                if entry["confidence"] >= min_conf:
                    store_prediction(
                        ticker=ticker,
                        signal=entry["signal"],
                        confidence=entry["confidence"],
                        strategy=strategy,
                        interval=interval,
                        periods=periods,
                        price=entry["price"],
                        reasons=result.get("reasons", []),
                        indicators=result.get("indicators"),
                    )

                if entry["signal"] in ("BUY", "SELL") and entry["confidence"] >= min_conf:
                    reasons = result.get("reasons", [])
                    msg = (
                        f" SEÑAL {entry['signal']} ({entry['confidence']:.0%}) | "
                        f"{ticker} | {strategy} | ${entry['price'] or 'N/A'} | "
                        f"{' | '.join(reasons)}"
                    )
                    logger.info("BACKGROUND SIGNAL: %s", msg)
                    debug.track_broker_event("background_signal", "background_analyzer", {
                        "ticker": ticker, "signal": entry["signal"],
                        "confidence": entry["confidence"],
                    })
                    if alert_wa:
                        from app.services.whatsapp_service import send_alert
                        send_alert(msg)

            except Exception as e:
                logger.warning("Background analysis failed for %s: %s", ticker, e)
                batch_results.append({
                    "ticker": ticker, "signal": "ERROR",
                    "confidence": 0.0, "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        # Resolve pending predictions
        try:
            resolved = resolve_predictions(count=20)
            if resolved:
                logger.info("Resolved %d predictions", resolved)
        except Exception as e:
            logger.warning("Prediction resolution error: %s", e)

        # Persist batch results to DB
        try:
            db = SessionLocal()
            try:
                for entry in batch_results:
                    record = BackgroundResult(
                        ticker=entry["ticker"],
                        signal=entry.get("signal", "NEUTRAL"),
                        confidence=entry.get("confidence", 0.0),
                        price=entry.get("price"),
                        strategy=strategy,
                        interval=interval,
                        periods=periods,
                        error=entry.get("error"),
                    )
                    db.add(record)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning("Failed to persist background results to DB: %s", e)

        with self._lock:
            self._results.extend(batch_results)
            max_r = self._config["max_results"]
            if len(self._results) > max_r:
                self._results = self._results[-max_r:]
            self._config["last_run"] = datetime.now(timezone.utc).isoformat()

        try:
            from app.services.ws_manager import ws_manager
            asyncio.run(ws_manager.broadcast({
                "type": "background_results",
                "data": batch_results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }))
        except Exception:
            pass

        logger.info("Background cycle complete: %d tickers analyzed", len(batch_results))


background_analyzer = BackgroundAnalyzer()
