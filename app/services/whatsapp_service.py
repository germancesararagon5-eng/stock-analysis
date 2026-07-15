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
        data = r.json()
        data["gateway_reachable"] = True
        return data
    except requests.ConnectionError:
        logger.warning("WhatsApp gateway no disponible (ConnectionError)")
        return {
            "connected": False,
            "gateway_reachable": False,
            "phone": None,
            "error": (
                f"No se puede conectar al gateway en {GATEWAY_URL}.\n"
                "Asegurate de que el gateway esté corriendo:\n"
                "  cd whatsapp-gateway && node index.js"
            ),
        }
    except requests.Timeout:
        logger.warning("WhatsApp gateway timeout")
        return {
            "connected": False,
            "gateway_reachable": False,
            "phone": None,
            "error": f"Gateway en {GATEWAY_URL} no respondió (timeout).",
        }
    except requests.RequestException as e:
        logger.warning("WhatsApp gateway error: %s", e)
        return {
            "connected": False,
            "gateway_reachable": False,
            "phone": None,
            "error": f"Error de conexión con el gateway: {e}",
        }


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
        if status.get("gateway_reachable") is False:
            reason = status.get("error", "WhatsApp gateway no disponible")
        else:
            reason = "WhatsApp gateway conectado pero no autenticado. Escaneá el QR en http://localhost:3001/qr"
        logger.warning("WhatsApp no disponible: %s", reason)
        return {"status": "skipped", "reason": reason}

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
        "gateway_reachable": status.get("gateway_reachable", True),
        "phone": status.get("phone"),
        "phone_number": phone,
    }
