# Stock Analysis Multi-Broker — Handover Completo

## 1. Propósito

Sistema de análisis técnico multi-broker con FastAPI/Docker, GUI en SPA vanilla,
auto-análisis en background con predicciones, gráficos Chart.js interactivos con zoom,
y gateway WhatsApp auto-hosteado (Baileys) sin Twilio.

---

## 2. Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NAVEGADOR                                    │
│  http://localhost:8000                                               │
│  SPA (index.html + app.js + styles.css)                             │
│  Tabs: Dashboard · Análisis · Alertas · Opciones · Depuración       │
│  Librerías CDN: Chart.js@4.4.7, chartjs-plugin-zoom@2.0.1          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────┼──────────────────────────────────────────┐
│  FastAPI  :8000           │                                          │
│  ┌───────────────────────┴──────────────────────┐                   │
│  │  /api/analysis/*        → analysis_router.py  │                   │
│  │  /api/alerts/*          → alerts_router.py    │                   │
│  │  /api/debug/*           → debug_router.py     │                   │
│  │  /api/config/*          → config_router.py    │                   │
│  │  /api/options/*         → options_router.py   │                   │
│  └───────────────────────┬──────────────────────┘                   │
│                          │                                          │
│  ┌───────────────────────┴──────────────────────┐                   │
│  │  Servicios                                    │                   │
│  │  ┌─────────────────┐  ┌──────────────────┐   │                   │
│  │  │ analysis_service │  │ prediction_service│  │                   │
│  │  └─────────────────┘  └──────────────────┘   │                   │
│  │  ┌─────────────────┐  ┌──────────────────┐   │                   │
│  │  │ technical_      │  │ whatsapp_service  │   │                   │
│  │  │ analysis.py     │  │ (httpx → gateway) │   │                   │
│  │  └─────────────────┘  └──────────────────┘   │                   │
│  │  ┌──────────────────────────────────┐         │                   │
│  │  │ background_analyzer (thread)      │         │                   │
│  │  └──────────────────────────────────┘         │                   │
│  └──────────────────────────────────────────────┘                   │
│                                                                     │
│  ┌───────────────────────┐  ┌──────────────────────┐                │
│  │  BrokerManager         │  │  DebugTracker         │               │
│  │  ┌────────┬─────────┐  │  │  (memoria, max 500)  │               │
│  │  │ Yahoo  │ Binance  │  │  └──────────────────────┘               │
│  │  │ (gratis)│(testnet)│  │                                        │
│  │  │ IBKR   │          │  │                                        │
│  │  │(place) │          │  │                                        │
│  │  └────────┴─────────┘  │                                        │
│  └───────────────────────┘                                           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP (docker network)
┌──────────────────────────┼──────────────────────────────────────────┐
│  PostgreSQL :5432         │  Redis :6379    │    whatsapp-gateway :3000 │
│  (sqlalchemy)             │  (reservado)   │    Node.js 20 + Baileys  │
│  Tablas:                  │                 │    Endpoints:            │
│  · broker_configs         │                 │    GET /status           │
│  · alert_configs          │                 │    GET /qr               │
│  · predictions            │                 │    POST /send-message    │
│  · whatsapp_configs       │                 │    Vol: /app/session     │
└───────────────────────────┴─────────────────┴────────────────────────┘
```

---

## 3. Estructura de Archivos

```
/home/sole/stock-analysis/
├── docker-compose.yml          # 4 servicios: api, whatsapp-gateway, db, redis
├── Dockerfile                  # Python 3.12-slim, multi-stage, --workers 1
├── requirements.txt            # 13 paquetes Python
│
├── .env                        # Variables activas
├── .env.example                # Template comentado en español
│
├── whatsapp-gateway/           # Gateway WhatsApp auto-hosteado
│   ├── Dockerfile              # Node.js 20-alpine + git
│   ├── package.json            # Baileys, Express, QRCode, Pino
│   └── index.js                # Servidor HTTP con Baileys
│
├── app/
│   ├── config.py               # Pydantic Settings (carga .env)
│   ├── database.py             # SQLAlchemy engine + SessionLocal + init_db()
│   ├── main.py                 # FastAPI app, lifespan, rutas / y /health
│   ├── models.py               # 4 modelos: BrokerConfig, AlertConfig, Prediction, WhatsAppConfig
│   ├── schemas.py              # Pydantic models para request/response
│   │
│   ├── brokers/                # Implementaciones de brokers
│   │   ├── yahoo_finance.py    # Gratuito, simulado
│   │   ├── binance.py          # Testnet
│   │   └── interactive_brokers.py  # Placeholder
│   │
│   ├── core/
│   │   ├── base_broker.py      # ABC: BaseBroker + BrokerConfig dataclass
│   │   ├── broker_manager.py   # Singleton, BROKER_MAP, load_from_db, switch
│   │   ├── strategies.py       # scalping_signals, swing_signals, compute_chart_data
│   │   ├── debug.py            # DebugTracker, @timed, DebugMiddleware
│   │   └── ai_models/          # Reservado para futura IA
│   │
│   ├── routers/                # FastAPI routers
│   │   ├── config_router.py     # POST/GET broker (switch, status, list)
│   │   ├── analysis_router.py   # analyze, chart, data, order, technical-analysis
│   │   ├── alerts_router.py     # CRUD alertas, test-whatsapp
│   │   ├── debug_router.py      # Dashboard debug, live polling, toggle, clear
│   │   └── options_router.py    # Background, predictions, whatsapp, broker, debug config
│   │
│   ├── services/
│   │   ├── analysis_service.py  # run_analysis(), get_historical_data()
│   │   ├── background_analyzer.py # Thread daemon, configurable, con lock
│   │   ├── prediction_service.py  # CRUD + resolve + stats
│   │   ├── technical_analysis.py  # Motor de reglas: EMA, RSI, BB, MACD
│   │   └── whatsapp_service.py    # HTTP client al gateway (sin Twilio)
│   │
│   └── static/
│       ├── index.html          # SPA: 5 tabs + modal + event log
│       ├── styles.css          # Dark theme, CSS variables, responsive
│       └── app.js              # ~1478 líneas, toda la lógica frontend
│
└── tests/
    ├── test_brokers.py
    ├── test_config.py
    └── test_strategies.py
```

---

## 4. Base de Datos (PostgreSQL)

### Tabla: `broker_configs`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| name | String(50) NOT NULL | |
| api_key | String(255) NULL | |
| api_secret | String(255) NULL | |
| endpoint | String(255) NULL | |
| sandbox | Boolean default True | |
| active | Boolean default False | Solo uno activo |
| extra | JSON NULL | |
| created_at | DateTime tz | server_default |
| updated_at | DateTime tz | onupdate |

### Tabla: `alert_configs`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| ticker | String(20) NOT NULL | |
| strategy | String(50) NOT NULL | scalping/swing |
| condition | String(20) NOT NULL | crossover, rsi_oversold, rsi_overbought, bb_touch |
| threshold | Float NULL | |
| enabled | Boolean default True | |
| whatsapp_enabled | Boolean default False | |
| created_at | DateTime tz | server_default |

### Tabla: `predictions`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| ticker | String(20) NOT NULL indexed | |
| signal | String(10) NOT NULL | BUY/SELL/NEUTRAL |
| confidence | Float default 0.0 | |
| strategy | String(50) default "scalping" | |
| interval | String(10) default "5m" | |
| periods | Integer default 100 | |
| price_at_prediction | Float NULL | |
| reasons | JSON NULL | Array de strings |
| indicators_snapshot | JSON NULL | |
| outcome | String(10) NULL indexed | PENDING/CORRECT/INCORRECT |
| price_at_outcome | Float NULL | |
| price_change_pct | Float NULL | |
| resolved_at | DateTime tz NULL | |
| created_at | DateTime tz | server_default |

### Tabla: `whatsapp_configs`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| phone_number | String(50) default "" | Solo dígitos, con código de país |
| connected | Boolean default False | Cache del status gateway |
| created_at | DateTime tz | server_default |
| updated_at | DateTime tz | onupdate |

---

## 5. API — Todos los Endpoints (36 total)

### Sistema (`main.py`)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Sirve index.html |
| GET | `/health` | `{active_broker, broker_connected, ...}` |

### Config (`config_router.py`)
| POST | `/api/config/broker` | Cambiar broker: `{name, sandbox}` |
| GET | `/api/config/broker/status` | `{active, connected}` |
| GET | `/api/config/brokers` | `{available_brokers: [string]}` |

### Análisis (`analysis_router.py`)
| POST | `/api/analysis/analyze` | Ejecutar estrategia. Body: `{ticker, strategy, interval, periods}` |
| GET | `/api/analysis/chart/{ticker}` | Series para gráfico. Query: `strategy, interval, periods` |
| GET | `/api/analysis/data/{ticker}` | Precio actual en tiempo real |
| POST | `/api/analysis/order` | Ejecutar orden simulada. Body: `{ticker, side, quantity}` |
| POST | `/api/analysis/technical-analysis` | Análisis técnico por reglas. Query: `ticker, strategy, interval, periods` |

### Alertas (`alerts_router.py`)
| POST | `/api/alerts/` | Crear alerta. Body: `{ticker, strategy, condition, threshold, whatsapp_enabled}` |
| GET | `/api/alerts/` | Listar alertas activas |
| DELETE | `/api/alerts/{id}` | Eliminar alerta |
| POST | `/api/alerts/test-whatsapp` | Enviar mensaje de prueba |

### Opciones (`options_router.py`)
| GET | `/api/options/background/status` | Estado + config del background analyzer |
| POST | `/api/options/background/start` | Iniciar |
| POST | `/api/options/background/stop` | Detener |
| POST | `/api/options/background/config` | Configurar: tickers, strategy, interval, periods, min_confidence, alert_whatsapp, run_every_seconds |
| GET | `/api/options/background/results` | Resultados acumulados (query: limit) |
| GET | `/api/options/predictions` | Listar predicciones (query: ticker, limit, offset) |
| GET | `/api/options/predictions/stats` | Estadísticas: total, resolved, correct, pending, accuracy_pct |
| POST | `/api/options/predictions/resolve` | Resolver pendientes (query: count) |
| GET | `/api/options/whatsapp/config` | Estado: `{connected, phone, phone_number}` |
| POST | `/api/options/whatsapp/config` | Guardar número: `?phone_number=...` |
| GET | `/api/options/whatsapp/qr` | QR en base64 `{qr: "data:image/png;base64,..."}` |
| GET | `/api/options/broker/list` | Brokers disponibles |
| GET | `/api/options/broker/status` | Broker activo + connected |
| GET | `/api/options/debug/status` | Debug enabled/disabled |
| POST | `/api/options/debug/toggle` | Toggle debug |
| POST | `/api/options/debug/clear` | Limpiar logs |

### Depuración (`debug_router.py`)
| GET | `/api/debug/` | Dashboard debug (query: show, limit) |
| GET | `/api/debug/live` | Polling live (query: after_id) |
| POST | `/api/debug/toggle` | Toggle |
| POST | `/api/debug/clear` | Clear |

---

## 6. Frontend — Componentes Clave

### Tabs (SPA)
- **Dashboard**: Estado del sistema, datos en tiempo real, órdenes
- **Análisis**: Análisis técnico con indicadores, gráfico multi-panel (precio+BB+EMAs, RSI, MACD), zoom, panel "Asistente de Trading"
- **Alertas**: CRUD de alertas, test WhatsApp
- **Opciones**: Background analyzer, predicciones, config WhatsApp (QR + phone), broker, debug
- **Depuración**: Dashboard de trazabilidad con auto-polling

### Autocomplete (5 campos)
- `createAutocomplete(inputId, dropdownId, onSelect, multi)`
- 50+ tickers precargados en `POPULAR_TICKERS`
- Búsqueda por símbolo o nombre, flechas ↑↓, Enter, Escape
- Modo `multi=true` para bg-tickers (append + dedup)

### Gráficos Chart.js
- **Modal sparkline**: Precio + BB + EMA 9/21, zoom, fill gradient
- **Panel Price**: BB superior/inferior, precio, EMA 9, EMA 21, zoom
- **Panel RSI**: RSI 14 con líneas 30/50/70, fill gradient, zoom
- **Panel MACD**: MACD + señal + histograma (solo swing), zoom

### Modal de Mercado
- Stats: precio, RSI, EMA 9, SMA 200, MACD, BB
- Sparkline con period selector (15/30/60/100/200)
- Análisis técnico integrado (veredicto + confianza + razones)

### Asistente de Trading
- Card "🤖 Asistente de Trading" en tab Análisis
- Se muestra automáticamente al analizar un ticker
- Veredicto BUY/SELL/ACCUMULATE/REDUCE/NEUTRAL
- Confianza %, señales activas, razones detalladas
- Botón 🔍 para ver análisis completo con grid de indicadores

---

## 7. Estrategias de Trading

### Scalping (corto plazo, 1m-5m)
```
Indicadores: EMA 9/21 crossover, RSI 14, Bollinger Bands (20,2)
BUY:  EMA9 cruza arriba EMA21 (+35%) | RSI < 30 (+25%) | Precio ≤ BB inferior (+20%)
SELL: EMA9 cruza abajo EMA21 (+35%) | RSI > 70 (+25%) | Precio ≥ BB superior (+20%)
```

### Swing (largo plazo, 1d)
```
Indicadores: MACD crossover, SMA 200, Soportes/Resistencias
BUY:  MACD cruza arriba señal (+40%) | Precio > SMA 200 (+15%) | Cerca soporte (+20%)
SELL: MACD cruza abajo señal (+40%) | Precio < SMA 200 (-10%) | Cerca resistencia (+20%)
```

---

## 8. WhatsApp Gateway (Self-Hosted)

### Contenedor: `whatsapp-gateway`
- **Puerto**: 3000
- **Lenguaje**: Node.js 20 + ESM
- **Librería**: `@whiskeysockets/baileys` (WhatsApp Web protocol)
- **API**:
  - `GET /status` → `{connected: bool, phone: string|null}`
  - `GET /qr` → `{qr: "data:image/png;base64,..."}` (o 404 si no disponible)
  - `POST /send-message` → body `{to, message}` → `{success: bool}`
- **Sesión persistente**: volumen `whatsapp-session:/app/session`
- **Auto-reconexión**: si se desconecta (excepto loggedOut)

### Backend: `app/services/whatsapp_service.py`
- `check_connection()` → GET /status del gateway
- `get_qr()` → GET /qr del gateway
- `send_alert()` → POST /send-message con phone desde DB o argumento
- `update_phone_number()` → guarda en DB
- `get_config()` → status + phone desde DB
- Sin Twilio, sin dependencias externas de pago

---

## 9. Dependencias

### Python (13 paquetes)
```
fastapi>=0.115.0, uvicorn[standard]>=0.32.0, sqlalchemy>=2.0.36,
asyncpg>=0.30.0, psycopg2-binary>=2.9.10, pydantic>=2.10.0,
pydantic-settings>=2.6.0, yfinance>=0.2.50, pandas>=2.2.0,
numpy>=1.26.0, ta>=0.11.0, requests>=2.32.0, python-dotenv>=1.0.0
```

### Node.js (5 paquetes)
```
@whiskeysockets/baileys@^6.7.10, express@^4.21.0, qrcode@^1.5.4,
pino@^9.5.0, pino-pretty@^11.3.0
```

### CDN
```
Chart.js@4.4.7, chartjs-plugin-zoom@2.0.1
```

---

## 10. Docker

### Servicios (docker-compose.yml)
| Servicio | Puerto | Build | Depende de | Volumen |
|----------|--------|-------|------------|---------|
| api | 8000 | ./Dockerfile | db (healthy), redis, whatsapp-gateway | .:/app |
| whatsapp-gateway | 3000 | ./whatsapp-gateway/Dockerfile | — | whatsapp-session |
| db | 5432 | postgres:16-alpine | — | pgdata |
| redis | 6379 | redis:7-alpine | — | — |

### API Dockerfile
- Multi-stage build (builder + runtime)
- `python:3.12-slim`
- `--workers 1` (evita crash SQLAlchemy por fork)
- `PYTHONPATH=/app`

### Gateway Dockerfile
- `node:20-alpine`
- `apk add --no-cache git` (para dependencias nativas de Baileys)
- `npm install` (sin omitir dev, algunas dependencias lo requieren)

---

## 11. Variables de Entorno (`.env`)

```
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/stockdb
DATABASE_URL_SYNC=postgresql://user:pass@db:5432/stockdb
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
WHATSAPP_GATEWAY_URL=http://whatsapp-gateway:3000
```

---

## 12. Decisiones de Diseño Clave

| Decisión | Razón |
|----------|-------|
| `--workers 1` | SQLAlchemy engine no soporta fork entre workers |
| BrokerManager singleton | Estado global del broker activo, thread-safe |
| BackgroundAnalyzer thread + Event + Lock | Control preciso de inicio/parada sin matar el proceso |
| @timed decorator | Medición automática de performance + error tracking |
| DebugTracker circular buffers (500) | Evita memory leak, mantiene historia útil |
| Lazy imports de WhatsApp | No bloquear startup si el gateway no responde |
| whatsapp-gateway separado | Aislar dependencia Node.js del ecosistema Python |
| chartjs-plugin-zoom v2 | Compatible con Chart.js v4, doble click resetea |
| SPA vanilla sin framework | Cero build step, recarga instantánea con uvicorn --reload |
| `createAutocomplete` con modo multi | Un solo componente para selector simple y multi-ticker |
| Session Baileys en volumen Docker | Persiste QR auth entre reinicios del contenedor |

---

## 13. Estado Actual de Funcionalidades

### Completado
- [x] Multi-broker: Yahoo Finance (funcional), Binance (testnet), IBKR (placeholder)
- [x] Cambio de broker en caliente vía API + GUI
- [x] Análisis técnico Scalping (EMA, RSI, BB) y Swing (MACD, SMA 200, S/R)
- [x] Gráficos Chart.js multi-panel con zoom + pan (rueda, pincha, doble click reset)
- [x] Modal de mercado con sparkline + BB + EMAs
- [x] Asistente de Trading (reglas → veredicto + confianza + razones)
- [x] Background analyzer configurable (tickers, estrategia, intervalo, periodicidad)
- [x] Sistema de predicciones con almacenamiento en DB y resolución automática
- [x] Alertas programables por ticker/estrategia/condición
- [x] WhatsApp Gateway auto-hosteado (Baileys, sin Twilio, sin costo)
- [x] QR code para escanear desde la GUI
- [x] Dashboard de depuración con live polling
- [x] Smart Search con autocomplete (50+ tickers)
- [x] Info popups educacionales con enlaces
- [x] Log de eventos en la interfaz
- [x] Persistencia de sesión WhatsApp entre reinicios Docker

### Pendiente / Mejorable
- [ ] Trading real (API keys de Binance/IBKR)
- [ ] WebSocket para streaming de datos en tiempo real
- [ ] Autenticación JWT + multi-usuario
- [ ] IA avanzada en `app/core/ai_models/`
- [ ] Tests automatizados (solo 3 tests básicos)
- [ ] Migraciones SQLAlchemy (actualmente `create_all()`)
- [ ] Manejo de errores más robusto en gateway (timeouts, reconexión)
- [ ] Dashboard de rendimiento histórico del sistema

---

## 14. Cómo Probar

```bash
# Ver todos los servicios
docker compose ps

# Logs del API
docker compose logs -f api

# Logs del gateway WhatsApp
docker compose logs -f whatsapp-gateway

# Health check
curl http://localhost:8000/health

# Análisis rápido
curl -X POST http://localhost:8000/api/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","strategy":"scalping","interval":"1d","periods":100}'

# WhatsApp status
curl http://localhost:8000/api/options/whatsapp/config

# QR code (base64)
curl http://localhost:8000/api/options/whatsapp/qr

# Guardar número WhatsApp
curl -X POST "http://localhost:8000/api/options/whatsapp/config?phone_number=521234567890"

# Technical analysis
curl -X POST "http://localhost:8000/api/analysis/technical-analysis?ticker=AAPL&strategy=scalping&interval=1d&periods=100"

# Abrir GUI
xdg-open http://localhost:8000/
```

---

## 15. Cómo Continuar el Desarrollo

1. **Nuevo broker**: Crear clase en `app/brokers/`, registrar en `BROKER_MAP` en `broker_manager.py`
2. **Nueva estrategia**: Agregar función en `strategies.py`, integrar en `analysis_service.py`
3. **Nuevo endpoint**: Agregar ruta en el router correspondiente (o crear nuevo router)
4. **Nuevo modelo DB**: Agregar clase en `models.py`, `init_db()` crea la tabla automáticamente
5. **Frontend**: Editar `index.html` (estructura), `styles.css` (estilos), `app.js` (lógica)
6. **Gateway**: Modificar `whatsapp-gateway/index.js` (API Baileys), reconstruir con `docker compose build whatsapp-gateway`

### Comandos frecuentes:
```bash
# Reconstruir todo
docker compose up -d --build

# Solo API
docker compose up -d --build api

# Solo gateway
docker compose up -d --build whatsapp-gateway

# Ver logs
docker compose logs -f api
docker compose logs -f whatsapp-gateway

# Acceder a DB
docker compose exec db psql -U user -d stockdb

# Shell en API
docker compose exec api bash
```

---

## 16. Gotchas y Problemas Conocidos

- **SQLAlchemy fork crash**: NO usar `--workers > 1` en uvicorn. El engine no sobrevive al fork.
- **Schema mismatch**: Si se cambia un modelo, hay que dropear la tabla manualmente (`DROP TABLE ... CASCADE`) y reiniciar. No hay migration system.
- **Baileys QR**: Solo se genera UNA vez si no hay sesión. Si se pierde la sesión (loggedOut), reiniciar el contenedor: `docker compose restart whatsapp-gateway`.
- **Gateway crypto error**: Node.js < 20 causa `crypto is not defined`. Usar `node:20-alpine`.
- **Gateway git dependency**: `apk add --no-cache git` es necesario porque Baileys tira de un repo de protocol buffers.
- **Chart.js zoom**: Si se agregan nuevos charts, recordar incluir `zoom: { pan: {...}, zoom: {...} }` en options.plugins.
- **Event log**: Máximo 100 entradas en memoria. Las más viejas se pierden.
- **Background analyzer**: Si el ticker lista está vacía, usa defaults de 16 tickers populares.
- **CORS**: La GUI y API están en el mismo origen (localhost:8000). Si se separan, actualizar `CORS_ORIGINS` en `.env`.
