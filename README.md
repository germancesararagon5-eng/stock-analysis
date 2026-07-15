# Stock Analysis — Multi-Broker Sistema de Análisis Técnico

Sistema de análisis técnico de acciones y criptomonedas con soporte multi-broker, 6 estrategias de trading, alertas WhatsApp, dataset ML y simulador de trading.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 + FastAPI |
| Base de datos | PostgreSQL 16 (SQLAlchemy ORM) |
| Indicadores | **Polars nativo** (sin pandas/ta) |
| Cache | Redis 7 (reservado) |
| Frontend | Vanilla JS + Chart.js 4.4.7 con zoom |
| WhatsApp | Node.js 20 + Baileys (WebSocket) |
| Contenedores | Docker Compose |

## Arquitectura

```
┌─────────┐     ┌──────────────┐     ┌──────────┐
│ Browser │────▶│  FastAPI     │────▶│ PostgreSQL│
│ :8000   │     │  :8000       │     │ :5432    │
└─────────┘     │ ──────────── │     └──────────┘
                │ /api/analysis │     ┌──────────┐
┌─────────┐     │ /api/alerts   │────▶│ Redis    │
│ WhatsApp│◀───▶│ /api/config   │     │ :6379    │
│ Gateway │     │ /api/options  │     └──────────┘
│ :3000   │     │ /api/debug    │
└─────────┘     │ /api/ml       │
                └──────────────┘
```

### Flujo de Análisis
1. Frontend envía ticker + estrategia + intervalo → `/api/analysis/analyze`
2. FastAPI llama a `get_historical_data()` que determina broker activo
3. Yahoo Finance o Binance API → DataFrame **Polars** con OHLCV
4. `run_strategy()` ejecuta indicadores (EMA, RSI, MACD, BB, SMA)
5. Estrategia devuelve señal (BUY/SELL/NEUTRAL) + confianza + razones
6. Resultado se persiste como predicción en DB
7. Opcional: notificación WhatsApp

## Inicio Rápido

```bash
# Clonar e iniciar
git clone <repo> && cd stock-analysis
docker compose up -d --build

# Abrir en navegador
open http://localhost:8000

# Tests
pytest -v

# Lint
ruff check .
```

## Servicios Docker

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `api` | 8000 | FastAPI (--workers 1) |
| `db` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 |
| `whatsapp-gateway` | 3000 | Node.js + Baileys |

## API — 40 Endpoints

### Análisis Técnico (`/api/analysis`)

**POST `/api/analysis/analyze`** — Análisis completo de un ticker

```json
// Request
{"ticker": "AAPL", "strategy": "scalping", "interval": "5m", "periods": 100}

// Response
{
  "ticker": "AAPL",
  "strategy": "scalping",
  "signal": "BUY",
  "confidence": 0.78,
  "indicators": {
    "price": 150.25,
    "rsi_14": 62.3,
    "ema_9": 149.8,
    "ema_21": 148.2,
    "bb_upper": 155.0,
    "bb_lower": 145.0,
    "macd": 1.2,
    "macd_signal": 0.8,
    "sma_50": 147.5,
    "sma_200": 140.0
  },
  "reasons": [
    "EMA 9 sobre EMA 21 (golden cross)",
    "MACD sobre línea de señal",
    "RSI en zona neutral-alcista"
  ]
}
```

**GET `/api/analysis/top-ranking`** — Top tickers por confianza (paralelizado)

```
GET /api/analysis/top-ranking?strategy=scalping&interval=1d&periods=100
```

Procesa hasta 44 tickers populares en paralelo con `ThreadPoolExecutor` (6 workers, timeout 90s).

**GET `/api/analysis/chart/{ticker}`** — Chart + indicadores toggleables

```
GET /api/analysis/chart/AAPL?strategy=scalping&interval=1d&periods=60
```

Retorna series de: close, EMA9, EMA21, BB (upper/mid/lower), RSI14, MACD, SMA50, SMA200, volumen.

**POST `/api/analysis/technical-analysis`** — Análisis multi-indicador detallado

**GET `/api/analysis/compare-strategies`** — Compara las 6 estrategias para un ticker

### Configuración (`/api/config`)

- `POST /broker` — Cambiar broker activo (yahoo_finance, binance, interactive_brokers)
- `GET /broker/status` — Estado del broker actual
- `GET /brokers` — Listar brokers disponibles

### Alertas (`/api/alerts`)

- `POST /` — Crear alerta programada
- `GET /` — Listar alertas activas
- `DELETE /{id}` — Eliminar alerta
- `POST /test-whatsapp` — Probar notificación WhatsApp

### ML (`/api/ml`)

- `GET /dataset` — Exportar dataset de entrenamiento (indicadores + outcomes)
- `GET /stats` — Estadísticas del dataset

### Opciones (`/api/options`)

- Background analyzer: start/stop/config/results
- Predicciones: list/stats/resolve
- Trading simulator: summary
- WhatsApp: config
- Debug: status/toggle/clear

## Estrategias de Trading

