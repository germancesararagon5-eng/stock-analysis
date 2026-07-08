import logging
from typing import Any

import requests

from app.core.base_broker import BaseBroker
from app.core.debug import debug, timed

logger = logging.getLogger(__name__)


class BinanceBroker(BaseBroker):
    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"

    @timed
    def connect(self) -> bool:
        try:
            url = self.TESTNET_URL if self.config.sandbox else self.BASE_URL
            resp = requests.get(f"{url}/api/v3/ping", timeout=5)
            if resp.status_code == 200:
                self._connected = True
                logger.info("Binance conectado (%s)", "testnet" if self.config.sandbox else "production")
                debug.track_broker_event("connect", self.config.name,
                                         {"sandbox": self.config.sandbox, "status": "ok"})
                return True
            logger.error("Binance ping failed: %d", resp.status_code)
            return False
        except Exception as e:
            logger.exception("Error conectando a Binance")
            debug.track_error("binance.connect", str(e))
            return False

    @timed
    def get_realtime_data(self, ticker: str) -> dict[str, Any]:
        if not self._connected:
            return {"error": "Not connected", "ticker": ticker}
        try:
            url = self.TESTNET_URL if self.config.sandbox else self.BASE_URL
            symbol = ticker.upper().replace("/", "")
            resp = requests.get(
                f"{url}/api/v3/ticker/24hr",
                params={"symbol": symbol},
                timeout=5,
            )
            if resp.status_code != 200:
                return {"error": resp.text, "ticker": ticker}

            data = resp.json()
            return {
                "ticker": symbol,
                "price": float(data["lastPrice"]),
                "high": float(data["highPrice"]),
                "low": float(data["lowPrice"]),
                "volume": float(data["volume"]),
                "change_pct": float(data["priceChangePercent"]),
                "source": "binance",
                "broker": self.config.name,
            }
        except Exception as e:
            logger.exception("Error fetching Binance data for %s", ticker)
            debug.track_error(f"binance.get_realtime_data({ticker})", str(e))
            return {"error": str(e), "ticker": ticker}

    @timed
    def execute_order(self, side: str, quantity: float, ticker: str) -> dict[str, Any]:
        if not self._connected:
            return {"error": "Not connected", "status": "failed"}
        try:
            symbol = ticker.upper().replace("/", "")
            logger.info(
                "Binance orden simulada: %s %f %s (implementar signing)",
                side, quantity, symbol,
            )
            return {
                "status": "filled",
                "side": side,
                "quantity": quantity,
                "ticker": symbol,
                "broker": self.config.name,
                "message": "Orden ejecutada en Binance (simulada - implementar HMAC)",
            }
        except Exception as e:
            logger.exception("Error executing order on Binance")
            debug.track_error(f"binance.execute_order({ticker})", str(e))
            return {"error": str(e), "status": "failed"}
