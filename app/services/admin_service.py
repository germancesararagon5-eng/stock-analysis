import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.broker_manager import BrokerManager
from app.core.debug import debug
from app.database import engine
from app.services.background_analyzer import background_analyzer
from app.services.ml_service import get_model_status

logger = logging.getLogger(__name__)
broker_manager = BrokerManager()

_START_TIME = datetime.now(timezone.utc)

TABLE_NAMES = [
    "broker_configs", "alert_configs", "predictions",
    "analysis_results", "background_results", "whatsapp_configs",
]


def _count_table(conn, table: str) -> int:
    try:
        return conn.execute(
            text(f'SELECT COUNT(*) FROM "{table}"')
        ).scalar() or 0
    except Exception:
        return 0


def _count_where(conn, table: str, condition: str) -> int:
    try:
        return conn.execute(
            text(f'SELECT COUNT(*) FROM "{table}" WHERE {condition}')
        ).scalar() or 0
    except Exception:
        return 0


def get_service_status() -> dict:
    uptime_secs = (datetime.now(timezone.utc) - _START_TIME).total_seconds()
    hours = int(uptime_secs // 3600)
    mins = int((uptime_secs % 3600) // 60)

    api_status = {
        "status": "ok",
        "version": "2.6.0",
        "uptime": f"{hours}h {mins}m",
        "uptime_seconds": int(uptime_secs),
        "endpoints": [
            {"path": "/api/analysis/technical-analysis", "method": "POST", "desc": "Análisis técnico completo de un ticker"},
            {"path": "/api/analysis/data/{ticker}", "method": "GET", "desc": "Datos OHLCV históricos"},
            {"path": "/api/analysis/chart/{ticker}", "method": "GET", "desc": "Datos para gráfico (close, indicadores)"},
            {"path": "/api/analysis/top-ranking", "method": "GET", "desc": "Top ranking por confianza (paralelizado)"},
            {"path": "/api/analysis/market-summary", "method": "GET", "desc": "Resumen de mercado multi-ticker"},
            {"path": "/api/config/*", "method": "GET/POST", "desc": "Configuración del broker activo"},
            {"path": "/api/alerts/*", "method": "GET/POST/DELETE", "desc": "Alertas programadas por ticker"},
            {"path": "/api/options/background/*", "method": "GET/POST", "desc": "Background analyzer (start/stop/config)"},
            {"path": "/api/options/predictions/*", "method": "GET/POST", "desc": "Predicciones, estadísticas, resolución"},
            {"path": "/api/options/trading/summary", "method": "GET", "desc": "Simulador de trading (P&L, win rate)"},
            {"path": "/api/options/whatsapp/*", "method": "GET/POST", "desc": "Config WhatsApp"},
            {"path": "/api/options/broker/*", "method": "GET", "desc": "Estado y lista de brokers"},
            {"path": "/api/options/debug/*", "method": "GET/POST", "desc": "Control de depuración"},
            {"path": "/api/ml/train", "method": "POST", "desc": "Entrenar modelo RandomForest"},
            {"path": "/api/ml/backtest", "method": "GET", "desc": "Backtest ML vs 6 estrategias"},
            {"path": "/api/ml/status", "method": "GET", "desc": "Estado del modelo ML"},
            {"path": "/api/ml/dataset", "method": "GET", "desc": "Exportar dataset ML como JSON"},
            {"path": "/api/admin/status", "method": "GET", "desc": "Estado de todos los servicios + data flow"},
            {"path": "/api/debug/*", "method": "GET/POST", "desc": "Logs de depuración"},
            {"path": "/docs", "method": "GET", "desc": "Swagger UI (OpenAPI)"},
        ],
    }

    db_status = {"status": "ok"}
    data_flow = {}
    try:
        with engine.connect() as conn:
            data_flow["tables_found"] = 0
            for tname in TABLE_NAMES:
                cnt = _count_table(conn, tname)
                data_flow[tname] = cnt
                if cnt > 0:
                    data_flow["tables_found"] += 1

            db_status["tables"] = len([
                t for t in TABLE_NAMES if data_flow.get(t, 0) > 0
            ])
            db_status["total_records"] = sum(data_flow.get(t, 0) for t in TABLE_NAMES)

            analysis_resolved = _count_where(
                conn, "analysis_results", "outcome IN ('WIN','LOSS')"
            )
            analysis_win = _count_where(
                conn, "analysis_results", "outcome = 'WIN'"
            )
            predictions_resolved = _count_where(
                conn, "predictions", "outcome IN ('CORRECT','INCORRECT')"
            )
            data_flow["analysis_resolved"] = analysis_resolved
            data_flow["analysis_win"] = analysis_win
            data_flow["analysis_win_rate"] = (
                round(analysis_win / analysis_resolved * 100, 1)
                if analysis_resolved > 0 else 0
            )
            data_flow["predictions_resolved"] = predictions_resolved
    except Exception as e:
        db_status["status"] = "error"
        db_status["error"] = str(e)

    debug_entries = (
        debug.get_entries() if hasattr(debug, "get_entries") else []
    )
    broker_fetches = sum(
        1 for e in debug_entries
        if isinstance(e, dict) and e.get("type") == "broker"
    )
    strategy_evals = sum(
        1 for e in debug_entries
        if isinstance(e, dict) and e.get("type") == "strategy"
    )
    data_flow["broker_fetches"] = broker_fetches
    data_flow["strategy_evaluations"] = strategy_evals

    redis_status = {"status": "not_configured", "configured": False}

    whatsapp_status = {"status": "unknown"}
    try:
        from app.services.whatsapp_service import get_config
        cfg = get_config()
        whatsapp_status["phone"] = cfg.get("phone_number") or cfg.get("phone", "")
        whatsapp_status["connected"] = cfg.get("connected", False)
        whatsapp_status["gateway_reachable"] = cfg.get("gateway_reachable", None)
        if cfg.get("connected"):
            whatsapp_status["status"] = "connected"
        elif cfg.get("gateway_reachable") is False:
            whatsapp_status["status"] = "gateway_unreachable"
        elif cfg.get("phone_number"):
            whatsapp_status["status"] = "waiting_qr"
        else:
            whatsapp_status["status"] = "not_configured"
    except Exception as e:
        whatsapp_status["status"] = "error"
        whatsapp_status["error"] = str(e)

    bg_status = {"status": "stopped"}
    try:
        cfg = background_analyzer.get_config()
        bg_status["enabled"] = cfg.get("enabled", False)
        bg_status["tickers"] = cfg.get("tickers", [])
        bg_status["strategy"] = cfg.get("strategy", "scalping")
        bg_status["interval"] = cfg.get("interval", "5m")
        bg_status["run_every_seconds"] = cfg.get("run_every_seconds", 300)
        bg_status["last_run"] = cfg.get("last_run")
        bg_status["min_confidence"] = cfg.get("min_confidence", 0.2)
        bg_status["alert_whatsapp"] = cfg.get("alert_whatsapp", False)
        bg_status["status"] = "running" if bg_status["enabled"] else "stopped"
    except Exception as e:
        bg_status["status"] = "error"
        bg_status["error"] = str(e)

    ml_status = get_model_status()
    ml_status["status"] = "trained" if ml_status.get("trained") else "not_trained"
    ml_status["requires_training"] = ml_status.get("samples", 0) < 10

    broker_status = {"status": "disconnected"}
    try:
        active = broker_manager.active_name
        broker_status["name"] = active
        if active:
            broker = broker_manager.get_broker()
            broker_status["connected"] = broker.is_connected
            broker_status["sandbox"] = getattr(broker.config, "sandbox", True)
            broker_status["status"] = "connected" if broker.is_connected else "disconnected"
        else:
            broker_status["status"] = "no_broker"
    except Exception as e:
        broker_status["status"] = "error"
        broker_status["error"] = str(e)

    debug_status = {
        "enabled": debug.enabled,
        "entries": len(debug_entries),
        "status": "enabled" if debug.enabled else "disabled",
    }

    return {
        "api": api_status,
        "database": db_status,
        "redis": redis_status,
        "whatsapp": whatsapp_status,
        "background_analyzer": bg_status,
        "ml_model": ml_status,
        "broker": broker_status,
        "debug": debug_status,
        "data_flow": data_flow,
    }
