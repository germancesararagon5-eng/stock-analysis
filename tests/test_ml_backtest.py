import pytest
from unittest.mock import patch

from app.models import AnalysisResult
from app.services import ml_service


@pytest.fixture(autouse=True)
def reset_model():
    ml_service._MODEL = None
    ml_service._MODEL_META = {}


def _make_result(ticker="AAPL", outcome="WIN", strategy="scalping", confidence=0.7):
    return AnalysisResult(
        ticker=ticker,
        strategy=strategy,
        interval="1d",
        periods=100,
        signal="BUY",
        confidence=confidence,
        price=150.0,
        rsi_14=35.0,
        ema_9=148.0,
        ema_21=147.0,
        ema_50=145.0,
        ema_200=140.0,
        bb_upper=155.0,
        bb_lower=145.0,
        macd=1.5,
        macd_signal=1.0,
        macd_histogram=0.5,
        volume=1000000,
        atr=2.5,
        support_1=142.0,
        resistance_1=158.0,
        outcome=outcome,
        price_change_pct=2.5,
    )


def test_get_model_status_not_trained(client):
    resp = client.get("/api/ml/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trained"] is False
    assert data["samples"] == 0


@patch("app.services.ml_service.SessionLocal")
def test_train_model_insufficient_data(mock_sl, client):
    mock_session = mock_sl.return_value
    mock_session.query.return_value.filter.return_value.all.return_value = []
    resp = client.post("/api/ml/train")
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert "necesitan al menos 10 muestras" in data["error"]


@patch("app.services.ml_service.SessionLocal")
def test_train_model_success(mock_sl, client):
    mock_session = mock_sl.return_value
    results = [_make_result(outcome="WIN") for _ in range(8)] + [_make_result(outcome="LOSS") for _ in range(8)]
    mock_session.query.return_value.filter.return_value.all.return_value = results
    resp = client.post("/api/ml/train")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trained"] is True
    assert data["samples"] == 16
    assert data["accuracy"] > 0
    assert len(data["feature_importance"]) == 15


@patch("app.services.ml_service.SessionLocal")
@patch("app.services.analysis_service.run_analysis")
def test_backtest_without_trained_model(mock_run, mock_sl, client):
    mock_session = mock_sl.return_value
    mock_session.query.return_value.filter.return_value.all.return_value = []
    resp = client.get("/api/ml/backtest?ticker=AAPL&interval=1d&periods=100")
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert "no entrenado" in data["error"]


@patch("app.services.ml_service.SessionLocal")
@patch("app.services.analysis_service.run_analysis")
def test_backtest_with_model(mock_run, mock_sl, client):
    mock_session = mock_sl.return_value
    results = [_make_result(outcome="WIN") for _ in range(8)] + [_make_result(outcome="LOSS") for _ in range(8)]
    mock_session.query.return_value.filter.return_value.all.return_value = results

    client.post("/api/ml/train")

    def fake_analysis(ticker, strategy, interval, periods, store_prediction=False, notify=False):
        return {
            "ticker": ticker,
            "strategy": strategy,
            "interval": interval,
            "signal": "BUY" if strategy != "market_structure" else "NEUTRAL",
            "confidence": 0.7,
            "indicators": {
                "price": 150.0,
                "rsi_14": 35.0,
                "ema_9": 148.0,
                "ema_21": 147.0,
                "ema_50": 145.0,
                "ema_200": 140.0,
                "bb_upper": 155.0,
                "bb_lower": 145.0,
                "macd": 1.5,
                "macd_signal": 1.0,
                "macd_histogram": 0.5,
                "volume": 1000000,
                "atr": 2.5,
                "support_1": 142.0,
                "resistance_1": 158.0,
            },
            "reasons": ["test reason"],
            "timestamp": "2024-01-01T00:00:00Z",
        }
    mock_run.side_effect = fake_analysis

    resp = client.get("/api/ml/backtest?ticker=AAPL&interval=1d&periods=100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert len(data["results"]) == 6
    assert data["summary"]["total_strategies"] == 6
    assert data["summary"]["agreement_rate"] >= 0


def test_backtest_endpoint_validation(client):
    resp = client.get("/api/ml/backtest")
    assert resp.status_code == 422
