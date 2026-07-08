# Frontend: SPA Vanilla + Chart.js

> **Fecha:** 2026-07-08

## ¿Qué es una SPA?

**Single Page Application** (SPA). Una sola página HTML que se actualiza
dinámicamente sin recargar. En vez de:

```
Click en link → servidor genera HTML → recarga completa
```

Hacemos:

```
Click en link → JS pide datos al API → actualiza solo la parte que cambió
```

No usamos React, Vue ni Angular. Es **JavaScript vanilla** — puro, sin frameworks.

## Stack del Frontend

| Archivo | Lenguaje | Función |
|---------|----------|---------|
| `index.html` | HTML5 + CSS | Estructura de la página |
| `styles.css` | CSS3 | Dark theme, responsive |
| `app.js` | JavaScript (~1478 líneas) | Toda la lógica |

## Componentes

### 5 Tabs (pestañas)

```
Dashboard │ Análisis │ Alertas │ Opciones │ Depuración
```

Cada tab es un `div` que se oculta/muestra con JavaScript.

### Autocomplete Inteligente

```javascript
createAutocomplete("input-id", "dropdown-id", onSelect, multi=true)
```

- 50+ tickers precargados
- Búsqueda por símbolo o nombre
- Flechas ↑↓ para navegar, Enter para seleccionar
- Modo `multi=true` para seleccionar varios tickers

### Chart.js + Zoom

```javascript
new Chart(canvas, {
    type: 'line',
    data: { labels, datasets: [{ data: prices, label: 'AAPL' }] },
    options: {
        plugins: {
            zoom: {           ← Plugin de zoom
                pan: { enabled: true },
                zoom: { wheel: { enabled: true } }
            }
        }
    }
});
```

Dos clics resetean el zoom.

### Modal de Mercado

Ventana emergente con:
- Precio actual, RSI, EMA 9/21, SMA 200, MACD
- Sparkline con Bollinger Bands
- Selector de período: 15, 30, 60, 100, 200 velas

### Event Log

Panel flotante abajo a la derecha con máximo 100 eventos.
Se usa para debug y notificaciones.

## Comunicación con el Backend

```javascript
async function api(method, url, body) {
    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined
    });
    return resp.json();
}

// Ejemplo:
const data = await api('POST', '/api/analysis/analyze', {
    ticker: 'AAPL', strategy: 'scalping'
});
```

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **fetch API** | Cómo hacer requests HTTP desde JS | https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API |
| **Chart.js docs** | Todos los tipos de gráficos | https://www.chartjs.org/docs/latest/ |
| **chartjs-plugin-zoom** | Zoom, pan, reset en gráficos | https://github.com/chartjs/chartjs-plugin-zoom |
| **CSS Grid / Flexbox** | Layout moderno sin frameworks | https://css-tricks.com/snippets/css/a-guide-to-flexbox/ |
| **Vanilla JS vs Frameworks** | ¿Cuándo usar React? | Buscar "vanilla js vs react" |
| **ES Modules** | Organizar JS en archivos | `import` / `export` en JS |
