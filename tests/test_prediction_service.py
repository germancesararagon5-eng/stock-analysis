from app.services.prediction_service import (
    get_prediction_stats,
    get_predictions,
    get_trading_summary,
    resolve_predictions,
    store_prediction,
)


def test_store_and_get_prediction():
    pred_id = store_prediction(
        ticker="TEST", signal="BUY", confidence=0.8,
        strategy="scalping", interval="5m", periods=100,
        price=150.0, reasons=["test"], indicators={"rsi": 30},
    )
    assert isinstance(pred_id, int) and pred_id > 0
    predictions = get_predictions(ticker="TEST")
    assert len(predictions) >= 1
    assert predictions[0]["ticker"] == "TEST"


def test_get_prediction_stats():
    store_prediction(
        ticker="STATS", signal="SELL", confidence=0.6,
        strategy="scalping", interval="1d", periods=100,
        reasons=[], indicators=None,
    )
    stats = get_prediction_stats(ticker="STATS")
    assert stats["total"] >= 1
    assert all(k in stats for k in ("pending", "resolved", "correct", "total_pnl", "winning_trades", "losing_trades"))


def test_get_prediction_stats_all():
    stats = get_prediction_stats()
    assert "total" in stats


def test_resolve_predictions():
    store_prediction(
        ticker="RESOLVE", signal="BUY", confidence=0.9,
        strategy="scalping", interval="5m", periods=100,
        price=100.0, reasons=[], indicators=None,
    )
    resolved = resolve_predictions(count=5)
    assert isinstance(resolved, int)


def test_resolve_predictions_zero():
    resolved = resolve_predictions(count=0)
    assert isinstance(resolved, int)


def test_get_predictions_no_ticker():
    preds = get_predictions()
    assert isinstance(preds, list)
    if preds:
        assert "pnl" in preds[0]
        assert "pnl_pct" in preds[0]


def test_get_predictions_with_offset():
    preds = get_predictions(limit=10, offset=0)
    assert isinstance(preds, list)


def test_store_prediction_fallback_values():
    pred_id = store_prediction(
        ticker="FALLBACK", signal="NEUTRAL", confidence=0.0,
        strategy="momentum", interval="1h", periods=50,
    )
    assert isinstance(pred_id, int) and pred_id > 0
    preds = get_predictions(ticker="FALLBACK")
    assert len(preds) >= 1
    assert preds[0]["signal"] == "NEUTRAL"
    assert preds[0]["strategy"] == "momentum"


def test_store_prediction_all_strategies():
    for s in ("scalping", "swing", "momentum", "mean_reversion", "breakout", "market_structure"):
        pred_id = store_prediction(
            ticker="STRAT", signal="BUY", confidence=0.7,
            strategy=s, interval="1d", periods=100,
            price=200.0,
        )
        assert pred_id > 0


def test_get_trading_summary_structure():
    summary = get_trading_summary()
    assert isinstance(summary, dict)
    for k in ("total_trades", "wins", "losses", "win_rate_pct", "total_pnl", "profit_factor", "trades"):
        assert k in summary


def test_get_trading_summary_filtered():
    store_prediction(
        ticker="SUMMARY", signal="BUY", confidence=0.7,
        strategy="scalping", interval="1d", periods=100,
        price=150.0,
    )
    summary = get_trading_summary(ticker="SUMMARY")
    assert "trades" in summary


def test_resolve_with_threshold():
    store_prediction(
        ticker="THRESH", signal="BUY", confidence=0.8,
        strategy="scalping", interval="1d", periods=100,
        price=100.0,
    )
    resolved = resolve_predictions(count=5, threshold_pct=1.0)
    assert isinstance(resolved, int)
