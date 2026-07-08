# GitHub Actions — CI/CD

> **Fecha:** 2026-07-08
> **Estado:** Pipeline funcionando en stock-analysis

## ¿Qué es?

GitHub Actions es un **servicio de integración continua** (CI) que corre
tareas automatizadas cada vez que pasa algo en tu repo (push, PR, etc.).

La analogía con un sysadmin tradicional:

```
Antes (sin CI):
  "Andá, pusheá el código y fijate si rompe algo"

Ahora (con CI):
  "Pusheá tranquilo, el robot revisa todo automáticamente"
```

## Cómo funciona

```
git push → GitHub recibe el código
                │
                ├─ 1. Compra una VM (Ubuntu, 2 cores, 7GB RAM)
                ├─ 2. checkout: baja tu código
                ├─ 3. setup-python: instala Python 3.12
                ├─ 4. pip install: instala dependencias
                ├─ 5. ruff check: verifica estilo
                ├─ 6. pytest: corre tests
                ├─ 7. docker compose build: compila imagen
                └─ 8. Apaga la VM
```

## Anatomía de un Workflow

```yaml
# .github/workflows/lo-que-sea.yml
name: CI                        # Nombre visible en GitHub

on:                             # ¿Cuándo se dispara?
  push:
    branches: [main]            # En push a main
  pull_request:
    branches: [main]            # En PR a main

env:                            # Variables para todos los jobs
  PYTHON_VERSION: "3.12"

jobs:                           # Los trabajos a ejecutar
  lint:                         # ID del job
    name: Lint                  # Nombre visible
    runs-on: ubuntu-latest      # Tipo de VM
    steps:                      # Pasos del job
      - uses: actions/checkout@v4
      - run: pip install ruff
      - run: ruff check .

  test:
    needs: [lint]               # Espera a que lint pase
    steps:
      - run: pytest
        env:                    # Variables específicas
          DATABASE_URL: sqlite:///test.db
```

## Jobs en Paralelo y Secuencia

Lint, Test y Build corren en **paralelo** (no se esperan).
Integration corre **después** de que los 3 pasan:

```
        ┌─ Lint ─┐
push ───├─ Test ─┤─── Integration
        └─ Build ┘
```

## Servicios (Services)

Los jobs pueden tener **contenedores auxiliares**. Por ejemplo,
la integración necesita Postgres:

```yaml
integration:
    services:
      postgres:
        image: postgres:16-alpine    # Docker run postgres
        ports:
          - 5432:5432               # Accesible en localhost:5432
        options: >-
          --health-cmd pg_isready
          --health-retries 10
```

## Errores Comunes (y cómo los arreglamos)

| Error | Causa | Solución |
|-------|-------|----------|
| `No module named 'app'` | PYTHONPATH no seteado | `PYTHONPATH=. pytest` |
| `pip install fails` | PEP 668 (Debian) | En runner no pasa (no es Debian) |
| `Service container fails` | Health check muy corto | `--health-retries 10` |
| `Token expired` | PAT vencido | Generar nuevo en settings/tokens |

## Debugging de Workflows

```bash
# Ver últimas runs
gh run list

# Ver logs de una run
gh run view --log

# Re-ejecutar un workflow fallido
gh run rerun
```

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **Expresiones y contextos** | Usar vars, secrets, condicionales | https://docs.github.com/en/actions/learn-github-actions/contexts |
| **Matrix builds** | Testear en múltiples versiones/OS | Buscar "github actions matrix strategy" |
| **Caching** | Acelerar pip, npm, docker | https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows |
| **Artefactos** | Guardar resultados de builds | `actions/upload-artifact` |
| **Self-hosted runners** | Correr Actions en tu propio servidor | https://docs.github.com/en/actions/hosting-your-own-runners |
| **Actions Marketplace** | Acciones pre-hechas por la comunidad | https://github.com/marketplace?type=actions |
| **Dependabot** | Actualizar automaticamente dependencias | Buscar "dependabot version updates" |
