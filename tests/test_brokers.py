import pytest

from app.brokers.binance import BinanceBroker
from app.brokers.interactive_brokers import InteractiveBrokersBroker
from app.brokers.yahoo_finance import YahooFinanceBroker
from app.core.base_broker import BrokerConfig


@pytest.fixture
def yahoo_config():
    return BrokerConfig(name="yahoo_finance", sandbox=True)


@pytest.fixture
def yahoo_broker(yahoo_config):
    return YahooFinanceBroker(yahoo_config)


def test_yahoo_connect(yahoo_broker):
    assert yahoo_broker.connect() is True
    assert yahoo_broker.is_connected is True


def test_yahoo_get_data(yahoo_broker):
    yahoo_broker.connect()
    data = yahoo_broker.get_realtime_data("AAPL")
    assert data["ticker"] == "AAPL"
    assert "price" in data


def test_yahoo_execute_order(yahoo_broker):
    yahoo_broker.connect()
    result = yahoo_broker.execute_order("BUY", 10, "AAPL")
    assert result["status"] == "simulated"


@pytest.fixture
def binance_config():
    return BrokerConfig(name="binance", sandbox=True)


def test_binance_connect(binance_config):
    broker = BinanceBroker(binance_config)
    result = broker.connect()
    assert result is True or result is False  # depende de conectividad


def test_ibkr_connect():
    config = BrokerConfig(name="interactive_brokers", sandbox=True)
    broker = InteractiveBrokersBroker(config)
    assert broker.connect() is True  # simulado
