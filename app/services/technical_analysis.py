import logging

logger = logging.getLogger(__name__)


def analyze_series(series: dict, ticker: str) -> dict:
    close = series.get("close") or []
    ema9 = series.get("ema_9") or []
    ema21 = series.get("ema_21") or []
    bb_upper = series.get("bb_upper") or []
    bb_lower = series.get("bb_lower") or []
    bb_mid = series.get("bb_mid") or []
    rsi = series.get("rsi_14") or []
    macd = series.get("macd") or []
    macd_signal = series.get("macd_signal") or []
    macd_hist = series.get("macd_histogram") or []

    signals = []
    reasons = []
    score = 0

    # ── Trend (EMA alignment) ──
    last_ema9 = _last(ema9)
    last_ema21 = _last(ema21)
    if last_ema9 is not None and last_ema21 is not None:
        if last_ema9 > last_ema21:
            signals.append("bullish")
            score += 1
            reasons.append(f"EMA 9 ({last_ema9:.2f}) sobre EMA 21 ({last_ema21:.2f}) = tendencia alcista")
        else:
            signals.append("bearish")
            score -= 1
            reasons.append(f"EMA 9 ({last_ema9:.2f}) bajo EMA 21 ({last_ema21:.2f}) = tendencia bajista")

    # ── EMA slope (direction) ──
    if len(ema9) >= 3:
        d1 = ema9[-1] - ema9[-2] if ema9[-1] is not None and ema9[-2] is not None else 0
        d2 = ema9[-2] - ema9[-3] if ema9[-2] is not None and ema9[-3] is not None else 0
        if d1 > 0 and d2 > 0:
            score += 1
            reasons.append("EMA 9 en pendiente positiva acelerando")
        elif d1 < 0 and d2 < 0:
            score -= 1
            reasons.append("EMA 9 en pendiente negativa acelerando")

    # ── RSI ──
    last_rsi = _last(rsi)
    if last_rsi is not None:
        if last_rsi > 70:
            signals.append("overbought")
            score -= 1
            reasons.append(f"RSI en {last_rsi:.1f} — sobrecompra, posible reversión bajista")
        elif last_rsi < 30:
            signals.append("oversold")
            score += 1
            reasons.append(f"RSI en {last_rsi:.1f} — sobreventa, posible rebote alcista")
        elif last_rsi > 60:
            signals.append("bullish")
            score += 1
            reasons.append(f"RSI en {last_rsi:.1f} — momentum alcista")
        elif last_rsi < 40:
            signals.append("bearish")
            score -= 1
            reasons.append(f"RSI en {last_rsi:.1f} — momentum bajista")
        else:
            reasons.append(f"RSI en {last_rsi:.1f} — neutral")

        # RSI divergence check
        if len(rsi) >= 5 and len(close) >= 5:
            rsi_trend = rsi[-1] - rsi[-5] if rsi[-1] is not None and rsi[-5] is not None else 0
            price_trend = close[-1] - close[-5] if close[-1] is not None and close[-5] is not None else 0
            if rsi_trend > 5 and price_trend < 0:
                score += 1
                reasons.append("Divergencia alcista: RSI sube mientras precio baja")
            elif rsi_trend < -5 and price_trend > 0:
                score -= 1
                reasons.append("Divergencia bajista: RSI baja mientras precio sube")

    # ── Bollinger Bands ──
    last_close = _last(close)
    last_bb_upper = _last(bb_upper)
    last_bb_lower = _last(bb_lower)
    last_bb_mid = _last(bb_mid)
    if all(v is not None for v in [last_close, last_bb_upper, last_bb_lower, last_bb_mid]):
        bb_width = last_bb_upper - last_bb_lower
        if bb_width > 0:
            bb_pct = (last_close - last_bb_lower) / bb_width
            if bb_pct > 0.95:
                score -= 1
                reasons.append(f"Precio tocando banda superior de Bollinger ({bb_pct:.0%}) — resistencia")
            elif bb_pct < 0.05:
                score += 1
                reasons.append(f"Precio tocando banda inferior de Bollinger ({bb_pct:.0%}) — soporte")
            else:
                reasons.append(f"Precio en {bb_pct:.0%} del rango de Bollinger")

        # Squeeze detection
        bb_range_5 = _bb_range(bb_upper, bb_lower, -5)
        bb_range_1 = _bb_range(bb_upper, bb_lower, -1)
        if bb_range_5 and bb_range_1 and bb_range_1 < bb_range_5 * 0.7:
            reasons.append("Bandas de Bollinger contrayéndose — posible squeeze/breakout pronto")

    # ── MACD ──
    last_macd = _last(macd)
    last_signal = _last(macd_signal)
    last_hist = _last(macd_hist)
    if last_macd is not None and last_signal is not None:
        if last_macd > last_signal:
            signals.append("bullish")
            score += 1
            reasons.append("MACD sobre línea de señal — bullish")
        else:
            signals.append("bearish")
            score -= 1
            reasons.append("MACD bajo línea de señal — bearish")

        if last_hist is not None:
            if last_hist > 0:
                reasons.append(f"Histograma MACD positivo ({last_hist:.2f})")
            else:
                reasons.append(f"Histograma MACD negativo ({last_hist:.2f})")

    # ── MACD crossover detection ──
    if len(macd) >= 3 and len(macd_signal) >= 3:
        prev_diff = (macd[-2] or 0) - (macd_signal[-2] or 0)
        curr_diff = (macd[-1] or 0) - (macd_signal[-1] or 0)
        if prev_diff < 0 and curr_diff > 0:
            score += 2
            reasons.append("Cruce alcista MACD (cross above signal)")
        elif prev_diff > 0 and curr_diff < 0:
            score -= 2
            reasons.append("Cruce bajista MACD (cross below signal)")

    # ── Overall verdict ──
    if score >= 3:
        verdict = "BUY"
        confidence = min(100, 50 + score * 10)
    elif score <= -3:
        verdict = "SELL"
        confidence = min(100, 50 + abs(score) * 10)
    elif score >= 1:
        verdict = "ACCUMULATE"
        confidence = 30 + score * 10
    elif score <= -1:
        verdict = "REDUCE"
        confidence = 30 + abs(score) * 10
    else:
        verdict = "NEUTRAL"
        confidence = 40 + abs(score) * 15

    # Unique signal types
    signal_types = list(set(signals)) if signals else ["neutral"]

    return {
        "ticker": ticker,
        "verdict": verdict,
        "confidence": min(confidence, 100),
        "score": score,
        "signals": signal_types,
        "reasons": reasons,
        "indicators": {
            "rsi": last_rsi,
            "ema9": last_ema9,
            "ema21": last_ema21,
            "bb_position_pct": (
                round((_last(close) - _last(bb_lower)) / (_last(bb_upper) - _last(bb_lower)) * 100, 1)
                if all(v is not None for v in [_last(close), _last(bb_upper), _last(bb_lower)])
                and (_last(bb_upper) - _last(bb_lower)) > 0
                else None
            ),
            "macd": last_macd,
            "macd_signal": last_signal,
            "macd_histogram": last_hist,
        },
    }


def _last(arr):
    return arr[-1] if arr and arr[-1] is not None else None


def _bb_range(upper, lower, offset):
    u = upper[offset] if len(upper) > abs(offset) and upper[offset] is not None else None
    lo = lower[offset] if len(lower) > abs(offset) and lower[offset] is not None else None
    if u is not None and lo is not None:
        return u - lo
    return None
