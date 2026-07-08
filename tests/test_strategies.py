import numpy as np
import pandas as pd

from app.core.strategies import scalping_signals, swing_signals


def _make_sample_df(close_prices: list[float]) -> pd.DataFrame:
    n = len(close_prices)
    return pd.DataFrame({
        "Open": close_prices,
        "High": [c * 1.02 for c in close_prices],
        "Low": [c * 0.98 for c in close_prices],
        "Close": close_prices,
        "Volume": [1000000] * n,
    })


def test_scalping_buy_signal():
    prices = [100 + np.sin(i * 0.3) * 15 for i in range(100)]
    df = _make_sample_df(prices)
    result = scalping_signals(df)
    assert "signal" in result
    assert "confidence" in result
    assert "indicators" in result
    assert result["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= result["confidence"] <= 1.0


def test_scalping_insufficient_data():
    df = _make_sample_df([100] * 10)
    result = scalping_signals(df)
    assert result["signal"] == "NEUTRAL"
    assert result["confidence"] == 0.0


def test_swing_buy_signal():
    prices = [100] * 180 + list(np.linspace(100, 115, 20))
    df = _make_sample_df(prices)
    result = swing_signals(df)
    assert "signal" in result
    assert "confidence" in result
    assert "indicators" in result
    assert "macd" in result["indicators"]
    assert "sma_200" in result["indicators"]


def test_swing_insufficient_data():
    df = _make_sample_df([100] * 50)
    result = swing_signals(df)
    assert result["signal"] == "NEUTRAL"
