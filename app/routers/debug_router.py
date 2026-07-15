from fastapi import APIRouter, Query

from app.core.broker_manager import BrokerManager
from app.core.debug import debug

router = APIRouter(prefix="/api/debug", tags=["debug"])

broker_manager = BrokerManager()


@router.get("/", summary="Dashboard de depuración con filtros")
def debug_dashboard(
    show: str = Query("all", pattern="^(all|requests|errors|broker|strategy)$"),
    limit: int = Query(20, ge=1, le=500),
):
    snap = debug.snapshot()
    # filter by category
    if show == "requests":
        snap["recent_requests"] = snap["recent_requests"][-limit:]
        snap.pop("recent_errors", None)
        snap.pop("recent_broker_events", None)
        snap.pop("recent_strategy_evals", None)
    elif show == "errors":
        snap["recent_errors"] = snap["recent_errors"][-limit:]
        snap.pop("recent_requests", None)
        snap.pop("recent_broker_events", None)
        snap.pop("recent_strategy_evals", None)
    elif show == "broker":
        snap["recent_broker_events"] = snap["recent_broker_events"][-limit:]
        snap.pop("recent_requests", None)
        snap.pop("recent_errors", None)
        snap.pop("recent_strategy_evals", None)
    elif show == "strategy":
        snap["recent_strategy_evals"] = snap["recent_strategy_evals"][-limit:]
        snap.pop("recent_requests", None)
        snap.pop("recent_errors", None)
        snap.pop("recent_broker_events", None)

    snap["active_broker"] = broker_manager.active_name
    snap["broker_connected"] = (
        broker_manager.get_broker().is_connected
        if broker_manager.active_broker
        else False
    )
    return snap


@router.post("/toggle", summary="Activar/desactivar depuración")
def toggle_debug():
    debug.enabled = not debug.enabled
    return {"enabled": debug.enabled}


@router.post("/clear", summary="Limpiar logs de depuración")
def clear_debug():
    debug.clear()
    return {"status": "cleared"}


@router.get("/live", summary="Polling en vivo de eventos de depuración")
def live_poll(after_id: int = Query(0, ge=0, description="Solo eventos con ID mayor a este")):
    snap = debug.snapshot()
    snap["new_requests"] = [r for r in snap.pop("recent_requests", []) if r["id"] > after_id]
    return snap
