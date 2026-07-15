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


def _nth(col: pl.Series, n: int) -> float:
    if abs(n) >= len(col):
        return None
    v = col[n]
    return float(v) if v is not None else None


def _rsi(close: pl.Series, period: int = 14) -> pl.Series:
    delta = close.diff().cast(pl.Float64)
    gain = delta.map_elements(lambda x: x if x is not None and x > 0 else 0.0, return_dtype=pl.Float64)
    loss = delta.map_elements(lambda x: -x if x is not None and x < 0 else 0.0, return_dtype=pl.Float64)
    avg_gain = gain.ewm_mean(span=period, adjust=False, min_samples=1)
    avg_loss = loss.ewm_mean(span=period, adjust=False, min_samples=1)
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.fill_nan(50.0).fill_null(50.0)
    return rsi


def _atr(high: pl.Series, low: pl.Series, close: pl.Series, period: int = 14) -> pl.Series:
    prev_close = close.shift(1)
    tr1 = (high - low)
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr_np = np.maximum(np.maximum(tr1.to_numpy(), tr2.to_numpy()), tr3.to_numpy())
    tr_np = np.nan_to_num(tr_np, nan=0.0)
    tr = pl.Series("tr", tr_np)
    return tr.ewm_mean(span=period, adjust=False, min_samples=period)


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


def _detect_divergence(price: pl.Series, oscillator: pl.Series, window: int = 5) -> tuple[bool, bool]:
    if len(price) < window + 2 or len(oscillator) < window + 2:
        return False, False
    p_start = float(price[-window]) if price[-window] is not None else None
    p_end = float(price[-1]) if price[-1] is not None else None
    o_start = float(oscillator[-window]) if oscillator[-window] is not None else None
    o_end = float(oscillator[-1]) if oscillator[-1] is not None else None
    if any(v is None for v in [p_start, p_end, o_start, o_end]):
        return False, False
    bullish = p_end < p_start and o_end > o_start
    bearish = p_end > p_start and o_end < o_start
    return bullish, bearish


# ── Base result struct ────────────────────────────────────────

