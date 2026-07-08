import logging
from typing import Optional

from app.brokers.binance import BinanceBroker
from app.brokers.interactive_brokers import InteractiveBrokersBroker
from app.brokers.yahoo_finance import YahooFinanceBroker
from app.core.base_broker import BaseBroker, BrokerConfig
from app.core.debug import debug, timed
from app.models import BrokerConfig as BrokerConfigModel

logger = logging.getLogger(__name__)

BROKER_MAP: dict[str, type[BaseBroker]] = {
    "yahoo_finance": YahooFinanceBroker,
    "interactive_brokers": InteractiveBrokersBroker,
    "binance": BinanceBroker,
}


class BrokerManager:
    _instance: Optional["BrokerManager"] = None
    _active_broker: Optional[BaseBroker] = None
    _active_name: Optional[str] = None

    def __new__(cls) -> "BrokerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_from_db(self, db_session) -> None:
        record = (
            db_session.query(BrokerConfigModel)
            .filter(BrokerConfigModel.active.is_(True))
            .first()
        )
        if record is None:
            logger.warning("No hay configuración de bróker activa en DB")
            return
        self.switch(
            name=record.name,
            api_key=record.api_key,
            api_secret=record.api_secret,
            endpoint=record.endpoint,
            sandbox=record.sandbox,
            extra=record.extra or {},
        )

    @timed
    def switch(
        self,
        name: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        endpoint: Optional[str] = None,
        sandbox: bool = True,
        extra: Optional[dict] = None,
    ) -> dict:
        broker_class = BROKER_MAP.get(name)
        if broker_class is None:
            raise ValueError(
                f"Bróker '{name}' no soportado. "
                f"Disponibles: {list(BROKER_MAP.keys())}"
            )

        if self._active_broker is not None:
            self._active_broker.disconnect()

        config = BrokerConfig(
            name=name,
            api_key=api_key,
            api_secret=api_secret,
            endpoint=endpoint,
            sandbox=sandbox,
            extra=extra or {},
        )
        broker = broker_class(config)
        connected = broker.connect()

        if connected:
            self._active_broker = broker
            self._active_name = name
            logger.info("Bróker activo cambiado a: %s", name)
        else:
            logger.error("Fallo al conectar bróker: %s", name)

        debug.track_broker_event(
            "switch" if connected else "switch_failed",
            name,
            {"sandbox": sandbox, "connected": connected},
        )

        return {
            "broker": name,
            "connected": connected,
            "sandbox": sandbox,
            "message": (
                "Conectado correctamente" if connected
                else "Fallo en la conexión"
            ),
        }

    def get_broker(self) -> BaseBroker:
        if self._active_broker is None:
            raise RuntimeError(
                "No hay un bróker activo. "
                "Configure uno vía POST /api/config/broker"
            )
        return self._active_broker

    @property
    def active_name(self) -> Optional[str]:
        return self._active_name
