# Referencia de API

La API expone **40 endpoints** agrupados en 6 routers + WebSocket + health. Todos retornan JSON.
Documentación interactiva en `/docs` (Swagger UI) y `/redoc` (ReDoc).
El servidor corre en `http://localhost:8000`.

## Router: Analysis (`/api/analysis/`)

Archivo: `app/routers/analysis_router.py`

### `POST /api/analysis/analyze`
Ejecuta análisis técnico completo sobre un ticker.

**Request body:**
```json
{
  "ticker": "AAPL",
  "strategy": "scalping",
  "interval": "5m",
  "periods": 100
}
```

| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| ticker | string | — | Símbolo del activo (AAPL, BTC-USD, ES=F, etc.) |
| strategy | string | "scalping" | "scalping" (corto) o "swing" (largo) |
| interval | string | "5m" | 1m, 5m, 15m, 30m, 1h, 4h, 1d |
| periods | int | 100 | Filas de datos históricos a usar |

**Response (200):**
```json
{
  "ticker": "AAPL",
  "strategy": "scalping",
  "signal": "BUY",
  "confidence": 0.35,
  "indicators": {
    "ema_9": 185.42,
    "ema_21": 184.15,
    "rsi_14": 58.32,
    "bb_upper": 190.10,
    "bb_mid": 185.00,
    "bb_lower": 179.90,
    "price": 186.50
  },
  "reasons": ["EMA 9 cruzó arriba EMA 21"],
  "interval": "5m",
  "timestamp": "2026-07-09T15:30:00"
}
```

**Señales:** `BUY`, `SELL`, `NEUTRAL`  
**Confianza:** 0.0 a 1.0 (ver `docs/indicators.md`)

### `GET /api/analysis/chart/{ticker}`
Datos de chart + análisis para un ticker.

| Query param | Tipo | Default |
|-------------|------|---------|
| strategy | string | "scalping" |
| interval | string | "1d" |
| periods | int | 100 |

**Response (200):** Incluye análisis + series completas para chart:
```json
{
  "ticker": "AAPL",
  "signal": "BUY",
  "confidence": 0.35,
  "indicators": {...},
  "reasons": [...],
  "series": {
    "timestamp": ["2026-07-01T...", ...],
    "close": [180.0, 181.5, ...],
    "ema_9": [...],
    "ema_21": [...],
    "bb_upper": [...],
    "bb_mid": [...],
    "bb_lower": [...],
    "rsi_14": [...],
    "macd": [...],
    "macd_signal": [...],
    "macd_histogram": [...]
  }
}
```

### `GET /api/analysis/data/{ticker}`
Datos en tiempo real del broker activo.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| ticker | string | Símbolo solicitado |
| price | float | Precio actual |
| error | string | null si OK |

### `POST /api/analysis/order`
Órdenes simuladas (todos los brokers).

**Request body:**
```json
{ "side": "BUY", "quantity": 10, "ticker": "AAPL" }
```

**Response:** `{ "status": "simulated", "side": "BUY", "quantity": 10, ... }`

### `GET /api/analysis/top-ranking`
Ranking de tickers populares por confianza. Correlo en paralelo con ThreadPoolExecutor.

| Query param | Tipo | Default |
|-------------|------|---------|
| strategy | string | "scalping" |
| interval | string | "1d" |
| periods | int | 100 |
| tickers | string | (todos los populares) |

**Response:**
```json
{
  "strategy": "scalping",
  "interval": "1d",
  "rankings": [
    { "ticker": "NVDA", "signal": "BUY", "confidence": 0.80, ... },
    { "ticker": "AAPL", "signal": "BUY", "confidence": 0.35, ... }
  ]
}
```

### `POST /api/analysis/technical-analysis`
Análisis técnico detallado multi-factor (scoring ±1/±2 por indicador).

| Campo | Tipo | Default |
|-------|------|---------|
| ticker | string | — |
| strategy | string | "scalping" |
| interval | string | "1d" |
| periods | int | 100 |

**Response:** `{ "ticker", "verdict", "confidence" (0-100), "signals", "reasons", "indicators" }`

**Veredictos:** BUY (score>=3), SELL (score<=-3), ACCUMULATE (score>=1), REDUCE (score<=-1), NEUTRAL

---

## Router: Config (`/api/config/`)

