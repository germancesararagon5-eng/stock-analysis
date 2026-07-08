# Stock Analysis — Boot Context

## Quick Start
```bash
docker compose up -d --build
# Open http://localhost:8000
```

## Stack
Python 3.12 + FastAPI + SQLAlchemy + PostgreSQL + Redis + Node.js 20 (Baileys) + Chart.js 4.4.7

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

## DB Models (4 tablas)
- broker_configs — credenciales de brokers
- alert_configs — alertas programadas por ticker
- predictions — señales almacenadas + resolución automática
- whatsapp_configs — solo phone_number + connected

## Key Files
- app/services/whatsapp_service.py — HTTP al gateway (sin Twilio)
- app/core/strategies.py — scalping_signals(), swing_signals(), compute_chart_data()
- app/services/technical_analysis.py — motor de reglas multi-indicador
- app/services/background_analyzer.py — thread daemon configurable
- app/services/prediction_service.py — CRUD + resolve + stats
- whatsapp-gateway/index.js — Baileys + Express + QRCode

## Critical Rules
- --workers 1 (SQLAlchemy no soporta fork)
- whatsapp-gateway necesita node:20-alpine (crypto global)
- Si se cambia modelo DB, dropear tabla manualmente (no hay migrations)
- Doble click en charts resetea zoom
- Background analyzer usa lock + event para thread seguro

## Frontend (SPA vanilla)
- 5 tabs: Dashboard · Análisis · Alertas · Opciones · Depuración
- Autocomplete en 5 inputs, modo multi para bg-tickers
- Chart.js con zoom plugin en todos los gráficos
- Modal de mercado con análisis técnico integrado
- Event log flotante abajo-derecha (max 100)

## LEARN.md
Contiene documentación exhaustiva: arquitectura, endpoints, DB schema, decisiones, estado. Leer para contexto completo.
