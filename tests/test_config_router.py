def test_get_broker_status(client):
    resp = client.get("/api/config/broker/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_broker" in data
    assert "connected" in data


def test_get_brokers(client):
    resp = client.get("/api/config/brokers")
    assert resp.status_code == 200
    data = resp.json()
    assert "available_brokers" in data
    assert isinstance(data["available_brokers"], list)
