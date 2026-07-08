import logging

from fastapi import APIRouter, Query

from app.core.broker_manager import BrokerManager
from app.core.strategies import compute_chart_data
from app.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    ChartResponse,
    ChartSeries,
    DataResponse,
    OrderRequest,
    OrderResponse,
)
from app.services.analysis_service import get_historical_data, run_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])

broker_manager = BrokerManager()


@router.post("/analyze", response_model=AnalysisResponse)
def analyze(payload: AnalysisRequest):
    result = run_analysis(
        ticker=payload.ticker,
        strategy=payload.strategy,
        interval=payload.interval,
        periods=payload.periods,
    )
    return AnalysisResponse(
        ticker=result["ticker"],
        strategy=result["strategy"],
        signal=result["signal"],
        confidence=result["confidence"],
        indicators=result.get("indicators", {}),
        reasons=result.get("reasons", []),
        interval=result.get("interval", payload.interval),
        timestamp=result.get("timestamp", ""),
    )


@router.get("/chart/{ticker}", response_model=ChartResponse)
def get_chart(
    ticker: str,
    strategy: str = Query("scalping"),
    interval: str = Query("1d"),
    periods: int = Query(60, ge=20, le=500),
):
    chart_periods = max(periods, 200) if strategy == "swing" else max(periods, 30)
    df = get_historical_data(ticker, interval, chart_periods)
    series = compute_chart_data(df)

    result = run_analysis(
        ticker=ticker,
        strategy=strategy,
        interval=interval,
        periods=periods,
    )

    return ChartResponse(
        ticker=result["ticker"],
        strategy=result["strategy"],
        interval=result.get("interval", interval),
        signal=result["signal"],
        confidence=result["confidence"],
        indicators=result.get("indicators", {}),
        reasons=result.get("reasons", []),
        series=ChartSeries(
            timestamp=series["timestamp"],
            close=series["close"],
            ema_9=series["ema_9"],
            ema_21=series["ema_21"],
            bb_upper=series["bb_upper"],
            bb_mid=series["bb_mid"],
            bb_lower=series["bb_lower"],
            rsi_14=series["rsi_14"],
            macd=series.get("macd", []),
            macd_signal=series.get("macd_signal", []),
            macd_histogram=series.get("macd_histogram", []),
        ),
    )


@router.get("/data/{ticker}", response_model=DataResponse)
def get_data(ticker: str):
    broker = broker_manager.get_broker()
    data = broker.get_realtime_data(ticker)
    if "error" in data:
        return DataResponse(ticker=ticker, error=data["error"])
    return DataResponse(ticker=ticker, price=data.get("price"), strategy_signals=None)


@router.post("/order", response_model=OrderResponse)
def place_order(payload: OrderRequest):
    broker = broker_manager.get_broker()
    result = broker.execute_order(
        side=payload.side,
        quantity=payload.quantity,
        ticker=payload.ticker,
    )
    return OrderResponse(
        status=result.get("status", "unknown"),
        side=payload.side,
        quantity=payload.quantity,
        ticker=payload.ticker,
        broker=broker.config.name,
        message=result.get("message", ""),
        error=result.get("error"),
    )


@router.post("/technical-analysis")
def technical_analysis(
    ticker: str = Query(...),
    strategy: str = Query("scalping"),
    interval: str = Query("1d"),
    periods: int = Query(100, ge=20, le=500),
):
    from app.services.technical_analysis import analyze_series

    chart_periods = max(periods, 200) if strategy == "swing" else max(periods, 30)
    df = get_historical_data(ticker, interval, chart_periods)
    series = compute_chart_data(df)
    return analyze_series(series, ticker)