def _clean_nans(val: Any) -> Any:
    if isinstance(val, float) and (val != val):
        return None
    if isinstance(val, dict):
        return {k: _clean_nans(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_clean_nans(v) for v in val]
    return val


def _result(signal: str, confidence: float, indicators: dict, reasons: list) -> dict[str, Any]:
    return _clean_nans({
        "signal": signal,
        "confidence": round(min(confidence, 1.0), 2),
        "indicators": indicators,
        "reasons": reasons,
        "strategy_type": "",
    })


# ═══════════════════════════════════════════════════════════════
# STRATEGY 1: Scalping (original, improved)
# ═══════════════════════════════════════════════════════════════

@timed
def scalping_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 26:
        return _result("NEUTRAL", 0.0, {}, ["Datos insuficientes (mín 26 velas)"])

    c = df["Close"]
    hi = df.get_column("High") if "High" in df.columns else c
    lo = df.get_column("Low") if "Low" in df.columns else c
    vol = df.get_column("Volume") if "Volume" in df.columns else pl.Series("Volume", [0.0] * df.height)

    ema_9 = c.ewm_mean(span=9, adjust=False)
    ema_21 = c.ewm_mean(span=21, adjust=False)
    rsi = _rsi(c, 14)
    bb_mid = c.rolling_mean(window_size=20)
    bb_std = c.rolling_std(window_size=20)
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    atr = _atr(hi, lo, c, 14)
    volume = vol

    last_price = _last(c)
    last_ema9 = _last(ema_9) if _last(ema_9) is not None else last_price
    last_ema21 = _last(ema_21) if _last(ema_21) is not None else last_price
    last_rsi = _last(rsi) if _last(rsi) is not None else 50.0
    last_bb_upper = _last(bb_upper) if _last(bb_upper) is not None else last_price
    last_bb_lower = _last(bb_lower) if _last(bb_lower) is not None else last_price
    last_bb_mid = _last(bb_mid) if _last(bb_mid) is not None else 0.0
    last_atr = _last(atr) if _last(atr) is not None else 0.0
    prev_ema9 = _prev(ema_9)
    prev_ema21 = _prev(ema_21)

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # EMA crossover
    if prev_ema9 is not None and prev_ema21 is not None:
        if last_ema9 > last_ema21 and prev_ema9 <= prev_ema21:
            signal = "BUY"
            confidence += 0.30
            reasons.append("EMA 9 cruzó arriba EMA 21 (golden cross rápido)")
        elif last_ema9 < last_ema21 and prev_ema9 >= prev_ema21:
            signal = "SELL"
            confidence += 0.30
            reasons.append("EMA 9 cruzó abajo EMA 21 (death cross rápido)")

    # EMA slope (momentum direction)
    if df.height >= 4:
        ema_slope_1 = (ema_9[-1] - ema_9[-2]) if ema_9[-1] is not None and ema_9[-2] is not None else 0
        ema_slope_2 = (ema_9[-2] - ema_9[-3]) if ema_9[-2] is not None and ema_9[-3] is not None else 0
        if ema_slope_1 > 0 and ema_slope_2 > 0:
            confidence += 0.10
            reasons.append("EMA 9 acelerando al alza")
        elif ema_slope_1 < 0 and ema_slope_2 < 0:
            confidence -= 0.10
            reasons.append("EMA 9 acelerando a la baja")

    # RSI
    if last_rsi < 30:
        if signal == "SELL":
            signal = "NEUTRAL"
        else:
            signal = "BUY"
            confidence += 0.20
        reasons.append(f"RSI sobrevendido ({last_rsi:.1f})")
    elif last_rsi > 70:
        if signal == "BUY":
            signal = "NEUTRAL"
        else:
            signal = "SELL"
            confidence += 0.20
        reasons.append(f"RSI sobrecomprado ({last_rsi:.1f})")
    elif last_rsi < 40:
        confidence += 0.05
        reasons.append(f"RSi inclinación alcista ({last_rsi:.1f})")
    elif last_rsi > 60:
        confidence -= 0.05
        reasons.append(f"RSI inclinación bajista ({last_rsi:.1f})")

    # Bollinger bands
    if last_price <= last_bb_lower:
        if signal != "SELL":
            signal = "BUY"
            confidence += 0.15
        reasons.append("Precio en banda inferior de Bollinger")
    elif last_price >= last_bb_upper:
        if signal != "BUY":
            signal = "SELL"
            confidence += 0.15
        reasons.append("Precio en banda superior de Bollinger")

    # Volume confirmation
    if df.height >= 3:
        avg_vol = float(volume[-20:].mean()) if df.height >= 20 else float(volume.mean())
        last_vol = float(volume[-1]) if volume[-1] is not None else 0
        if avg_vol > 0 and last_vol > avg_vol * 1.5:
            if signal == "BUY":
                confidence += 0.10
                reasons.append("Volumen alto confirma movimiento alcista")
            elif signal == "SELL":
                confidence += 0.10
                reasons.append("Volumen alto confirma movimiento bajista")
            else:
                reasons.append("Volumen elevado — posible movimiento inminente")

    # ATR volatility context
    if last_atr > 0 and last_price > 0:
        atr_pct = (last_atr / last_price) * 100
        if atr_pct < 0.5:
            reasons.append(f"Volatilidad baja (ATR {atr_pct:.2f}%) — mercado tranquilo")
        elif atr_pct > 2.0:
            reasons.append(f"Volatilidad alta (ATR {atr_pct:.2f}%) — mercado agitado")

    confidence = max(0.0, min(confidence, 1.0))

    indicators = {
        "ema_9": round(last_ema9, 2),
        "ema_21": round(last_ema21, 2),
        "rsi_14": round(last_rsi, 2),
        "bb_upper": round(last_bb_upper, 2),
        "bb_mid": round(last_bb_mid, 2),
        "bb_lower": round(last_bb_lower, 2),
        "price": round(last_price, 2),
        "atr": round(last_atr, 4),
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
        "strategy_type": "scalping",
    }


# ═══════════════════════════════════════════════════════════════
# STRATEGY 2: Swing (original, improved)
# ═══════════════════════════════════════════════════════════════

@timed
def swing_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 200:
        return _result("NEUTRAL", 0.0, {}, ["Datos insuficientes (mín 200 velas)"])

    c = df["Close"]
    hi = df["High"].to_numpy()
    lo = df["Low"].to_numpy()

    ema12 = c.ewm_mean(span=12, adjust=False)
    ema26 = c.ewm_mean(span=26, adjust=False)
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm_mean(span=9, adjust=False)
    histogram = macd_line - signal_line
    sma_50 = c.rolling_mean(window_size=50)
    sma_200 = c.rolling_mean(window_size=200)
    rsi = _rsi(c, 14)

    last_price = _last(c)
    last_sma50 = _last(sma_50) if _last(sma_50) is not None else last_price
    last_sma200 = _last(sma_200) if _last(sma_200) is not None else last_price
    last_macd = _last(macd_line) if _last(macd_line) is not None else 0.0
    last_signal = _last(signal_line) if _last(signal_line) is not None else 0.0
    last_hist = _last(histogram) if _last(histogram) is not None else 0.0
    last_rsi_val = _last(rsi) if _last(rsi) is not None else 50.0
    prev_macd = _prev(macd_line)
    prev_signal = _prev(signal_line)

    supports = _find_levels(lo, kind="support")
    resistances = _find_levels(hi, kind="resistance")

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # MACD crossover
    if prev_macd is not None and prev_signal is not None:
        if last_macd > last_signal and prev_macd <= prev_signal:
            signal = "BUY"
            confidence += 0.30
            reasons.append("MACD cruzó arriba signal line")
        elif last_macd < last_signal and prev_macd >= prev_signal:
            signal = "SELL"
            confidence += 0.30
            reasons.append("MACD cruzó abajo signal line")

    # MACD histogram direction
    prev_hist = _prev(histogram)
    if prev_hist is not None and last_hist is not None:
        if last_hist > prev_hist and last_hist > 0:
            confidence += 0.10
            reasons.append("Histograma MACD creciendo positivo — momentum alcista")
        elif last_hist < prev_hist and last_hist < 0:
            confidence -= 0.10
            reasons.append("Histograma MACD cayendo negativo — momentum bajista")
        elif last_hist > prev_hist and last_hist < 0:
            confidence += 0.05
            reasons.append("Histograma MACD acercándose a cero — posible cambio de tendencia")

    # SMA trend alignment
    if last_price > last_sma200:
        confidence += 0.10
        reasons.append(f"Precio sobre SMA 200 ({last_sma200:.2f}) — tendencia alcista larga")
    else:
        confidence -= 0.10
        reasons.append(f"Precio bajo SMA 200 ({last_sma200:.2f}) — tendencia bajista larga")

    if last_price > last_sma50:
        confidence += 0.10
        reasons.append(f"Precio sobre SMA 50 ({last_sma50:.2f}) — tendencia alcista media")
    else:
        confidence -= 0.05
        reasons.append(f"Precio bajo SMA 50 ({last_sma50:.2f}) — tendencia bajista media")

    # Golden/death cross detection (SMA 50 x SMA 200)
    if df.height >= 250:
        sma50_prev = _nth(sma_50, -2) or last_price
        sma200_prev = _nth(sma_200, -2) or last_price
        if last_sma50 > last_sma200 and sma50_prev <= sma200_prev:
            signal = "BUY"
            confidence += 0.25
            reasons.append("Golden cross detectado (SMA 50 cruzó SMA 200)")
        elif last_sma50 < last_sma200 and sma50_prev >= sma200_prev:
            signal = "SELL"
            confidence += 0.25
            reasons.append("Death cross detectado (SMA 50 cruzó SMA 200)")

    # RSI para confirmación en swing
    if last_rsi_val > 70:
        if signal != "BUY":
            confidence -= 0.05
        reasons.append(f"RSI sobrecomprado ({last_rsi_val:.1f}) — posible techo")
    elif last_rsi_val < 30:
        if signal != "SELL":
            confidence += 0.10
        reasons.append(f"RSI sobrevendido ({last_rsi_val:.1f}) — posible piso")
    elif 40 <= last_rsi_val <= 60:
        reasons.append(f"RSI neutral ({last_rsi_val:.1f})")

    # S/R levels
    for level in supports:
        if abs(last_price - level) / level < 0.015:
            if signal != "SELL":
                signal = "BUY"
                confidence += 0.15
            reasons.append(f"Apoyado en soporte histórico ({level:.2f})")
            break

    for level in resistances:
        if abs(last_price - level) / level < 0.015:
            if signal != "BUY":
                signal = "SELL"
                confidence += 0.15
            reasons.append(f"Rechazado en resistencia histórica ({level:.2f})")
            break

    confidence = max(0.0, min(confidence, 1.0))

    nearest_support = supports[-1] if supports else None
    nearest_resistance = resistances[0] if resistances else None

    indicators = {
        "macd": round(last_macd, 4),
        "macd_signal": round(last_signal, 4),
        "macd_histogram": round(last_hist, 4),
        "sma_50": round(last_sma50, 2),
        "sma_200": round(last_sma200, 2),
        "price": round(last_price, 2),
        "rsi_14": round(last_rsi_val, 2),
        "nearest_support": round(nearest_support, 2) if nearest_support else None,
        "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
        "strategy_type": "swing",
    }


# ═══════════════════════════════════════════════════════════════
# STRATEGY 3: Momentum
# ═══════════════════════════════════════════════════════════════

@timed
def momentum_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 50:
        return _result("NEUTRAL", 0.0, {}, ["Datos insuficientes (mín 50 velas)"])

    c = df["Close"]
    hi = df["High"]
    lo = df["Low"]
    volume = df["Volume"]

    roc_5 = c.diff(5) / c.shift(5) * 100
    roc_10 = c.diff(10) / c.shift(10) * 100
    roc_20 = c.diff(20) / c.shift(20) * 100
    rsi = _rsi(c, 14)
    ema_9 = c.ewm_mean(span=9, adjust=False)
    ema_21 = c.ewm_mean(span=21, adjust=False)
    atr = _atr(hi, lo, c, 14)

    last_price = _last(c)
    last_roc5 = _last(roc_5) if _last(roc_5) is not None else 0.0
    last_roc10 = _last(roc_10) if _last(roc_10) is not None else 0.0
    last_roc20 = _last(roc_20) if _last(roc_20) is not None else 0.0
    last_rsi = _last(rsi) if _last(rsi) is not None else 50.0
    last_ema9 = _last(ema_9) if _last(ema_9) is not None else last_price
    last_ema21 = _last(ema_21) if _last(ema_21) is not None else last_price
    last_atr = _last(atr) if _last(atr) is not None else 0.0
    prev_roc5 = _prev(roc_5)
    prev_roc10 = _prev(roc_10)

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # ROC acceleration
    if prev_roc5 is not None and prev_roc10 is not None:
        if last_roc5 > prev_roc5 and last_roc10 > 2:
            signal = "BUY"
            confidence += 0.25
            reasons.append(f"ROC(5) acelerando ({last_roc5:+.2f}%) — momentum alcista")
        elif last_roc5 < prev_roc5 and last_roc10 < -2:
            signal = "SELL"
            confidence += 0.25
            reasons.append(f"ROC(5) cayendo ({last_roc5:+.2f}%) — momentum bajista")

    # ROC multi-period confirmation
    if last_roc5 > 3 and last_roc10 > 2 and last_roc20 > 1:
        if signal != "SELL":
            signal = "BUY"
            confidence += 0.20
        reasons.append("Momentum positivo en múltiples horizontes (5/10/20)")
    elif last_roc5 < -3 and last_roc10 < -2 and last_roc20 < -1:
        if signal != "BUY":
            signal = "SELL"
            confidence += 0.20
        reasons.append("Momentum negativo en múltiples horizontes (5/10/20)")

    # RSI momentum
    if last_rsi > 60 and signal == "BUY":
        confidence += 0.10
        reasons.append(f"RSI respalda momentum ({last_rsi:.1f})")
    elif last_rsi < 40 and signal == "SELL":
        confidence += 0.10
        reasons.append(f"RSI respalda momentum ({last_rsi:.1f})")

    # EMA alignment for trend
    if last_ema9 > last_ema21:
        confidence += 0.10
        reasons.append("EMAs alineadas alcistas")
    else:
        confidence -= 0.10
        reasons.append("EMAs alineadas bajistas")

    # Volume momentum
    if df.height >= 20:
        avg_vol = float(volume[-20:].mean())
        last_vol = float(volume[-1]) if volume[-1] is not None else 0
        if avg_vol > 0 and last_vol > avg_vol * 1.3:
            confidence += 0.10
            reasons.append("Volumen creciente confirma momentum")

    # Divergence check
    bullish_div, bearish_div = _detect_divergence(c, rsi, window=7)
    if bullish_div:
        if signal != "SELL":
            signal = "BUY"
        confidence += 0.15
        reasons.append("Divergencia alcista RSI-precio — momentum latente")
    if bearish_div:
        if signal != "BUY":
            signal = "SELL"
        confidence += 0.15
        reasons.append("Divergencia bajista RSI-precio — agotamiento")

    confidence = max(0.0, min(confidence, 1.0))

    indicators = {
        "roc_5": round(last_roc5, 2),
        "roc_10": round(last_roc10, 2),
        "roc_20": round(last_roc20, 2),
        "rsi_14": round(last_rsi, 2),
        "price": round(last_price, 2),
        "ema_9": round(last_ema9, 2),
        "ema_21": round(last_ema21, 2),
        "atr": round(last_atr, 4),
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
        "strategy_type": "momentum",
    }


# ═══════════════════════════════════════════════════════════════
# STRATEGY 4: Mean Reversion
# ═══════════════════════════════════════════════════════════════

@timed
def mean_reversion_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 30:
        return _result("NEUTRAL", 0.0, {}, ["Datos insuficientes (mín 30 velas)"])

    c = df["Close"]
    hi = df["High"]
    lo = df["Low"]

    bb_mid = c.rolling_mean(window_size=20)
    bb_std = c.rolling_std(window_size=20)
    bb_upper = bb_mid + 2.5 * bb_std
    bb_lower = bb_mid - 2.5 * bb_std
    bb_mid_inner = bb_mid
    bb_inner_upper = bb_mid + 1.5 * bb_std
    bb_inner_lower = bb_mid - 1.5 * bb_std
    rsi = _rsi(c, 14)
    rsi_7 = _rsi(c, 7)
    ema_9 = c.ewm_mean(span=9, adjust=False)
    ema_21 = c.ewm_mean(span=21, adjust=False)
    atr = _atr(hi, lo, c, 14)

    last_price = _last(c)
    last_bb_mid = _last(bb_mid) if _last(bb_mid) is not None else last_price
    last_bb_upper = _last(bb_upper) if _last(bb_upper) is not None else last_price + 1
    last_bb_lower = _last(bb_lower) if _last(bb_lower) is not None else last_price - 1
    last_bb_inner_upper = _last(bb_inner_upper) if _last(bb_inner_upper) is not None else last_price
    last_bb_inner_lower = _last(bb_inner_lower) if _last(bb_inner_lower) is not None else last_price
    last_rsi = _last(rsi) if _last(rsi) is not None else 50.0
    last_rsi7 = _last(rsi_7) if _last(rsi_7) is not None else 50.0
    last_ema9 = _last(ema_9) if _last(ema_9) is not None else last_price
    last_ema21 = _last(ema_21) if _last(ema_21) is not None else last_price
    last_atr = _last(atr) if _last(atr) is not None else 0.0
    prev_ema9 = _prev(ema_9)
    prev_ema21 = _prev(ema_21)

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # Extreme Bollinger Band touches (2.5 std dev — strong reversal signal)
    if last_price <= last_bb_lower:
        signal = "BUY"
        confidence += 0.30
        reasons.append("Precio extremadamente bajo banda Bollinger (2.5σ) — fuerte señal de reversión")
    elif last_price >= last_bb_upper:
        signal = "SELL"
        confidence += 0.30
        reasons.append("Precio extremadamente alto banda Bollinger (2.5σ) — fuerte señal de reversión")
    elif last_price <= last_bb_inner_lower:
        if signal != "SELL":
            signal = "BUY"
        confidence += 0.20
        reasons.append("Precio en banda Bollinger inferior (1.5σ) — posible reversión alcista")
    elif last_price >= last_bb_inner_upper:
        if signal != "BUY":
            signal = "SELL"
        confidence += 0.20
        reasons.append("Precio en banda Bollinger superior (1.5σ) — posible reversión bajista")

    # RSI extreme oversold/overbought (mean reversion)
    if last_rsi < 25:
        if signal != "SELL":
            signal = "BUY"
        confidence += 0.20
        reasons.append(f"RSI(14) extremo ({last_rsi:.1f}) — fuerte sobreventa")
    elif last_rsi > 75:
        if signal != "BUY":
            signal = "SELL"
        confidence += 0.20
        reasons.append(f"RSI(14) extremo ({last_rsi:.1f}) — fuerte sobrecompra")
    elif last_rsi < 35:
        confidence += 0.10
        reasons.append(f"RSI(14) en zona de sobreventa ({last_rsi:.1f})")
    elif last_rsi > 65:
        confidence -= 0.10
        reasons.append(f"RSI(14) en zona de sobrecompra ({last_rsi:.1f})")

    # Fast RSI(7) for early reversal detection
    if last_rsi7 < 20:
        if signal != "SELL":
            signal = "BUY"
        confidence += 0.15
        reasons.append(f"RSI(7) extremo ({last_rsi7:.1f}) — rebote inminente")
    elif last_rsi7 > 80:
        if signal != "BUY":
            signal = "SELL"
        confidence += 0.15
        reasons.append(f"RSI(7) extremo ({last_rsi7:.1f}) — corrección inminente")

    # z-score price vs EMA
    bb_width = last_bb_upper - last_bb_lower
    if bb_width > 0:
        z_score = (last_price - last_bb_mid) / (bb_width / 5)
        if abs(z_score) > 2.0:
            confidence += 0.10
            reasons.append(f"Desviación estadística significativa (z={z_score:.1f})")

    # Divergence (early reversal signal)
    bullish_div, bearish_div = _detect_divergence(c, rsi, window=5)
    if bullish_div and signal != "SELL":
        signal = "BUY"
        confidence += 0.15
        reasons.append("Divergencia alcista RSI — posible agotamiento bajista")
    if bearish_div and signal != "BUY":
        signal = "SELL"
        confidence += 0.15
        reasons.append("Divergencia bajista RSI — posible agotamiento alcista")

    # EMA crossover as confirmation
    if prev_ema9 is not None and prev_ema21 is not None:
        if last_ema9 > last_ema21 and prev_ema9 <= prev_ema21 and signal == "BUY":
            confidence += 0.10
            reasons.append("Golden cross rápido confirma reversión")
        elif last_ema9 < last_ema21 and prev_ema9 >= prev_ema21 and signal == "SELL":
            confidence += 0.10
            reasons.append("Death cross rápido confirma reversión")

    # Return to mean proximity
    dist_to_mid_pct = abs(last_price - last_bb_mid) / last_bb_mid * 100 if last_bb_mid > 0 else 0
    if dist_to_mid_pct < 0.5:
        reasons.append("Precio cerca de la media — sin señal de reversión clara")

    confidence = max(0.0, min(confidence, 1.0))

    indicators = {
        "bb_upper_2.5": round(last_bb_upper, 2),
        "bb_inner_upper": round(last_bb_inner_upper, 2),
        "bb_mid": round(last_bb_mid, 2),
        "bb_inner_lower": round(last_bb_inner_lower, 2),
        "bb_lower_2.5": round(last_bb_lower, 2),
        "rsi_14": round(last_rsi, 2),
        "rsi_7": round(last_rsi7, 2),
        "price": round(last_price, 2),
        "z_score": round(z_score, 2) if bb_width > 0 else None,
        "atr": round(last_atr, 4),
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
        "strategy_type": "mean_reversion",
    }


# ═══════════════════════════════════════════════════════════════
# STRATEGY 5: Breakout
# ═══════════════════════════════════════════════════════════════

@timed
def breakout_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 40:
        return _result("NEUTRAL", 0.0, {}, ["Datos insuficientes (mín 40 velas)"])

    c = df["Close"]
    hi = df["High"]
    lo = df["Low"]
    volume = df["Volume"]

    bb_mid = c.rolling_mean(window_size=20)
    bb_std = c.rolling_std(window_size=20)
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    rsi = _rsi(c, 14)
    atr = _atr(hi, lo, c, 14)
    ema_9 = c.ewm_mean(span=9, adjust=False)
    ema_21 = c.ewm_mean(span=21, adjust=False)

    last_price = _last(c)
    last_high = _last(hi)
    last_low = _last(lo)
    last_bb_upper = _last(bb_upper) if _last(bb_upper) is not None else last_price
    last_bb_lower = _last(bb_lower) if _last(bb_lower) is not None else last_price
    last_bb_mid = _last(bb_mid) if _last(bb_mid) is not None else last_price
    last_ema9 = _last(ema_9) if _last(ema_9) is not None else last_price
    last_ema21 = _last(ema_21) if _last(ema_21) is not None else last_price
    last_atr = _last(atr) if _last(atr) is not None else 0.0
    last_rsi = _last(rsi) if _last(rsi) is not None else 50.0

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # Range detection (consolidation)
    window_range = 20
    if df.height >= window_range:
        recent_high = float(hi[-window_range:].max()) if hi[-window_range:].max() is not None else last_price
        recent_low = float(lo[-window_range:].min()) if lo[-window_range:].min() is not None else last_price
        range_pct = (recent_high - recent_low) / recent_low * 100 if recent_low > 0 else 0
    else:
        range_pct = 0

    is_consolidating = range_pct < 5.0 and range_pct > 0

    # Resistance breakout
    if df.height >= 20:
        resistance_level = float(hi[-20:-1].max()) if len(hi) >= 21 else last_price
        support_level = float(lo[-20:-1].min()) if len(lo) >= 21 else last_price

        if last_price > resistance_level and is_consolidating:
            signal = "BUY"
            confidence += 0.30
            reasons.append(f"Breakout alcista de resistencia ({resistance_level:.2f}) con consolidación previa")
        elif last_price > resistance_level:
            signal = "BUY"
            confidence += 0.20
            reasons.append(f"Breakout alcista de resistencia ({resistance_level:.2f})")
        elif last_price < support_level and is_consolidating:
            signal = "SELL"
            confidence += 0.30
            reasons.append(f"Breakout bajista de soporte ({support_level:.2f}) con consolidación previa")
        elif last_price < support_level:
            signal = "SELL"
            confidence += 0.20
            reasons.append(f"Breakout bajista de soporte ({support_level:.2f})")

    # Volume expansion
    if df.height >= 21:
        avg_vol = float(volume[-20:].mean())
        last_vol = float(volume[-1]) if volume[-1] is not None else 0
        vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1.0

        if vol_ratio > 2.0:
            if signal == "BUY":
                confidence += 0.20
                reasons.append(f"Volumen {vol_ratio:.1f}x el promedio — breakout con convicción")
            elif signal == "SELL":
                confidence += 0.20
                reasons.append(f"Volumen {vol_ratio:.1f}x el promedio — breakdown con convicción")
            else:
                reasons.append(f"Volumen {vol_ratio:.1f}x el promedio — posible breakout inminente")
        elif vol_ratio > 1.5:
            if signal in ("BUY", "SELL"):
                confidence += 0.10
                reasons.append(f"Volumen {vol_ratio:.1f}x el promedio")
            else:
                reasons.append(f"Volumen elevado ({vol_ratio:.1f}x)")

    # Volatility expansion (ATR breakout)
    if df.height >= 20:
        atr_avg = float(atr[-10:].mean()) if len(atr) >= 10 else last_atr
        if atr_avg > 0 and last_atr > atr_avg * 1.4:
            confidence += 0.10
            reasons.append("Expansión de volatilidad — breakout en curso")

    # Price relative to Bollinger (breakout confirmation)
    if last_price > last_bb_upper and last_atr > 0:
        if signal == "BUY":
            confidence += 0.10
            reasons.append("Precio sobre banda superior de Bollinger — breakout fuerte")
    elif last_price < last_bb_lower and last_atr > 0:
        if signal == "SELL":
            confidence += 0.10
            reasons.append("Precio bajo banda inferior de Bollinger — breakdown fuerte")

    # EMA momentum confirmation
    if last_ema9 > last_ema21:
        if signal == "BUY":
            confidence += 0.10
            reasons.append("EMAs confirman tendencia alcista")
    else:
        if signal == "SELL":
            confidence += 0.10
            reasons.append("EMAs confirman tendencia bajista")

    # RSI filter
    if last_rsi > 70 and signal == "BUY":
        reasons.append("RSI sobrecomprado — posible agotamiento del breakout")
    elif last_rsi < 30 and signal == "SELL":
        reasons.append("RSI sobrevendido — posible agotamiento del breakdown")

    confidence = max(0.0, min(confidence, 1.0))

    indicators = {
        "price": round(last_price, 2),
        "range_pct": round(range_pct, 2),
        "atr": round(last_atr, 4) if last_atr and last_atr == last_atr else None,
        "rsi_14": round(last_rsi, 2),
        "bb_upper": round(last_bb_upper, 2),
        "bb_mid": round(last_bb_mid, 2),
        "bb_lower": round(last_bb_lower, 2),
        "ema_9": round(last_ema9, 2),
        "ema_21": round(last_ema21, 2),
        "is_consolidating": is_consolidating,
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
        "strategy_type": "breakout",
    }


# ═══════════════════════════════════════════════════════════════
# STRATEGY 6: Market Structure
# ═══════════════════════════════════════════════════════════════

@timed
def market_structure_signals(df: pl.DataFrame) -> dict[str, Any]:
    if df.height < 100:
        return _result("NEUTRAL", 0.0, {}, ["Datos insuficientes (mín 100 velas)"])

    c = df["Close"]
    hi = df["High"]
    lo = df["Low"]

    ema_9 = c.ewm_mean(span=9, adjust=False)
    ema_21 = c.ewm_mean(span=21, adjust=False)
    sma_50 = c.rolling_mean(window_size=50)
    sma_200 = c.rolling_mean(window_size=200) if df.height >= 200 else None
    rsi = _rsi(c, 14)

    last_price = _last(c)
    last_ema9 = _last(ema_9) if _last(ema_9) is not None else last_price
    last_ema21 = _last(ema_21) if _last(ema_21) is not None else last_price
    last_sma50 = _last(sma_50) if _last(sma_50) is not None else last_price
    last_rsi = _last(rsi) if _last(rsi) is not None else 50.0
    last_sma200 = _last(sma_200) if sma_200 is not None and _last(sma_200) is not None else None

    signal = "NEUTRAL"
    confidence = 0.0
    reasons = []

    highs = hi.to_numpy()
    lows = lo.to_numpy()

    # Swing highs/lows
    swing_highs = []
    swing_lows = []
    lookback = 5
    for i in range(lookback, len(highs) - lookback):
        if all(highs[i] >= highs[i - j] for j in range(1, lookback + 1)) and all(highs[i] >= highs[i + j] for j in range(1, lookback + 1)):
            swing_highs.append((i, highs[i]))
        if all(lows[i] <= lows[i - j] for j in range(1, lookback + 1)) and all(lows[i] <= lows[i + j] for j in range(1, lookback + 1)):
            swing_lows.append((i, lows[i]))

    last_swing_high = swing_highs[-1][1] if swing_highs else None
    last_swing_low = swing_lows[-1][1] if swing_lows else None

    # Trend determination
    if last_swing_high and last_swing_low:
        if len(swing_highs) >= 3 and len(swing_lows) >= 3:
            higher_highs = all(swing_highs[i][1] > swing_highs[i - 1][1] for i in range(-2, 0)) if len(swing_highs) >= 2 else False
            higher_lows = all(swing_lows[i][1] > swing_lows[i - 1][1] for i in range(-2, 0)) if len(swing_lows) >= 2 else False
            lower_highs = all(swing_highs[i][1] < swing_highs[i - 1][1] for i in range(-2, 0)) if len(swing_highs) >= 2 else False
            lower_lows = all(swing_lows[i][1] < swing_lows[i - 1][1] for i in range(-2, 0)) if len(swing_lows) >= 2 else False

            if higher_highs and higher_lows:
                signal = "BUY"
                confidence += 0.25
                reasons.append("Estructura alcista: máximos y mínimos crecientes")
            elif lower_highs and lower_lows:
                signal = "SELL"
                confidence += 0.25
                reasons.append("Estructura bajista: máximos y mínimos decrecientes")
            elif higher_highs and not higher_lows:
                reasons.append("Posible tope de mercado: máximos crecientes pero sin soporte")
            elif lower_lows and not lower_highs:
                reasons.append("Posible piso de mercado: mínimos decrecientes pero sin techo")
            else:
                reasons.append("Mercado lateral — sin estructura direccional clara")
        else:
            reasons.append("Pocos swings para determinar estructura")

    # EMA hierarchy (bullish/bearish alignment)
    if last_ema9 > last_ema21 > last_sma50:
        confidence += 0.15
        reasons.append("Jerarquía EMAs alcista (9 > 21 > 50)")
    elif last_ema9 < last_ema21 < last_sma50:
        confidence -= 0.15
        reasons.append("Jerarquía EMAs bajista (9 < 21 < 50)")

    # Market phase detection
    if last_price > last_sma50:
        if last_sma50 > (sma_50[-2] if len(sma_50) > 1 and sma_50[-2] is not None else last_sma50):
            reasons.append("Fase de expansión alcista (precio > SMA50, SMA50 subiendo)")
        else:
            reasons.append("Fase de consolidación alcista (precio > SMA50, SMA50 plana)")
    else:
        if last_sma50 < (sma_50[-2] if len(sma_50) > 1 and sma_50[-2] is not None else last_sma50):
            reasons.append("Fase de contracción bajista (precio < SMA50, SMA50 cayendo)")
        else:
            reasons.append("Fase de consolidación bajista (precio < SMA50, SMA50 plana)")

    # SMA200 as macro trend filter
    if last_sma200 is not None:
        if last_price > last_sma200:
            confidence += 0.10
            reasons.append(f"Macro-tendencia alcista (precio > SMA200 {last_sma200:.2f})")
        else:
            confidence -= 0.10
            reasons.append(f"Macro-tendencia bajista (precio < SMA200 {last_sma200:.2f})")
    else:
        reasons.append("Sin datos suficientes para SMA200")

    # RSI structure
    if last_rsi > 60:
        confidence += 0.05
        reasons.append(f"RSI en zona alcista ({last_rsi:.1f})")
    elif last_rsi < 40:
        confidence -= 0.05
        reasons.append(f"RSI en zona bajista ({last_rsi:.1f})")

    # Distance to nearest swing
    if last_swing_high and last_swing_low:
        dist_to_high = (last_swing_high - last_price) / last_price * 100
        dist_to_low = (last_price - last_swing_low) / last_price * 100
        if dist_to_high < 1.0:
            reasons.append(f"Cerca del último máximo ({last_swing_high:.2f}) — posible resistencia")
        if dist_to_low < 1.0:
            reasons.append(f"Cerca del último mínimo ({last_swing_low:.2f}) — posible soporte")

    confidence = max(0.0, min(confidence, 1.0))

    indicators = {
        "price": round(last_price, 2),
        "ema_9": round(last_ema9, 2),
        "ema_21": round(last_ema21, 2),
        "sma_50": round(last_sma50, 2),
        "sma_200": round(last_sma200, 2) if last_sma200 else None,
        "rsi_14": round(last_rsi, 2),
        "last_swing_high": round(last_swing_high, 2) if last_swing_high else None,
        "last_swing_low": round(last_swing_low, 2) if last_swing_low else None,
        "swing_highs_count": len(swing_highs),
        "swing_lows_count": len(swing_lows),
    }

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "reasons": reasons,
        "strategy_type": "market_structure",
    }


