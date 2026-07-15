# Arquitectura General

## Diagrama de alto nivel

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│ Browser  │────▶│  FastAPI     │────▶│ PostgreSQL│
│ :8000    │     │  :8000       │     │ :5432    │
└──────────┘     │              │     └──────────┘
                 │ /api/analysis │     ┌──────────┐
┌──────────┐     │ /api/alerts   │────▶│ Redis    │
│ WhatsApp │◀───▶│ /api/config   │     │ :6379    │
│ Gateway  │     │ /api/options  │     └──────────┘
│ :3000    │     │ /api/debug    │
└──────────┘     │ /api/ml       │
                 └──────┬───────┘
                        │
            ┌───────────┴───────────┐
            │                       │
     ┌──────▼──────┐       ┌───────▼───────┐
     │ Yahoo       │       │ Binance       │
     │ Finance API │       │ REST API      │
     │ (yfinance)  │       │ (kline data)  │
     └─────────────┘       └───────────────┘
```

## Stack

| Capa | Tecnología | Versión | Propósito |
|------|-----------|---------|-----------|
| API Framework | FastAPI | 0.115+ | Rutas HTTP + WebSocket + Pydantic validation |
| ASGI Server | Uvicorn | 0.32+ | `--workers 1` (SQLAlchemy no soporta fork) |
| Estrategias | **Polars nativo** | 1.42+ | Cálculo de indicadores técnicos (sin pandas/ta) |
| ORM | SQLAlchemy | 2.0+ | Mapeo objeto-relacional, 7 tablas |
| DB (dev) | SQLite | — | Archivo local `app.db` |
| DB (prod) | PostgreSQL | 16 | Servicio Docker |
| Cache | Redis | 7 | Reservado (no implementado) |
| Frontend | Vanilla JS | — | SPA, Chart.js 4.4.7, zoom plugin |
| WhatsApp | Baileys | 6.7 | Protocolo WhatsApp Web (Node.js) |
| Data source | yfinance | 0.50+ | Datos históricos y tiempo real gratuitos |
| Linting | Ruff | — | E, F, W, I (line-length 120) |
| Testing | pytest + coverage | — | TestClient, mock, fixture parametrizadas |

## Estructura de directorios

```
stock-analysis/
├── app/                          # Código principal
│   ├── main.py                   # Entry point, lifespan, routers, CORS
│   ├── config.py                 # Settings desde .env (pydantic-settings)
│   ├── database.py               # SQLAlchemy engine + session + init_db()
│   ├── models.py                 # 7 modelos ORM (Prediction, BrokerConfig, etc.)
│   ├── schemas.py                # Pydantic request/response models
│   ├── routers/                  # 6 routers
│   │   ├── analysis_router.py    # POST /analyze, GET /chart, GET /top-ranking, etc.
│   │   ├── alerts_router.py      # CRUD de alertas + test WhatsApp
│   │   ├── auth_router.py        # Auth (NO incluido en main.py)
│   │   ├── config_router.py      # Switch broker, status, list
│   │   ├── debug_router.py       # Debug dashboard, live poll
│   │   └── options_router.py     # Background, predictions, trading, WhatsApp, debug
│   ├── services/                 # Lógica de negocio
│   │   ├── analysis_service.py   # run_analysis() + get_historical_data()
│   │   ├── auth_service.py       # JWT, bcrypt, magic links, Google OAuth
│   │   ├── background_analyzer.py# Thread daemon de análisis automático
│   │   ├── prediction_service.py # CRUD + resolve + stats + trading summary
│   │   ├── technical_analysis.py # Análisis multi-factor por reglas
│   │   ├── whatsapp_service.py   # Cliente del gateway WhatsApp
│   │   └── ws_manager.py         # WebSocket ConnectionManager
│   ├── core/                     # Lógica fundamental
│   │   ├── base_broker.py        # ABC + BrokerConfig dataclass
│   │   ├── broker_manager.py     # Singleton, switch con rollback
│   │   ├── chart_registry.py     # ChartDef registry + tests parametrizados
│   │   ├── debug.py              # DebugTracker singleton + @timed + DebugMiddleware
│   │   └── strategies.py         # scalping_signals(), swing_signals(), _rsi(), _find_levels()
│   ├── brokers/                  # Implementaciones de brokers
│   │   ├── yahoo_finance.py      # Yahoo Finance (funcional)
│   │   ├── binance.py            # Binance testnet (conecta + data)
│   │   └── interactive_brokers.py# IBKR (placeholder)
│   └── static/                   # Frontend SPA
│       ├── index.html            # 5 tabs, modals, estructura HTML
│       ├── app.js                # 1700 líneas de JS vanilla
│       └── styles.css            # Tema oscuro GitHub-inspired
├── whatsapp-gateway/             # Gateway Node.js auto-hosteado
│   ├── index.js                  # Baileys + Express + QR
│   ├── package.json              # Dependencias
│   └── Dockerfile                # node:20-alpine
├── tests/                        # 17 archivos, 113 tests
│   ├── conftest.py               # Fixtures globales
│   ├── test_main.py              # 6 tests
│   ├── test_strategies.py        # 11 tests
│   ├── test_analysis_router.py   # 8 tests
│   ├── test_charts.py            # 11 tests (parametrizados)
│   └── ... (12 archivos más)
├── docs/                         # Documentación técnica
│   ├── architecture.md           # Este archivo
│   ├── api-reference.md          # Referencia de API
│   ├── indicators.md             # Fórmulas de indicadores
│   ├── whatsapp-gateway.md       # Gateway WhatsApp
│   ├── frontend.md               # Frontend SPA
│   ├── deployment.md             # Docker + CI/CD
│   └── ci-cd-guide.md            # Guía educativa CI/CD
├── .opencode/                    # Configuración de opencode
│   ├── context.md                # Boot context de cada sesión
│   └── skills/stock-analysis/    # Skill del proyecto
│       └── SKILL.md              # Plan, convenciones, workflow
├── docker-compose.yml            # 4 servicios (api, gateway, db, redis)
├── Dockerfile                    # Multi-stage build de la API
├── requirements.txt              # Dependencias Python
├── .env                          # Config local (gitignorado)
├── .env.example                  # Template de configuración
├── CHANGELOG                     # Historial de cambios
└── TASKS.md                      # Lista de tareas
```

## Flujo de datos end-to-end

### Análisis individual
```
Cliente → POST /api/analysis/analyze { ticker, strategy, interval, periods }
  │
  ├── analysis_router.py:analyze()
  │   Valida con AnalysisRequest (schemas.py)
  │
  ├── analysis_service.py:run_analysis()
  │   @timed decorator (debug.py)
  │   │
  │   ├── get_historical_data(ticker, interval, periods)
  │   │   BrokerManager → YahooFinanceBroker
  │   │   yf.Ticker(ticker).history(period, interval) → pandas
  │   │   pl.from_pandas() → Polars DataFrame
  │   │
  │   ├── scalping_signals(df) o swing_signals(df)
  │   │   Estrategia pura en Polars (sin dependencias externas)
  │   │   Retorna { signal, confidence, indicators, reasons }
  │   │
  │   ├── debug.track_strategy() → DebugTracker en memoria
  │   │
  │   └── store_prediction() → DB (prediction_service.py)
  │       Si notify=True y señal BUY/SELL → send_alert() vía WhatsApp
  │
  └── AnalysisResponse { signal, confidence, indicators, reasons, ... }
