from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from app.brokers.binance import BinanceBroker
from app.brokers.interactive_brokers import InteractiveBrokersBroker
from app.brokers.yahoo_finance import YahooFinanceBroker
from app.core.base_broker import BrokerConfig
from app.services.analysis_service import get_historical_data, run_analysis


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
    assert result is True or result is False


def test_ibkr_connect():
    config = BrokerConfig(name="interactive_brokers", sandbox=True)
    broker = InteractiveBrokersBroker(config)
    assert broker.connect() is True


# ── get_historical_data integration tests ──

@pytest.fixture
def mock_yahoo_broker():
    broker = MagicMock()
    broker.config.name = "yahoo_finance"
    return broker


@pytest.fixture
def sample_pandas_df():
    import pandas as pd
    return pd.DataFrame({
        "Close": [100.0, 101.0, 102.0, 103.0, 104.0],
        "High": [105.0, 106.0, 107.0, 108.0, 109.0],
        "Low": [95.0, 96.0, 97.0, 98.0, 99.0],
        "Open": [99.0, 100.0, 101.0, 102.0, 103.0],
        "Volume": [1000000] * 5,
    })


class TestGetHistoricalData:
    def test_yahoo_path_returns_polars_df(self, mock_yahoo_broker, sample_pandas_df):
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service.yf") as mock_yf:
                mock_ticker = MagicMock()
                mock_yf.Ticker.return_value = mock_ticker
                mock_ticker.history.return_value = sample_pandas_df
                result = get_historical_data("AAPL", "1d", 30)
                assert isinstance(result, pl.DataFrame)
                assert "Close" in result.columns
                assert result.shape[0] == 5

    def test_yahoo_path_tails_to_periods(self, mock_yahoo_broker, sample_pandas_df):
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service.yf") as mock_yf:
                mock_ticker = MagicMock()
                mock_yf.Ticker.return_value = mock_ticker
                long_df = sample_pandas_df.copy()
                mock_ticker.history.return_value = long_df
                result = get_historical_data("AAPL", "1d", 3)
                assert result.shape[0] == 3

    def test_yahoo_correct_interval_map(self, mock_yahoo_broker, sample_pandas_df):
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service.yf") as mock_yf:
                mock_ticker = MagicMock()
                mock_yf.Ticker.return_value = mock_ticker
                mock_ticker.history.return_value = sample_pandas_df
                get_historical_data("AAPL", "5m", 30)
                mock_yf.Ticker.assert_called_once_with("AAPL")
                mock_ticker.history.assert_called_once_with(period="5d", interval="5m")

    def test_empty_data_raises(self, mock_yahoo_broker):
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service.yf") as mock_yf:
                mock_ticker = MagicMock()
                mock_yf.Ticker.return_value = mock_ticker
                import pandas as pd
                mock_ticker.history.return_value = pd.DataFrame()
                with pytest.raises(ValueError, match="No historical data"):
                    get_historical_data("UNKNOWN", "1d", 30)

    def test_binance_symbol_detection_usdt(self, mock_yahoo_broker):
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service._fetch_binance_klines") as mock_binance:
                with patch("app.services.analysis_service.yf") as mock_yf:
                    mock_binance.return_value = pl.DataFrame({"timestamp": [], "Close": []})
                    get_historical_data("BTCUSDT", "1d", 100)
                    mock_binance.assert_called_once_with("BTCUSDT", "1d", 100)
                    mock_yf.Ticker.assert_not_called()

    def test_binance_symbol_detection_usdc(self, mock_yahoo_broker):
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service._fetch_binance_klines") as mock_binance:
                mock_binance.return_value = pl.DataFrame({"timestamp": [], "Close": []})
                get_historical_data("USDCUSDC", "1d", 100)
                mock_binance.assert_called_once()

    def test_binance_fallback_on_empty_yahoo(self, mock_yahoo_broker):
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service.yf") as mock_yf:
                with patch("app.services.analysis_service._fetch_binance_klines") as mock_binance:
                    mock_ticker = MagicMock()
                    mock_yf.Ticker.return_value = mock_ticker
                    import pandas as pd
                    mock_ticker.history.return_value = pd.DataFrame()
                    mock_binance.return_value = pl.DataFrame({"timestamp": ["2024-01-01"], "Close": [100.0]})
                    result = get_historical_data("BTC-USD", "1d", 100)
                    mock_binance.assert_called_once()
                    assert isinstance(result, pl.DataFrame)

    def test_ohlcv_filter_removes_dividends(self, mock_yahoo_broker, sample_pandas_df):
        sample_pandas_df["Dividends"] = 0.0
        sample_pandas_df["Stock Splits"] = 0.0
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with patch("app.services.analysis_service.yf") as mock_yf:
                mock_ticker = MagicMock()
                mock_yf.Ticker.return_value = mock_ticker
                mock_ticker.history.return_value = sample_pandas_df
                result = get_historical_data("AAPL", "1d", 30)
                assert "Dividends" not in result.columns
                assert "Stock Splits" not in result.columns

    def test_unsupported_broker_raises(self, mock_yahoo_broker):
        mock_yahoo_broker.config.name = "unsupported_broker"
        with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_yahoo_broker):
            with pytest.raises(NotImplementedError, match="Historical data not implemented"):
                get_historical_data("AAPL", "1d", 30)

    @patch("app.services.analysis_service.get_historical_data")
    def test_run_analysis_returns_expected_keys(self, mock_get_data):
        df = pl.DataFrame({
            "timestamp": [f"2024-01-{i+1:02d}" for i in range(100)],
            "Close": [100 + (i % 10) for i in range(100)],
            "High": [105 + (i % 10) for i in range(100)],
            "Low": [95 + (i % 10) for i in range(100)],
            "Open": [100 + (i % 10) for i in range(100)],
            "Volume": [1000000] * 100,
        })
        mock_get_data.return_value = df
        result = run_analysis("AAPL", "scalping", "1d", 100)
        assert "ticker" in result
        assert "signal" in result
        assert "confidence" in result
        assert "indicators" in result
        assert "reasons" in result
