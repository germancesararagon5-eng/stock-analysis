import logging
from datetime import datetime, timezone
from typing import Any

import polars as pl
import requests as req
import yfinance as yf

from app.core.broker_manager import BrokerManager
from app.core.debug import debug, timed
from app.core.strategies import STRATEGY_MAP, STRATEGY_MIN_PERIODS, run_strategy

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


BINANCE_INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w",
}


def _fetch_binance_klines(
    symbol: str, interval: str, limit: int
) -> pl.DataFrame:
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": BINANCE_INTERVAL_MAP.get(interval, "1d"), "limit": limit}
    resp = req.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    rows = []
    for k in data:
        rows.append({
            "timestamp": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
            "Open": float(k[1]), "High": float(k[2]), "Low": float(k[3]),
            "Close": float(k[4]), "Volume": float(k[5]),
        })
    return pl.DataFrame(rows)


def get_historical_data(
    ticker: str,
    interval: str = "5m",
    periods: int = 100,
) -> pl.DataFrame:
    broker = broker_manager.get_broker()

    # Detectar ticker crypto por sufijo USDT, USD, o prefijo CRYPTO: o contener -
    is_binance_symbol = any(ticker.upper().endswith(suf) for suf in ["USDT", "USDC", "BUSD", "ETH", "BTC"])

    if is_binance_symbol:
        return _fetch_binance_klines(ticker, interval, periods)

    if broker.config.name == "yahoo_finance":
        yf_interval = INTERVAL_MAP.get(interval, "5m")
        yf_period = PERIOD_MAP.get(interval, "5d")
        stock = yf.Ticker(ticker)
        df_pd = stock.history(period=yf_period, interval=yf_interval)
        if df_pd.empty:
            # Fallback a Binance si termina en USD
            if ticker.upper().endswith("USD"):
                return _fetch_binance_klines(ticker, interval, periods)
            raise ValueError(f"No historical data for {ticker}")
        df_pd = df_pd.tail(periods)
        ohlcv_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df_pd.columns]
        df_pd = df_pd[ohlcv_cols]
        df = pl.from_pandas(df_pd.reset_index())
        df = df.rename({df.columns[0]: "timestamp"})
        return df

    raise NotImplementedError(
        f"Historical data not implemented for {broker.config.name}"
    )


def _get_min_periods(strategy: str, periods: int) -> int:
    return max(periods, STRATEGY_MIN_PERIODS.get(strategy, 26))


@timed
def run_analysis(
    ticker: str,
    strategy: str = "scalping",
    interval: str = "5m",
    periods: int = 100,
    notify: bool = False,
    store_prediction: bool = True,
) -> dict[str, Any]:
    min_periods = _get_min_periods(strategy, periods)
    df = get_historical_data(ticker, interval, min_periods)

    result = run_strategy(df, strategy)

    result["ticker"] = ticker
    result["strategy"] = strategy
    result["interval"] = interval
    result["timestamp"] = datetime.now(timezone.utc).isoformat()

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

    if store_prediction:
        try:
            from app.services.prediction_service import store_prediction
            store_prediction(
                ticker=ticker,
                signal=result["signal"],
                confidence=result["confidence"],
                strategy=strategy,
                interval=interval,
                periods=periods,
                price=result.get("indicators", {}).get("price"),
                reasons=result.get("reasons", []),
                indicators=result.get("indicators", {}),
            )
        except Exception as e:
            logger.warning("Failed to auto-store prediction for %s: %s", ticker, e)

    if notify and result["signal"] in ("BUY", "SELL"):
        from app.services.whatsapp_service import send_alert

        msg = (
            f" SEÑAL {result['signal']} ({result['confidence']:.0%}) | "
            f"{ticker} | {strategy} | ${result['indicators'].get('price', 'N/A')} | "
            f"{' | '.join(result.get('reasons', []))}"
        )
        send_alert(msg)

    return result
