from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture
def mock_broker():
    broker = MagicMock()
    broker.config.name = "yahoo_finance"
    broker.get_realtime_data.return_value = {"price": 150.0}
    broker.execute_order.return_value = {"status": "filled", "message": "OK"}
    with patch("app.routers.analysis_router.broker_manager.get_broker", return_value=broker):
        yield broker


@pytest.fixture
def mock_service_data():
    n = 100
    df = pd.DataFrame({
        "Close": [100 + (i % 10) for i in range(n)],
        "High": [105 + (i % 10) for i in range(n)],
        "Low": [95 + (i % 10) for i in range(n)],
        "Open": [100 + (i % 10) for i in range(n)],
        "Volume": [1000000] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="D"))
    with (
        patch("app.services.analysis_service.get_historical_data", return_value=df),
        patch("app.routers.analysis_router.get_historical_data", return_value=df),
    ):
        yield df


def test_analyze(client, mock_service_data):
    resp = client.post("/api/analysis/analyze", json={
        "ticker": "AAPL",
        "strategy": "scalping",
        "interval": "1d",
        "periods": 100,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert data["strategy"] == "scalping"
    assert data["signal"] in ("BUY", "SELL", "NEUTRAL")


def test_analyze_swing(client, mock_service_data):
    resp = client.post("/api/analysis/analyze", json={
        "ticker": "MSFT",
        "strategy": "swing",
        "interval": "1d",
        "periods": 200,
    })
    assert resp.status_code == 200


def test_get_chart(client, mock_service_data):
    resp = client.get("/api/analysis/chart/AAPL?strategy=scalping&interval=1d&periods=60")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert "series" in data
    assert "timestamp" in data["series"]


def test_get_data(client, mock_broker):
    resp = client.get("/api/analysis/data/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert data["price"] == 150.0


def test_place_order(client, mock_broker):
    resp = client.post("/api/analysis/order", json={
        "ticker": "AAPL",
        "side": "BUY",
        "quantity": 10,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "filled"
    assert data["side"] == "BUY"


def test_technical_analysis(client, mock_service_data):
    resp = client.post("/api/analysis/technical-analysis?ticker=AAPL&strategy=scalping&interval=1d&periods=100")
    assert resp.status_code == 200