# ═══════════════════════════════════════════════════════════════
# STRATEGY REGISTRY
# ═══════════════════════════════════════════════════════════════

STRATEGY_MAP = {
    "scalping": scalping_signals,
    "swing": swing_signals,
    "momentum": momentum_signals,
    "mean_reversion": mean_reversion_signals,
    "breakout": breakout_signals,
    "market_structure": market_structure_signals,
}

STRATEGY_DESCRIPTIONS = {
    "scalping": "Compra/venta rápidas en minutos. Usa medias móviles 9/21, RSI y Bandas de Bollinger. Ideal para movimientos pequeños e intradía.",
    "swing": "Comprar y mantener días o semanas. Usa MACD, medias 50/200 y soporte/resistencia. Para seguir tendencias de mediano plazo.",
    "momentum": "Detecta acciones que suben fuerte con volumen creciente. Compra cuando hay impulso alcista claro y la tendencia es sólida.",
    "mean_reversion": "Compra cuando el precio está muy por debajo de lo normal, vende cuando está muy arriba. Asume que todo vuelve a su media.",
    "breakout": "Detecta cuando el precio rompe un techo o piso importante con fuerza. Compra en rupturas al alza, vende en rupturas a la baja.",
    "market_structure": "Analiza máximos y mínimos para determinar si el mercado está en tendencia alcista, bajista o lateral. Da contexto general.",
}

