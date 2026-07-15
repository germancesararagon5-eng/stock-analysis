from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

STRATEGY_TYPES = Literal["scalping", "swing", "momentum", "mean_reversion", "breakout", "market_structure"]


class BrokerSwitchRequest(BaseModel):
    """Payload para cambiar de broker activo."""

    name: str = Field(description="Nombre del broker (yahoo_finance, binance, interactive_brokers)")
    api_key: Optional[str] = Field(None, description="API key del broker")
    api_secret: Optional[str] = Field(None, description="API secret del broker")
    endpoint: Optional[str] = Field(None, description="Endpoint personalizado del broker")
    sandbox: bool = Field(True, description="Usar sandbox/paper-trading")
    extra: Optional[dict[str, Any]] = Field(None, description="Configuración adicional específica del broker")


class BrokerSwitchResponse(BaseModel):
    """Resultado del cambio de broker."""

    broker: str = Field(description="Nombre del broker seleccionado")
    connected: bool = Field(description="Estado de conexión")
    sandbox: bool = Field(description="Si está en modo sandbox")
    message: str = Field(description="Mensaje informativo del resultado")


class DataResponse(BaseModel):
    """Datos en tiempo real de un ticker."""

    ticker: str = Field(description="Símbolo del ticker")
    price: Optional[float] = Field(None, description="Precio actual")
    error: Optional[str] = Field(None, description="Mensaje de error si ocurrió")
    strategy_signals: Optional[dict] = Field(None, description="Señales de estrategia")


class OrderRequest(BaseModel):
    """Payload para simular una orden de compra/venta."""

    ticker: str = Field(description="Símbolo del ticker")
    side: str = Field(description="BUY o SELL", examples=["BUY"])
    quantity: float = Field(description="Cantidad de acciones/contratos", examples=[10])


class OrderResponse(BaseModel):
    """Resultado de una orden simulada."""

    status: str = Field(description="Estado de la orden (filled, rejected, etc.)")
    side: str = Field(description="Lado de la orden")
    quantity: float = Field(description="Cantidad ejecutada")
    ticker: str = Field(description="Símbolo del ticker")
    broker: str = Field(description="Broker que ejecutó")
    message: str = Field(description="Mensaje descriptivo")
    error: Optional[str] = Field(None, description="Error si ocurrió")


