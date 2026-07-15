import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.debug import debug
from app.database import get_db
from app.models import AlertConfig as AlertConfigModel
from app.schemas import AlertRequest, AlertResponse
from app.services.whatsapp_service import send_alert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post("/", response_model=AlertResponse, summary="Crear alerta programada")
def create_alert(payload: AlertRequest, db: Session = Depends(get_db)):
    record = AlertConfigModel(
        ticker=payload.ticker.upper(),
        strategy=payload.strategy,
        condition=payload.condition,
        threshold=payload.threshold,
        enabled=True,
        whatsapp_enabled=payload.whatsapp_enabled,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("Alerta creada: %s %s %s", record.ticker, record.strategy, record.condition)
    return AlertResponse(
        id=record.id,
        ticker=record.ticker,
        strategy=record.strategy,
        condition=record.condition,
        threshold=record.threshold,
        enabled=record.enabled,
        whatsapp_enabled=record.whatsapp_enabled,
    )


@router.get("/", response_model=list[AlertResponse], summary="Listar alertas activas")
def list_alerts(db: Session = Depends(get_db)):
    records = db.query(AlertConfigModel).filter(AlertConfigModel.enabled.is_(True)).all()
    return [
        AlertResponse(
            id=r.id,
            ticker=r.ticker,
            strategy=r.strategy,
            condition=r.condition,
            threshold=r.threshold,
            enabled=r.enabled,
            whatsapp_enabled=r.whatsapp_enabled,
        )
        for r in records
    ]


@router.delete("/{alert_id}", summary="Eliminar alerta por ID")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    record = db.query(AlertConfigModel).filter(AlertConfigModel.id == alert_id).first()
    if record:
        db.delete(record)
        db.commit()
    return {"deleted": alert_id}


@router.post("/test-whatsapp", summary="Enviar alerta de prueba por WhatsApp")
def test_whatsapp():
    result = send_alert(" Test de alerta desde Stock Analysis System")
    if result["status"] == "skipped":
        debug.track_error("whatsapp_test", result.get("reason", ""))
        logger.warning("WhatsApp test skipped: %s", result.get("reason"))
    elif result["status"] == "error":
        logger.error("WhatsApp test error: %s", result.get("error"))
    return result
