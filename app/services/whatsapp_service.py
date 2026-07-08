import logging
from typing import Optional

import requests

from app.config import settings
from app.core.debug import debug, timed

logger = logging.getLogger(__name__)

GATEWAY_URL = settings.whatsapp_gateway_url


def check_connection() -> dict:
    try:
        r = requests.get(f"{GATEWAY_URL}/status", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.warning("WhatsApp gateway no disponible: %s", e)
        return {"connected": False, "phone": None}


def get_qr() -> dict:
    try:
        r = requests.get(f"{GATEWAY_URL}/qr", timeout=10)
        if r.status_code == 404:
            return {"qr": None, "error": "No QR available — check if already connected"}
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.warning("Error obteniendo QR: %s", e)
        return {"qr": None, "error": str(e)}


@timed
def send_alert(message: str, to: Optional[str] = None) -> dict:
    if not to:
        from app.database import SessionLocal
        from app.models import WhatsAppConfig as WhatsAppConfigModel

        db = SessionLocal()
        try:
            row = db.query(WhatsAppConfigModel).order_by(WhatsAppConfigModel.id.desc()).first()
            to = row.phone_number if row else None
        finally:
            db.close()

    if not to:
        logger.warning("Número destino no configurado")
        return {"status": "skipped", "reason": "No target number"}

    status = check_connection()
    if not status.get("connected"):
        logger.warning("WhatsApp no conectado")
        return {"status": "skipped", "reason": "WhatsApp not connected"}

    try:
        r = requests.post(
            f"{GATEWAY_URL}/send-message",
            json={"to": to, "message": message},
            timeout=10,
        )
        data = r.json()
        if data.get("success"):
            logger.info("Mensaje enviado a %s", to)
            return {"status": "sent", "to": to}
        else:
            logger.error("Error del gateway: %s", data.get("error"))
            return {"status": "error", "error": data.get("error")}
    except requests.RequestException as e:
        logger.exception("Error enviando mensaje WhatsApp")
        debug.track_error("whatsapp.send_alert", str(e))
        return {"status": "error", "error": str(e)}


def update_phone_number(phone: str) -> dict:
    from app.database import SessionLocal
    from app.models import WhatsAppConfig as WhatsAppConfigModel

    db = SessionLocal()
    try:
        row = db.query(WhatsAppConfigModel).order_by(WhatsAppConfigModel.id.desc()).first()
        if not row:
            row = WhatsAppConfigModel()
            db.add(row)
        row.phone_number = phone
        db.commit()
        db.refresh(row)
        logger.info("Número WhatsApp actualizado: %s", phone)
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        logger.exception("Error guardando número WhatsApp")
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


def get_config() -> dict:
    from app.database import SessionLocal
    from app.models import WhatsAppConfig as WhatsAppConfigModel

    status = check_connection()
    phone = ""
    db = SessionLocal()
    try:
        row = db.query(WhatsAppConfigModel).order_by(WhatsAppConfigModel.id.desc()).first()
        if row:
            phone = row.phone_number or ""
    finally:
        db.close()

    return {
        "connected": status.get("connected", False),
        "phone": status.get("phone"),
        "phone_number": phone,
    }
