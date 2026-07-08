def test_broker_list(client):
    resp = client.get("/api/options/broker/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "available" in data
    assert isinstance(data["available"], list)


def test_broker_status(client):
    resp = client.get("/api/options/broker/status")
    assert resp.status_code == 200
    assert "active" in resp.json()


def test_background_status(client):
    resp = client.get("/api/options/background/status")
    assert resp.status_code == 200


def test_predictions_empty(client):
    resp = client.get("/api/options/predictions")
    assert resp.status_code == 200
    data = resp.json()
    assert "predictions" in data


def test_predictions_stats(client):
    resp = client.get("/api/options/predictions/stats")
    assert resp.status_code == 200
