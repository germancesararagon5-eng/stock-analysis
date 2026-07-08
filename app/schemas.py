from typing import Any, Optional

from pydantic import BaseModel


class BrokerSwitchRequest(BaseModel):
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    endpoint: Optional[str] = None
    sandbox: bool = True
    extra: Optional[dict[str, Any]] = None


class BrokerSwitchResponse(BaseModel):
    broker: str
    connected: bool
    sandbox: bool
    message: str


class DataResponse(BaseModel):
    ticker: str
    price: Optional[float] = None
    error: Optional[str] = None
    strategy_signals: Optional[dict] = None


class OrderRequest(BaseModel):
    ticker: str
    side: str
    quantity: float


class OrderResponse(BaseModel):
    status: str
    side: str
    quantity: float
    ticker: str
    broker: str
    message: str
    error: Optional[str] = None


class AnalysisRequest(BaseModel):
    ticker: str
    strategy: str = "scalping"
    interval: str = "5m"
    periods: int = 100


class AnalysisResponse(BaseModel):
    ticker: str
    strategy: str
    signal: str
    confidence: float
    indicators: dict[str, Any]
    reasons: list[str] = []
    interval: str = ""
    timestamp: str


class ChartSeries(BaseModel):
    timestamp: list[str]
    close: list[float]
    ema_9: list[Optional[float]]
    ema_21: list[Optional[float]]
    bb_upper: list[Optional[float]]
    bb_mid: list[Optional[float]]
    bb_lower: list[Optional[float]]
    rsi_14: list[Optional[float]]
    macd: list[Optional[float]] = []
    macd_signal: list[Optional[float]] = []
    macd_histogram: list[Optional[float]] = []


class ChartResponse(BaseModel):
    ticker: str
    interval: str
    strategy: str
    signal: str
    confidence: float
    indicators: dict[str, Any]
    reasons: list[str]
    series: ChartSeries


class AlertRequest(BaseModel):
    ticker: str
    strategy: str
    condition: str
    threshold: Optional[float] = None
    whatsapp_enabled: bool = False


class AlertResponse(BaseModel):
    id: int
    ticker: str
    strategy: str
    condition: str
    threshold: Optional[float]
    enabled: bool
    whatsapp_enabled: bool
