# Stock Analysis — Boot Context

## Quick Start
```bash
docker compose up -d --build
# Open http://localhost:8000
```

## Stack
Python 3.12 + FastAPI + SQLAlchemy + PostgreSQL + **Polars nativo** + Redis + Node.js 20 (Baileys) + Chart.js 4.4.7 + **scikit-learn (RandomForest ML)**

## Services (docker-compose.yml)
- `api` :8000 — FastAPI (--workers 1, no fork)
- `whatsapp-gateway` :3000 — Node.js + Baileys (volumen whatsapp-session)
- `db` :5432 — PostgreSQL 16 (volumen pgdata)
- `redis` :6379 — Redis 7 (reservado)

## API Endpoints (40 total)
| Area | File | Prefix |
|------|------|--------|
| Config | config_router.py | /api/config/ |
| Analysis | analysis_router.py | /api/analysis/ |
| Alerts | alerts_router.py | /api/alerts/ |
| Debug | debug_router.py | /api/debug/ |
| Options | options_router.py | /api/options/ |
| ML | ml_router.py | /api/ml/ |
| Admin | admin_router.py | /api/admin/ |

Key: POST /api/analysis/technical-analysis (reglas → verdict+confidence+reasons), GET /api/options/whatsapp/qr (base64 QR), POST /api/ml/train (RandomForest), GET /api/ml/backtest (ML vs clásicas), GET /api/admin/status (todos los servicios + data flow)

## DB Models (5 tablas)
- broker_configs — credenciales de brokers
- alert_configs — alertas programadas por ticker
- predictions — señales almacenadas + resolución automática
- whatsapp_configs — solo phone_number + connected
- **background_results** — resultados persistentes del background analyzer (ya no se pierden al reiniciar)
- **analysis_results** — dataset ML con 15 features + outcome WIN/LOSS

## Key Files
- app/core/strategies.py — indicadores **Polars nativos**: ewm_mean, rolling_mean, rolling_std; scalping_signals(), swing_signals(), compute_chart_data(), find_levels(), top_ranking()
- app/services/technical_analysis.py — motor de reglas multi-indicador
- app/services/analysis_service.py — get_historical_data() devuelve pl.DataFrame, filtro OHLCV + pyarrow
- app/services/background_analyzer.py — thread daemon, ahora persiste resultados en DB (BackgroundResult)
- app/services/prediction_service.py — CRUD + resolve + stats
- app/services/ml_service.py — store_analysis_result(), resolve_outcomes(), export_dataset(), train_model(), predict_outcome(), backtest_comparison()
- app/services/admin_service.py — get_service_status() agrega estado de todos los servicios + data flow
- app/routers/admin_router.py — GET /api/admin/status
- whatsapp-gateway/index.js — Baileys + Express + QRCode
- app/models.py — BackgroundResult + AnalysisResult agregados (ticker, signal, confidence, price, strategy, 15 features ML, outcome)

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
- 6 tabs: Dashboard · Análisis · Alertas · Opciones · Admin · Depuración
- Autocomplete en 5 inputs, modo multi para bg-tickers
- Chart.js con zoom plugin en todos los gráficos
- Modal de mercado con análisis técnico integrado
- Event log flotante abajo-derecha (max 100)
- **Top ranking**: pestaña Análisis → cards por confianza, click → chart + indicadores toggleables (BB, EMA9, EMA21, RSI, MACD) + botones Comprar/Vender

## Última sesión (2026-07-14)
### Completado
- **Migración pandas+ta → Polars nativo**: strategies.py y analysis_service.py reescritos con pl.Expr nativas
- **Top ranking**: GET /api/analysis/top-ranking, frontend con cards + chart + toggles + buy/sell
- **Login deshabilitado**: router, pantalla, JS auth removidos; tests skip
- **Persistencia BackgroundResult**: modelo en DB, _run_cycle guarda batch_results, get_results lee de DB
- **Documentación**: CHANGELOG 1.5.0 + 1.6.0, TASKS.md actualizado, estudio/04 y 05 actualizados, SKILL.md actualizado
- **ML Backtesting**: RandomForest entrenado con indicators→outcome, comparación 6 estrategias vs ML
- **Admin unificada**: GET /api/admin/status con estado de todos los servicios + data flow pipeline visual
- Tests: 304 pasando, 2 skip (auth)

### Próximos pasos
- **[ALTA]** Tests de lógica real para estrategias (RSI <30→BUY, RSI >70→SELL, golden/death cross)
- **[ALTA]** Subir cobertura prediction_service (61%)
- **[MEDIA]** background_analyzer coverage, WebSocket tests, integración broker
- **[BAJA]** Frontend tests (Playwright), OpenAPI/Swagger, Docker compose tests
- **[MEDIA]** Persistencia de modelo ML en disco (pickle) para no perderlo al reiniciar

Ver `TASKS.md` para lista completa actualizada.