STRATEGY_MIN_PERIODS = {
    "scalping": 26,
    "swing": 200,
    "momentum": 50,
    "mean_reversion": 30,
    "breakout": 40,
    "market_structure": 100,
}


def run_strategy(df: pl.DataFrame, strategy: str = "scalping") -> dict[str, Any]:
    func = STRATEGY_MAP.get(strategy)
    if func is None:
        raise ValueError(f"Estrategia '{strategy}' no reconocida. Disponibles: {list(STRATEGY_MAP.keys())}")
    result = func(df)
    result["strategy_type"] = strategy
    return _clean_nans(result)


# ═══════════════════════════════════════════════════════════════
# CHART DATA
# ═══════════════════════════════════════════════════════════════

def compute_chart_data(df: pl.DataFrame) -> dict:
    if df.height == 0:
        return {"timestamp": [], "close": [], "ema_9": [], "ema_21": [],
                "bb_upper": [], "bb_mid": [], "bb_lower": [], "rsi_14": [],
                "macd": [], "macd_signal": [], "macd_histogram": [],
                "volume": [], "sma_50": [], "sma_200": []}

    c = df["Close"]
    timestamps = df.get_column("timestamp").to_list() if "timestamp" in df.columns else []

    valid_mask = [v is not None for v in c]
    close_vals = [round(float(v), 2) for v in c if v is not None]
    if len(close_vals) != len(timestamps):
        timestamps = [t for t, keep in zip(timestamps, valid_mask) if keep]
    timestamps = [t.isoformat() if hasattr(t, 'isoformat') else str(t) for t in timestamps]

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
    macd_signal_line = macd_line.ewm_mean(span=9, adjust=False)
    macd_hist = macd_line - macd_signal_line

    sma_50 = c.rolling_mean(window_size=50) if df.height >= 50 else pl.Series([None] * df.height)
    sma_200 = c.rolling_mean(window_size=200) if df.height >= 200 else pl.Series([None] * df.height)

    volume_vals = [round(float(v), 0) if v is not None else None for v in df["Volume"]] if "Volume" in df.columns else []

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
        "macd_signal": _to_series(macd_signal_line),
        "macd_histogram": _to_series(macd_hist),
        "volume": volume_vals,
        "sma_50": _to_series(sma_50),
        "sma_200": _to_series(sma_200),
    }
