# Stock Analysis

## Stack
Python 3.12 + FastAPI + SQLAlchemy + PostgreSQL + **Polars nativo** + Redis + Node.js 20 (Baileys WhatsApp) + Chart.js 4.4.7

## Quick Start
```bash
docker compose up -d --build
# Open http://localhost:8000
```

## Services
- `api` :8000 — FastAPI (--workers 1, no fork)
- `whatsapp-gateway` :3000 — Node.js + Baileys (volumen whatsapp-session)
- `db` :5432 — PostgreSQL 16 (volumen pgdata)
- `redis` :6379 — Redis 7

## Project Structure
- `app/` — Backend Python/FastAPI
  - `routers/` — config, analysis, alerts, debug, options
  - `services/` — technical_analysis, analysis_service, background_analyzer, prediction_service
  - `core/` — strategies.py (indicadores Polars nativos)
  - `models.py` — DB models (broker_configs, alert_configs, predictions, background_results, whatsapp_configs)
  - `static/` — Frontend SPA vanilla (5 tabs: Dashboard, Análisis, Alertas, Opciones, Depuración)
- `tests/` — Pytest tests
- `docs/` — architecture, api-reference, indicators, deployment, frontend, whatsapp-gateway
- `whatsapp-gateway/` — Node.js + Baileys WhatsApp gateway

## Critical Rules
- `--workers 1` (SQLAlchemy no soporta fork)
- CPU sin AVX/AVX2 → `POLARS_SKIP_CPU_CHECK=1`, usar polars[rtcompat]
- pl.from_pandas requiere pyarrow, filtrar columnas OHLCV
- No hay migrations DB — dropear tabla manualmente si se cambia modelo
- Login deshabilitado temporalmente (auth_router no incluido en main.py)
- Background analyzer usa lock + event para thread seguro

## Key Commands
```bash
docker compose up -d --build       # Levantar todo
pytest -v                           # Tests
pytest tests/test_charts.py -v      # Chart tests
ruff check .                        # Lint
```

## Tests
- 258 tests pasando
- `test_strategies.py` — 50+ tests (lógica real incluida: RSI<30→BUY, EMA cross, SMA cross)
- `test_background_result.py` — 9 tests de persistencia
- `test_prediction_service_coverage.py` — coverage 98%
- Auth tests: skip (login deshabilitado)

## Contexto adicional
- `TASKS.md` — lista de tareas y prioridades
- `.opencode/context.md` — boot context detallado
- `docs/` — documentación por área

## Próximos pasos prioritarios
1. Tests de lógica de paralelización en top-ranking
2. Entrenar modelo ML con dataset de analysis_results
3. Backtesting ML vs estrategias clásicas
4. Tests de background_analyzer, integración broker, WebSocket
