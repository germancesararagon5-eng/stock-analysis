from unittest.mock import patch

import polars as pl
import pytest

from app.core.chart_registry import get_registered_charts


def _mock_df(n=100):
    return pl.DataFrame({
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(n)],
        "Close": [100 + (i % 10) for i in range(n)],
        "High": [105 + (i % 10) for i in range(n)],
        "Low": [95 + (i % 10) for i in range(n)],
        "Open": [100 + (i % 10) for i in range(n)],
        "Volume": [1000000] * n,
    })


def _empty_df():
    return pl.DataFrame({
        "timestamp": [],
        "Close": [],
        "High": [],
        "Low": [],
        "Open": [],
        "Volume": [],
    })


# ── Parametrize over the chart registry ─────────────────────────


@pytest.mark.parametrize("chart", get_registered_charts(), ids=lambda c: c.name)
def test_chart_endpoint_returns_200_and_valid_structure(chart, client):
    endpoint = chart.endpoint.replace("{ticker}", "AAPL")
    params = {k: (v.replace("{ticker}", "AAPL") if isinstance(v, str) else v)
              for k, v in chart.params.items()}

    df = _mock_df()
    with (
        patch("app.services.analysis_service.get_historical_data", return_value=df),
        patch("app.routers.analysis_router.get_historical_data", return_value=df),
    ):
        if chart.method == "GET":
            resp = client.get(endpoint, params=params)
        else:
            resp = client.post(endpoint, params=params)

    assert resp.status_code == 200, f"{chart.name}: esperado 200, obtuvo {resp.status_code}: {resp.text[:200]}"
    data = resp.json()

    assert "ticker" in data or "rankings" in data, f"{chart.name}: falta ticker/rankings en respuesta"

    if "series" in data:
        s = data["series"]
        assert isinstance(s.get("timestamp"), list), f"{chart.name}: series.timestamp debe ser lista"
        assert isinstance(s.get("close"), list), f"{chart.name}: series.close debe ser lista"

    if "signal" in data:
        assert data["signal"] in ("BUY", "SELL", "NEUTRAL"), f"{chart.name}: signal inesperado"
        assert 0.0 <= data.get("confidence", 0) <= 1.0, f"{chart.name}: confidence fuera de rango"


@pytest.mark.parametrize("chart", get_registered_charts(), ids=lambda c: c.name)
def test_chart_endpoint_empty_data_does_not_crash(chart, client):
    endpoint = chart.endpoint.replace("{ticker}", "EMPTY")
    params = {k: (v.replace("{ticker}", "EMPTY") if isinstance(v, str) else v)
              for k, v in chart.params.items()}

    with (
        patch("app.services.analysis_service.get_historical_data",
              side_effect=ValueError("sin datos mock")),
        patch("app.routers.analysis_router.get_historical_data",
              side_effect=ValueError("sin datos mock")),
    ):
        if chart.method == "GET":
            resp = client.get(endpoint, params=params)
        else:
            resp = client.post(endpoint, params=params)

    assert resp.status_code == 200, f"{chart.name}: debe devolver 200 aun sin datos, obtuvo {resp.status_code}: {resp.text[:200]}"
    data = resp.json()

    if "series" in data:
        assert data["series"]["timestamp"] == []

    if "signal" in data:
        assert data["signal"] == "NEUTRAL"


@pytest.mark.parametrize("chart", get_registered_charts(), ids=lambda c: c.name)
def test_chart_endpoint_error_response_has_reasons(chart, client):
    endpoint = chart.endpoint.replace("{ticker}", "ERROR")
    params = {k: (v.replace("{ticker}", "ERROR") if isinstance(v, str) else v)
              for k, v in chart.params.items()}

    with (
        patch("app.services.analysis_service.get_historical_data",
              side_effect=RuntimeError("error controlado")),
        patch("app.routers.analysis_router.get_historical_data",
              side_effect=RuntimeError("error controlado")),
    ):
        if chart.method == "GET":
            resp = client.get(endpoint, params=params)
        else:
            resp = client.post(endpoint, params=params)

    assert resp.status_code == 200
    data = resp.json()
    if "reasons" in data:
        assert len(data["reasons"]) > 0, f"{chart.name}: error response debe tener reasons"
        assert data["reasons"][0] == "error controlado"
    else:
        pytest.skip(f"{chart.name}: no tiene campo reasons")


# ── Filtering tests: sparkline with short data ─────────────────


def test_sparkline_short_data_returns_valid_json(client):
    df = pl.DataFrame({
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(25)],
        "Close": [100.0 + (i % 5) for i in range(25)],
        "High": [105.0] * 25,
        "Low": [95.0] * 25,
        "Open": [100.0] * 25,
        "Volume": [1000000] * 25,
    })
    with (
        patch("app.services.analysis_service.get_historical_data", return_value=df),
        patch("app.routers.analysis_router.get_historical_data", return_value=df),
    ):
        resp = client.get("/api/analysis/chart/SPARK?strategy=scalping&interval=1d&periods=20")

    assert resp.status_code == 200
    data = resp.json()
    s = data["series"]
    assert len(s["close"]) == 25
    assert len(s["ema_9"]) == 25
    assert len(s["timestamp"]) == 25


# ── Coherence: same ticker same params = same signal ────────────


def test_coherent_signal_across_endpoints(client):
    df = _mock_df()
    with (
        patch("app.services.analysis_service.get_historical_data", return_value=df),
        patch("app.routers.analysis_router.get_historical_data", return_value=df),
    ):
        r1 = client.get("/api/analysis/chart/AAPL?strategy=scalping&interval=1d&periods=100")
        r2 = client.post("/api/analysis/analyze", json={
            "ticker": "AAPL", "strategy": "scalping", "interval": "1d", "periods": 100,
        })
        r3 = client.get("/api/analysis/top-ranking?strategy=scalping&interval=1d&periods=100&tickers=AAPL")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200

    d1 = r1.json()
    d2 = r2.json()
    d3 = r3.json()

    s1 = d1["signal"]
    s2 = d2["signal"]
    s3 = d3["rankings"][0]["signal"] if d3["rankings"] else None

    assert s1 in ("BUY", "SELL", "NEUTRAL")
    assert s1 == s2, f"Chart ({s1}) vs Analyze ({s2}) — mismo ticker/strategy/interval/periods debe dar misma señal"

    if s3 is not None:
        assert s3 == s1, f"Top-ranking ({s3}) difiere de chart ({s1})"


# ── Registry completeness: every UI chart is registered ─────────


def test_all_frontend_charts_registered():
    names = {c.name for c in get_registered_charts()}
    for required in ("sparkline", "multi-panel", "technical-analysis"):
        assert required in names, f"Falta chart registrado: {required}"
