import numpy as np
import pandas as pd

from app.core.strategies import (
    _find_levels,
    compute_chart_data,
    scalping_signals,
    swing_signals,
)


def _df_from(prices):
    n = len(prices)
    return pd.DataFrame({
        "Close": prices,
        "High": [p * 1.02 for p in prices],
        "Low": [p * 0.98 for p in prices],
        "Open": prices,
        "Volume": [1000000] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="D"))


def test_scalping_insufficient_data():
    data = {"Close": [100] * 10, "High": [105] * 10, "Low": [95] * 10, "Open": [100] * 10, "Volume": [1000000] * 10}
    df = pd.DataFrame(data)
    r = scalping_signals(df)
    assert r["signal"] == "NEUTRAL"
    assert r["confidence"] == 0.0


def test_scalping_empty():
    r = scalping_signals(pd.DataFrame())
    assert r["signal"] == "NEUTRAL"


def test_scalping_returns_structure():
    prices = [100] * 20 + list(range(100, 130))
    df = _df_from(prices)
    r = scalping_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= r["confidence"] <= 1.0
    assert all(k in r.get("indicators", {}) for k in ("ema_9", "ema_21", "rsi_14", "price"))


def test_scalping_rsi_oversold():
    low_prices = [100] * 20 + [95, 90, 85, 80, 75, 70] * 15
    df = _df_from(low_prices[:110])
    r = scalping_signals(df)
    assert r["signal"] in ("BUY", "NEUTRAL")
    if r.get("indicators", {}).get("rsi_14", 50) < 30:
        assert "sobrevendido" in " ".join(r.get("reasons", []))


def test_swing_insufficient_data():
    data = {"Close": [100] * 50, "High": [105] * 50, "Low": [95] * 50, "Open": [100] * 50, "Volume": [1000000] * 50}
    df = pd.DataFrame(data)
    r = swing_signals(df)
    assert r["signal"] == "NEUTRAL"
    assert r["confidence"] == 0.0


def test_swing_empty():
    r = swing_signals(pd.DataFrame())
    assert r["signal"] == "NEUTRAL"


def test_swing_returns_structure():
    prices = [100] * 180 + list(range(100, 120))
    df = _df_from(prices)
    r = swing_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= r["confidence"] <= 1.0
    assert all(k in r.get("indicators", {}) for k in ("macd", "macd_signal", "sma_200", "price"))


def test_compute_chart_data_empty():
    r = compute_chart_data(pd.DataFrame())
    assert isinstance(r, dict)
    assert r["timestamp"] == []


def test_compute_chart_data_returns():
    prices = [100 + (i % 5) for i in range(50)]
    df = _df_from(prices)
    r = compute_chart_data(df)
    assert len(r["timestamp"]) == 50
    assert len(r["close"]) == 50
    assert len(r["ema_9"]) == 50
    assert len(r["bb_upper"]) == 50
    assert len(r["rsi_14"]) == 50


def test_find_levels_insufficient():
    assert _find_levels(np.array([1, 2, 3]), "support") == []


def test_find_levels_support():
    values = np.array([100] * 50 + [95] * 30 + [105] * 20)
    levels = _find_levels(values, "support")
    assert isinstance(levels, list)
    assert all(isinstance(v, float) for v in levels)
    assert len(levels) <= 5


def test_find_levels_resistance():
    values = np.array([100] * 50 + [105] * 30 + [95] * 20)
    levels = _find_levels(values, "resistance")
    assert isinstance(levels, list)
    assert len(levels) <= 5