| Estrategia | Timeframe | Descripción |
|-----------|-----------|-------------|
| **Scalping** ⚡ | 1m-5m | EMA9/21 crossover, RSI, Bollinger. Señales rápidas. |
| **Swing** 📈 | 1d | MACD, SMA200, S&R. Tendencia de mediano plazo. |
| **Momentum** 🚀 | Cualquiera | RSI + volumen. Detecta impulso alcista fuerte. |
| **Mean Reversion** 🔄 | Cualquiera | RSI extremo + BB. Compra en sobreventa, vende en sobrecompra. |
| **Breakout** 💥 | Cualquiera | BB squeeze + resistencia/soporte. Ruptura de niveles. |
| **Market Structure** 📊 | Cualquiera | Máximos/mínimos + divergencia RSI. Tendencia estructural. |

### Indicadores Técnicos (todos calculados con Polars nativo)

- **EMA 9/21/50/200** — `ewm_mean(span=X, adjust=False)`
- **RSI 14** — Compara ganancias/pérdidas promedio en 14 períodos
- **Bollinger Bands** — SMA 20 ± 2 desviaciones estándar
- **MACD** — EMA12 - EMA26, línea de señal EMA9
- **SMA 50/200** — `rolling_mean(window_size=X)`
- **Soporte/Resistencia** — Mínimos/máximos locales con tolerancia 3%
- **ATR** — Rango verdadero promedio en 14 períodos
- **Volumen** — Comparación contra media móvil de 20

## Frontend — SPA Vanilla

5 pestañas + modal de mercado:

### Dashboard
- Estado del sistema, broker activo, conexión
- Precio en tiempo real de cualquier ticker
- Cards de Top Ranking con confianza

### Análisis
- Input con autocomplete de 44 tickers populares
- Selector de estrategia e intervalo
- Resultado: señal, confianza, indicadores, razones
- Chart interactivo con indicadores toggleables
- Botones Comprar/Vender (simulados)

### Alertas
- Crear alertas programadas por ticker
- Prueba de WhatsApp

### Opciones
- Background analyzer: configuración multi-estrategia
- Predicciones: historial + stats + resolución
- Simulador de trading: P&L, win rate, profit factor
- Configuración WhatsApp

### Depuración
- Logs en vivo de requests, errores, eventos de broker y estrategia

### Temas
- Dark (default), Grey (escala de grises), Light (claro)
- Persistencia en localStorage

## Background Analyzer

Analizador automático en segundo plano que corre en un thread daemon:

- Analiza N tickers × 6 estrategias cada ciclo
- Usa `ThreadPoolExecutor(max_workers=4)` + `as_completed()`
- Persiste resultados en tabla `BackgroundResult`
- Envía alertas WhatsApp para señales fuertes (confianza ≥ 50%)
- Almacena en tabla `AnalysisResult` para dataset ML
- Lock threading para acceso seguro a configuración

```python
# Configurar desde API
POST /api/options/background/config
{
  "tickers": "AAPL,MSFT,TSLA",
  "strategy": "all",         # o una específica
  "interval": "1d",
  "periods": 100,
  "min_confidence": 0.3,
  "run_every_seconds": 3600  # cada hora
}
```

## Simulador de Trading

Cada predicción almacenada puede "resolverse": se compara el precio actual contra el precio de la señal.

- **BUY correcto**: precio actual ≥ precio entrada × (1 - threshold)
- **SELL correcto**: precio actual ≤ precio entrada × (1 + threshold)
- **P&L acumulado**: ganancia/pérdida sumada de todas las predicciones resueltas
- **Win rate**: correctas / total resueltas
- **Profit factor**: ganancia total / pérdida total

```bash
# Resolver predicciones pendientes
curl -X POST "/api/options/predictions/resolve?count=50&threshold=0.5"
# threshold = 0.5% de cambio mínimo para considerar correcta
```

## Dataset ML

Cada análisis se almacena en `AnalysisResult` con indicadores completos desnormalizados:

```
ticker, strategy, interval, signal, confidence, price,
rsi_14, ema_9, ema_21, ema_50, ema_200,
bb_upper, bb_lower, macd, macd_signal, macd_histogram,
volume, atr, support_1, resistance_1,
outcome, price_change_pct, created_at
```

```bash
# Exportar dataset
curl "/api/ml/dataset?strategies=scalping,swing&limit=5000&min_confidence=0.3"
```

## Tests — 297 pasando

```bash
pytest -v                    # Todos
pytest -v -k "strategy"      # Solo estrategias
pytest --cov=app --cov-report=term-missing  # Cobertura
```

| Archivo | Tests | Cobertura |
|---------|-------|-----------|
| `test_strategies.py` | 50+ | Lógica real de indicadores |
| `test_background_analyzer.py` | 34 | **100%** |
| `test_background_result.py` | 9 | Persistencia |
| `test_prediction_service_coverage.py` | 10 | **98%** |
| `test_analysis_router.py` | 15 | Endpoints |
| `test_docker_compose.py` | 12 | Docker |
| `test_brokers.py` | 15 | Integración broker |

## Despliegue

### Producción
```bash
docker compose up -d --build
```

