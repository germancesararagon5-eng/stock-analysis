def test_get_debug_dashboard(client):
    resp = client.get("/api/debug/")
    assert resp.status_code == 200


def test_clear_debug(client):
    resp = client.post("/api/debug/clear")
    assert resp.status_code == 200


def test_toggle_debug(client):
    resp = client.post("/api/debug/toggle")
    assert resp.status_code == 200
    assert "enabled" in resp.json()


def test_debug_filter_requests(client):
    resp = client.get("/api/debug/?show=requests&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "recent_requests" in data


def test_debug_filter_errors(client):
    resp = client.get("/api/debug/?show=errors")
    assert resp.status_code == 200
    data = resp.json()
    assert "recent_errors" in data


def test_debug_filter_broker(client):
    resp = client.get("/api/debug/?show=broker")
    assert resp.status_code == 200
    assert "recent_broker_events" in resp.json()


def test_debug_filter_strategy(client):
    resp = client.get("/api/debug/?show=strategy")
    assert resp.status_code == 200
    assert "recent_strategy_evals" in resp.json()


def test_debug_live_poll(client):
    resp = client.get("/api/debug/live?after_id=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "new_requests" in data
