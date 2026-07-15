import pytest
from app.services.technical_analysis import analyze_series, _last, _bb_range


def make_series(**overrides):
    base = {
        "close": [100, 101, 102, 103, 104],
        "ema_9": [100, 101, 102, 103, 104],
        "ema_21": [99, 100, 100, 101, 101],
        "bb_upper": [110, 111, 112, 113, 114],
        "bb_lower": [90, 91, 92, 93, 94],
        "bb_mid": [100, 101, 102, 103, 104],
        "rsi_14": [50, 52, 54, 56, 58],
        "macd": [0.5, 0.6, 0.7, 0.8, 0.9],
        "macd_signal": [0.4, 0.5, 0.6, 0.7, 0.8],
        "macd_histogram": [0.1, 0.1, 0.1, 0.1, 0.1],
    }
    base.update(overrides)
    return base


# ── _last helper tests ──

class TestLast:
    def test_empty_list(self):
        assert _last([]) is None

    def test_none_list(self):
        assert _last(None) is None

    def test_none_last(self):
        assert _last([1, 2, None]) is None

    def test_normal(self):
        assert _last([1, 2, 3]) == 3


# ── _bb_range helper tests ──

class TestBBRange:
    def test_normal(self):
        assert _bb_range([10, 20, 30], [5, 10, 15], -1) == 15

    def test_insufficient_data(self):
        assert _bb_range([1], [0], -5) is None

    def test_none_in_data(self):
        assert _bb_range([10, None, 30], [5, 10, 15], -2) is None

    def test_none_upper(self):
        assert _bb_range([None], [5], -1) is None


# ── analyze_series tests ──

class TestAnalyzeSeriesEmpty:
    def test_empty_series(self):
        result = analyze_series({}, "TEST")
        assert result["ticker"] == "TEST"
        assert result["verdict"] == "NEUTRAL"
        assert result["confidence"] >= 0

    def test_missing_keys(self):
        result = analyze_series({"close": [100, 101]}, "TEST")
        assert result["ticker"] == "TEST"


class TestAnalyzeSeriesTrendEMA:
    def test_bullish_ema(self):
        s = make_series(ema_9=[99, 100, 101, 102, 103], ema_21=[95, 96, 97, 98, 99])
        result = analyze_series(s, "TEST")
        assert "bullish" in result["signals"]
        assert any("sobre EMA 21" in r for r in result["reasons"])

    def test_bearish_ema(self):
        s = make_series(ema_9=[101, 100, 99, 98, 97], ema_21=[102, 102, 101, 101, 100])
        result = analyze_series(s, "TEST")
        assert "bearish" in result["signals"]
        assert any("bajo EMA 21" in r for r in result["reasons"])

    def test_ema_slope_positive(self):
        s = make_series(ema_9=[90, 95, 100, 105, 110])
        result = analyze_series(s, "TEST")
        assert any("pendiente positiva" in r for r in result["reasons"])

    def test_ema_slope_negative(self):
        s = make_series(ema_9=[110, 105, 100, 95, 90])
        result = analyze_series(s, "TEST")
        assert any("pendiente negativa" in r for r in result["reasons"])


class TestAnalyzeSeriesRSI:
    def test_rsi_overbought(self):
        s = make_series(rsi_14=[70, 72, 74, 76, 78])
        result = analyze_series(s, "TEST")
        assert "overbought" in result["signals"]
        assert any("sobrecompra" in r for r in result["reasons"])

    def test_rsi_oversold(self):
        s = make_series(rsi_14=[30, 28, 26, 24, 22])
        result = analyze_series(s, "TEST")
        assert "oversold" in result["signals"]
        assert any("sobreventa" in r for r in result["reasons"])

    def test_rsi_bullish_momentum(self):
        s = make_series(rsi_14=[55, 58, 60, 62, 65])
        result = analyze_series(s, "TEST")
        assert "bullish" in result["signals"]
        assert any("momentum alcista" in r for r in result["reasons"])

    def test_rsi_bearish_momentum(self):
        s = make_series(rsi_14=[45, 43, 41, 39, 37])
        result = analyze_series(s, "TEST")
        assert "bearish" in result["signals"]
        assert any("momentum bajista" in r for r in result["reasons"])

    def test_rsi_neutral(self):
        s = make_series(rsi_14=[45, 47, 49, 51, 53])
        result = analyze_series(s, "TEST")
        assert any("neutral" in r for r in result["reasons"])

    def test_bullish_divergence(self):
        s = make_series(
            rsi_14=[40, 42, 44, 46, 48],
            close=[105, 104, 103, 102, 101],
        )
        result = analyze_series(s, "TEST")
        assert any("Divergencia alcista" in r for r in result["reasons"])

    def test_bearish_divergence(self):
        s = make_series(
            rsi_14=[60, 58, 56, 54, 52],
            close=[100, 101, 102, 103, 104],
        )
        result = analyze_series(s, "TEST")
        assert any("Divergencia bajista" in r for r in result["reasons"])


class TestAnalyzeSeriesBollinger:
    def test_touching_upper(self):
        s = make_series(close=[113.5, 113.8, 114.0, 113.9, 113.95])
        result = analyze_series(s, "TEST")
        assert any("banda superior" in r for r in result["reasons"])

    def test_touching_lower(self):
        s = make_series(close=[90.5, 90.3, 90.1, 90.2, 90.05])
        result = analyze_series(s, "TEST")
        assert any("banda inferior" in r for r in result["reasons"])

    def test_mid_range(self):
        s = make_series(close=[100, 101, 102, 103, 104])
        result = analyze_series(s, "TEST")
        assert any("rango de Bollinger" in r for r in result["reasons"])

    def test_bb_squeeze_detected(self):
        s = make_series(
            bb_upper=[130, 125, 120, 115, 110, 105],
            bb_lower=[70, 75, 80, 85, 90, 95],
        )
        result = analyze_series(s, "TEST")
        assert any("squeeze" in r.lower() for r in result["reasons"])

    def test_bb_all_none(self):
        s = make_series(close=[None], bb_upper=[None], bb_lower=[None], bb_mid=[None])
        result = analyze_series(s, "TEST")
        assert result["ticker"] == "TEST"


