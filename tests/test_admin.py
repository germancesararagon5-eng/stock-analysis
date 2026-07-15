import pytest


def test_admin_status_endpoint(client):
    resp = client.get("/api/admin/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "api" in data
    assert "database" in data
    assert "redis" in data
    assert "whatsapp" in data
    assert "background_analyzer" in data
    assert "ml_model" in data
    assert "broker" in data
    assert "debug" in data

    assert data["api"]["status"] == "ok"
    assert data["api"]["version"] == "2.6.0"
    assert data["ml_model"]["status"] in ("trained", "not_trained")
    assert data["debug"]["status"] in ("enabled", "disabled")
