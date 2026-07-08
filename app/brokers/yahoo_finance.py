import logging
from typing import Any

import yfinance as yf

from app.core.base_broker import BaseBroker
from app.core.debug import debug, timed

logger = logging.getLogger(__name__)


class YahooFinanceBroker(BaseBroker):
    @timed
    def connect(self) -> bool:
        self._connected = True
        logger.info("YahooFinanceBroker conectado (simulado - datos públicos)")
        debug.track_broker_event("connect", self.config.name, {"status": "ok"})
        return True

    @timed
    def get_realtime_data(self, ticker: str) -> dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d", interval="1m")
            if hist.empty:
                return {"error": f"No data for {ticker}", "ticker": ticker}

            last = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else last

            return {
                "ticker": ticker,
                "price": float(last["Close"]),
                "open": float(last["Open"]),
                "high": float(last["High"]),
                "low": float(last["Low"]),
                "volume": int(last["Volume"]),
                "change": float(last["Close"] - prev["Close"]),
                "change_pct": float((last["Close"] - prev["Close"]) / prev["Close"] * 100),
                "source": "yahoo_finance",
                "broker": self.config.name,
            }
        except Exception as e:
            logger.exception("Error fetching data for %s", ticker)
            debug.track_error(f"yahoo_finance.get_realtime_data({ticker})", str(e))
            return {"error": str(e), "ticker": ticker}

    def execute_order(self, side: str, quantity: float, ticker: str) -> dict[str, Any]:
        logger.warning(
            "YahooFinanceBroker NO ejecuta órdenes reales. "
            "Simulación: %s %f %s", side, quantity, ticker
        )
        return {
            "status": "simulated",
            "side": side,
            "quantity": quantity,
            "ticker": ticker,
            "broker": self.config.name,
            "message": "Yahoo Finance es solo datos. Orden simulada.",
        }