class TestAnalyzeSeriesMACD:
    def test_macd_over_signal(self):
        s = make_series(macd=[0.5, 0.6, 0.7, 0.8, 0.9], macd_signal=[0.4, 0.5, 0.6, 0.7, 0.8])
        result = analyze_series(s, "TEST")
        assert "bullish" in result["signals"]
        assert any("MACD sobre" in r for r in result["reasons"])

    def test_macd_under_signal(self):
        s = make_series(macd=[0.8, 0.7, 0.6, 0.5, 0.4], macd_signal=[0.9, 0.8, 0.7, 0.6, 0.5])
        result = analyze_series(s, "TEST")
        assert "bearish" in result["signals"]
        assert any("MACD bajo" in r for r in result["reasons"])

    def test_macd_histogram_positive(self):
        s = make_series(macd_histogram=[0.1, 0.2, 0.3, 0.4, 0.5])
        result = analyze_series(s, "TEST")
        assert any("positivo" in r for r in result["reasons"])

    def test_macd_histogram_negative(self):
        s = make_series(macd_histogram=[-0.1, -0.2, -0.3, -0.4, -0.5])
        result = analyze_series(s, "TEST")
        assert any("negativo" in r for r in result["reasons"])

    def test_macd_bullish_crossover(self):
        s = make_series(
            macd=[0.3, 0.35, 0.4, 0.45, 0.9],
            macd_signal=[0.5, 0.5, 0.5, 0.5, 0.5],
        )
        result = analyze_series(s, "TEST")
        assert any("Cruce alcista" in r for r in result["reasons"])

    def test_macd_bearish_crossover(self):
        s = make_series(
            macd=[0.9, 0.8, 0.7, 0.6, 0.3],
            macd_signal=[0.5, 0.5, 0.5, 0.5, 0.5],
        )
        result = analyze_series(s, "TEST")
        assert any("Cruce bajista" in r for r in result["reasons"])


class TestAnalyzeSeriesVerdict:
    def test_buy_verdict(self):
        s = make_series(
            ema_9=[100, 102, 104, 106, 108],
            ema_21=[90, 92, 94, 96, 98],
            rsi_14=[50, 52, 54, 56, 58],
            macd=[1, 1.5, 2, 2.5, 3],
            macd_signal=[0.5, 0.8, 1, 1.2, 1.5],
        )
        result = analyze_series(s, "TEST")
        assert result["verdict"] == "BUY"
        assert result["confidence"] >= 50

    def test_sell_verdict(self):
        s = make_series(
            ema_9=[108, 106, 104, 102, 100],
            ema_21=[110, 109, 108, 107, 106],
            rsi_14=[80, 78, 76, 74, 72],
            macd=[3, 2.5, 2, 1.5, 1],
            macd_signal=[1.5, 1.5, 1.5, 1.5, 1.5],
        )
        result = analyze_series(s, "TEST")
        assert result["verdict"] == "SELL"

    def test_accumulate_verdict(self):
        s = make_series(
            ema_9=[100, 101, 102, 103, 104],
            ema_21=[99, 100, 100, 101, 102],
            rsi_14=[50, 51, 52, 53, 54],
            macd=[0.5, 0.5, 0.5, 0.5, 0.5],
            macd_signal=[0.5, 0.5, 0.5, 0.5, 0.5],
        )
        result = analyze_series(s, "TEST")
        assert result["verdict"] == "ACCUMULATE"

    def test_reduce_verdict(self):
        s = make_series(
            ema_9=[104, 103, 102, 101, 100],
            ema_21=[105, 104, 104, 103, 102],
            rsi_14=[50, 48, 46, 44, 42],
        )
        result = analyze_series(s, "TEST")
        assert result["verdict"] == "REDUCE"

    def test_neutral_verdict(self):
        s = make_series(
            ema_9=[102, 102, 102, 102, 102],
            ema_21=[102, 102, 102, 102, 102],
            rsi_14=[49, 50, 51, 50, 49],
        )
        result = analyze_series(s, "TEST")
        assert result["verdict"] == "NEUTRAL"

    def test_indicators_in_output(self):
        s = make_series()
        result = analyze_series(s, "TEST")
        ind = result["indicators"]
        assert ind["rsi"] is not None
        assert ind["ema9"] is not None
        assert ind["ema21"] is not None
        assert ind["bb_position_pct"] is not None
        assert ind["macd"] is not None


class TestAnalyzeSeriesEdgeCases:
    def test_single_element_arrays(self):
        s = {
            "close": [100],
            "ema_9": [100],
            "ema_21": [100],
            "bb_upper": [110],
            "bb_lower": [90],
            "bb_mid": [100],
            "rsi_14": [50],
            "macd": [0.5],
            "macd_signal": [0.4],
            "macd_histogram": [0.1],
        }
        result = analyze_series(s, "TEST")
        assert result["ticker"] == "TEST"

    def test_none_values_in_arrays(self):
        s = make_series(close=[None, None, None, None, None])
        result = analyze_series(s, "TEST")
        assert result["ticker"] == "TEST"

    def test_mixed_none_values(self):
        s = make_series(
            ema_9=[100, None, 102, None, 104],
            ema_21=[99, None, 101, None, 103],
        )
        result = analyze_series(s, "TEST")
        assert result["ticker"] == "TEST"
