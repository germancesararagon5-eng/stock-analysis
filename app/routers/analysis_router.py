import logging
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

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
    try:
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
    except Exception as e:
        logger.warning("Analyze error for %s: %s", payload.ticker, e)
        return AnalysisResponse(
            ticker=payload.ticker,
            strategy=payload.strategy,
            signal="NEUTRAL",
            confidence=0.0,
            indicators={},
            reasons=[str(e)],
            interval=payload.interval,
            timestamp="",
        )


@router.get("/chart/{ticker}", response_model=ChartResponse)
def get_chart(
    ticker: str,
    strategy: str = Query("scalping"),
    interval: str = Query("1d"),
    periods: int = Query(60, ge=20, le=500),
):
    try:
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
    except Exception as e:
        logger.warning("Chart error for %s: %s", ticker, e)
        empty = ChartSeries(
            timestamp=[], close=[], ema_9=[], ema_21=[],
            bb_upper=[], bb_mid=[], bb_lower=[], rsi_14=[],
            macd=[], macd_signal=[], macd_histogram=[],
        )
        return ChartResponse(
            ticker=ticker,
            strategy=strategy,
            interval=interval,
            signal="NEUTRAL",
            confidence=0.0,
            indicators={},
            reasons=[str(e)],
            series=empty,
        )


@router.get("/data/{ticker}", response_model=DataResponse)
def get_data(ticker: str):
    try:
        broker = broker_manager.get_broker()
        data = broker.get_realtime_data(ticker)
        if "error" in data:
            return DataResponse(ticker=ticker, error=data["error"])
        return DataResponse(ticker=ticker, price=data.get("price"), strategy_signals=None)
    except Exception as e:
        logger.warning("Data error for %s: %s", ticker, e)
        return DataResponse(ticker=ticker, error=str(e))


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


POPULAR_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "JNJ",
    "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC", "NFLX", "ADBE", "CRM",
    "PEP", "KO", "INTC", "AMD", "CSCO", "NKE", "ABBV", "AVGO", "TXN", "QCOM",
    "COST", "PYPL", "UBER", "SPY", "QQQ", "DIA", "BTC-USD", "ETH-USD",
    "SOL-USD", "BNB-USD", "XRP-USD", "GC=F", "CL=F",
]


@router.get("/top-ranking")
def top_ranking(
    strategy: str = Query("scalping"),
    interval: str = Query("5m"),
    periods: int = Query(100, ge=20, le=500),
    tickers: str = Query("", description="Comma-separated subset; empty = all popular"),
):
    selected = [t.strip().upper() for t in tickers.split(",") if t.strip()] if tickers else POPULAR_TICKERS

    def _process(ticker: str) -> dict | None:
        try:
            r = run_analysis(ticker=ticker, strategy=strategy, interval=interval, periods=periods)
            if r["signal"] == "NEUTRAL" and r["confidence"] == 0:
                return None
            return {
                "ticker": ticker,
                "signal": r["signal"],
                "confidence": r["confidence"],
                "price": r.get("indicators", {}).get("price"),
                "reasons": r.get("reasons", []),
            }
        except Exception as e:
            logger.warning("top-ranking error %s: %s", ticker, e)
            return None

    results = []
    max_workers = min(6, len(selected))
    deadline = time.monotonic() + 90
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_process, t): t for t in selected}
        while futures:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning("top-ranking timed out, %d tickers pending", len(futures))
                break
            done, futures = wait(futures, timeout=min(30, remaining), return_when=FIRST_COMPLETED)
            for future in done:
                try:
                    item = future.result()
                    if item is not None:
                        results.append(item)
                except Exception as e:
                    logger.warning("top-ranking future error: %s", e)

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return {"strategy": strategy, "interval": interval, "rankings": results}


@router.post("/technical-analysis")
def technical_analysis(
    ticker: str = Query(...),
    strategy: str = Query("scalping"),
    interval: str = Query("1d"),
    periods: int = Query(100, ge=20, le=500),
):
    from app.services.technical_analysis import analyze_series

    try:
        chart_periods = max(periods, 200) if strategy == "swing" else max(periods, 30)
        df = get_historical_data(ticker, interval, chart_periods)
        series = compute_chart_data(df)
        return analyze_series(series, ticker)
    except Exception as e:
        logger.warning("Technical analysis error for %s: %s", ticker, e)
        return {
            "ticker": ticker, "strategy": strategy, "interval": interval,
            "verdict": "NEUTRAL", "confidence": 0, "signals": [],
            "summary": str(e), "error": str(e),
        }
