import logging

from fastapi import APIRouter, Query

from app.core.broker_manager import BrokerManager
from app.core.debug import debug
from app.services.background_analyzer import background_analyzer
from app.services.prediction_service import (
    get_prediction_stats,
    get_predictions,
    get_trading_summary,
    resolve_all_predictions,
)
from app.services.prediction_service import (
    resolve_predictions as resolve_preds,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/options", tags=["options"])

broker_manager = BrokerManager()


# ── Background Analyzer ──────────────────────────────────────

@router.get("/background/status", summary="Estado del background analyzer")
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


@router.post("/background/start", summary="Iniciar background analyzer")
def background_start():
    result = background_analyzer.start()
    debug.track_broker_event("background_start", "background_analyzer", result)
    return result


@router.post("/background/stop", summary="Detener background analyzer")
def background_stop():
    result = background_analyzer.stop()
    debug.track_broker_event("background_stop", "background_analyzer", result)
    return result


@router.post("/background/config", summary="Configurar background analyzer")
def background_config(
    tickers: str = Query("", description="Tickers separados por coma"),
    strategy: str = Query("all", description="Estrategia o 'all' para todas"),
    interval: str = Query("5m", description="Intervalo de velas"),
    periods: int = Query(100, ge=20, le=500, description="Períodos por análisis"),
    min_confidence: float = Query(0.2, ge=0.0, le=1.0, description="Confianza mínima para almacenar"),
    alert_whatsapp: bool = Query(False, description="Enviar alertas por WhatsApp"),
    run_every_seconds: int = Query(300, ge=30, le=3600, description="Segundos entre ciclos"),
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


@router.get("/background/results", summary="Resultados del background analyzer")
def background_results(limit: int = Query(20, ge=1, le=200, description="Máximo de resultados")):
    return {
        "results": background_analyzer.get_results(limit),
        "total": len(background_analyzer._results) if hasattr(background_analyzer, '_results') else 0,
    }


# ── Predictions ───────────────────────────────────────────────

@router.get("/predictions", summary="Listar predicciones almacenadas")
def predictions_list(
    ticker: str = Query("", description="Filtrar por ticker"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
):
    kw = {"limit": limit, "offset": offset}
    if ticker.strip():
        kw["ticker"] = ticker.strip().upper()
    return {"predictions": get_predictions(**kw)}


@router.get("/predictions/stats", summary="Estadísticas de predicciones")
def predictions_stats(ticker: str = Query("", description="Filtrar por ticker")):
    kw = {}
    if ticker.strip():
        kw["ticker"] = ticker.strip().upper()
    return get_prediction_stats(**kw)


@router.post("/predictions/resolve", summary="Resolver predicciones pendientes")
def predictions_resolve(
    count: int = Query(20, ge=1, le=200, description="Cantidad a resolver"),
    threshold: float = Query(0.0, ge=0.0, le=100.0, description="Cambio de precio mínimo % para considerar correcta"),
):
    resolved = resolve_preds(count=count, threshold_pct=threshold)
    return {"resolved": resolved}


@router.post("/predictions/resolve-all", summary="Resolver TODAS las predicciones pendientes")
def predictions_resolve_all(
    threshold: float = Query(0.0, ge=0.0, le=100.0, description="Cambio de precio mínimo % para considerar correcta"),
):
    resolved = resolve_all_predictions(threshold_pct=threshold)
    return {"resolved": resolved}


# ── Trading Simulator ────────────────────────────────────────

@router.get("/trading/summary", summary="Resumen del simulador de trading")
def trading_summary(ticker: str = Query("", description="Filtrar por ticker")):
    kw = {}
    if ticker.strip():
        kw["ticker"] = ticker.strip().upper()
    return get_trading_summary(**kw)


# ── WhatsApp Config (Self-Hosted Gateway) ──────────────────

@router.get("/whatsapp/config", summary="Obtener configuración de WhatsApp")
def whatsapp_config_get():
    from app.services.whatsapp_service import get_config
    return get_config()


@router.post("/whatsapp/config", summary="Actualizar número de teléfono WhatsApp")
def whatsapp_config_set(phone_number: str = Query("", description="Número con código de país, ej: 521234567890")):
    from app.services.whatsapp_service import update_phone_number

    result = update_phone_number(phone_number)
    debug.track_broker_event("whatsapp_config", "whatsapp", {"has_phone": bool(phone_number)})
    return result


# ── Broker Config (moved from dashboard) ────────────────────

@router.get("/broker/list", summary="Listar brokers disponibles")
def broker_list():
    from app.core.broker_manager import BROKER_MAP
    return {"available": list(BROKER_MAP.keys())}


@router.get("/broker/status", summary="Estado del broker activo desde opciones")
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

@router.get("/debug/status", summary="Estado de la depuración")
def debug_status():
    return {"enabled": debug.enabled}


@router.post("/debug/toggle", summary="Activar/desactivar depuración desde opciones")
def debug_toggle():
    debug.enabled = not debug.enabled
    return {"enabled": debug.enabled}


@router.post("/debug/clear", summary="Limpiar logs de depuración desde opciones")
def debug_clear():
    debug.clear()
    return {"status": "cleared"}
