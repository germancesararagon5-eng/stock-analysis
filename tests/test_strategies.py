import numpy as np
import polars as pl

from app.core.strategies import (
    STRATEGY_MAP,
    _atr,
    _detect_divergence,
    _find_levels,
    _rsi,
    breakout_signals,
    compute_chart_data,
    market_structure_signals,
    mean_reversion_signals,
    momentum_signals,
    run_strategy,
    scalping_signals,
    swing_signals,
)


def _df_from(prices, extra_cols: bool = True):
    n = len(prices)
    prices_f = [float(p) for p in prices]
    d = {
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(n)],
        "Close": prices_f,
        "High": [p * 1.02 for p in prices_f],
        "Low": [p * 0.98 for p in prices_f],
        "Open": prices_f,
        "Volume": [1000000] * n,
    }
    if not extra_cols:
        d = {"Close": prices_f}
    return pl.DataFrame(d)


# ═══════════════════════════════════════════════════════════════
# SCALPING
# ═══════════════════════════════════════════════════════════════

def test_scalping_insufficient_data():
    df = pl.DataFrame({
        "Close": [100] * 10, "High": [105] * 10, "Low": [95] * 10,
        "Open": [100] * 10, "Volume": [1000000] * 10,
    })
    r = scalping_signals(df)
    assert r["signal"] == "NEUTRAL"
    assert r["confidence"] == 0.0


def test_scalping_empty():
    r = scalping_signals(pl.DataFrame())
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


def test_scalping_volume_confirmation():
    n = 50
    prices = [100] * 10 + [100 + i * 0.1 for i in range(n - 10)]
    volumes = [100000] * 48 + [10000000, 10000000]
    df = pl.DataFrame({
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(n)],
        "Close": [float(p) for p in prices],
        "High": [float(p) * 1.02 for p in prices],
        "Low": [float(p) * 0.98 for p in prices],
        "Open": [float(p) for p in prices],
        "Volume": volumes,
    })
    r = scalping_signals(df)
    if r["signal"] in ("BUY", "SELL"):
        assert "Volumen" in " ".join(r.get("reasons", []))


def test_scalping_ema_golden_cross():
    prices = [100] * 25 + list(range(100, 130))
    df = _df_from(prices)
    r = scalping_signals(df)
    if r["signal"] == "BUY":
        assert any("cruzó arriba" in reason for reason in r.get("reasons", []))


def test_scalping_no_crash_with_missing_cols():
    df = pl.DataFrame({"Close": [100.0] * 30})
    r = scalping_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")


# ═══════════════════════════════════════════════════════════════
# SWING
# ═══════════════════════════════════════════════════════════════

def test_swing_insufficient_data():
    df = pl.DataFrame({
        "Close": [100] * 50, "High": [105] * 50, "Low": [95] * 50,
        "Open": [100] * 50, "Volume": [1000000] * 50,
    })
    r = swing_signals(df)
    assert r["signal"] == "NEUTRAL"
    assert r["confidence"] == 0.0


def test_swing_empty():
    r = swing_signals(pl.DataFrame())
    assert r["signal"] == "NEUTRAL"


def test_swing_returns_structure():
    prices = [100] * 180 + list(range(100, 120))
    df = _df_from(prices)
    r = swing_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= r["confidence"] <= 1.0
    assert all(k in r.get("indicators", {}) for k in ("macd", "macd_signal", "sma_200", "price"))


def test_swing_macd_bullish_cross():
    flat = [100] * 190
    uptrend = [100 + i * 0.5 for i in range(30)]
    df = _df_from(flat + uptrend)
    r = swing_signals(df)
    if r["signal"] == "BUY":
        assert any("cruzó arriba" in reason.lower() for reason in r.get("reasons", []))


def test_swing_sma_golden_cross():
    flat = [50] * 200
    uptrend = [50 + i * 0.3 for i in range(60)]
    df = _df_from(flat + uptrend)
    r = swing_signals(df)
    if r["signal"] == "BUY":
        assert any("golden" in reason.lower() for reason in r.get("reasons", []))


# ═══════════════════════════════════════════════════════════════
# MOMENTUM
# ═══════════════════════════════════════════════════════════════

def test_momentum_insufficient_data():
    r = momentum_signals(_df_from([100] * 20))
    assert r["signal"] == "NEUTRAL"
    assert r["confidence"] == 0.0


def test_momentum_empty():
    r = momentum_signals(pl.DataFrame())
    assert r["signal"] == "NEUTRAL"


