from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from app.services.analysis_service import run_analysis, get_historical_data


def test_get_historical_data():
    mock_broker = MagicMock()
    mock_broker.config.name = "yahoo_finance"

    with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_broker):
        with patch("app.services.analysis_service.yf") as mock_yf:
            mock_ticker = MagicMock()
            mock_yf.Ticker.return_value = mock_ticker
            df = pd.DataFrame({
                "Close": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [95, 96, 97],
                "Open": [100, 101, 102],
                "Volume": [1000000] * 3,
            })
            mock_ticker.history.return_value = df

            result = get_historical_data("AAPL", "1d", 30)
            assert isinstance(result, pd.DataFrame)
            assert "Close" in result.columns


@patch("app.services.analysis_service.get_historical_data")
def test_run_analysis_scalping(mock_get_data):
    n = 100
    df = pd.DataFrame({
        "Close": [100 + (i % 10) for i in range(n)],
        "High": [105 + (i % 10) for i in range(n)],
        "Low": [95 + (i % 10) for i in range(n)],
        "Open": [100 + (i % 10) for i in range(n)],
        "Volume": [1000000] * n,
    })
    mock_get_data.return_value = df

    result = run_analysis("AAPL", "scalping", "1d", 100)
    assert result["ticker"] == "AAPL"
    assert result["strategy"] == "scalping"
    assert result["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= result["confidence"] <= 1.0
    assert "indicators" in result


@patch("app.services.analysis_service.get_historical_data")
@patch("app.services.analysis_service.debug")
def test_run_analysis_swing(mock_debug, mock_get_data):
    n = 200
    prices = [100] * 180 + list(range(100, 120))
    df = pd.DataFrame({
        "Close": prices,
        "High": [p * 1.02 for p in prices],
        "Low": [p * 0.98 for p in prices],
        "Open": prices,
        "Volume": [1000000] * n,
    })
    mock_get_data.return_value = df

    result = run_analysis("MSFT", "swing", "1d", 200)
    assert result["ticker"] == "MSFT"
    assert result["signal"] in ("BUY", "SELL", "NEUTRAL")


@patch("app.services.analysis_service.get_historical_data")
def test_run_analysis_insufficient_data(mock_get_data):
    df = pd.DataFrame({
        "Close": [100] * 10, "High": [105] * 10,
        "Low": [95] * 10, "Open": [100] * 10, "Volume": [1000000] * 10,
    })
    mock_get_data.return_value = df

    result = run_analysis("AAPL", "scalping", "1d", 10)
    assert result["signal"] == "NEUTRAL"
    assert result["confidence"] == 0.0
