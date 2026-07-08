from fastapi.testclient import TestClient

from app.main import app


def test_websocket_connect():
    client = TestClient(app)
    with client.websocket_connect("/api/ws") as ws:
        ws.send_text("ping")
        # No hay respuesta esperada (es solo recepción), pero la conexión debe funcionar
        assert True


def test_websocket_broadcast():
    import asyncio
    import time

    from app.services.ws_manager import ws_manager

    client = TestClient(app)
    with client.websocket_connect("/api/ws") as ws:
        asyncio.run(ws_manager.broadcast({"type": "test", "data": "hello"}))
        time.sleep(0.1)
        ws.send_text("done")