def test_momentum_returns_structure():
    prices = [100] * 20 + [100 + i for i in range(40)]
    df = _df_from(prices)
    r = momentum_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= r["confidence"] <= 1.0
    assert all(k in r.get("indicators", {}) for k in ("roc_5", "roc_10", "rsi_14", "price"))


def test_momentum_positive_roc():
    uptrend = list(range(100, 200))
    df = _df_from(uptrend)
    r = momentum_signals(df)
    if r["signal"] == "BUY":
        assert any("Momentum" in reason for reason in r.get("reasons", []))


def test_momentum_negative_roc():
    downtrend = list(range(200, 100, -1))
    df = _df_from(downtrend)
    r = momentum_signals(df)
    if r["signal"] == "SELL":
        assert any("Momentum" in reason for reason in r.get("reasons", []))


def test_momentum_bullish_divergence():
    prices = [100] * 20 + [90 + np.sin(i * 0.2) * 5 for i in range(40)]
    df = _df_from([p if isinstance(p, (int, float)) else float(p) for p in prices])
    r = momentum_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")


# ═══════════════════════════════════════════════════════════════
# MEAN REVERSION
# ═══════════════════════════════════════════════════════════════

def test_mean_reversion_insufficient_data():
    r = mean_reversion_signals(_df_from([100] * 20))
    assert r["signal"] == "NEUTRAL"


def test_mean_reversion_empty():
    r = mean_reversion_signals(pl.DataFrame())
    assert r["signal"] == "NEUTRAL"


def test_mean_reversion_returns_structure():
    prices = [100] * 15 + [100 + np.sin(i * 0.5) * 10 for i in range(40)]
    df = _df_from(prices)
    r = mean_reversion_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= r["confidence"] <= 1.0
    assert all(k in r.get("indicators", {}) for k in ("bb_upper_2.5", "bb_lower_2.5", "rsi_14", "price"))


def test_mean_reversion_oversold_bounce():
    prices = [100] * 15 + [100 - i * 2 for i in range(35)]
    df = _df_from(prices)
    r = mean_reversion_signals(df)
    if r.get("indicators", {}).get("rsi_14", 50) < 30:
        assert r["signal"] in ("BUY", "NEUTRAL")


def test_mean_reversion_overbought_drop():
    prices = [100] * 15 + [100 + i * 2 for i in range(35)]
    df = _df_from(prices)
    r = mean_reversion_signals(df)
    if r.get("indicators", {}).get("rsi_14", 50) > 70:
        assert r["signal"] in ("SELL", "NEUTRAL")


# ═══════════════════════════════════════════════════════════════
# BREAKOUT
# ═══════════════════════════════════════════════════════════════

def test_breakout_insufficient_data():
    r = breakout_signals(_df_from([100] * 20))
    assert r["signal"] == "NEUTRAL"


def test_breakout_empty():
    r = breakout_signals(pl.DataFrame())
    assert r["signal"] == "NEUTRAL"


def test_breakout_returns_structure():
    prices = [100] * 30 + [100 + i for i in range(20)]
    df = _df_from(prices)
    r = breakout_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= r["confidence"] <= 1.0
    if r.get("indicators"):
        assert all(k in r["indicators"] for k in ("price", "atr", "rsi_14", "is_consolidating"))


def test_breakout_detects_consolidation():
    tight_range = [100.0 + np.sin(i * 0.05) * 1.0 for i in range(50)]
    df = _df_from(tight_range)
    r = breakout_signals(df)
    assert r.get("indicators", {}).get("range_pct", 100) < 5.0


def test_breakout_volume_expansion():
    n = 60
    prices = [100.0] * 30 + [102.0, 105.0, 108.0, 110.0]
    volumes = [1000000] * 30 + [3000000, 3500000, 4000000, 5000000]
    while len(prices) < n:
        prices.append(float(prices[-1] * 1.01))
        volumes.append(int(volumes[-1] * 1.1))
    df = pl.DataFrame({
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(n)],
        "Close": prices[:n],
        "High": [float(p) * 1.02 for p in prices[:n]],
        "Low": [float(p) * 0.98 for p in prices[:n]],
        "Open": prices[:n],
        "Volume": volumes[:n],
    })
    r = breakout_signals(df)
    if r["signal"] == "BUY":
        assert any("Volumen" in reason for reason in r.get("reasons", []))


