# Testing con pytest

> **Fecha:** 2026-07-09

## ¿Por Qué Testear?

Sin tests:
```
Cambio una línea → ¿funciona? → probar todo manualmente → me olvido de algo
→ bug en producción → "pero en mi máquina funciona"
```

Con tests:
```
Cambio una línea → corro tests → 101 tests verifican → si pasa, funciona
```

## pytest — El Framework

pytest descubre y ejecuta tests automáticamente:

```
tests/
├── test_analysis_router.py   # 9 tests de endpoints (analyze, chart, top-ranking, etc.)
├── test_alerts_router.py     # Tests de alertas
├── test_broker_manager.py    # Tests de BrokerManager + switch
├── test_config_router.py     # Tests de config endpoints
├── test_debug.py             # Tests de DebugTracker
├── test_main.py              # Tests de health, CORS, lifespan
├── test_options_router.py    # Tests de opciones
├── test_prediction_service.py# Tests de predicciones y resolución
├── test_strategies.py        # Tests de scalping + swing
├── test_whatsapp_service.py  # Tests de WhatsApp
└── conftest.py               # Fixtures compartidas
```

```bash
# Todos los tests
POLARS_SKIP_CPU_CHECK=1 python3 -m pytest tests/ -q --tb=short

# Con cobertura
POLARS_SKIP_CPU_CHECK=1 python3 -m pytest --cov=app --cov-report=term --tb=short

# Test específico
POLARS_SKIP_CPU_CHECK=1 python3 -m pytest tests/test_analysis_router.py -v
```

**Nota:** `POLARS_SKIP_CPU_CHECK=1` es necesario porque la CPU del proyecto
no soporta AVX/AVX2 (polars corre con `rtcompat`).

## Nuestros Tests (101 tests, 10 archivos)

### 1. test_analysis_router.py — Endpoints de análisis

Usa **TestClient** de FastAPI + fixtures con DataFrames Polars mockeados:

```python
@pytest.fixture
def mock_service_data():
    n = 100
    df = pl.DataFrame({
        "timestamp": [f"2024-01-{i+1:02d}" for i in range(n)],
        "Close": [100 + (i % 10) for i in range(n)],
        "High": [105 + (i % 10) for i in range(n)],
        "Low": [95 + (i % 10) for i in range(n)],
    })
    with patch("app.services.analysis_service.get_historical_data", return_value=df):
        yield df

def test_top_ranking(client, mock_service_data):
    resp = client.get("/api/analysis/top-ranking?tickers=AAPL,MSFT")
    assert resp.status_code == 200
    assert "rankings" in resp.json()
```

### 2. test_strategies.py — Lógica de trading

Estrategias con DataFrames Polars reales (no mockeados):

```python
def test_scalping_rsi_oversold():
    df = _df_from(precios_bajos)  # helper con pl.DataFrame
    r = scalping_signals(df)
    assert r["signal"] == "BUY"
    assert "sobrevendido" in " ".join(r["reasons"])
```

### 3. test_broker_manager.py — Conexión a brokers

```python
def test_switch_broker():
    with patch("app.core.broker_manager.BROKER_MAP", {"test": MockBroker}):
        result = bm.switch("test")
        assert result["connected"] is True
```

## conftest.py — Configuración Compartida

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)   # Crea tablas
    yield
    Base.metadata.drop_all(bind=engine)     # Las borra después
```

`autouse=True` significa que se ejecuta antes/después de CADA test.

También hay fixtures para `client` (TestClient) y configuraciones de entorno
(`DATABASE_URL=sqlite:///./test.db`, `POLARS_SKIP_CPU_CHECK=1`).

## Mocking de APIs externas

Para no depender de Yahoo Finance en los tests, se parcha
`get_historical_data` con un `pl.DataFrame` fijo:

```python
@patch("app.services.analysis_service.get_historical_data")
def test_algo(mock_get_data):
    mock_get_data.return_value = pl.DataFrame({...})
    result = mi_funcion()
    assert result["status"] == "ok"
```

Esto permite testear la lógica sin conexión a internet y
sin rate limiting de Yahoo.

## Cobertura actual

| Área | Archivos | Estado |
|------|----------|--------|
| Analysis router | 9 tests | ✅ |
| Strategies (scalping + swing) | Tests estructurales | ✅ |
| BrokerManager + switch | Tests de conexión | ✅ |
| Config router | CRUD de brokers | ✅ |
| Prediction service | Persistencia + resolución | ⚠️ 61% |
| Background analyzer | Sin tests específicos | ❌ |
| WebSocket manager | Sin tests | ❌ |
| Frontend (JS) | Sin tests (Playwright pendiente) | ❌ |

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **pytest fixtures** | Reutilizar datos de prueba | https://docs.pytest.org/en/stable/fixture.html |
| **pytest-mock** | Simular APIs externas | `pip install pytest-mock` |
| **Cobertura (coverage)** | Medir qué código testeamos | `pytest --cov=app` |
| **TDD** | Escribir tests antes del código | Buscar "Test Driven Development" |
| **Test parametrizados** | Un test, múltiples inputs | `@pytest.mark.parametrize` |
| **Playwright** | Tests de frontend (JS) | https://playwright.dev/ |
