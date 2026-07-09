# Indicadores Técnicos

Todos los indicadores se calculan con **Polars nativo** (sin pandas, sin TA-Lib).
Archivo: `app/core/strategies.py`

## Estrategia Scalping (`scalping_signals`)

Período mínimo: **26 filas** de datos.
Diseñada para operativas de corto plazo (5m, 15m, 1h).

### EMA 9/21 — Crossover

```
ema_9  = close.ewm_mean(span=9, adjust=False)
ema_21 = close.ewm_mean(span=21, adjust=False)
```

**Lógica:**
- `ema_9 > ema_21` y `prev_ema9 <= prev_ema21` → **BUY** (`+0.35`)
- `ema_9 < ema_21` y `prev_ema9 >= prev_ema21` → **SELL** (`+0.35`)

Usa EMA exponencial (`adjust=False`) para dar más peso a datos recientes.
Detecta el **cruce** (golden/death cross) comparando valor actual vs anterior.

### RSI 14 — Relative Strength Index

```
delta = close.diff()
gain = delta positivo → delta, sino 0
loss = delta negativo → -delta, sino 0
avg_gain = gain.ewm_mean(span=14, adjust=False)
avg_loss = loss.ewm_mean(span=14, adjust=False)
rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
```

**Lógica:**
- `RSI < 30` → sobrevendido → **BUY** (`+0.25`)
- `RSI > 70` → sobrecomprado → **SELL** (`+0.25`)
- Si RSI contradice la señal de EMA, revierte a NEUTRAL

### Bollinger Bands (20, 2)

```
bb_mid  = close.rolling_mean(window_size=20)
bb_std  = close.rolling_std(window_size=20)
bb_up   = bb_mid + 2 * bb_std
bb_low  = bb_mid - 2 * bb_std
```

**Lógica:**
- Precio `<=` banda inferior → **BUY** (`+0.20`)
- Precio `>=` banda superior → **SELL** (`+0.20`)
- Si la señal de banda contradice EMA, prioriza banda

### Confianza (Scalping)

```
confianza = 0.0
confianza += 0.35  si hay cruce EMA
confianza += 0.25  si RSI extremo
confianza += 0.20  si toque de Banda Bollinger
confianza = min(confianza, 1.0)
```

| Combinación | Confianza |
|------------|-----------|
| Solo EMA crossover | 0.35 |
| EMA + RSI | 0.60 |
| EMA + Bollinger | 0.55 |
| EMA + RSI + Bollinger | 0.80 |
| RSI + Bollinger (sin EMA) | 0.45 |
| Todos alineados | 0.80 |

---

## Estrategia Swing (`swing_signals`)

Período mínimo: **200 filas** de datos.
Diseñada para operativas de largo plazo (1d, 4h).

### MACD — Moving Average Convergence Divergence

```
ema_12     = close.ewm_mean(span=12, adjust=False)
ema_26     = close.ewm_mean(span=26, adjust=False)
macd_line  = ema_12 - ema_26
signal     = macd_line.ewm_mean(span=9, adjust=False)
histogram  = macd_line - signal
```

**Lógica:**
- `macd_line > signal` y `prev_macd <= prev_signal` → **BUY** (`+0.40`)
- `macd_line < signal` y `prev_macd >= prev_signal` → **SELL** (`+0.40`)

### SMA 200 — Simple Moving Average

```
sma_200 = close.rolling_mean(window_size=200)
```

**Lógica:**
- Precio `>` SMA 200 → tendencia alcista (`+0.15`)
- Precio `<` SMA 200 → tendencia bajista (`-0.10`)

### Soportes y Resistencias Históricos

```
hist, edges = np.histogram(values, bins=30)
levels = [ (edges[i] + edges[i+1]) / 2
           for i where hist[i] >= percentile(hist, 80) ]
```

Usa **histograma de frecuencia** sobre los precios máximos/mínimos:
1. Divide el rango de precios en 30 bins
2. Encuentra bins en el percentil 80 de frecuencia (niveles visitados múltiples veces)
3. Retorna hasta 5 niveles de soporte y 5 de resistencia

**Lógica:**
- Precio dentro del 1% de un soporte → **BUY** (`+0.20`)
- Precio dentro del 1% de una resistencia → **SELL** (`+0.20`)

### Confianza (Swing)

```
confianza = 0.0
confianza += 0.40  si cruce MACD
confianza += 0.15  si precio > SMA 200 (o -0.10 si está abajo)
confianza += 0.20  si en soporte o resistencia
confianza = max(0.0, min(confianza, 1.0))
```

| Combinación | Confianza |
|------------|-----------|
| Solo MACD crossover | 0.40 |
| MACD + precio sobre SMA200 | 0.55 |
| MACD + S/R | 0.60 |
| MACD + SMA200 + S/R | 0.75 |
| Precio bajo SMA200 (penaliza) | resta 0.10 |

---

## Chart Data (`compute_chart_data`)

Calcula **todas las series temporales** para renderizado en frontend:

```python
# Retorna dict con arrays paralelos:
{
  "timestamp":    [...],    # ISO strings
  "close":        [...],    # Precios de cierre
  "ema_9":        [...],    # EMA rápida
  "ema_21":       [...],    # EMA lenta
  "bb_upper":     [...],    # Banda superior Bollinger
  "bb_mid":       [...],    # Banda media (SMA 20)
  "bb_lower":     [...],    # Banda inferior Bollinger
  "rsi_14":       [...],    # RSI
  "macd":         [...],    # Línea MACD
  "macd_signal":  [...],    # Línea de señal
  "macd_histogram": [...]   # Histograma MACD
}
```

Los timestamps se convierten a ISO string para compatibilidad con Pydantic.
Los valores None en Close alinean los timestamps (se filtran juntos).

---

## Análisis Técnico (`technical_analysis.py`)

Sistema de **puntuación multi-factor** (independiente de las estrategias principales).

| Indicador | Score | Detalle |
|-----------|-------|---------|
| EMA 9 vs EMA 21 | ±1 | Bullish/bearish alignment |
| EMA 9 slope | ±1 | Aceleración de la pendiente |
| RSI nivel | ±1 | Sobrecompra/sobreventa |
| RSI divergencia | ±1 | Divergencia bullish/bearish |
| Bollinger touch | ±1 | Toque de banda superior/inferior |
| Bollinger squeeze | ±1 | Bandas se contraen >30% |
| MACD vs signal | ±1 | Posición relativa |
| MACD crossover | ±2 | Cruce de líneas |

**Veredicto por score:**
| Score | Veredicto | Confianza |
|-------|-----------|-----------|
| >= 3 | BUY | 50 + score * 10 (max 100) |
| <= -3 | SELL | 50 + \|score\| * 10 (max 100) |
| >= 1 | ACCUMULATE | 30 + score * 10 |
| <= -1 | REDUCE | 30 + \|score\| * 10 |
| 0 | NEUTRAL | 40 |

---

## Helper: `_find_levels`

Encuentra niveles de soporte/resistencia usando numpy histogram:

```python
def _find_levels(values, kind="support", bins=30):
    if len(values) < 10: return []
    hist, edges = np.histogram(values, bins=bins)
    for i in range(len(hist)):
        if hist[i] >= np.percentile(hist, 80):
            level = (edges[i] + edges[i+1]) / 2
            levels.append(level)
    # kind="support": primeros 5 (más bajos)
    # kind="resistance": últimos 5 (más altos)
```

Criterio: un nivel de precio es relevante si está en el **20% superior** de frecuencias del histograma.
