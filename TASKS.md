# Stock Analysis — Lista de Tareas

> Estado: 106 tests pasando · Cobertura 84%

## Alta Prioridad

- [ ] Tests de lógica real para estrategias (scalping y swing)
  - RSI < 30 → señal BUY + razón "sobrevendido"
  - RSI > 70 → señal SELL + razón "sobrecomprado"
  - EMA9 > EMA21 (golden cross) → BUY
  - EMA9 < EMA21 (death cross) → SELL
- [ ] Subir cobertura `prediction_service.py` (61%)
- [ ] Subir cobertura `technical_analysis.py` (64%)

## Media Prioridad

- [ ] Subir cobertura `background_analyzer.py` (76%)
- [ ] Tests de integración con broker (yahoo_finance)
- [ ] Tests de WebSocket (ws_manager)
- [ ] Tests de autenticación (auth_router + auth_service)

## Baja Prioridad

- [ ] Tests de frontend (JavaScript)
- [ ] Documentación OpenAPI
- [ ] Docker compose tests
