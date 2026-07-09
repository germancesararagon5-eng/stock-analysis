from unittest.mock import MagicMock, patch

import pytest

from app.core.broker_manager import BrokerManager


@pytest.fixture
def manager():
    BrokerManager._instance = None
    BrokerManager._active_broker = None
    BrokerManager._active_name = None
    return BrokerManager()


def test_singleton(manager):
    m2 = BrokerManager()
    assert manager is m2


def test_initial_state(manager):
    assert manager.active_name is None
    assert manager.active_broker is None


def test_get_broker_raises(manager):
    with pytest.raises(RuntimeError, match="No hay un bróker activo"):
        manager.get_broker()


def test_switch_unknown_broker(manager):
    with pytest.raises(ValueError, match="no soportado"):
        manager.switch("unknown")


def test_switch_yahoo_success(manager):
    result = manager.switch("yahoo_finance", sandbox=True)
    assert result["broker"] == "yahoo_finance"
    assert result["connected"] is True
    assert manager.active_name == "yahoo_finance"
    assert manager.active_broker is not None


def test_switch_rollback(manager):
    manager.switch("yahoo_finance", sandbox=True)

    mock_fail = MagicMock()
    mock_fail.connect.return_value = False
    with patch("app.core.broker_manager.BROKER_MAP", {"yahoo_finance": lambda cfg: mock_fail}):
        result = manager.switch("yahoo_finance", sandbox=True)
        assert result["connected"] is False


def test_load_from_db_no_record(manager):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = None

    manager.load_from_db(mock_db)
    assert manager.active_name is None


def test_load_from_db_with_record(manager):
    mock_db = MagicMock()
    mock_record = MagicMock()
    mock_record.name = "yahoo_finance"
    mock_record.api_key = None
    mock_record.api_secret = None
    mock_record.endpoint = None
    mock_record.sandbox = True
    mock_record.extra = None
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = mock_record

    manager.load_from_db(mock_db)
    assert manager.active_name == "yahoo_finance"
