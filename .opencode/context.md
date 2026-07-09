# Stock Analysis — Boot Context

## Quick Start
```bash
docker compose up -d --build
# Open http://localhost:8000
```

## Stack
Python 3.12 + FastAPI + SQLAlchemy + PostgreSQL + **Polars nativo** + Redis + Node.js 20 (Baileys) + Chart.js 4.4.7

## Services (docker-compose.yml)
- `api` :8000 — FastAPI (--workers 1, no fork)
- `whatsapp-gateway` :3000 — Node.js + Baileys (volumen whatsapp-session)
- `db` :5432 — PostgreSQL 16 (volumen pgdata)
- `redis` :6379 — Redis 7 (reservado)

## API Endpoints (36 total)
| Area | File | Prefix |
|------|------|--------|
| Config | config_router.py | /api/config/ |
| Analysis | analysis_router.py | /api/analysis/ |
| Alerts | alerts_router.py | /api/alerts/ |
| Debug | debug_router.py | /api/debug/ |
| Options | options_router.py | /api/options/ |

Key: POST /api/analysis/technical-analysis (reglas → verdict+confidence+reasons), GET /api/options/whatsapp/qr (base64 QR)

## DB Models (5 tablas)
- broker_configs — credenciales de brokers
- alert_configs — alertas programadas por ticker
- predictions — señales almacenadas + resolución automática
- whatsapp_configs — solo phone_number + connected
- **background_results** — resultados persistentes del background analyzer (ya no se pierden al reiniciar)

## Key Files
- app/core/strategies.py — indicadores **Polars nativos**: ewm_mean, rolling_mean, rolling_std; scalping_signals(), swing_signals(), compute_chart_data(), find_levels(), top_ranking()
- app/services/technical_analysis.py — motor de reglas multi-indicador
- app/services/analysis_service.py — get_historical_data() devuelve pl.DataFrame, filtro OHLCV + pyarrow
- app/services/background_analyzer.py — thread daemon, ahora persiste resultados en DB (BackgroundResult)
- app/services/prediction_service.py — CRUD + resolve + stats
- whatsapp-gateway/index.js — Baileys + Express + QRCode
- app/models.py — BackgroundResult agregado (ticker, signal, confidence, price, strategy, interval, periods, error, created_at)

## Critical Rules
- --workers 1 (SQLAlchemy no soporta fork)
- whatsapp-gateway necesita node:20-alpine (crypto global)
- CPU sin AVX/AVX2 → POLARS_SKIP_CPU_CHECK=1 (ya en conftest.py), usar polars[rtcompat]
- pl.from_pandas requiere pyarrow, filtrar columnas OHLCV (Dividends/Stock Splits rompen conversión)
- Si se cambia modelo DB, dropear tabla manualmente (no hay migrations)
- Doble click en charts resetea zoom
- Background analyzer usa lock + event para thread seguro
- **Login deshabilitado temporalmente** (auth_router no incluido en main.py)

## Frontend (SPA vanilla)
- 5 tabs: Dashboard · Análisis · Alertas · Opciones · Depuración
- Autocomplete en 5 inputs, modo multi para bg-tickers
- Chart.js con zoom plugin en todos los gráficos
- Modal de mercado con análisis técnico integrado
- Event log flotante abajo-derecha (max 100)
- **Top ranking**: pestaña Análisis → cards por confianza, click → chart + indicadores toggleables (BB, EMA9, EMA21, RSI, MACD) + botones Comprar/Vender

## Última sesión (2026-07-09)
### Completado
- **Migración pandas+ta → Polars nativo**: strategies.py y analysis_service.py reescritos con pl.Expr nativas
- **Top ranking**: GET /api/analysis/top-ranking, frontend con cards + chart + toggles + buy/sell
- **Login deshabilitado**: router, pantalla, JS auth removidos; tests skip
- **Persistencia BackgroundResult**: modelo en DB, _run_cycle guarda batch_results, get_results lee de DB
- **Documentación**: CHANGELOG 1.5.0 + 1.6.0, TASKS.md actualizado, estudio/04 y 05 actualizados, SKILL.md actualizado
- Tests: 101 pasando, 3 top-ranking nuevos, 5 skip auth

### Próximos pasos
- **[ALTA]** Tests de lógica real para estrategias (RSI <30→BUY, RSI >70→SELL, golden/death cross)
- **[ALTA]** Tests de top-ranking endpoint + persistencia BackgroundResult
- **[ALTA]** Subir cobertura prediction_service (61%)
- **[MEDIA]** background_analyzer coverage, WebSocket tests, integración broker
- **[BAJA]** Frontend tests (Playwright), OpenAPI/Swagger, Docker compose tests

Ver `TASKS.md` para lista completa actualizada.