# ═══════════════════════════════════════════════════════════════
# MARKET STRUCTURE
# ═══════════════════════════════════════════════════════════════

def test_market_structure_insufficient_data():
    r = market_structure_signals(_df_from([100] * 50))
    assert r["signal"] == "NEUTRAL"


def test_market_structure_empty():
    r = market_structure_signals(pl.DataFrame())
    assert r["signal"] == "NEUTRAL"


def test_market_structure_returns_structure():
    prices = [100] * 80 + list(range(100, 130))
    df = _df_from(prices)
    r = market_structure_signals(df)
    assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
    assert 0.0 <= r["confidence"] <= 1.0
    assert all(k in r.get("indicators", {}) for k in ("price", "ema_9", "sma_50", "rsi_14"))


def test_market_structure_bullish():
    n = 120
    uptrend = [100 + i * 0.5 + np.sin(i * 0.3) * 3 for i in range(n)]
    df = _df_from(uptrend)
    r = market_structure_signals(df)
    assert r["signal"] in ("BUY", "NEUTRAL")


def test_market_structure_bearish():
    n = 120
    downtrend = [200 - i * 0.5 + np.sin(i * 0.3) * 3 for i in range(n)]
    df = _df_from(downtrend)
    r = market_structure_signals(df)
    assert r["signal"] in ("SELL", "NEUTRAL")


# ═══════════════════════════════════════════════════════════════
# RUN_STRATEGY DISPATCH
# ═══════════════════════════════════════════════════════════════

def test_run_strategy_dispatches_correctly():
    df = _df_from([100] * 60)
    for name in STRATEGY_MAP:
        r = run_strategy(df, name)
        assert r["signal"] in ("BUY", "SELL", "NEUTRAL")
        assert 0.0 <= r["confidence"] <= 1.0
        assert r["strategy_type"] == name


def test_run_strategy_invalid():
    import pytest
    with pytest.raises(ValueError, match="no reconocida"):
        run_strategy(_df_from([100] * 30), "nonexistent")


# ═══════════════════════════════════════════════════════════════
# CHART DATA
# ═══════════════════════════════════════════════════════════════

def test_compute_chart_data_empty():
    r = compute_chart_data(pl.DataFrame())
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
    assert len(r["volume"]) == 50


def test_compute_chart_includes_new_series():
    prices = [100 + (i % 5) for i in range(250)]
    df = _df_from(prices)
    r = compute_chart_data(df)
    assert len(r["sma_50"]) == 250
    assert len(r["sma_200"]) == 250
    assert any(v is not None for v in r["sma_50"])
    assert any(v is not None for v in r["sma_200"])


# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

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


def test_rsi_all_ones():
    s = pl.Series("close", [100.0] * 20)
    r = _rsi(s, 14)
    assert r[-1] == 50.0


def test_rsi_up_trend():
    s = pl.Series("close", [float(i) for i in range(110, 200)])
    r = _rsi(s, 14)
    if r[-1] is not None:
        assert r[-1] > 50


def test_rsi_down_trend():
    s = pl.Series("close", [float(i) for i in range(200, 110, -1)])
    r = _rsi(s, 14)
    if r[-1] is not None:
        assert r[-1] < 50


def test_atr():
    hi = pl.Series("high", [110.0 + i for i in range(30)])
    lo = pl.Series("low", [90.0 + i for i in range(30)])
    cl = pl.Series("close", [100.0 + i for i in range(30)])
    a = _atr(hi, lo, cl, 14)
    assert a[-1] is not None
    assert isinstance(a[-1], float)
    assert a[-1] > 0
    assert isinstance(a, pl.Series)


def test_detect_divergence_insufficient():
    p = pl.Series("p", [100.0] * 3)
    o = pl.Series("o", [50.0] * 3)
    b, s = _detect_divergence(p, o)
    assert b is False
    assert s is False


def test_detect_bullish_divergence():
    p = pl.Series("p", [100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 94.0])
    o = pl.Series("o", [30.0, 29.0, 28.0, 27.0, 28.0, 29.0, 30.0])
    b, s = _detect_divergence(p, o)
    assert b is True
    assert s is False


def test_detect_bearish_divergence():
    p = pl.Series("p", [94.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0])
    o = pl.Series("o", [70.0, 71.0, 72.0, 73.0, 72.0, 71.0, 70.0])
    b, s = _detect_divergence(p, o)
    assert b is False
    assert s is True


# ═══════════════════════════════════════════════════════════════
# REAL LOGIC: RSI < 30 / > 70
# ═══════════════════════════════════════════════════════════════

