import asyncio
import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.ws_manager import ws_manager


def test_websocket_connect_and_disconnect():
    client = TestClient(app)
    with client.websocket_connect("/api/ws") as ws:
        ws.send_text("ping")
        assert len(ws_manager._connections) == 1
    assert len(ws_manager._connections) == 0


def test_websocket_broadcast_receives_data():
    client = TestClient(app)
    with client.websocket_connect("/api/ws") as ws:
        asyncio.run(ws_manager.broadcast({"type": "test", "data": "hello"}))
        received = ws.receive_text()
        parsed = json.loads(received)
        assert parsed["type"] == "test"
        assert parsed["data"] == "hello"


def test_websocket_broadcast_multiple_clients():
    client = TestClient(app)
    with client.websocket_connect("/api/ws") as ws1:
        with client.websocket_connect("/api/ws") as ws2:
            asyncio.run(ws_manager.broadcast({"type": "broadcast", "msg": "to all"}))
            r1 = json.loads(ws1.receive_text())
            r2 = json.loads(ws2.receive_text())
            assert r1["msg"] == "to all"
            assert r2["msg"] == r1["msg"]
            assert len(ws_manager._connections) == 2


def test_websocket_broadcast_empty_data():
    client = TestClient(app)
    with client.websocket_connect("/api/ws") as ws:
        asyncio.run(ws_manager.broadcast({}))
        received = json.loads(ws.receive_text())
        assert received == {}



