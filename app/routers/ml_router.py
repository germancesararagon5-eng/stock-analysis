import logging

from fastapi import APIRouter, Query

from app.services.ml_service import export_dataset, get_dataset_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.get("/dataset", summary="Exportar dataset de entrenamiento ML")
def api_export_dataset(
    strategies: str = Query("", description="Filtrar por estrategias (coma separada)"),
    tickers: str = Query("", description="Filtrar por tickers (coma separada)"),
    limit: int = Query(10000, ge=1, le=100000, description="Máximo de filas"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Confianza mínima"),
):
    s_list = [s.strip() for s in strategies.split(",") if s.strip()] if strategies else None
    t_list = [t.strip() for t in tickers.split(",") if t.strip()] if tickers else None
    data = export_dataset(strategies=s_list, tickers=t_list, limit=limit, min_confidence=min_confidence)
    return {"total": len(data), "rows": data, "columns": [
        "ticker", "strategy", "interval", "signal", "confidence",
        "price", "rsi_14", "ema_9", "ema_21", "ema_50", "ema_200",
        "bb_upper", "bb_lower", "macd", "macd_signal", "macd_histogram",
        "volume", "atr", "support_1", "resistance_1",
        "outcome", "price_change_pct", "created_at",
    ]}


@router.get("/stats", summary="Estadísticas del dataset ML")
def api_dataset_stats():
    return get_dataset_stats()
