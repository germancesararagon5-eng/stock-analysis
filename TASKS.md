# Stock Analysis — Lista de Tareas

> Estado: 304 tests pasando · Login deshabilitado · Stack: Polars nativo · ML: RandomForest · v2.5.0

## ✅ Completado

- [x] Migración pandas+ta → **Polars nativo** (`strategies.py`, `analysis_service.py`)
- [x] **Top ranking** por confianza: endpoint + frontend con chart + indicadores toggleables + botones Comprar/Vender
- [x] **Login deshabilitado**: auth_router no incluido, pantalla auth removida, JS auth removido, tests skip
- [x] **Persistencia background analyzer**: modelo `BackgroundResult` en DB, get_results lee de DB
- [x] **Predicciones automáticas**: todo análisis se guarda como predicción en DB (store_prediction=True)
- [x] **Simulador de trading**: panel P&L, win rate, profit factor, historial en frontend
- [x] **P&L tracking**: cada predicción resuelta calcula ganancia/pérdida simulada
- [x] **Anchored summaries** activados en opencode.json para no perder contexto entre sesiones
- [x] `estudio/04-python-fastapi.md` actualizado con Polars y ThreadPoolExecutor
- [x] `SKILL.md` actualizado con Polars, top-ranking, login deshabilitado
- [x] Top ranking: paralelización con ThreadPoolExecutor (evita timeouts de red)
- [x] Frontend POPULAR_TICKERS sincronizado con backend
- [x] **Chart endpoint resiliente**: try/except en GET /api/analysis/chart/{ticker} — retorna series vacías + error en vez de 500
- [x] **Sparkline error real**: drawSparkline muestra el error del backend en vez de "Datos insuficientes" genérico
- [x] **Top-ranking click-through consistente**: el click pasa periods=100 al formulario de análisis
- [x] **Predicciones centralizadas**: run_analysis() es el único punto de almacenamiento para todas las rutas
- [x] **Chart Registry** (`app/core/chart_registry.py`): todos los charts registrados con ChartDef
- [x] **Chart tests parametrizados** (`tests/test_charts.py`): 11 tests (estructura, vacío, error, coherencia)
- [x] **Frontend api() robusta**: valida Content-Type antes de JSON.parse()
- [x] **try/except en technical_analysis endpoint**: evita 500 con datos faltantes
- [x] **compute_chart_data timestamp alignment**: timestamps se filtran cuando close tiene None
- [x] **SKILL.md**: nuevo workflow (análisis → plan → implementación → self-review → test loop → documentar → commit → push)
- [x] **Broker default en startup**: si no hay broker en DB, usa yahoo_finance automáticamente
- [x] **try/except en GET /api/analysis/data/{ticker} y POST /api/analysis/analyze**: evitan 500 si no hay broker o datos
- [x] **compute_chart_data datetime→str**: convierte datetime a ISO string para que Pydantic valide correctamente
- [x] **test de regresión con datetime timestamps**: chart endpoint no crashea cuando timestamps son datetime objects

## ✅ Completado (documentación)

- [x] `docs/architecture.md` — arquitectura general, flujo end-to-end, patrones
- [x] `docs/api-reference.md` — 55+ endpoints, schemas, mapeo de intervalos, POPULAR_TICKERS
- [x] `docs/indicators.md` — fórmulas de EMA, RSI, Bollinger, MACD, SMA200, S/R, scoring TA
- [x] `docs/whatsapp-gateway.md` — gateway Node.js + Baileys, ciclo de QR, endpoints, troubleshooting
- [x] `docs/frontend.md` — SPA vanilla, Chart.js, WebSocket, funciones clave, chart registry
- [x] `docs/deployment.md` — Docker, desarrollo local, CI/CD, env vars, troubleshooting
- [x] `SKILL.md` actualizado con stack completo (Node.js 22, Python 3.13), convenciones, estado v2.2.0

## ✅ Completado (v2.4.0)

- [x] **Tests de lógica real para estrategias**: RSI<30→sobrevendido, RSI>70→sobrecomprado, EMA golden/death cross, SMA golden/death cross
- [x] **Tests de persistencia BackgroundResult**: 9 tests (creación, campos, timestamps, índices, eliminación)
- [x] **Cobertura prediction_service 61%→98%**: resolución BUY/SELL/NEUTRAL, threshold, rollback, PnL accumulation
- [x] **Fix timezone en resolve_predictions**: `now` naive UTC para compatibilidad SQLite
- [x] **Tests de paralelización en top-ranking**: error parcial, filtro NEUTRAL+0, todos fallan, defaults, ticker único, ordenamiento, todos neutral

## Alta Prioridad

- [x] Entrenar modelo ML con dataset de analysis_results (RandomForest, scikit-learn)
- [x] Backtesting: comparar señales de ML vs señales de estrategias clásicas (GET /api/ml/backtest)

## Media Prioridad

- [x] Subir cobertura `background_analyzer.py` (100%)
- [x] Tests de integración con broker (yahoo_finance): Yahoo path, Binance auto-detection, fallback, OHLCV filter, unsupported broker
- [x] Tests de WebSocket (ws_manager): connect/disconnect, broadcast receive, multiple clients, empty data
- [ ] Tests de frontend (JavaScript con Playwright)

## Baja Prioridad

- [ ] Documentación OpenAPI (Swagger)
- [x] Docker compose tests: 12 tests (compose YML válido, servicios requeridos, puertos, volúmenes, Dockerfiles)
