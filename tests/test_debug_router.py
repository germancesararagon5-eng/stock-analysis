def test_get_debug_dashboard(client):
    resp = client.get("/api/debug/")
    assert resp.status_code == 200


def test_clear_debug(client):
    resp = client.post("/api/debug/clear")
    assert resp.status_code == 200


def test_toggle_debug(client):
    resp = client.post("/api/debug/toggle")
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data
