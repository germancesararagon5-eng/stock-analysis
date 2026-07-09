# Python 3.12+ y FastAPI

> **Fecha:** 2026-07-08

## Python 3.12 — Lo nuevo

La versión 3.12 trajo varias mejoras que usamos:

| Feature | Cómo lo usamos |
|---------|---------------|
| **`list[dict]`** en vez de `List[Dict]` | En todos los type hints |
| **`Optional[X]`** en vez de `Union[X, None]` | En parámetros opcionales |
| **`@dataclass`** | `BrokerConfig` en `base_broker.py` |
| **Namespace packages** | Sin `__init__.py` — los borramos todos |
| **`match` statement** | No lo usamos (todavía) |

## FastAPI — El Framework Web

FastAPI es un framework moderno para APIs REST en Python. Características:

- **Auto-documentación** en `/docs` (Swagger UI) y `/redoc`
- **Validación automática** con Pydantic
- **Async nativo** (aunque nosotros usamos sync por SQLAlchemy)

### Endpoints en el proyecto

```python
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/analisis", tags=["analisis"])

@router.post("/analyze")
def analyze(ticker: str, strategy: str = "scalping"):
    """El tipo de dato ES la documentación."""
    return {"ticker": ticker, "signal": "BUY"}
```

### La app principal

```python
app = FastAPI(
    title="Stock Analysis Multi-Broker API",
    version="1.0.0",
    lifespan=lifespan,   # On startup / shutdown
)
app.add_middleware(CORSMiddleware, ...)
app.include_router(config_router.router)
```

### Lifespan (antes startup/shutdown)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                         # Crear tablas
    broker_manager.load_from_db(db)   # Cargar broker activo
    yield                             # App corriendo
    # Cleanup si hiciera falta
```

## Pydantic Settings

Las configuraciones se cargan desde `.env` automáticamente:

```python
class Settings(BaseSettings):
    database_url_sync: str = "postgresql://user:pass@db:5432/stockdb"
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}

settings = Settings()
```

## Autenticación JWT

Agregamos autenticación JWT (JSON Web Token) para proteger los endpoints.

### Cómo funciona

```
POST /api/auth/register  →  { username, email, password }  →  token JWT
POST /api/auth/login     →  { username, password }         →  token JWT
GET  /api/auth/me        →  Header: Bearer <token>         →  user info
```

El token se genera con `python-jose` y se verifica con una clave secreta:

```python
# app/services/auth_service.py
def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=1440)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
```

### Proteger un endpoint

```python
from app.services.auth_service import get_current_user

@router.get("/secreto")
def secreto(current_user: User = Depends(get_current_user)):
    return {"msg": f"Hola {current_user.username}"}
