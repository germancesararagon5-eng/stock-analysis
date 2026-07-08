# Docker y Docker Compose

> **Fecha:** 2026-07-08

## ¿Qué es?

Docker empaqueta una aplicación con todo lo que necesita para correr
(Python, librerías, configuraciones) en una **imagen**. Cuando ejecutás
esa imagen, se crea un **contenedor** aislado.

Un contenedor es como una VM, pero:
- No tiene kernel propio (usa el del host)
- Arranca en segundos (no minutos)
- Ocupa MB, no GB

## Componentes

| Componente | Es como... |
|------------|-----------|
| **Dockerfile** | Un script de instalación (preseed/kickstart) |
| **Imagen** | Un ISO comprimido |
| **Contenedor** | Una VM corriendo |
| **Docker Compose** | Un orquestador para levantar múltiples servicios |
| **Volumen** | Un disco persistente (sobrevive a reinicios) |
| **Puerto** | Un bridge de red (host:contenedor) |

## Nuestro Dockerfile

```dockerfile
FROM python:3.12-slim        # Base: Debian slim con Python 3.12
WORKDIR /app                  # Directorio de trabajo
COPY requirements.txt .       # Copiar dependencias
RUN pip install -r requirements.txt  # Instalar
COPY . .                      # Copiar el código
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Nota importante:** Usamos `--workers 1` porque SQLAlchemy no soporta
fork entre workers. Con más de 1 worker, la base de datos se rompe.

## Nuestro docker-compose.yml

```yaml
services:
  api:                    # FastAPI
    build: .              # Construir desde ./Dockerfile
    ports: ["8000:8000"]
    depends_on:
      db: condition: service_healthy

  db:                     # PostgreSQL
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]  # Datos persistentes
    healthcheck:
      test: pg_isready -U user -d stockdb

  redis:                  # Redis (reservado)
    image: redis:7-alpine

  whatsapp-gateway:       # Node.js + Baileys
    build: ./whatsapp-gateway
    volumes: [whatsapp-session:/app/session]  # Sesión WhatsApp persistente
```

## Comandos Esenciales

```bash
# Build y start
docker compose up -d                # Levantar todo
docker compose up -d --build api    # Reconstruir solo api

# Ver estado
docker compose ps                   # Procesos
docker compose logs -f api          # Logs en vivo

# Ejecutar comandos dentro del contenedor
docker compose exec api bash        # Shell
docker compose exec db psql -U user -d stockdb  # SQL

# Limpiar
docker compose down                 # Parar todo
docker compose down -v              # Parar y borrar volúmenes

# Docker solo (sin compose)
docker build -t stock-api .         # Build imagen
docker run -p 8000:8000 stock-api   # Run contenedor
```

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **Multi-stage builds** | Imágenes más chicas (usamos una básica) | Buscar "docker multi-stage build" |
| **Docker networks** | Cómo se comunican los contenedores | `docker network` |
| **Docker volumes** | Diferencia entre bind mount y volume | https://docs.docker.com/storage/volumes/ |
| **Healthchecks** | Cómo Docker sabe si un servicio está vivo | `HEALTHCHECK` en Dockerfile |
| **Dockerfile best practices** | Capas, caching, seguridad | https://docs.docker.com/develop/develop-images/dockerfile_best-practices/ |
| **docker scout** | Análisis de vulnerabilidades | `docker scout quickview` |
| **Podman** | Alternativa a Docker sin daemon | https://podman.io/ |
