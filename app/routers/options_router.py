import logging

from fastapi import APIRouter, Query

from app.core.broker_manager import BrokerManager
from app.core.debug import debug
from app.services.background_analyzer import background_analyzer
from app.services.prediction_service import (
    get_prediction_stats,
    get_predictions,
    get_trading_summary,
)
from app.services.prediction_service import (
    resolve_predictions as resolve_preds,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/options", tags=["options"])

broker_manager = BrokerManager()


# ── Background Analyzer ──────────────────────────────────────

@router.get("/background/status")
def background_status():
    cfg = background_analyzer.get_config()
    return {
        "enabled": cfg["enabled"],
        "tickers": cfg["tickers"],
        "strategy": cfg["strategy"],
        "interval": cfg["interval"],
        "periods": cfg["periods"],
        "min_confidence": cfg["min_confidence"],
        "alert_whatsapp": cfg["alert_whatsapp"],
        "run_every_seconds": cfg["run_every_seconds"],
        "last_run": cfg["last_run"],
    }


@router.post("/background/start")
def background_start():
    result = background_analyzer.start()
    debug.track_broker_event("background_start", "background_analyzer", result)
    return result


@router.post("/background/stop")
def background_stop():
    result = background_analyzer.stop()
    debug.track_broker_event("background_stop", "background_analyzer", result)
    return result


@router.post("/background/config")
def background_config(
    tickers: str = Query("", description="Comma-separated tickers"),
    strategy: str = Query("scalping"),
    interval: str = Query("5m"),
    periods: int = Query(100, ge=20, le=500),
    min_confidence: float = Query(0.2, ge=0.0, le=1.0),
    alert_whatsapp: bool = Query(False),
    run_every_seconds: int = Query(300, ge=30, le=3600),
):
    updates = {
        "strategy": strategy,
        "interval": interval,
        "periods": periods,
        "min_confidence": min_confidence,
        "alert_whatsapp": alert_whatsapp,
        "run_every_seconds": run_every_seconds,
    }
    if tickers.strip():
        updates["tickers"] = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    else:
        updates["tickers"] = []

    cfg = background_analyzer.update_config(updates)
    debug.track_broker_event("background_config", "background_analyzer", updates)
    return cfg


@router.get("/background/results")
def background_results(limit: int = Query(20, ge=1, le=200)):
    return {
        "results": background_analyzer.get_results(limit),
        "total": len(background_analyzer._results) if hasattr(background_analyzer, '_results') else 0,
    }


# ── Predictions ───────────────────────────────────────────────

@router.get("/predictions")
def predictions_list(
    ticker: str = Query("", description="Filter by ticker"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    kw = {"limit": limit, "offset": offset}
    if ticker.strip():
        kw["ticker"] = ticker.strip().upper()
    return {"predictions": get_predictions(**kw)}


@router.get("/predictions/stats")
def predictions_stats(ticker: str = Query("", description="Filter by ticker")):
    kw = {}
    if ticker.strip():
        kw["ticker"] = ticker.strip().upper()
    return get_prediction_stats(**kw)


@router.post("/predictions/resolve")
def predictions_resolve(
    count: int = Query(20, ge=1, le=200),
    threshold: float = Query(0.0, ge=0.0, le=100.0, description="Min price change % to consider correct"),
):
    resolved = resolve_preds(count=count, threshold_pct=threshold)
    return {"resolved": resolved}


# ── Trading Simulator ────────────────────────────────────────

@router.get("/trading/summary")
def trading_summary(ticker: str = Query("", description="Filter by ticker")):
    kw = {}
    if ticker.strip():
        kw["ticker"] = ticker.strip().upper()
    return get_trading_summary(**kw)


# ── WhatsApp Config (Self-Hosted Gateway) ──────────────────

@router.get("/whatsapp/config")
def whatsapp_config_get():
    from app.services.whatsapp_service import get_config
    return get_config()


@router.post("/whatsapp/config")
def whatsapp_config_set(phone_number: str = Query("")):
    from app.services.whatsapp_service import update_phone_number

    result = update_phone_number(phone_number)
    debug.track_broker_event("whatsapp_config", "whatsapp", {"has_phone": bool(phone_number)})
    return result


# ── Broker Config (moved from dashboard) ────────────────────

@router.get("/broker/list")
def broker_list():
    from app.core.broker_manager import BROKER_MAP
    return {"available": list(BROKER_MAP.keys())}


@router.get("/broker/status")
def broker_status():
    connected = False
    active = broker_manager.active_name
    if active:
        try:
            connected = broker_manager.get_broker().is_connected
        except RuntimeError:
            pass
    return {"active": active, "connected": connected}


# ── Debug Config (moved from debug tab) ─────────────────────

@router.get("/debug/status")
def debug_status():
    return {"enabled": debug.enabled}


@router.post("/debug/toggle")
def debug_toggle():
    debug.enabled = not debug.enabled
    return {"enabled": debug.enabled}


@router.post("/debug/clear")
def debug_clear():
    debug.clear()
    return {"status": "cleared"}