```

### Dependencias

Se agregaron 3 paquetes:

```txt
python-jose[cryptography]  # JWT encode/decode
passlib[bcrypt]            # Hash de contraseñas
bcrypt                     # Algoritmo de hash
```

### Frontend

El token se guarda en `localStorage` y se envía en cada request:

```javascript
localStorage.setItem('token', token);
fetch('/api/algo', {
    headers: { 'Authorization': 'Bearer ' + token }
});
```

## WebSockets en FastAPI

FastAPI soporta WebSocket de forma nativa con `@app.websocket()`:

```python
@app.websocket("/api/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.receive_text()   # Espera mensajes del cliente
    except Exception:
        pass
    finally:
        ws_manager.disconnect(ws)
```

Ver `estudio/10-websockets.md` para la guía completa.

## Uvicorn — El Servidor ASGI

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**`--workers 1` es obligatorio.** Si ponés más, SQLAlchemy crashea
porque el engine no soporta ser copiado por fork().

## Polars Nativo (reemplaza pandas + ta)

Migración completa pandas+ta → polars nativo en `strategies.py` y `analysis_service.py`.

**Por qué Polars:**
- Ejecución en paralelo (SIMD, multi-thread), sin depender de AVX/AVX2
- API lazy (`pl.LazyFrame`) y eager (`pl.DataFrame`) optimizada para datasets medianos/grandes
- Sin dependencia de `ta-lib` ni `pandas-ta` (que requieren numpy compilado)

**Cómo convertimos datos de yfinance:**
```python
import polars as pl

def _to_polars(df_dict: dict) -> pl.DataFrame:
    import pyarrow as pa
    table = pa.Table.from_pydict(df_dict)
    return pl.from_arrow(table)
```

**Indicadores con Polars nativos:**

| Indicador | Implementación |
|-----------|---------------|
| EMA 9/21 | `pl.col("close").ewm_mean(span=9, adjust=False)` |
| Bollinger Bands | `rolling_mean + 2 * rolling_std` |
| RSI | Ganancia/pérdida promedio con `ewm_mean`, `map_elements` para normalización |
| MACD | Diferencia de dos EMAs |
| SMA 200 | `rolling_mean(200)` |
| Soportes/Resistencias | `pl.Expr.min()`, `pl.Expr.max()` sobre ventana |

**Ejemplo concreto — EMA en Polars vs pandas:**
```python
# Antes (pandas + ta)
df_ta = ta.add_all_ta_features(df_ta, open="open", high="high", low="low", close="close", volume="volume")
ema_9 = df_ta["EMA_9"].iloc[-1]

# Ahora (polars nativo)
df_pl = df_pl.with_columns(
    pl.col("close").ewm_mean(span=9, adjust=False).alias("ema_9")
)
ema_9 = df_pl.select("ema_9").tail(1).item()
```

**⚠️ pyarrow requerido:** `pl.from_pandas()` necesita `pyarrow` instalado.
Además, hay que filtrar columnas no numéricas (Dividends, Stock Splits) antes de convertir:

```python
ohlcv_cols = ["Open", "High", "Low", "Close", "Volume"]
df_dict = {k: v for k, v in df_dict.items() if k in ohlcv_cols}
```

## Paralelización con ThreadPoolExecutor

El endpoint `GET /api/analysis/top-ranking` procesaba los tickers **secuencialmente**, haciendo una llamada HTTP a Yahoo Finance por cada uno. Con 48 tickers, eso tomaba ~27 segundos — causando timeouts de red en el frontend.

**Solución: `ThreadPoolExecutor` con 6 workers:**

```python
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

def _process(ticker: str) -> dict | None:
    try:
        r = run_analysis(ticker=ticker, ...)
        return {...} if r["signal"] != "NEUTRAL" else None
    except Exception:
        return None

results = []
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = {pool.submit(_process, t): t for t in selected}
    while futures:
        done, futures = wait(futures, timeout=30, return_when=FIRST_COMPLETED)
        for future in done:
            item = future.result()
            if item is not None:
                results.append(item)
```

Esto redujo el tiempo de ~27s a ~6s. Se agregó un deadline global de 90s como safety net.

**Alternativas consideradas:**
- `asyncio.gather` — no servía porque `yfinance` es sincrónico
- `concurrent.futures.as_completed(timeout=90)` — el timeout se aplica por iteración, no global

## Persistencia del Background Analyzer

El `BackgroundAnalyzer` originalmente guardaba sus resultados solo en memoria (`self._results`), perdiéndose al reiniciar el servidor. Ahora persiste en DB vía modelo `BackgroundResult`.

**Modelo:**
```python
class BackgroundResult(Base):
    __tablename__ = "background_results"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal = Column(String(10), nullable=False)
    confidence = Column(Float, default=0.0)
    price = Column(Float, nullable=True)
    strategy = Column(String(50), default="scalping")
    interval = Column(String(10), default="5m")
    periods = Column(Integer, default=100)
    error = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

**Flujo de persistencia:**
1. `_run_cycle()` ejecuta análisis para cada ticker
2. Resultados se agregan a `batch_results` (éxito o error)
3. Se persisten todos en DB: `db.add_all([BackgroundResult(...) for entry in batch_results])`
4. `get_results()` lee de DB con `ORDER BY created_at DESC LIMIT :limit`
5. Si DB falla, fallback a `self._results` en memoria

## Manejo de Errores en Endpoint de Chart

El endpoint `GET /api/analysis/chart/{ticker}` originalmente no tenía manejo de errores. Cuando `get_historical_data()` fallaba (ej. Yahoo Finance no tiene datos para cierto ticker), FastAPI devolvía un 500 con el mensaje de error, y el frontend mostraba "Datos insuficientes" sin explicación.

**Solución — try/except con respuesta graceful:**

```python
@router.get("/chart/{ticker}", response_model=ChartResponse)
def get_chart(ticker: str, ...):
    try:
        df = get_historical_data(ticker, interval, periods)
        series = compute_chart_data(df)
        result = run_analysis(ticker, ...)
        return ChartResponse(series=ChartSeries(...), ...)
    except Exception as e:
        logger.warning("Chart error for %s: %s", ticker, e)
        empty = ChartSeries(timestamp=[], close=[], ...)
        return ChartResponse(
            ticker=ticker, signal="NEUTRAL", confidence=0.0,
            reasons=[str(e)], series=empty,
        )
```

El error se propaga al frontend vía `reasons[]`, y la UI lo muestra sin romper la experiencia.

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **Async/Await en FastAPI** | Para no bloquear requests lentas | https://fastapi.tiangolo.com/async/ |
| **Pydantic V2** | Validación más rápida | https://docs.pydantic.dev/latest/ |
| **Depends + Dependency Injection** | Cómo inyectar DB, auth, etc. | `from fastapi import Depends` |
| **BackgroundTasks** | Tareas asíncronas sin celery | https://fastapi.tiangolo.com/tutorial/background-tasks/ |
| **SQLAlchemy 2.0 style** | El nuevo ORM (usamos estilo antiguo) | https://docs.sqlalchemy.org/en/20/ |
| **Alembic** | Migraciones de base de datos profesionales | https://alembic.sqlalchemy.org/ |
| **Poetry / uv** | Gestión de dependencias moderna | https://docs.astral.sh/uv/ |
