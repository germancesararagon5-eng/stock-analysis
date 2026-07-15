from unittest.mock import MagicMock, patch

import pytest
import requests


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_GATEWAY_URL", "http://localhost:3000")
    monkeypatch.setenv("WHATSAPP_GROUP_ID", "test-group-id")


@patch("app.services.whatsapp_service.requests.post")
@patch("app.services.whatsapp_service.requests.get")
@patch("app.database.SessionLocal")
def test_send_alert_success(mock_session_local, mock_get, mock_post):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_row = MagicMock()
    mock_row.phone_number = "+1234567890"
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db

    mock_get.return_value.json.return_value = {"connected": True}
    mock_post.return_value.json.return_value = {"success": True}

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test signal BUY AAPL")
    assert result["status"] == "sent"


@patch("app.services.whatsapp_service.requests.post")
@patch("app.services.whatsapp_service.requests.get")
@patch("app.database.SessionLocal")
def test_send_alert_gateway_error(mock_session_local, mock_get, mock_post):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_row = MagicMock()
    mock_row.phone_number = "+1234567890"
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db

    mock_get.return_value.json.return_value = {"connected": True}
    mock_post.return_value.json.return_value = {"success": False, "error": "gateway error"}

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test")
    assert result["status"] == "error"


@patch("app.services.whatsapp_service.requests.post")
@patch("app.services.whatsapp_service.requests.get")
@patch("app.database.SessionLocal")
def test_send_alert_no_target(mock_session_local, mock_get, mock_post):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_query.order_by.return_value.first.return_value = None
    mock_session_local.return_value = mock_db

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test")
    assert result["status"] == "skipped"
    assert result["reason"] == "No target number"


@patch("app.services.whatsapp_service.requests.post")
@patch("app.services.whatsapp_service.requests.get")
@patch("app.database.SessionLocal")
def test_send_alert_request_exception(mock_session_local, mock_get, mock_post):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_row = MagicMock()
    mock_row.phone_number = "+1234567890"
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db

    mock_get.return_value.json.return_value = {"connected": True}
    mock_post.side_effect = requests.RequestException("Connection refused")

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test")
    assert result["status"] == "error"


@patch("app.services.whatsapp_service.requests.post")
@patch("app.services.whatsapp_service.requests.get")
@patch("app.database.SessionLocal")
def test_send_alert_not_connected(mock_session_local, mock_get, mock_post):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_row = MagicMock()
    mock_row.phone_number = "+1234567890"
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db

    mock_get.side_effect = requests.ConnectionError("Not connected")

    from app.services.whatsapp_service import send_alert

    result = send_alert("Test")
    assert result["status"] == "skipped"
    assert "No se puede conectar al gateway" in result["reason"]


@patch("app.services.whatsapp_service.requests.get")
def test_check_connection(mock_get):
    mock_get.return_value.json.return_value = {"connected": True}
    from app.services.whatsapp_service import check_connection
    result = check_connection()
    assert result["connected"] is True
    assert result["gateway_reachable"] is True


@patch("app.services.whatsapp_service.requests.get")
def test_check_connection_failure(mock_get):
    mock_get.side_effect = requests.RequestException("Connection error")
    from app.services.whatsapp_service import check_connection
    result = check_connection()
    assert result["connected"] is False
    assert result["gateway_reachable"] is False
    assert "error" in result


@patch("app.database.SessionLocal")
def test_update_phone_number(mock_session_local):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_query.order_by.return_value.first.return_value = None
    mock_session_local.return_value = mock_db
    from app.services.whatsapp_service import update_phone_number
    result = update_phone_number("+1234567890")
    assert result["status"] == "ok"


@patch("app.database.SessionLocal")
def test_update_phone_number_existing(mock_session_local):
    mock_db = MagicMock()
    mock_row = MagicMock()
    mock_query = mock_db.query.return_value
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db
    from app.services.whatsapp_service import update_phone_number
    result = update_phone_number("+0987654321")
    assert result["status"] == "ok"


@patch("app.database.SessionLocal")
def test_update_phone_number_error(mock_session_local):
    mock_db = MagicMock()
    mock_db.commit.side_effect = Exception("DB error")
    mock_query = mock_db.query.return_value
    mock_query.order_by.return_value.first.return_value = None
    mock_session_local.return_value = mock_db
    from app.services.whatsapp_service import update_phone_number
    result = update_phone_number("+1234567890")
    assert result["status"] == "error"


@patch("app.services.whatsapp_service.requests.get")
@patch("app.database.SessionLocal")
def test_get_config(mock_session_local, mock_get):
    mock_get.return_value.json.return_value = {"connected": True}
    mock_db = MagicMock()
    mock_row = MagicMock()
    mock_row.phone_number = "+1234567890"
    mock_query = mock_db.query.return_value
    mock_query.order_by.return_value.first.return_value = mock_row
    mock_session_local.return_value = mock_db
    from app.services.whatsapp_service import get_config
    result = get_config()
    assert result["connected"] is True
    assert result["gateway_reachable"] is True
    assert result["phone_number"] == "+1234567890"
