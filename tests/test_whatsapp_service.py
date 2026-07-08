from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_GATEWAY_URL", "http://localhost:3000")
    monkeypatch.setenv("WHATSAPP_GROUP_ID", "test-group-id")


@patch("app.services.whatsapp_service.requests")
@patch("app.database.SessionLocal")
def test_send_alert_success(mock_session_local, mock_requests):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_row = MagicMock()
    mock_row.phone_number = "+1234567890"
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": True}
    mock_requests.post.return_value = mock_resp

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test signal BUY AAPL")
    assert result["status"] == "sent"


@patch("app.services.whatsapp_service.requests")
@patch("app.database.SessionLocal")
def test_send_alert_gateway_error(mock_session_local, mock_requests):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_row = MagicMock()
    mock_row.phone_number = "+1234567890"
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": False, "error": "gateway error"}
    mock_requests.post.return_value = mock_resp

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test")
    assert result["status"] == "error"


@patch("app.services.whatsapp_service.requests")
@patch("app.database.SessionLocal")
def test_send_alert_no_target(mock_session_local, mock_requests):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_query.order_by.return_value.first.return_value = None
    mock_session_local.return_value = mock_db

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test")
    assert result["status"] == "skipped"
    assert result["reason"] == "No target number"


@patch("app.services.whatsapp_service.requests")
def test_check_connection(mock_requests):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"connected": True}
    mock_requests.get.return_value = mock_resp

    from app.services.whatsapp_service import check_connection

    result = check_connection()
    assert result == {"connected": True}
