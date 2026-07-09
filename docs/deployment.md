# Deploy y Operación

## Docker Compose (producción)

```bash
docker compose up -d --build
```

### Servicios

| Servicio | Puerto | Imagen | Depende de |
|----------|--------|--------|------------|
| api | 8000 | build local | db (healthy), redis, whatsapp-gateway |
| whatsapp-gateway | 3000 | build local | — |
| db | 5432 | postgres:16-alpine | — |
| redis | 6379 | redis:7-alpine | — |

```yaml
# docker-compose.yml (servicios clave)
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes: [".:/app"]  # hot-reload en desarrollo
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
      whatsapp-gateway: { condition: service_started }
```

### Volúmenes persistentes

| Volumen | Monta en | Propósito |
|---------|----------|-----------|
| pgdata | /var/lib/postgresql/data | Datos de PostgreSQL |
| whatsapp-session | /app/session | Sesión de WhatsApp (no re-escanear QR) |

## Desarrollo local (sin Docker)

### Requisitos

- Python 3.13+
- Node.js 22+ (para WhatsApp gateway)
- SQLite (dev) o PostgreSQL (prod)

### Inicio rápido

```bash
# 1. Python: instalar dependencias e iniciar API
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Node.js: iniciar WhatsApp gateway
cd whatsapp-gateway
npm install
node index.js

# 3. Abrir http://localhost:8000
```

### Variables de entorno (`.env`)

```bash
# DB (SQLite para dev, PostgreSQL para prod)
DATABASE_URL=sqlite:///./app.db
DATABASE_URL_SYNC=sqlite:///./app.db

# DB PostgreSQL (producción)
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/stockdb
# DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/stockdb

# Redis (reservado)
REDIS_URL=redis://localhost:6379/0

# WhatsApp gateway
WHATSAPP_GATEWAY_URL=http://localhost:3000

# API
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
APP_URL=http://localhost:8000

# JWT (cambiar en producción)
JWT_SECRET=cambiar-en-produccion-123456
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Google OAuth (opcional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# SMTP (opcional, para magic links)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=
```

## CI/CD Pipeline

Archivo: `.github/workflows/ci.yml`

### Jobs

```
git push
   │
   ├── Lint (ruff check .)
   │   Python 3.12, ruff install
   │
   ├── Test (pytest -v --tb=short)
   │   Python 3.12, pip cache, SQLite (DATABASE_URL=sqlite:///./test.db)
   │
   ├── Build (docker compose build api)
   │   Verifica que el Dockerfile compile
   │
   └── Integration (tests contra PostgreSQL)
       Espera a lint + test + build
       Servicio: postgres:16-alpine
       DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/stockdb
```

### Comandos CI

```bash
# Tests como los corre el CI
PYTHONPATH=. pytest -v --tb=short

# Tests con SQLite explícito
DATABASE_URL=sqlite:///./test.db DATABASE_URL_SYNC=sqlite:///./test.db \
  PYTHONPATH=. pytest -v --tb=short

# Lint
ruff check .

# Build
docker compose build api
```

## Tests

### Suite completa
```bash
POLARS_SKIP_CPU_CHECK=1 .venv/bin/python -m pytest tests/ -q --tb=short
```

### Con cobertura
```bash
POLARS_SKIP_CPU_CHECK=1 .venv/bin/python -m pytest --cov=app --cov-report=term --tb=short
```

### Tests específicos
```bash
POLARS_SKIP_CPU_CHECK=1 .venv/bin/python -m pytest tests/test_strategies.py -v
POLARS_SKIP_CPU_CHECK=1 .venv/bin/python -m pytest tests/test_analysis_router.py -v
```

### Tests de chart (parametrizados sobre registry)
```bash
POLARS_SKIP_CPU_CHECK=1 .venv/bin/python -m pytest tests/test_charts.py -v
```

## Troubleshooting

### Error: `no such column: predictions.pnl`

La DB fue creada con un schema anterior. Agregar columnas faltantes:
```sql
ALTER TABLE predictions ADD COLUMN pnl FLOAT;
ALTER TABLE predictions ADD COLUMN pnl_pct FLOAT;
```
O dropear la tabla (pérdida de datos):
```bash
rm app.db
# Se recrea automáticamente al iniciar la app
```

### Error: `sqlite3.OperationalError: no such table`

La DB no existe o está corrupta. Reiniciar la app la recrea vía `init_db()`.

### Error: `EADDRINUSE :::3000`

El puerto del WhatsApp gateway está ocupado:
```bash
sudo fuser -k 3000/tcp    # Matar proceso en puerto 3000
# O cambiar puerto en index.js y .env
```

### Error: `POLARS_SKIP_CPU_CHECK`

CPU sin soporte AVX/AVX2:
```bash
export POLARS_SKIP_CPU_CHECK=1
# O usar polars[rtcompat] (ya incluido en requirements.txt)
```

### Error: `Connection refused: whatsapp-gateway:3000`

El gateway no está disponible (solo en Docker). Verificar:
```bash
docker compose ps             # ¿whatsapp-gateway está running?
docker compose logs whatsapp-gateway  # Logs del gateway
```
En desarrollo local, asegurar `WHATSAPP_GATEWAY_URL=http://localhost:3000` en `.env`.

### Error: `ModuleNotFoundError: No module named 'app'`

El PYTHONPATH no incluye el directorio raíz:
```bash
PYTHONPATH=. pytest ...
```

### Docker compose build lento

Usar cache de Docker:
```bash
docker compose build --no-cache api   # rebuild completo
docker compose build api               # con cache
```

### WhatsApp QR no aparece

1. Verificar que el gateway esté corriendo: `curl http://localhost:3000/status`
2. Si responde `{"connected":true,...}` → ya está conectado, no hace falta QR
3. Si responde `{"connected":false}` → ver logs: `cat /tmp/whatsapp-gateway.log`
4. Si hay error de autenticación → borrar `whatsapp-gateway/session/` y reiniciar

## Notas de producción

- **Workers**: Siempre 1 (`--workers 1`). SQLAlchemy no soporta fork.
- **DB migrations**: No hay Alembic. Cambios de schema requieren dropear tabla manualmente.
- **Redis**: Reservado pero no implementado. No afecta el funcionamiento.
- **Login**: Deshabilitado. El auth_router existe pero no se incluye en main.py.
- **CPU**: Sin AVX/AVX2 → usar `polars[rtcompat]` + `POLARS_SKIP_CPU_CHECK=1`.
