import logging
from datetime import datetime, timezone

from app.core.broker_manager import BrokerManager
from app.core.debug import debug
from app.database import engine
from app.services.background_analyzer import background_analyzer
from app.services.ml_service import get_model_status

logger = logging.getLogger(__name__)
broker_manager = BrokerManager()

_START_TIME = datetime.now(timezone.utc)


def get_service_status() -> dict:
    # ── API ──
    uptime_secs = (datetime.now(timezone.utc) - _START_TIME).total_seconds()
    hours = int(uptime_secs // 3600)
    mins = int((uptime_secs % 3600) // 60)
    api_status = {
        "status": "ok",
        "version": "2.5.0",
        "uptime": f"{hours}h {mins}m",
        "uptime_seconds": int(uptime_secs),
    }

    # ── Database ──
    db_status = {"status": "ok"}
    try:
        with engine.connect() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            tables = result.scalar() or 0
            total_records = 0
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ):
                tname = row[0]
                cnt = conn.execute(f"SELECT COUNT(*) FROM \"{tname}\"").scalar()
                total_records += cnt
            db_status["tables"] = tables
            db_status["total_records"] = total_records
    except Exception as e:
        db_status["status"] = "error"
        db_status["error"] = str(e)

    # ── Redis (reserved, not configured) ──
    redis_status = {"status": "not_configured", "configured": False}

    # ── WhatsApp ──
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

    # ── Background Analyzer ──
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
        if bg_status["enabled"]:
            bg_status["status"] = "running"
        else:
            bg_status["status"] = "stopped"
    except Exception as e:
        bg_status["status"] = "error"
        bg_status["error"] = str(e)

    # ── ML Model ──
    ml_status = get_model_status()
    if ml_status.get("trained"):
        ml_status["status"] = "trained"
    else:
        ml_status["status"] = "not_trained"
    ml_status["requires_training"] = ml_status["samples"] < 10

    # ── Broker ──
    broker_status = {"status": "disconnected"}
    try:
        active = broker_manager.active_name
        broker_status["name"] = active
        if active:
            broker = broker_manager.get_broker()
            broker_status["connected"] = broker.is_connected
            broker_status["sandbox"] = getattr(broker.config, "sandbox", True)
            if broker.is_connected:
                broker_status["status"] = "connected"
            else:
                broker_status["status"] = "disconnected"
        else:
            broker_status["status"] = "no_broker"
    except Exception as e:
        broker_status["status"] = "error"
        broker_status["error"] = str(e)

    # ── Debug ──
    debug_status = {
        "enabled": debug.enabled,
        "entries": len(debug.get_entries()) if hasattr(debug, "get_entries") else 0,
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
    }
