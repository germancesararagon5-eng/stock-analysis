from unittest.mock import MagicMock, patch

import polars as pl
import pytest
from app.routers.analysis_router import POPULAR_TICKERS


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
    df = pl.DataFrame({
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(n)],
        "Close": [100 + (i % 10) for i in range(n)],
        "High": [105 + (i % 10) for i in range(n)],
        "Low": [95 + (i % 10) for i in range(n)],
        "Open": [100 + (i % 10) for i in range(n)],
        "Volume": [1000000] * n,
    })
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


def test_top_ranking(client, mock_service_data):
    resp = client.get("/api/analysis/top-ranking?strategy=scalping&interval=1d&periods=100&tickers=AAPL,MSFT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["strategy"] == "scalping"
    assert data["interval"] == "1d"
    assert isinstance(data["rankings"], list)
    if data["rankings"]:
        assert "ticker" in data["rankings"][0]
        assert "signal" in data["rankings"][0]
        assert "confidence" in data["rankings"][0]
        assert data["rankings"][0]["confidence"] >= data["rankings"][-1]["confidence"]


def test_top_ranking_all_tickers(client, mock_service_data):
    resp = client.get(f"/api/analysis/top-ranking?strategy=scalping&interval=1d&periods=100&tickers={','.join(POPULAR_TICKERS[:10])}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["rankings"]) <= 10


def test_top_ranking_swing(client, mock_service_data):
    resp = client.get("/api/analysis/top-ranking?strategy=swing&interval=1d&periods=200&tickers=AAPL,MSFT,TSLA")
    assert resp.status_code == 200


def test_compare_strategies(client, mock_service_data):
    resp = client.get("/api/analysis/compare-strategies?ticker=AAPL&interval=1d&periods=100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert "results" in data
    for sname, sdata in data["results"].items():
        assert "signal" in sdata
        assert "confidence" in sdata


def test_list_strategies(client):
    resp = client.get("/api/analysis/strategies")
    assert resp.status_code == 200
    data = resp.json()
    assert "strategies" in data
    names = [s["name"] for s in data["strategies"]]
    assert "scalping" in names
    assert "swing" in names
    assert "momentum" in names
    assert "mean_reversion" in names
    assert "breakout" in names
    assert "market_structure" in names


def test_top_ranking_partial_failures(client, mock_service_data):
    """Tick with error excluded; good tickers still present."""
    from unittest.mock import patch as _patch

    with _patch("app.routers.analysis_router.run_analysis") as mock_ra:
        def _side(ticker, strategy="scalping", interval="1d", periods=100):
            if ticker == "FAIL":
                raise RuntimeError("broker error")
            return {
                "ticker": ticker,
                "signal": "BUY",
                "confidence": 0.8,
                "reasons": ["test"],
                "indicators": {"price": 150.0},
                "strategy": strategy,
                "interval": interval,
                "timestamp": "2024-01-01T00:00:00",
            }
        mock_ra.side_effect = _side
        resp = client.get("/api/analysis/top-ranking?tickers=AAPL,FAIL,MSFT")
    assert resp.status_code == 200
    data = resp.json()
    tickers = [r["ticker"] for r in data["rankings"]]
    assert "FAIL" not in tickers
    assert set(tickers) == {"AAPL", "MSFT"}


def test_top_ranking_neutral_filter(client, mock_service_data):
    """NEUTRAL + 0 confidence ticker excluded from results."""
    from unittest.mock import patch as _patch

    with _patch("app.routers.analysis_router.run_analysis") as mock_ra:
        def _side(ticker, strategy="scalping", interval="1d", periods=100):
            if ticker == "NEUTRAL_TICKER":
                return {
                    "ticker": "NEUTRAL_TICKER",
                    "signal": "NEUTRAL",
                    "confidence": 0.0,
                    "reasons": [],
                    "indicators": {"price": 100.0},
                    "strategy": strategy,
                    "interval": interval,
                    "timestamp": "2024-01-01T00:00:00",
                }
            return {
                "ticker": ticker,
                "signal": "BUY",
                "confidence": 0.8,
                "reasons": ["test"],
                "indicators": {"price": 150.0},
                "strategy": strategy,
                "interval": interval,
                "timestamp": "2024-01-01T00:00:00",
            }
        mock_ra.side_effect = _side
        resp = client.get("/api/analysis/top-ranking?tickers=AAPL,NEUTRAL_TICKER,MSFT")
    assert resp.status_code == 200
    data = resp.json()
    tickers = [r["ticker"] for r in data["rankings"]]
    assert "NEUTRAL_TICKER" not in tickers
    assert set(tickers) == {"AAPL", "MSFT"}


def test_top_ranking_all_failures(client, mock_service_data):
    """All tickers fail → empty rankings (no crash)."""
    from unittest.mock import patch as _patch

    with _patch("app.routers.analysis_router.run_analysis", side_effect=RuntimeError("fail")):
        resp = client.get("/api/analysis/top-ranking?tickers=AAPL,MSFT,TSLA")
    assert resp.status_code == 200
    assert resp.json()["rankings"] == []


def test_top_ranking_default_tickers(client, mock_service_data):
    """Omitting tickers param defaults to POPULAR_TICKERS."""
    resp = client.get("/api/analysis/top-ranking?strategy=scalping&interval=1d&periods=100")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["rankings"]) <= len(POPULAR_TICKERS)


def test_top_ranking_all_neutral(client, mock_service_data):
    """All tickers return NEUTRAL → empty rankings (no crash)."""
    from unittest.mock import patch as _patch

    with _patch("app.routers.analysis_router.run_analysis") as mock_ra:
        mock_ra.return_value = {
            "ticker": "X",
            "signal": "NEUTRAL",
            "confidence": 0.0,
            "reasons": [],
            "indicators": {"price": 100.0},
            "strategy": "scalping",
            "interval": "1d",
            "timestamp": "2024-01-01T00:00:00",
        }
        resp = client.get("/api/analysis/top-ranking?tickers=AAPL,MSFT,TSLA")
    assert resp.status_code == 200
    assert resp.json()["rankings"] == []


def test_top_ranking_single_ticker(client, mock_service_data):
    """Single ticker works (max_workers = min(6, 1) = 1)."""
    resp = client.get("/api/analysis/top-ranking?tickers=AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["rankings"]) == 1
    assert data["rankings"][0]["ticker"] == "AAPL"


def test_top_ranking_sorting(client, mock_service_data):
    """Rankings sorted by confidence descending when confidences differ."""
    from unittest.mock import patch as _patch

    with _patch("app.routers.analysis_router.run_analysis") as mock_ra:
        calls = {"AAPL": 0.9, "MSFT": 0.5, "TSLA": 0.7}

        def _side(ticker, strategy="scalping", interval="1d", periods=100):
            conf = calls.get(ticker, 0.0)
            return {
                "ticker": ticker,
                "signal": "BUY" if conf > 0.5 else "SELL",
                "confidence": conf,
                "reasons": ["test"],
                "indicators": {"price": 150.0},
                "strategy": strategy,
                "interval": interval,
                "timestamp": "2024-01-01T00:00:00",
            }
        mock_ra.side_effect = _side
        resp = client.get("/api/analysis/top-ranking?tickers=AAPL,MSFT,TSLA")
    assert resp.status_code == 200
    data = resp.json()
    confidences = [r["confidence"] for r in data["rankings"]]
    assert confidences == sorted(confidences, reverse=True)
