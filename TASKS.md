# Stock Analysis — Lista de Tareas

> Estado: 101 tests pasando · Login deshabilitado · Stack: Polars nativo

## ✅ Completado

- [x] Migración pandas+ta → **Polars nativo** (`strategies.py`, `analysis_service.py`)
- [x] **Top ranking** por confianza: endpoint + frontend con chart + indicadores toggleables + botones Comprar/Vender
- [x] **Login deshabilitado**: auth_router no incluido, pantalla auth removida, JS auth removido, tests skip
- [x] **Persistencia background analyzer**: modelo `BackgroundResult` en DB, get_results lee de DB
- [x] **Anchored summaries** activados en opencode.json para no perder contexto entre sesiones
- [x] `estudio/04-python-fastapi.md` actualizado con Polars
- [x] `SKILL.md` actualizado con Polars, top-ranking, login deshabilitado
- [x] Top ranking: paralelización con ThreadPoolExecutor (evita timeouts de red)
- [x] Frontend POPULAR_TICKERS sincronizado con backend

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