```

### Top ranking (paralelo)
```
Cliente → GET /api/analysis/top-ranking?tickers=AAPL,MSFT,...
  │
  ├── analysis_router.py:top_ranking()
  │   ThreadPoolExecutor(max_workers=6)
  │   as_completed(...FIRST_COMPLETED, timeout=90)
  │   │
  │   ├── run_analysis(ticker) para CADA ticker en paralelo
  │   │   └── Cada uno: fetch data → estrategia → predicción
  │   │
  │   └── Ordena resultados por confidence descendente
  │
  └── { "rankings": [ { ticker, signal, confidence, ... }, ... ] }
```

### Background analyzer (loop automático)
```
background_analyzer.py:_loop()
  │
  └── Cada `run_every_seconds` (default 300):
      │
      ├── _run_cycle()
      │   │
      │   ├── Para cada ticker configurado:
      │   │   run_analysis(ticker) → signal + confidence
      │   │   Si confidence >= min_confidence → store_prediction()
      │   │   Si alert_whatsapp y señal BUY/SELL → send_alert()
      │   │
      │   ├── resolve_predictions() → revisa predicciones pendientes
      │   │
      │   ├── Guarda batch_results en BackgroundResult (DB)
      │   │
      │   └── ws_manager.broadcast() → WebSocket a todos los clientes
```

## Patrones de diseño

| Patrón | Implementación | Archivo |
|--------|---------------|---------|
| **Singleton** | `__new__` override | BrokerManager, DebugTracker, BackgroundAnalyzer, ConnectionManager |
| **Abstract Base Class** | `ABC` + abstractmethods | `base_broker.py` (BaseBroker) |
| **Strategy** | `scalping_signals()` / `swing_signals()` | `strategies.py` |
| **Registry** | `register_chart()` / `get_registered_charts()` | `chart_registry.py` |
| **Middleware** | ASGI middleware class | `debug.py` (DebugMiddleware) |
| **Decorator** | `@timed` para medición + error tracking | `debug.py` |
| **Bridge** | yfinance → pandas → pl.from_pandas() → Polars | `analysis_service.py` |
| **Proxy** | `whatsapp_qr()` → `whatsapp_service.get_qr()` → gateway HTTP | `options_router.py` |

## Reglas críticas

1. **`--workers 1`**: SQLAlchemy no soporta fork de procesos. Usar 1 worker siempre.
2. **Sin AVX/AVX2**: Esta CPU no soporta instrucciones vectoriales. Usar `polars[rtcompat]`.
3. **DB migrations**: No hay Alembic. Si se cambia el modelo, dropear tabla manualmente.
4. **Único punto de storage**: Todo análisis pasa por `run_analysis()` para guardar predicciones.
5. **Resiliencia**: Ningún endpoint debe devolver 500 por datos faltantes. Siempre respuesta válida con `reasons`.

## Tests Suite

297 tests Pytest, 2 skip (auth). Coberturas clave:

| Módulo | Tests | Cobertura |
|--------|-------|-----------|
| `background_analyzer.py` | 34 | **100%** |
| `prediction_service.py` | 20+ | **98%** |
| `strategies.py` | 55+ | Lógica real (RSI, EMA cross, SMA cross) |
| `analysis_service.py` | 5 | 92% |
| `analysis_router.py` | 15 | Endpoints + paralelización |
| `brokers.py` | 15 | Yahoo + Binance + fallback |
| `websocket.py` | 4 | Connect + broadcast + multiple clients |
| `docker_compose.py` | 12 | YML + Dockerfiles |

Todos los tests corren con SQLite (no requieren PostgreSQL).
