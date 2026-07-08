from unittest.mock import patch


def test_create_alert(client, db_session):
    resp = client.post("/api/alerts/", json={
        "ticker": "AAPL",
        "strategy": "scalping",
        "condition": ">",
        "threshold": 150.0,
        "whatsapp_enabled": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert data["strategy"] == "scalping"
    assert data["enabled"] is True
    assert data["id"] > 0


def test_list_alerts(client, db_session):
    client.post("/api/alerts/", json={
        "ticker": "MSFT", "strategy": "swing",
        "condition": "<", "threshold": 300.0,
        "whatsapp_enabled": False,
    })
    resp = client.get("/api/alerts/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_delete_alert(client, db_session):
    create = client.post("/api/alerts/", json={
        "ticker": "GOOG", "strategy": "scalping",
        "condition": ">", "threshold": 2000.0,
        "whatsapp_enabled": False,
    })
    alert_id = create.json()["id"]
    resp = client.delete(f"/api/alerts/{alert_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == alert_id


@patch("app.routers.alerts_router.send_alert")
def test_test_whatsapp(mock_send_alert, client):
    mock_send_alert.return_value = {"status": "sent"}
    resp = client.post("/api/alerts/test-whatsapp")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "sent"
