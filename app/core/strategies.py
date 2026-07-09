import logging
from typing import Any

import numpy as np
import polars as pl

from app.core.debug import timed

logger = logging.getLogger(__name__)


def _to_series(col: pl.Series) -> list:
    return [None if v is None else round(float(v), 2) for v in col]


def _last(col: pl.Series) -> float:
    v = col[-1]
    return float(v) if v is not None else None


def _prev(col: pl.Series) -> float:
    v = col[-2]
    return float(v) if v is not None else None


@timed
def scalping_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 26:
        return {"signal": "NEUTRAL", "confidence": 0.0, "indicators": {}}

    c = df["Close"]

    ema_9_s = c.ewm_mean(span=9, adjust=False)
    ema_21_s = c.ewm_mean(span=21, adjust=False)
    rsi_s = _rsi(c, 14)
    bb_mid_s = c.rolling_mean(window_size=20)
    bb_std_s = c.rolling_std(window_size=20)
    bb_upper_s = bb_mid_s + 2 * bb_std_s
    bb_lower_s = bb_mid_s - 2 * bb_std_s

    last_price = _last(c)
    last_ema9 = _last(ema_9_s) if _last(ema_9_s) is not None else last_price
    last_ema21 = _last(ema_21_s) if _last(ema_21_s) is not None else last_price
    last_rsi = _last(rsi_s) if _last(rsi_s) is not None else 50.0
    last_bb_upper = _last(bb_upper_s) if _last(bb_upper_s) is not None else last_price
    last_bb_lower = _last(bb_lower_s) if _last(bb_lower_s) is not None else last_price
    last_bb_mid = _last(bb_mid_s) if _last(bb_mid_s) is not None else 0.0
    prev_ema9 = _prev(ema_9_s)
    prev_ema21 = _prev(ema_21_s)

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # EMA crossover
    if prev_ema9 is not None and prev_ema21 is not None:
        if last_ema9 > last_ema21 and prev_ema9 <= prev_ema21:
            signal = "BUY"
            confidence += 0.35
            reasons.append("EMA 9 cruzó arriba EMA 21")
        elif last_ema9 < last_ema21 and prev_ema9 >= prev_ema21:
            signal = "SELL"
            confidence += 0.35
            reasons.append("EMA 9 cruzó abajo EMA 21")

    # RSI
    if last_rsi < 30:
        if signal == "SELL":
            signal = "NEUTRAL"
        else:
            signal = "BUY"
            confidence += 0.25
        reasons.append(f"RSI sobrevendido ({last_rsi:.1f})")
    elif last_rsi > 70:
        if signal == "BUY":
            signal = "NEUTRAL"
        else:
            signal = "SELL"
            confidence += 0.25
        reasons.append(f"RSI sobrecomprado ({last_rsi:.1f})")

    # Bollinger bands
    if last_price <= last_bb_lower:
        if signal != "SELL":
            signal = "BUY"
            confidence += 0.20
        reasons.append("Precio tocó banda inferior de Bollinger")
    elif last_price >= last_bb_upper:
        if signal != "BUY":
            signal = "SELL"
            confidence += 0.20
        reasons.append("Precio tocó banda superior de Bollinger")

    confidence = min(confidence, 1.0)

    indicators = {
        "ema_9": round(last_ema9, 2),
        "ema_21": round(last_ema21, 2),
        "rsi_14": round(last_rsi, 2),
        "bb_upper": round(last_bb_upper, 2),
        "bb_mid": round(last_bb_mid, 2),
        "bb_lower": round(last_bb_lower, 2),
        "price": round(last_price, 2),
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
    }


