import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.broker_manager import BrokerManager
from app.database import get_db
from app.models import BrokerConfig as BrokerConfigModel
from app.schemas import BrokerSwitchRequest, BrokerSwitchResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["config"])

broker_manager = BrokerManager()


@router.post("/broker", response_model=BrokerSwitchResponse)
def switch_broker(payload: BrokerSwitchRequest, db: Session = Depends(get_db)):
    db.query(BrokerConfigModel).filter(BrokerConfigModel.active.is_(True)).update(
        {BrokerConfigModel.active: False}
    )

    record = (
        db.query(BrokerConfigModel)
        .filter(BrokerConfigModel.name == payload.name)
        .first()
    )
    if record:
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(record, field, value)
        record.active = True
    else:
        record = BrokerConfigModel(**payload.model_dump(exclude_none=True), active=True)
        db.add(record)

    db.commit()

    result = broker_manager.switch(
        name=payload.name,
        api_key=payload.api_key,
        api_secret=payload.api_secret,
        endpoint=payload.endpoint,
        sandbox=payload.sandbox,
        extra=payload.extra,
    )

    return BrokerSwitchResponse(**result)


@router.get("/broker/status")
def broker_status():
    connected = False
    active = broker_manager.active_name
    if active:
        try:
            connected = broker_manager.get_broker().is_connected
        except RuntimeError:
            pass
    return {"active_broker": active, "connected": connected}


@router.get("/brokers")
def list_brokers():
    from app.core.broker_manager import BROKER_MAP

    return {"available_brokers": list(BROKER_MAP.keys())}
