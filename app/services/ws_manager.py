import json
import logging
from typing import Any, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.info("WebSocket conectado (%d activos)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.info("WebSocket desconectado (%d activos)", len(self._connections))

    async def broadcast(self, data: dict[str, Any]) -> None:
        message = json.dumps(data, default=str)
        stale = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                stale.add(ws)
        for ws in stale:
            self._connections.discard(ws)


ws_manager = ConnectionManager()
