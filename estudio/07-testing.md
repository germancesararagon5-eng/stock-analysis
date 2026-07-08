# Testing con pytest

> **Fecha:** 2026-07-08

## ¿Por qué Testear?

Sin tests:
```
Cambio una línea → ¿funciona? → probar todo manualmente → me olvido de algo
→ bug en producción → "pero en mi máquina funciona"
```

Con tests:
```
Cambio una línea → corro tests → 13 tests verifican → si pasa, funciona
```

## pytest — El Framework

pytest descubre y ejecuta tests automáticamente:

```
tests/
├── test_brokers.py     # Tests de brokers
├── test_config.py      # Tests de API endpoints
└── test_strategies.py  # Tests de estrategias
```

```bash
pytest                    # Corre todos los tests
pytest -v                 # Verboso (muestra cada test)
pytest -k "yahoo"         # Solo tests que matchean "yahoo"
pytest --tb=short         # Traza corta en errores
```

## Nuestros Tests (13 tests, 3 archivos)

### 1. test_brokers.py — Conexión a brokers

```python
def test_yahoo_connect(yahoo_broker):
    assert yahoo_broker.connect() is True

def test_yahoo_get_data(yahoo_broker):
    data = yahoo_broker.get_realtime_data("AAPL")
    assert "price" in data
```

### 2. test_config.py — API Endpoints

Usa **TestClient** de FastAPI para simular requests HTTP sin
necesidad de tener el servidor corriendo:

```python
from fastapi.testclient import TestClient

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
```

### 3. test_strategies.py — Lógica de trading

```python
def test_scalping_buy_signal():
    prices = [100 + sin(i) * 15 for i in range(100)]
    df = make_sample_df(prices)
    result = scalping_signals(df)
    assert result["signal"] in ("BUY", "SELL", "NEUTRAL")
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

## ¿Qué cubrimos?

| Área | Tests | Estado |
|------|-------|--------|
| Yahoo Finance (conectar, datos, orden) | 3 | ✅ |
| Binance (conectar) | 1 | ✅ |
| IBKR (conectar) | 1 | ✅ |
| API endpoints (health, brokers, status) | 4 | ✅ |
| Scalping signals | 2 | ✅ |
| Swing signals | 2 | ✅ |

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **pytest fixtures** | Reutilizar datos de prueba | https://docs.pytest.org/en/stable/fixture.html |
| **pytest-mock** | Simular APIs externas | `pip install pytest-mock` |
| **Cobertura (coverage)** | Medir qué código testeamos | `pytest --cov=app` |
| **TDD** | Escribir tests antes del código | Buscar "Test Driven Development" |
| **Test parametrizados** | Un test, múltiples inputs | `@pytest.mark.parametrize` |
| **Hypothesis** | Tests basados en propiedades | https://hypothesis.readthedocs.io/ |
