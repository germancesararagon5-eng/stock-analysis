# Stock Analysis — Lista de Tareas

> Estado: 101 tests pasando · Login deshabilitado · Stack: Polars nativo · v2.1.0

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

## Alta Prioridad

- [ ] Tests de lógica real para estrategias (scalping y swing con Polars)
  - RSI < 30 → señal BUY + razón "sobrevendido"
  - RSI > 70 → señal SELL + razón "sobrecomprado"
  - EMA9 > EMA21 (golden cross) → BUY
  - EMA9 < EMA21 (death cross) → SELL
- [ ] Tests de persistencia BackgroundResult (modelo nuevo, 0 tests)
- [ ] Subir cobertura `prediction_service.py` (61%)
- [ ] Tests de lógica de paralelización en top-ranking

## Media Prioridad

- [ ] Subir cobertura `background_analyzer.py`
- [ ] Tests de integración con broker (yahoo_finance)
- [ ] Tests de WebSocket (ws_manager)
- [ ] Tests de frontend (JavaScript con Playwright)

## Baja Prioridad

- [ ] Documentación OpenAPI (Swagger)
- [ ] Docker compose tests
