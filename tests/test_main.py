def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_root_redirects(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_cors_headers(client):
    resp = client.options(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert "access-control-allow-origin" in resp.headers


import pytest


def test_websocket_accepts(client):
    with client.websocket_connect("/api/ws") as ws:
        assert ws is not None


def test_404(client):
    resp = client.get("/nonexistent")
    assert resp.status_code == 404
