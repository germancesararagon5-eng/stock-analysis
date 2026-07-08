import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

from app.core.broker_manager import BrokerManager
from app.core.debug import debug, timed
from app.core.strategies import scalping_signals, swing_signals

logger = logging.getLogger(__name__)

broker_manager = BrokerManager()

INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "60m",
    "4h": "4h",
    "1d": "1d",
}

PERIOD_MAP = {
    "1m": "1d",
    "5m": "5d",
    "15m": "1mo",
    "30m": "1mo",
    "1h": "2mo",
    "4h": "6mo",
    "1d": "1y",
}


def get_historical_data(
    ticker: str,
    interval: str = "5m",
    periods: int = 100,
) -> pd.DataFrame:
    broker = broker_manager.get_broker()

    if broker.config.name == "yahoo_finance":
        yf_interval = INTERVAL_MAP.get(interval, "5m")
        yf_period = PERIOD_MAP.get(interval, "5d")
        stock = yf.Ticker(ticker)
        df = stock.history(period=yf_period, interval=yf_interval)
        if df.empty:
            raise ValueError(f"No historical data for {ticker}")
        return df.tail(periods)

    # Para brokers no-yahoo: construir OHLC desde get_realtime_data
    # Placeholder: requeriría almacenamiento histórico local
    raise NotImplementedError(
        f"Historical data not implemented for {broker.config.name}"
    )


@timed
def run_analysis(
    ticker: str,
    strategy: str = "scalping",
    interval: str = "5m",
    periods: int = 100,
    notify: bool = False,
) -> dict[str, Any]:
    min_periods = 200 if strategy == "swing" else 26
    df = get_historical_data(ticker, interval, max(periods, min_periods))

    if strategy == "swing":
        result = swing_signals(df)
    else:
        result = scalping_signals(df)

    result["ticker"] = ticker
    result["strategy"] = strategy
    result["interval"] = interval
    result["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Overwrite strategy-level debug entry with real ticker
    if result.get("indicators"):
        debug.track_strategy(
            ticker=ticker,
            strategy=strategy,
            signal=result["signal"],
            confidence=result["confidence"],
            indicators=result["indicators"],
            reasons=result.get("reasons", []),
            raw_data_shape=df.shape,
        )

    if notify and result["signal"] in ("BUY", "SELL"):
        from app.services.whatsapp_service import send_alert

        msg = (
            f" SEÑAL {result['signal']} ({result['confidence']:.0%}) | "
            f"{ticker} | {strategy} | ${result['indicators'].get('price', 'N/A')} | "
            f"{' | '.join(result.get('reasons', []))}"
        )
        send_alert(msg)

    return result
