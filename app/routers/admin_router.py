import logging

from fastapi import APIRouter

from app.services.admin_service import get_service_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/status", summary="Estado de todos los servicios de infraestructura")
def admin_status():
    return get_service_status()