class AnalysisRequest(BaseModel):
    """Payload para ejecutar análisis técnico."""

    ticker: str = Field(description="Símbolo del ticker")
    strategy: STRATEGY_TYPES = Field("scalping", description="Estrategia de trading")
    interval: str = Field("5m", description="Intervalo de velas (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    periods: int = Field(100, description="Número de velas a analizar", ge=20, le=500)


class AnalysisResponse(BaseModel):
    """Resultado completo del análisis técnico."""

    ticker: str = Field(description="Símbolo del ticker")
    strategy: str = Field(description="Estrategia utilizada")
    signal: str = Field(description="Señal generada (BUY, SELL, NEUTRAL)")
    confidence: float = Field(description="Confianza de la señal (0.0 a 1.0)", ge=0.0, le=1.0)
    indicators: dict[str, Any] = Field(description="Valores de indicadores técnicos")
    reasons: list[str] = Field(default=[], description="Razones que fundamentan la señal")
    interval: str = Field(default="", description="Intervalo analizado")
    timestamp: str = Field(description="Timestamp del análisis")


class ChartSeries(BaseModel):
    """Series de datos para renderizar gráficos."""

    timestamp: list[str] = Field(description="Timestamps de cada vela")
    close: list[float] = Field(description="Precios de cierre")
    ema_9: list[Optional[float]] = Field(description="EMA de 9 períodos")
    ema_21: list[Optional[float]] = Field(description="EMA de 21 períodos")
    bb_upper: list[Optional[float]] = Field(description="Banda superior de Bollinger")
    bb_mid: list[Optional[float]] = Field(description="Banda media (SMA 20) de Bollinger")
    bb_lower: list[Optional[float]] = Field(description="Banda inferior de Bollinger")
    rsi_14: list[Optional[float]] = Field(description="RSI de 14 períodos")
    macd: list[Optional[float]] = Field(default=[], description="Línea MACD")
    macd_signal: list[Optional[float]] = Field(default=[], description="Línea de señal MACD")
    macd_histogram: list[Optional[float]] = Field(default=[], description="Histograma MACD")
    volume: list[Optional[float]] = Field(default=[], description="Volumen")
    sma_50: list[Optional[float]] = Field(default=[], description="SMA de 50 períodos")
    sma_200: list[Optional[float]] = Field(default=[], description="SMA de 200 períodos")


class ChartResponse(BaseModel):
    """Respuesta completa de chart con análisis técnico."""

    ticker: str = Field(description="Símbolo del ticker")
    interval: str = Field(description="Intervalo del chart")
    strategy: str = Field(description="Estrategia aplicada")
    signal: str = Field(description="Señal (BUY, SELL, NEUTRAL)")
    confidence: float = Field(description="Confianza de la señal")
    indicators: dict[str, Any] = Field(description="Valores actuales de indicadores")
    reasons: list[str] = Field(description="Razones de la señal")
    series: ChartSeries = Field(description="Series de datos del chart")


class AlertRequest(BaseModel):
    """Payload para crear una alerta programada."""

    ticker: str = Field(description="Símbolo del ticker a monitorear")
    strategy: STRATEGY_TYPES = Field("scalping", description="Estrategia a evaluar")
    condition: str = Field(description="Condición de alerta", examples=["signal == 'BUY'", "confidence > 0.7"])
    threshold: Optional[float] = Field(None, description="Umbral numérico adicional")
    whatsapp_enabled: bool = Field(False, description="Notificar por WhatsApp")


class AlertResponse(BaseModel):
    """Alerta programada."""

    id: int = Field(description="ID único de la alerta")
    ticker: str = Field(description="Símbolo del ticker")
    strategy: str = Field(description="Estrategia asociada")
    condition: str = Field(description="Condición configurada")
    threshold: Optional[float] = Field(None, description="Umbral configurado")
    enabled: bool = Field(description="Si está activa")
    whatsapp_enabled: bool = Field(description="Notificación WhatsApp activa")


class StrategyInfo(BaseModel):
    """Información de una estrategia de trading disponible."""

    name: str = Field(description="Nombre interno de la estrategia")
    description: str = Field(description="Descripción de la estrategia")
    min_periods: int = Field(description="Períodos mínimos requeridos")


class TopRankingItem(BaseModel):
    """Item del ranking top por confianza."""

    ticker: str = Field(description="Símbolo del ticker")
    signal: str = Field(description="Señal generada")
    confidence: float = Field(description="Confianza de la señal", ge=0.0, le=1.0)
    price: Optional[float] = Field(None, description="Precio actual")
    reasons: list[str] = Field(default=[], description="Razones de la señal")


class TopRankingResponse(BaseModel):
    """Ranking de tickers ordenados por confianza descendente."""

    strategy: str = Field(description="Estrategia utilizada")
    interval: str = Field(description="Intervalo analizado")
    rankings: list[TopRankingItem] = Field(description="Lista de resultados ordenados por confianza")


class BackgroundConfigResponse(BaseModel):
    """Configuración actual del background analyzer."""

    enabled: bool = Field(description="Si está activo")
    tickers: list[str] = Field(description="Tickers monitoreados")
    strategy: str = Field(description="Estrategia configurada")
    interval: str = Field(description="Intervalo de análisis")
    periods: int = Field(description="Períodos por análisis")
    min_confidence: float = Field(description="Confianza mínima para alertar")
    alert_whatsapp: bool = Field(description="Enviar alertas por WhatsApp")
    run_every_seconds: int = Field(description="Intervalo entre ciclos en segundos")
    last_run: Optional[str] = Field(None, description="Timestamp del último ciclo")


class PredictionStats(BaseModel):
    """Estadísticas de predicciones."""

    total: int = Field(description="Total de predicciones")
    buy: int = Field(description="Predicciones BUY")
    sell: int = Field(description="Predicciones SELL")
    neutral: int = Field(description="Predicciones NEUTRAL")
    resolved: int = Field(description="Predicciones resueltas")
    correct: int = Field(description="Predicciones correctas")
    incorrect: int = Field(description="Predicciones incorrectas")
    accuracy: float = Field(description="Precisión (0.0 a 1.0)")
    pending: int = Field(description="Predicciones pendientes de resolución")


class TradingSummaryStats(BaseModel):
    """Estadísticas del simulador de trading."""

    total_trades: int = Field(description="Total de trades simulados")
    wins: int = Field(description="Trades ganadores")
    losses: int = Field(description="Trades perdedores")
    win_rate: float = Field(description="Porcentaje de aciertos")
    total_pnl: float = Field(description="P&L acumulado")
    avg_win: float = Field(description="Ganancia promedio por trade ganador")
    avg_loss: float = Field(description="Pérdida promedio por trade perdedor")
    profit_factor: float = Field(description="Ratio ganancia/pérdida")
    sharpe: float = Field(description="Ratio Sharpe aproximado")
