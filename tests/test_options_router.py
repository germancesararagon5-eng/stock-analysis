from unittest.mock import patch


def test_broker_list(client):
    resp = client.get("/api/options/broker/list")
    assert resp.status_code == 200
    assert "available" in resp.json()


def test_broker_status(client):
    resp = client.get("/api/options/broker/status")
    assert resp.status_code == 200
    assert "active" in resp.json()


def test_background_status(client):
    resp = client.get("/api/options/background/status")
    assert resp.status_code == 200


def test_background_start_stop(client):
    resp = client.post("/api/options/background/start")
    assert resp.status_code == 200
    resp = client.post("/api/options/background/stop")
    assert resp.status_code == 200


def test_background_config(client):
    resp = client.post("/api/options/background/config?tickers=AAPL,MSFT&strategy=swing&interval=1d&periods=200&run_every_seconds=60")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("strategy") == "swing"


def test_background_config_empty_tickers(client):
    resp = client.post("/api/options/background/config?strategy=scalping")
    assert resp.status_code == 200


def test_background_results(client):
    resp = client.get("/api/options/background/results?limit=5")
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_predictions_empty(client):
    resp = client.get("/api/options/predictions")
    assert resp.status_code == 200
    assert "predictions" in resp.json()


def test_predictions_with_ticker(client):
    resp = client.get("/api/options/predictions?ticker=AAPL")
    assert resp.status_code == 200


def test_predictions_stats(client):
    resp = client.get("/api/options/predictions/stats")
    assert resp.status_code == 200


def test_predictions_stats_with_ticker(client):
    resp = client.get("/api/options/predictions/stats?ticker=AAPL")
    assert resp.status_code == 200


def test_predictions_resolve(client):
    resp = client.post("/api/options/predictions/resolve?count=10")
    assert resp.status_code == 200
    assert "resolved" in resp.json()


@patch("app.services.whatsapp_service.update_phone_number")
def test_whatsapp_config_set(mock_update, client):
    mock_update.return_value = {"status": "ok"}
    resp = client.post("/api/options/whatsapp/config?phone_number=+1234567890")
    assert resp.status_code == 200


def test_debug_status(client):
    resp = client.get("/api/options/debug/status")
    assert resp.status_code == 200
    assert "enabled" in resp.json()


def test_debug_toggle(client):
    resp = client.post("/api/options/debug/toggle")
    assert resp.status_code == 200


def test_debug_clear(client):
    resp = client.post("/api/options/debug/clear")
    assert resp.status_code == 200