def _assert_reason_contains(reasons: list, fragment: str) -> None:
    assert any(fragment.lower() in r.lower() for r in reasons), f"Expected reason containing '{fragment}' in {reasons}"


def test_scalping_rsi_under30_sets_buy():
    """RSI < 30 → BUY signal + 'sobrevendido' reason (no death cross at last bar)."""
    prices = [100.0 - i * 0.8 for i in range(40)]
    df = _df_from(prices)
    r = scalping_signals(df)
    assert r['indicators']['rsi_14'] < 30, f"RSI={r['indicators']['rsi_14']} should be < 30"
    assert r['signal'] == 'BUY', f'RSI<30 should set BUY, got {r["signal"]}'
    _assert_reason_contains(r['reasons'], 'sobrevendido')


def test_scalping_rsi_under30_neutralizes_deathcross():
    """Death cross + RSI<30 at same bar → both signals detected correctly."""
    uptrend = [100.0 + i * 0.3 for i in range(20)]
    flat = [uptrend[-1]] * 5
    crash = [uptrend[-1] - 47.0]
    prices = uptrend + flat + crash
    df = _df_from(prices)
    r = scalping_signals(df)
    assert r['indicators']['rsi_14'] < 30, f"RSI={r['indicators']['rsi_14']} should be < 30"
    _assert_reason_contains(r['reasons'], 'sobrevendido')
    _assert_reason_contains(r['reasons'], 'cruzó abajo')


def test_scalping_rsi_over70_sets_sell():
    """RSI > 70 → SELL signal + 'sobrecomprado' reason (no golden cross at last bar)."""
    prices = [50.0 + i * 0.8 for i in range(40)]
    df = _df_from(prices)
    r = scalping_signals(df)
    assert r['indicators']['rsi_14'] > 70, f"RSI={r['indicators']['rsi_14']} should be > 70"
    assert r['signal'] == 'SELL', f'RSI>70 should set SELL, got {r["signal"]}'
    _assert_reason_contains(r['reasons'], 'sobrecomprado')


def test_scalping_rsi_over70_neutralizes_goldencross():
    """Golden cross + RSI>70 at same bar → both signals detected correctly."""
    downtrend = [100.0 - i * 0.2 for i in range(20)]
    flat = [downtrend[-1]] * 5
    spike = [downtrend[-1] + 35.0]
    prices = downtrend + flat + spike
    df = _df_from(prices)
    r = scalping_signals(df)
    assert r['indicators']['rsi_14'] > 70, f"RSI={r['indicators']['rsi_14']} should be > 70"
    _assert_reason_contains(r['reasons'], 'sobrecomprado')
    _assert_reason_contains(r['reasons'], 'cruzó arriba')


# ═══════════════════════════════════════════════════════════════
# REAL LOGIC: EMA CROSSOVERS (scalping) at LAST bar
# ═══════════════════════════════════════════════════════════════

def test_scalping_ema_golden_cross_reason():
    """EMA9 crossing above EMA21 at last bar adds 'cruzó arriba' reason."""
    prices = [100.0] * 25 + [101.0]
    df = _df_from(prices)
    r = scalping_signals(df)
    _assert_reason_contains(r['reasons'], 'cruzó arriba')


def test_scalping_ema_death_cross_reason():
    """EMA9 crossing below EMA21 at last bar adds 'cruzó abajo' reason."""
    prices = [100.0] * 20 + [100.5] * 5 + [98.0]
    df = _df_from(prices)
    r = scalping_signals(df)
    _assert_reason_contains(r['reasons'], 'cruzó abajo')


# ═══════════════════════════════════════════════════════════════
# REAL LOGIC: SMA CROSSOVERS (swing) at LAST bar
# ═══════════════════════════════════════════════════════════════

def test_swing_sma_golden_cross_reason():
    """SMA50 crossing above SMA200 adds 'golden cross' reason."""
    prices = [50.0] * 200 + [50.0] * 49 + [100.0]
    df = _df_from(prices)
    r = swing_signals(df)
    _assert_reason_contains(r['reasons'], 'golden cross')


def test_swing_sma_death_cross_reason():
    """SMA50 crossing below SMA200 adds 'death cross' reason."""
    prices = [100.0] * 200 + [100.0] * 49 + [50.0]
    df = _df_from(prices)
    r = swing_signals(df)
    _assert_reason_contains(r['reasons'], 'death cross')
