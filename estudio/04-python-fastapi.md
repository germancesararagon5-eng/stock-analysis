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

## Uvicorn — El Servidor ASGI

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**`--workers 1` es obligatorio.** Si ponés más, SQLAlchemy crashea
porque el engine no soporta ser copiado por fork().

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
