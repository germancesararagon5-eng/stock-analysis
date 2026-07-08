from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data


def test_list_brokers():
    resp = client.get("/api/config/brokers")
    assert resp.status_code == 200
    data = resp.json()
    assert "available_brokers" in data
    assert "yahoo_finance" in data["available_brokers"]


def test_switch_broker():
    payload = {
        "name": "yahoo_finance",
        "sandbox": True,
    }
    resp = client.post("/api/config/broker", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["broker"] == "yahoo_finance"
    assert data["connected"] is True


def test_broker_status():
    resp = client.get("/api/config/broker/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_broker" in data
    assert "connected" in data
