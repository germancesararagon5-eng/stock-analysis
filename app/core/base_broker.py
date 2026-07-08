from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class BrokerConfig:
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    endpoint: Optional[str] = None
    sandbox: bool = True
    extra: Optional[dict[str, Any]] = None


class BaseBroker(ABC):
    def __init__(self, config: BrokerConfig):
        self.config = config
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        ...

    @abstractmethod
    def get_realtime_data(self, ticker: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def execute_order(self, side: str, quantity: float, ticker: str) -> dict[str, Any]:
        ...

    @property
    def is_connected(self) -> bool:
        return self._connected

    def disconnect(self) -> None:
        self._connected = False
