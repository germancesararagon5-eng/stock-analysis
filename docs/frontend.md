# Frontend SPA

Archivos: `app/static/index.html` (643 líneas), `app/static/app.js` (1698 líneas), `app/static/styles.css` (266 líneas)

## Stack

| Componente | Tecnología |
|------------|-----------|
| Framework | Vanilla JS (sin React/Vue) |
| Charts | Chart.js 4.4.7 + chartjs-plugin-zoom |
| CSS | Tema oscuro custom (GitHub-inspired dark) |
| Comunicación | Fetch API + WebSocket |
| Estado | Global variables (sin store) |

## Estructura de la SPA

### index.html — 6 tabs principales

```
┌──────────────────────────────────────────────────┐
│  Header: Logo + Navigation (6 tabs)               │
├──────────────────────────────────────────────────┤
│                                                   │
│  Tab 1: Dashboard                                 │
│   ├── Ticker autocomplete (single)                │
│   ├── Modal de mercado (price + sparkline + TA)   │
│   └── Live event log (flotante abajo-derecha)     │
│                                                   │
│  Tab 2: Análisis                                   │
│   ├── Ticker autocomplete + strategy + interval   │
│   ├── Resultado: señal, confianza, indicadores    │
│   ├── Botones Comprar/Vender (simulado)           │
│   ├── Multi-panel charts (price+BB+EMA, RSI, MACD)│
│   └── Top ranking (cards por confianza)           │
│                                                   │
│  Tab 3: Alertas                                   │
│   ├── Crear alerta (ticker, strategy, condition)  │
│   ├── Lista de alertas activas                    │
│   └── Test WhatsApp                               │
│                                                   │
│  Tab 4: Opciones                                  │
│   ├── Background analyzer (start/stop/config)     │
│   ├── ML Backtesting (train + compare)            │
│   ├── Predicciones (stats + historial + resolve)  │
│   ├── Trading simulator (P&L, win rate)           │
│   ├── WhatsApp config (QR + phone number)          │
│   ├── Broker config (switch + status)             │
│   └── Debug toggle                                │
│                                                   │
│  Tab 5: Admin                                     │
│   ├── API status (version, uptime)                │
│   ├── DB status (tables, records)                 │
│   ├── Redis status                                 │
│   ├── WhatsApp connection                          │
│   ├── Background analyzer status                   │
│   ├── ML Model status                              │
│   ├── Broker status                                │
│   └── Debug status                                 │
│                                                   │
│  Tab 6: Depuración                                │
│   ├── Live polling de requests                    │
│   ├── Strategy evaluations                        │
│   ├── Broker events                               │
│   └── Errores                                     │
│                                                   │
└──────────────────────────────────────────────────┘
```

### app.js — Funciones clave

```javascript
// Comunicación con API
api(method, path, body)
  → Valida Content-Type: application/json antes de JSON.parse()
  → Evita error "unexpected character line 1"

// WebSocket
connectWebSocket()
  → Conexión a WS /api/ws
  → Auto-reconexión cada 5 segundos si se pierde
  → Recibe broadcasts del background analyzer

// Autocomplete
createAutocomplete(inputId, dropdownId, onSelect, multi)
  → Busca en POPULAR_TICKERS (44 tickers)
  → Navegación por teclado (↑↓ Enter)
  → Modo multi-ticker para background analyzer

// Charts
drawSparkline(ticker)              → Chart en modal de mercado
fetchChart(ticker, strategy, interval, periods, visible) → Multi-panel analysis
  → Panel 1: Price + EMAs + Bollinger Bands (con relleno gradiente)
  → Panel 2: RSI con niveles 30/70
  → Panel 3: MACD + Signal + Histograma
  → Toggle de indicadores (BB, EMA9, EMA21, RSI, MACD)
  → Doble click resetea zoom

// Análisis
runAnalysis()            → POST /api/analysis/analyze
showAnalysisResult(r)    → Renderiza badge, indicadores, razones
showMarketModal(ticker)  → Modal con datos en tiempo real + sparkline + TA

// Top ranking
loadTopRanking()
  → GET /api/analysis/top-ranking?tickers=...
  → Renderiza cards con barra de confianza
  → Click → abre chart + indicadores en panel lateral

// Alertas
loadAlerts(), createAlert(), deleteAlert(), testWhatsApp()

// Opciones
loadOptions()                    → Carga todos los paneles
toggleBackgroundAnalyzer()       → Start/Stop
configureBackgroundAnalyzer()    → Config (tickers, strategy, etc.)
loadWhatsAppConfig()             → Estado + QR + número
loadQRCode()                     → GET /api/options/whatsapp/qr (refresh periódico)
saveWhatsAppConfig()             → Guarda número
loadPredictionStats()            → Estadísticas de predicciones
loadPredictions()                → Historial paginado
resolvePendingPredictions()      → Resolver manualmente
loadTradingSummary(ticker)       → P&L, win rate, profit factor

// Debug
loadDebug(), toggleDebug(), clearDebug()
```

### Constantes

```javascript
POPULAR_TICKERS = [
  "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
  "AMD", "INTC", "NFLX", "DIS", "BA", "NKE", "JPM", "V", "MA",
  "COST", "WMT", "HD", "PG", "KO", "PEP", "XOM", "CVX", "JNJ",
  "PFE", "MRK", "ABBV",
  "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD",
  "ADA-USD", "DOT-USD", "MATIC-USD",
  "^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX",
  "ES=F", "NQ=F", "YM=F", "CL=F", "GC=F"
]

CHART_COLORS = { price: '#4CAF50', ema9: '#FF9800', ema21: '#2196F3', ... }

INFO = { tooltips definitions for indicator explanations }
```

### styles.css — Tema oscuro

- Color scheme: GitHub-inspired dark (#0d1117 fondo, #c9d1d9 texto)
- Cards con bordes #30363d
- Badges de señal: BUY (verde), SELL (rojo), NEUTRAL (gris)
- Barras de confianza: gradiente verde-rojo
- Inputs, botones, dropdowns con estilo consistente
- Toggle switch para debug
- Animaciones sutiles en hover

## WebSocket

El frontend mantiene una conexión WebSocket permanente para recibir actualizaciones:

```
1. initApp() llama a connectWebSocket()
2. Abre conexión a ws://localhost:8000/api/ws
3. Si se cierra, reintenta cada 5 segundos
4. Al recibir mensaje JSON:
   - Si tiene type: "background_update" → actualiza resultados
   - Si tiene type: "prediction_resolved" → actualiza stats
```

## Chart Registry

Los charts registrados en `app/core/chart_registry.py` se sincronizan con los tests:

| Nombre | Ubicación | Endpoint | Props |
|--------|-----------|----------|-------|
| sparkline | Modal de mercado | GET /api/analysis/chart/{ticker} | scalping, 1d, 60 |
| multi-panel | Tab Análisis | GET /api/analysis/chart/{ticker} | scalping, 1d, 100 |
| technical-analysis | Modal de mercado | POST /api/analysis/technical-analysis | scalping, 1d, 100 |

Los tests se parametrizan sobre `get_registered_charts()`: si se agrega un chart al registry, los tests lo cubren automáticamente.
