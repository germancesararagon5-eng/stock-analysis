# 📚 Estudio: Tecnologías Aplicadas al Proyecto

> **Sysadmin desde 1990s → Full Stack 2026**
> Este directorio documenta todo lo que pregunté y aprendí durante el
> desarrollo de **stock-analysis**, con recomendaciones para profundizar.

## Estado actual del proyecto

- **101 tests** pasando · Cobertura 84%
- **Estrategias:** scalping (EMA 9/21, RSI, BB), swing (MACD, SMA 200, soportes/resistencias)
- **Indicadores:** implementados en Polars nativo (sin pandas/ta)
- **Brokers:** Yahoo Finance (activo), Binance (testnet), Interactive Brokers (placeholder)
- **Persistencia:** BackgroundResult en DB (no se pierden resultados al reiniciar)

## Estructura

| Archivo | Qué contiene | Última actualización |
|---------|-------------|---------------------|
| `01-git-github.md` | Git, GitHub, tokens, repositorios | 2026-07-08 |
| `02-github-actions.md` | CI/CD con GitHub Actions (el más importante) | 2026-07-08 |
| `03-docker.md` | Docker, Docker Compose, contenedores | 2026-07-08 |
| `04-python-fastapi.md` | Python 3.12+, FastAPI, async, endpoints, ThreadPoolExecutor | 2026-07-09 |
| `05-bases-de-datos.md` | PostgreSQL, SQLAlchemy, SQLite, migraciones | 2026-07-08 |
| `06-frontend.md` | SPA vanilla, Chart.js, CDN, DOM | 2026-07-08 |
| `07-testing.md` | pytest, TestClient, mocks, cobertura, 101 tests | 2026-07-09 |
| `08-whatsapp-baileys.md` | WhatsApp gateway, Node.js, Baileys | 2026-07-08 |
| `09-herramientas.md` | Ruff, linting, formateo, calidad de código | 2026-07-08 |
| `10-websockets.md` | WebSockets, tiempo real, broadcast, ws_manager | 2026-07-08 |

## Cómo usar esto

1. Empezá por `02-github-actions.md` (es lo más nuevo para un sysadmin)
2. Seguí por `01-git-github.md` (fundación de todo)
3. Después `03-docker.md` (ya debés conocerlo, pero hay Tips nuevos)
4. El resto en cualquier orden

Cada archivo tiene:
- **Conceptos clave** explicados para un sysadmin
- **Comandos útiles** para usar en el día a día
- **Recomendaciones** de qué investigar después
- **Enlaces** a documentación oficial y tutoriales

> "No sabía nada de CI/CD hace una semana, hoy tengo un pipeline
>  corriendo en GitHub que hace lint, tests, build e integración solo."