### Variables de Entorno (`.env`)
```
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/stockdb
DATABASE_URL_SYNC=postgresql://user:pass@db:5432/stockdb
REDIS_URL=redis://redis:6379/0
WHATSAPP_GATEWAY_URL=http://whatsapp-gateway:3000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Reglas Críticas
- **`--workers 1`**: SQLAlchemy no soporta fork entre workers
- **Sin AVX/AVX2**: Usar `POLARS_SKIP_CPU_CHECK=1` + `polars[rtcompat]`
- **pyarrow**: `pl.from_pandas()` requiere pyarrow, filtrar columnas no OHLCV
- **Sin migrations**: Si se cambia modelo DB, dropear tabla manualmente
- **Login deshabilitado**: Temporalmente, auth_router no incluido

## Ejemplos de Uso

### Análisis rápido de AAPL con Swing
```bash
curl -X POST "http://localhost:8000/api/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","strategy":"swing","interval":"1d","periods":200}'
```

### Ver chart de Bitcoin con indicadores
```bash
curl "http://localhost:8000/api/analysis/chart/BTC-USD?strategy=scalping&interval=1h&periods=100"
```

### Crear alerta
```bash
curl -X POST "http://localhost:8000/api/alerts/" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"TSLA","strategy":"scalping","condition":"signal == BUY","whatsapp_enabled":true}'
```

### Top ranking semanal
```bash
curl "http://localhost:8000/api/analysis/top-ranking?strategy=swing&interval=1d&periods=100"
```

### Comparar estrategias
```bash
curl "http://localhost:8000/api/analysis/compare-strategies?ticker=AAPL&interval=1d&periods=100"
```

### Iniciar background analyzer
```bash
curl -X POST "http://localhost:8000/api/options/background/start"
```

### Exportar dataset ML
```bash
curl "http://localhost:8000/api/ml/dataset?strategies=scalping&limit=100&min_confidence=0.5"
```

## Workflow de Desarrollo

1. Implementar cambios en código
2. `pytest -v` — verificar tests
3. `ruff check .` — lint
4. Actualizar `CHANGELOG`
5. Actualizar `TASKS.md`
6. Actualizar `AGENTS.md` (contador de tests, estado)
7. `git add -A && git commit -m "tipo: descripcion"`
8. `git push origin main`

## Estructura del Proyecto

```
stock-analysis/
├── app/                          # Backend FastAPI
│   ├── main.py                   # Entry point, lifespan, routers
│   ├── config.py                 # Settings (env vars)
│   ├── database.py               # SQLAlchemy engine/session
│   ├── models.py                 # ORM models (5 tablas)
│   ├── schemas.py                # Pydantic schemas con docs
│   ├── core/
│   │   ├── strategies.py         # Indicadores Polars nativos
│   │   ├── broker_manager.py     # Gestor de brokers singleton
│   │   ├── chart_registry.py     # Registro de charts Chart.js
│   │   └── debug.py              # Debug middleware + tracker
│   ├── routers/
│   │   ├── analysis_router.py    # /api/analysis (8 endpoints)
│   │   ├── config_router.py      # /api/config (3 endpoints)
│   │   ├── alerts_router.py      # /api/alerts (4 endpoints)
│   │   ├── options_router.py     # /api/options (16 endpoints)
│   │   ├── debug_router.py       # /api/debug (4 endpoints)
│   │   └── ml_router.py          # /api/ml (2 endpoints)
│   ├── services/
│   │   ├── analysis_service.py   # get_historical_data + run_analysis
│   │   ├── background_analyzer.py # Daemon multi-estrategia
│   │   ├── prediction_service.py  # CRUD predicciones + resolución
│   │   ├── ml_service.py          # Dataset ML + stats
│   │   ├── technical_analysis.py  # Análisis multi-indicador
│   │   ├── whatsapp_service.py    # Cliente gateway WhatsApp
│   │   └── ws_manager.py          # WebSocket connection manager
│   └── static/
│       ├── index.html            # SPA (5 tabs)
│       ├── styles.css            # Temas Dark/Grey/Light
│       └── app.js                # ~1740 líneas de JS vanilla
├── tests/                        # 297 tests Pytest
│   ├── conftest.py               # Fixtures globales
│   ├── test_strategies.py        # 50+ tests de indicadores
│   ├── test_background_analyzer.py # 34 tests, 100% coverage
│   └── ... (20 archivos)
├── docs/                         # Documentación por área
│   ├── architecture.md
│   ├── api-reference.md
│   ├── indicators.md
│   ├── deployment.md
│   ├── frontend.md
│   ├── whatsapp-gateway.md
│   └── ci-cd-guide.md
├── whatsapp-gateway/             # Gateway Node.js + Baileys
│   ├── Dockerfile
│   ├── index.js                  # Express + Baileys + QR
│   └── session/                  # Sesión persistente
├── docker-compose.yml            # Servicios Docker
├── Dockerfile                    # Python 3.12
├── AGENTS.md                     # Contexto para asistentes
├── TASKS.md                      # Prioridades y estado
├── CHANGELOG                     # Historial de versiones
└── README.md                     # Este archivo
```
