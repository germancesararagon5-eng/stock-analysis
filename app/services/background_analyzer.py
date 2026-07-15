import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.debug import debug
from app.core.strategies import STRATEGY_MAP
from app.database import SessionLocal
from app.models import BackgroundResult
from app.services.analysis_service import run_analysis
from app.services.ml_service import store_analysis_result, resolve_outcomes
from app.services.prediction_service import resolve_predictions, store_prediction

logger = logging.getLogger(__name__)

ALL_STRATEGIES = list(STRATEGY_MAP.keys())
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META",
    "TSLA", "JPM", "V", "JNJ", "WMT", "PG",
    "SPY", "QQQ", "BTC-USD", "ETH-USD",
    # Crypto spot pairs (Binance format)
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT",
]


class BackgroundAnalyzer:
    def __init__(self):
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._config: dict[str, Any] = self._default_config()
        self._results: list[dict] = []
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _default_config(self) -> dict:
        return {
            "enabled": False,
            "tickers": [],
            "strategy": "all",  # "all" = ejecuta todas las estrategias
            "interval": "1d",
            "periods": 100,
            "min_confidence": 0.0,
            "alert_whatsapp": False,
            "run_every_seconds": 3600,
            "last_run": None,
            "max_results": 200,
            "multi_strategy": True,
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
            logger.info("Background analyzer started (multi-strategy)")
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

    def get_results(self, limit: int = 50) -> list[dict]:
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
        logger.info("Background analyzer loop started (all strategies)")
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
            interval = self._config["interval"]
            periods = self._config["periods"]
            min_conf = self._config["min_confidence"]
            alert_wa = self._config["alert_whatsapp"]
            strategies = ALL_STRATEGIES

        if not tickers:
            tickers = list(DEFAULT_TICKERS)

        total_combos = len(tickers) * len(strategies)
        logger.info(
            "Background cycle: %d tickers x %d strategies = %d analyses",
            len(tickers), len(strategies), total_combos,
        )

        batch_results = []
        futures = []

        for ticker in tickers:
            for strategy in strategies:
                if self._stop_event.is_set():
                    break
                future = self._executor.submit(
                    self._analyze_single, ticker, strategy, interval, periods
                )
                futures.append(future)

        for future in as_completed(futures):
            if self._stop_event.is_set():
                break
            try:
                entry = future.result()
                batch_results.append(entry)
            except Exception as e:
                logger.warning("Background analysis future error: %s", e)

        # Resolve outcomes para el dataset ML
        try:
            for ticker in tickers:
                resolve_outcomes(ticker, 0.0)  # price 0 = skip resolve, just flag
        except Exception as e:
            logger.warning("Outcome resolution error: %s", e)

        # Store high-confidence signals as predictions
        for entry in batch_results:
            if entry.get("signal") in ("BUY", "SELL") and entry.get("confidence", 0) >= min_conf:
                try:
                    store_prediction(
                        ticker=entry["ticker"],
                        signal=entry["signal"],
                        confidence=entry["confidence"],
                        strategy=entry["strategy"],
                        interval=interval,
                        periods=periods,
                        price=entry.get("price"),
                        reasons=entry.get("reasons", []),
                        indicators=entry.get("indicators", {}),
                    )
                except Exception as e:
                    logger.warning("Prediction store error: %s", e)

        # WhatsApp alert for strong signals
        if alert_wa:
            strong = [
                e for e in batch_results
                if e.get("signal") in ("BUY", "SELL") and e.get("confidence", 0) >= 0.5
            ]
            for entry in strong[:5]:
                reasons = entry.get("reasons", [])
                msg = (
                    f" SEÑAL {entry['signal']} ({entry['confidence']:.0%}) | "
                    f"{entry['ticker']} | {entry['strategy']} | "
                    f"${entry.get('price') or 'N/A'} | {' | '.join(reasons)}"
                )
                logger.info("BACKGROUND SIGNAL: %s", msg)
                try:
                    from app.services.whatsapp_service import send_alert
                    send_alert(msg)
                except Exception:
                    pass

        # Persist to BackgroundResult table
        try:
            db = SessionLocal()
            try:
                for entry in batch_results:
                    record = BackgroundResult(
                        ticker=entry.get("ticker", "UNKNOWN"),
                        signal=entry.get("signal", "NEUTRAL"),
                        confidence=entry.get("confidence", 0.0),
                        price=entry.get("price"),
                        strategy=entry.get("strategy", "unknown"),
                        interval=interval,
                        periods=periods,
                        error=entry.get("error"),
                    )
                    db.add(record)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning("Failed to persist background results: %s", e)

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

        logger.info(
            "Background cycle complete: %d results (%.1f/sec)",
            len(batch_results),
            len(batch_results) / max(self._config["run_every_seconds"], 1),
        )

    def _analyze_single(
        self, ticker: str, strategy: str, interval: str, periods: int
    ) -> dict:
        result = {
            "ticker": ticker,
            "strategy": strategy,
            "signal": "ERROR",
            "confidence": 0.0,
            "price": None,
            "reasons": [],
            "indicators": {},
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            analysis = run_analysis(
                ticker=ticker,
                strategy=strategy,
                interval=interval,
                periods=periods,
                store_prediction=False,
            )
            result["signal"] = analysis.get("signal", "NEUTRAL")
            result["confidence"] = analysis.get("confidence", 0.0)
            result["price"] = analysis.get("indicators", {}).get("price")
            result["reasons"] = analysis.get("reasons", [])
            result["indicators"] = analysis.get("indicators", {})

            # Store every result in AnalysisResult table (ML dataset)
            store_analysis_result(
                ticker=ticker,
                strategy=strategy,
                interval=interval,
                period=periods,
                signal=result["signal"],
                confidence=result["confidence"],
                price=result["price"],
                indicators=analysis.get("indicators"),
                reasons=analysis.get("reasons"),
            )
        except Exception as e:
            logger.debug("Analysis failed %s/%s: %s", ticker, strategy, e)
            result["error"] = str(e)
            store_analysis_result(
                ticker=ticker, strategy=strategy, interval=interval,
                period=periods, signal="ERROR", confidence=0.0, error=str(e),
            )
        return result

    def shutdown(self):
        self._executor.shutdown(wait=False)


background_analyzer = BackgroundAnalyzer()