@timed
def swing_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 200:
        return {"signal": "NEUTRAL", "confidence": 0.0, "indicators": {}}

    c = df["Close"]
    high = df["High"].to_numpy()
    low = df["Low"].to_numpy()

    ema12 = c.ewm_mean(span=12, adjust=False)
    ema26 = c.ewm_mean(span=26, adjust=False)
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm_mean(span=9, adjust=False)
    histogram = macd_line - signal_line
    sma_200 = c.rolling_mean(window_size=200)

    last_price = _last(c)
    last_sma200 = _last(sma_200) if _last(sma_200) is not None else last_price
    last_macd = _last(macd_line) if _last(macd_line) is not None else 0.0
    last_signal = _last(signal_line) if _last(signal_line) is not None else 0.0
    last_hist = _last(histogram) if _last(histogram) is not None else 0.0
    prev_macd = _prev(macd_line)
    prev_signal = _prev(signal_line)

    # Soportes y resistencias históricos
    supports = _find_levels(low, kind="support")
    resistances = _find_levels(high, kind="resistance")

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # MACD crossover
    if prev_macd is not None and prev_signal is not None:
        if last_macd > last_signal and prev_macd <= prev_signal:
            signal = "BUY"
            confidence += 0.40
            reasons.append("MACD cruzó arriba signal line")
        elif last_macd < last_signal and prev_macd >= prev_signal:
            signal = "SELL"
            confidence += 0.40
            reasons.append("MACD cruzó abajo signal line")

    # SMA 200 tendencia
    if last_price > last_sma200:
        confidence += 0.15
        reasons.append(f"Precio sobre SMA 200 ({last_sma200:.2f})")
    else:
        confidence -= 0.10
        reasons.append(f"Precio bajo SMA 200 ({last_sma200:.2f})")

    # Soporte/Resistencia
    for level in supports:
        if abs(last_price - level) / level < 0.01:
            if signal != "SELL":
                signal = "BUY"
                confidence += 0.20
            reasons.append(f"En soporte histórico ({level:.2f})")
            break

    for level in resistances:
        if abs(last_price - level) / level < 0.01:
            if signal != "BUY":
                signal = "SELL"
                confidence += 0.20
            reasons.append(f"En resistencia histórica ({level:.2f})")
            break

    confidence = max(0.0, min(confidence, 1.0))

    indicators = {
        "macd": round(last_macd, 4),
        "macd_signal": round(last_signal, 4),
        "macd_histogram": round(last_hist, 4),
        "sma_200": round(last_sma200, 2),
        "price": round(last_price, 2),
        "nearest_support": round(supports[-1], 2) if supports else None,
        "nearest_resistance": round(resistances[0], 2) if resistances else None,
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
    }


def compute_chart_data(df: pl.DataFrame) -> dict:
    if df.height == 0:
        return {"timestamp": [], "close": [], "ema_9": [], "ema_21": [],
                "bb_upper": [], "bb_mid": [], "bb_lower": [], "rsi_14": [],
                "macd": [], "macd_signal": [], "macd_histogram": []}

    c = df["Close"]
    timestamps = df.get_column("timestamp").to_list() if "timestamp" in df.columns else []

    valid_mask = [v is not None for v in c]
    close_vals = [round(float(v), 2) for v in c if v is not None]
    if len(close_vals) != len(timestamps):
        timestamps = [t for t, keep in zip(timestamps, valid_mask) if keep]

    ema9 = c.ewm_mean(span=9, adjust=False)
    ema21 = c.ewm_mean(span=21, adjust=False)
    rsi = _rsi(c, 14)
    bb_mid = c.rolling_mean(window_size=20)
    bb_std = c.rolling_std(window_size=20)
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std

    m_ema12 = c.ewm_mean(span=12, adjust=False)
    m_ema26 = c.ewm_mean(span=26, adjust=False)
    macd_line = m_ema12 - m_ema26
    macd_signal = macd_line.ewm_mean(span=9, adjust=False)
    macd_hist = macd_line - macd_signal

    return {
        "timestamp": timestamps,
        "close": close_vals,
        "ema_9": _to_series(ema9),
        "ema_21": _to_series(ema21),
        "bb_upper": _to_series(bb_upper),
        "bb_mid": _to_series(bb_mid),
        "bb_lower": _to_series(bb_lower),
        "rsi_14": _to_series(rsi),
        "macd": _to_series(macd_line),
        "macd_signal": _to_series(macd_signal),
        "macd_histogram": _to_series(macd_hist),
    }


def _rsi(close: pl.Series, period: int = 14) -> pl.Series:
    delta = close.diff().cast(pl.Float64)
    gain = delta.map_elements(lambda x: x if x is not None and x > 0 else 0.0, return_dtype=pl.Float64)
    loss = delta.map_elements(lambda x: -x if x is not None and x < 0 else 0.0, return_dtype=pl.Float64)
    avg_gain = gain.ewm_mean(span=period, adjust=False)
    avg_loss = loss.ewm_mean(span=period, adjust=False)
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def _find_levels(values: np.ndarray, kind: str = "support", bins: int = 30) -> list[float]:
    if len(values) < 10:
        return []
    hist, edges = np.histogram(values, bins=bins)
    levels = []
    for i in range(len(hist)):
        if hist[i] >= np.percentile(hist, 80):
            level = (edges[i] + edges[i + 1]) / 2
            levels.append(level)
    levels.sort()
    if kind == "support":
        return levels[:5]
    return levels[-5:] if levels else []