Archivo: `app/routers/config_router.py`

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/api/config/broker` | Cambiar broker activo (body: name, api_key, api_secret, endpoint, sandbox) |
| GET | `/api/config/broker/status` | Estado del broker actual |
| GET | `/api/config/brokers` | Lista de brokers disponibles |

**Brokers disponibles:** `"yahoo_finance"`, `"binance"`, `"interactive_brokers"`

---

## Router: Alerts (`/api/alerts/`)

Archivo: `app/routers/alerts_router.py`

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/api/alerts/` | Crear alerta (body: ticker, strategy, condition, threshold, whatsapp_enabled) |
| GET | `/api/alerts/` | Listar alertas activas |
| DELETE | `/api/alerts/{alert_id}` | Eliminar alerta |
| POST | `/api/alerts/test-whatsapp` | Probar envío WhatsApp |

---

## Router: Debug (`/api/debug/`)

Archivo: `app/routers/debug_router.py`

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/api/debug/` | Dashboard debug (query: show, limit) |
| POST | `/api/debug/toggle` | Activar/desactivar debug |
| POST | `/api/debug/clear` | Limpiar historial |
| GET | `/api/debug/live` | Live polling (query: after_id) |

---

## Router: Options (`/api/options/`)

Archivo: `app/routers/options_router.py`

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/api/options/background/status` | Estado del background analyzer |
| POST | `/api/options/background/start` | Iniciar background analyzer |
| POST | `/api/options/background/stop` | Detener background analyzer |
| POST | `/api/options/background/config` | Configurar (run_every, tickers, strategy, etc.) |
| GET | `/api/options/background/results` | Resultados (query: limit) |
| GET | `/api/options/predictions` | Listar predicciones (query: ticker, limit, offset) |
| GET | `/api/options/predictions/stats` | Estadísticas (query: ticker) |
| POST | `/api/options/predictions/resolve` | Resolver predicciones pendientes (query: count, threshold) |
| GET | `/api/options/trading/summary` | Resumen trading simulator (query: ticker) |
| GET | `/api/options/whatsapp/config` | Config WhatsApp |
| POST | `/api/options/whatsapp/config` | Guardar número WhatsApp (query: phone_number) |
| GET | `/api/options/whatsapp/qr` | QR para conectar WhatsApp |
| GET | `/api/options/broker/list` | Lista de brokers |
| GET | `/api/options/broker/status` | Estado del broker |
| GET | `/api/options/debug/status` | Estado del debug |
| POST | `/api/options/debug/toggle` | Toggle debug |
| POST | `/api/options/debug/clear` | Limpiar debug |

### Router: ML (`/api/ml/`)

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/api/ml/dataset` | Exportar dataset de entrenamiento (query: strategies, tickers, limit, min_confidence) |
| GET | `/api/ml/stats` | Estadísticas del dataset (total por estrategia, win rate) |

---

## Otros endpoints

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/` | Sirve `static/index.html` (SPA) |
| GET | `/health` | Health check: `{ status, active_broker, broker_connected }` |
| WS | `/api/ws` | WebSocket para broadcast en tiempo real |
| GET | `/static/*` | Archivos estáticos (JS, CSS) |

---

## Códigos de error

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 400 | Bad request (payload inválido) |
| 404 | No encontrado (ticker sin datos, QR no disponible) |
| 500 | Error interno (con try/except, se retorna NEUTRAL con reasons) |

## Intervalos y períodos

Mapeo de intervalos de la app a yfinance / Binance:

| App | yfinance Interval | yfinance Period | Binance |
|-----|------------------|-----------------|---------|
| 1m | 1m | 1d | 1m |
| 5m | 5m | 5d | 5m |
| 15m | 15m | 1mo | 15m |
| 30m | 30m | 1mo | 30m |
| 1h | 60m | 2mo | 1h |
| 4h | 4h | 6mo | 4h |
| 1d | 1d | 1y | 1d |

## POPULAR_TICKERS (44)

Acciones: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, AMD, INTC, NFLX, DIS, BA, NKE, JPM, V, MA, COST, WMT, HD, PG, KO, PEP, XOM, CVX, JNJ, PFE, MRK, ABBV

Crypto: BTC-USD, ETH-USD, SOL-USD, XRP-USD, DOGE-USD, ADA-USD, DOT-USD, MATIC-USD

Índices: ^GSPC, ^IXIC, ^DJI, ^RUT, ^VIX

Futuros: ES=F, NQ=F, YM=F, CL=F, GC=F
