# CI/CD con GitHub Actions — Guía Educativa

## 1. ¿Qué es CI/CD?

CI/CD significa **Integración Continua** y **Despliegue Continuo**.

Pensalo como un **robot que revisa tu código automáticamente** cada vez que hacés
`git push`. No importa si soy yo, vos u otro dev — el robot siempre hace las
mismas vérificaciones.

| Concepto | Explicación para sysadmin |
|----------|---------------------------|
| **CI (Integración Continua)** | Cada vez que subís código, se compila, se pasan tests, se verifica estilo. Si algo está roto, lo sabés al toque |
| **CD (Despliegue Continuo)** | Si los tests pasan, el código se depliega automáticamente a producción (no implementado aún en este proyecto) |

Sin CI/CD:
```
git push → "en mi máquina funciona" → bugs en producción → caos
```

Con CI/CD:
```
git push → lint + tests + build → ✅ todos verifican → tranquilidad
```

---

## 2. ¿Qué es GitHub Actions?

GitHub Actions es un **servicio de GitHub** que ejecuta tareas automatizadas
cuando pasa algo en tu repositorio (push, pull request, etc.).

En criollo: **GitHub te presta una máquina virtual limpia** para que corras
los comandos que quieras. Es como tener un servidor Jenkins pero sin instalarlo,
sin mantenerlo, y sin pagar (hasta ciertos límites).

### Componentes

```
Evento (push, PR, etc.)
  └─ Workflow (archivo YAML en .github/workflows/)
        └─ Jobs (corren en paralelo, o en secuencia si usás "needs")
              └─ Steps (comandos individuales)
                    └─ Actions (pasos reutilizables: checkout, setup-python, etc.)
```

### Analogía

Imaginá que cada vez que subís código, GitHub hace:

```
1. "Compro una VM de Ubuntu"
2. "Bajo el código del repo"            (actions/checkout)
3. "Instalo Python 3.12"                (actions/setup-python)
4. "Corro ruff check ."                  (lint)
5. "Corro pytest"                        (tests)
6. "Compilo la imagen Docker"            (build)
7. "Apago la VM"
```

Si el paso 4 o 5 fallan → ❌. Si todo pasa → ✅.

---

## 3. Nuestro Pipeline Explicado

### Vista general

```
    git push
       │
       ▼
  ┌────────┐  ┌────────┐  ┌────────┐
  │  Lint  │  │  Test  │  │  Build │  ←── corren EN PARALELO
  └────┬───┘  └────┬───┘  └────┬───┘
       │           │           │
       └───────────┬───────────┘
                   ▼
            ┌─────────────┐
            │ Integration │  ←── espera a los 3 anteriores
            └─────────────┘
```

### Job 1: Lint (código limpio)

```yaml
lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4        # Trae tu código
      - uses: actions/setup-python@v5    # Instala Python
      - run: pip install ruff            # Instala el linter
      - run: ruff check .                # Revisa que el código sea limpio
```

**¿Qué verifica?** Que el código siga las reglas de estilo:
- Imports ordenados
- Variables no usadas no existen
- Líneas no muy largas
- Nombres de variables claros

**Si falla:** git te marca el commit como rojo y tenés que arreglar el estilo.

### Job 2: Test (unit tests)

```yaml
test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          cache: pip                     # Cachea dependencias (más rápido)
      - run: pip install -r requirements.txt pytest httpx
      - run: PYTHONPATH=. pytest -v --tb=short
        env:
          DATABASE_URL: sqlite:///./test.db   # Usa SQLite (rápido)
```

**¿Qué prueba?** Los 13 tests unitarios del proyecto:
- Conexión a brokers (Yahoo, Binance, IBKR)
- Estrategias de trading (scalping, swing)
- Endpoints de la API (health, config)

**Detalle importante:** `PYTHONPATH=.` le dice a Python "buscá módulos en
el directorio actual". Sin esto, Python no encuentra el módulo `app`.

### Job 3: Build (Docker)

```yaml
build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build api
```

**¿Qué prueba?** Que el `Dockerfile` compile correctamente. Si alguien rompe
el Dockerfile, te enterás acá, no cuando querés deployar.

### Job 4: Integration (tests contra base de datos real)

```yaml
integration:
    needs: [lint, test, build]           # Espera a los 3
    services:
      postgres:
        image: postgres:16-alpine         # Levanta Postgres
    steps:
      - run: PYTHONPATH=. pytest -k "test_health..."
        env:
          DATABASE_URL_SYNC: postgresql://user:pass@localhost:5432/stockdb
```

**¿Qué prueba?** Los mismos tests pero contra **Postgres real** en vez de SQLite.
Verifica que la app funciona con la base de datos de producción.

---

## 4. ¿Cómo lee los resultados?

### Opción 1: GitHub → pestaña Actions

```
1. GitHub.com → tu repo
2. Clic en "Actions" (arriba)
3. Ves la lista de workflows
   - ✅ Verde = pasó
   - ❌ Rojo = falló
   - 🟡 Amarillo = corriendo
4. Clic en uno rojo → ves qué job falló
5. Clic en el job → ves el paso exacto que falló
```

### Opción 2: notificaciones por email

GitHub te manda un email si un workflow que vos iniciaste falla.

### Opción 3: badges en el README

Si querés mostrar el estado en la página del repo:

```
![CI](https://github.com/TU_USUARIO/stock-analysis/actions/workflows/ci.yml/badge.svg)
```

---

## 5. ¿Por qué falló la primera vez?

El error fue:

```
ModuleNotFoundError: No module named 'app'
```

**Causa:** En tu máquina, cuando corrés `pytest`, estás parado en
`/home/sole/stock-analysis/`, y Python automáticamente busca módulos ahí.
En el runner de GitHub, el directorio de trabajo es otro, y Python no sabía
dónde buscar el módulo `app`.

**Solución:** `PYTHONPATH=.` antes de `pytest`.

**Lección:** Los pipelines de CI corren en máquinas LIMPIAS. No tienen tu
configuración local. Todo lo que necesiten hay que decírselo explícitamente.

---

## 6. Comandos útiles

```bash
# Ver el estado del CI desde terminal (necesitás gh CLI)
gh run list

# Ver los logs del último workflow
gh run view --log

# Si querés correr los tests como los corre el CI
PYTHONPATH=. pytest -v --tb=short

# Con SQLite (como el CI)
DATABASE_URL=sqlite:///./test.db DATABASE_URL_SYNC=sqlite:///./test.db \
  PYTHONPATH=. pytest -v --tb=short
```

---

## 7. Buenas prácticas

| Regla | Por qué |
|-------|---------|
| **Nunca pushear a `main` directo** | Siempre usar ramas + PR para que el CI revise antes |
| **Mirar el CI antes de pedir review** | No le hagas perder tiempo a otro dev si ya sabés que está rojo |
| **Si el CI falla, es prioridad** | Los builds rotos afectan a todo el equipo |
| **Un commit = un cambio lógico** | Facilita encontrar qué rompió algo |
| **Usar ramas cortas** | Una semana máximo. Ramas largas = conflictos |

---

## 8. Arquitectura general del proyecto

```
stock-analysis/
├── .github/workflows/ci.yml      ←  El pipeline (todo lo que leíste acá)
├── app/                           ←  Código de la app
├── tests/                         ←  Tests unitarios
├── requirements.txt               ←  Dependencias Python
├── Dockerfile                     ←  Cómo se construye la imagen
└── docker-compose.yml             ←  Orquestación de servicios
```
