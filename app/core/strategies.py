import logging
from typing import Any

import numpy as np
import pandas as pd
import ta

from app.core.debug import timed

logger = logging.getLogger(__name__)


@timed
def scalping_signals(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or len(df) < 26:
        return {"signal": "NEUTRAL", "confidence": 0.0, "indicators": {}}

    close = df["Close"]

    ema_9 = ta.trend.ema_indicator(close, window=9)
    ema_21 = ta.trend.ema_indicator(close, window=21)
    rsi = ta.momentum.rsi(close, window=14)
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband()
    bb_lower = bb.bollinger_lband()
    bb_mid = bb.bollinger_mavg()

    last_price = float(close.iloc[-1])
    last_ema9 = float(ema_9.iloc[-1]) if not pd.isna(ema_9.iloc[-1]) else last_price
    last_ema21 = float(ema_21.iloc[-1]) if not pd.isna(ema_21.iloc[-1]) else last_price
    last_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    last_bb_upper = float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else last_price
    last_bb_lower = float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else last_price

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # EMA crossover
    if last_ema9 > last_ema21 and ema_9.iloc[-2] <= ema_21.iloc[-2]:
        signal = "BUY"
        confidence += 0.35
        reasons.append("EMA 9 cruzó arriba EMA 21")
    elif last_ema9 < last_ema21 and ema_9.iloc[-2] >= ema_21.iloc[-2]:
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
        "bb_mid": round(bb_mid.iloc[-1], 2) if not pd.isna(bb_mid.iloc[-1]) else 0,
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
def swing_signals(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or len(df) < 200:
        return {"signal": "NEUTRAL", "confidence": 0.0, "indicators": {}}

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    macd = ta.trend.MACD(close)
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    histogram = macd.macd_diff()
    sma_200 = ta.trend.sma_indicator(close, window=200)

    last_price = float(close.iloc[-1])
    last_sma200 = float(sma_200.iloc[-1]) if not pd.isna(sma_200.iloc[-1]) else last_price
    last_macd = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0
    last_signal = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0
    last_hist = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0

    # Soportes y resistencias históricos
    supports = _find_levels(low.values, kind="support")
    resistances = _find_levels(high.values, kind="resistance")

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # MACD crossover
    if last_macd > last_signal and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        signal = "BUY"
        confidence += 0.40
        reasons.append("MACD cruzó arriba signal line")
    elif last_macd < last_signal and macd_line.iloc[-2] >= signal_line.iloc[-2]:
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


def compute_chart_data(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"timestamp": [], "close": [], "ema_9": [], "ema_21": [],
                "bb_upper": [], "bb_mid": [], "bb_lower": [], "rsi_14": [],
                "macd": [], "macd_signal": [], "macd_histogram": []}

    close = df["Close"]

    ema9 = ta.trend.ema_indicator(close, window=9)
    ema21 = ta.trend.ema_indicator(close, window=21)
    rsi = ta.momentum.rsi(close, window=14)
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)

    macd = ta.trend.MACD(close)
    macd_line = macd.macd()
    macd_signal = macd.macd_signal()
    macd_hist = macd.macd_diff()

    timestamps = [str(ts) for ts in df.index]

    def _clean(series):
        return [None if pd.isna(v) else round(float(v), 2) for v in series]

    return {
        "timestamp": timestamps,
        "close": [round(float(v), 2) for v in close],
        "ema_9": _clean(ema9),
        "ema_21": _clean(ema21),
        "bb_upper": _clean(bb.bollinger_hband()),
        "bb_mid": _clean(bb.bollinger_mavg()),
        "bb_lower": _clean(bb.bollinger_lband()),
        "rsi_14": _clean(rsi),
        "macd": _clean(macd_line),
        "macd_signal": _clean(macd_signal),
        "macd_histogram": _clean(macd_hist),
    }


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
