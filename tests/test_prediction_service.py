from app.services.prediction_service import (
    get_prediction_stats,
    get_predictions,
    resolve_predictions,
    store_prediction,
)


def test_store_and_get_prediction():
    pred_id = store_prediction(
        ticker="TEST",
        signal="BUY",
        confidence=0.8,
        strategy="scalping",
        interval="5m",
        periods=100,
        price=150.0,
        reasons=["test reason"],
        indicators={"rsi": 30},
    )
    assert isinstance(pred_id, int)
    assert pred_id > 0

    predictions = get_predictions(ticker="TEST")
    assert len(predictions) >= 1
    assert predictions[0]["ticker"] == "TEST"


def test_get_prediction_stats():
    store_prediction(
        ticker="STATS",
        signal="SELL",
        confidence=0.6,
        strategy="scalping",
        interval="1d",
        periods=100,
        reasons=[],
        indicators=None,
    )
    stats = get_prediction_stats(ticker="STATS")
    assert stats["total"] >= 1
    assert "pending" in stats
    assert "resolved" in stats
    assert "correct" in stats


def test_resolve_predictions():
    store_prediction(
        ticker="RESOLVE",
        signal="BUY",
        confidence=0.9,
        strategy="scalping",
        interval="5m",
        periods=100,
        price=100.0,
        reasons=[],
        indicators=None,
    )
    resolved = resolve_predictions(count=5)
    assert isinstance(resolved, int)
