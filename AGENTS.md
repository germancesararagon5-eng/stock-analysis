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
  - `routers/` — config, analysis, alerts, debug, options, ml
  - `services/` — analysis_service, background_analyzer, prediction_service, ml_service, technical_analysis, whatsapp_service
  - `core/` — strategies.py (indicadores Polars nativos), broker_manager, chart_registry, debug
  - `models.py` — DB models (broker_configs, alert_configs, predictions, background_results, whatsapp_configs)
  - `static/` — Frontend SPA vanilla (5 tabs + theme modes)
- `tests/` — 297 tests Pytest
- `docs/` — architecture, api-reference, indicators, deployment, frontend, whatsapp-gateway
- `whatsapp-gateway/` — Node.js + Baileys WhatsApp gateway

## Workflow (leer después de cada cambio)
1. Implementar cambios
2. `pytest -v` (verificar tests pasando)
3. `ruff check .` (lint)
4. Actualizar `CHANGELOG`
5. Actualizar `TASKS.md` (marcar completados, mover prioridades)
6. Actualizar `AGENTS.md` (test count, estado)
7. `git add -A && git commit -m "tipo: descripcion"`
8. `git push origin main`

## Critical Rules
- `--workers 1` (SQLAlchemy no soporta fork)
- CPU sin AVX/AVX2 → `POLARS_SKIP_CPU_CHECK=1`, usar polars[rtcompat]
- pl.from_pandas requiere pyarrow, filtrar columnas OHLCV (Dividends/Stock Splits rompen conversión)
- No hay migrations DB — dropear tabla manualmente si se cambia modelo
- Login deshabilitado temporalmente (auth_router no incluido en main.py)
- Background analyzer usa lock + event + ThreadPoolExecutor para thread seguro
- Double click en charts resetea zoom

## Tests
- 297 tests pasando, 2 skip (auth)
- Cobertura: background_analyzer 100%, prediction_service 98%, analysis_service 92%
- Tests clave: test_strategies.py (50+), test_background_result.py (9), test_background_analyzer.py (34)
- Auth tests: skip (login deshabilitado)

## Documentación
- `README.md` — Manual completo de la app
- `docs/` — Documentación por área
- `TASKS.md` — Lista de tareas y prioridades
- `.opencode/context.md` — Boot context detallado
- `CHANGELOG` — Historial de versiones

## Próximos pasos prioritarios
1. Entrenar modelo ML con dataset de analysis_results
2. Backtesting ML vs estrategias clásicas
