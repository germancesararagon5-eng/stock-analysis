from unittest.mock import MagicMock, patch

import polars as pl

from app.services.analysis_service import get_historical_data, run_analysis


def _make_df(close, high=None, low=None):
    n = len(close)
    return pl.DataFrame({
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(n)],
        "Close": close,
        "High": high or [c * 1.02 for c in close],
        "Low": low or [c * 0.98 for c in close],
        "Open": close,
        "Volume": [1000000] * n,
    })


def test_get_historical_data():
    mock_broker = MagicMock()
    mock_broker.config.name = "yahoo_finance"

    with patch("app.services.analysis_service.broker_manager.get_broker", return_value=mock_broker):
        with patch("app.services.analysis_service.yf") as mock_yf:
            import pandas as pd
            mock_ticker = MagicMock()
            mock_yf.Ticker.return_value = mock_ticker
            df_pd = pd.DataFrame({
                "Close": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [95, 96, 97],
                "Open": [100, 101, 102],
                "Volume": [1000000] * 3,
            })
            mock_ticker.history.return_value = df_pd

            result = get_historical_data("AAPL", "1d", 30)
            assert isinstance(result, pl.DataFrame)
            assert "Close" in result.columns


@patch("app.services.analysis_service.get_historical_data")
def test_run_analysis_scalping(mock_get_data):
    n = 100
    df = _make_df([100 + (i % 10) for i in range(n)])
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
    df = _make_df(prices)
    mock_get_data.return_value = df

    result = run_analysis("MSFT", "swing", "1d", 200)
    assert result["ticker"] == "MSFT"
    assert result["signal"] in ("BUY", "SELL", "NEUTRAL")


@patch("app.services.analysis_service.get_historical_data")
def test_run_analysis_insufficient_data(mock_get_data):
    df = _make_df([100] * 10)
    mock_get_data.return_value = df

    result = run_analysis("AAPL", "scalping", "1d", 10)
    assert result["signal"] == "NEUTRAL"
    assert result["confidence"] == 0.0
