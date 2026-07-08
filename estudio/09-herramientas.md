# Herramientas: Ruff, Linting y Calidad de Código

> **Fecha:** 2026-07-08

## ¿Qué es Linting?

Un **linter** es un programa que analiza tu código buscando errores,
malas prácticas, y violaciones de estilo. Es como tener un revisor
de código automático.

## Ruff — El Linter (y Formatter)

Ruff es el linter más rápido para Python (escrito en Rust, no en Python).

```bash
ruff check .          # Analiza todo el proyecto
ruff check --fix .    # Autocorrige lo que pueda
ruff format .         # Formatea el código (como black)
```

### ¿Qué detecta?

| Regla | Ejemplo de lo que detecta |
|-------|--------------------------|
| `F401` | Import que no se usa |
| `F841` | Variable asignada pero nunca usada |
| `E501` | Línea muy larga |
| `I001` | Imports desordenados |
| `E712` | `== True` en vez de `is True` |

## Configuración (pyproject.toml)

```toml
[tool.ruff]
line-length = 120                     # Máximo de caracteres
target-version = "py312"              # Versión de Python

[tool.ruff.lint]
select = ["E", "F", "W", "I"]        # Reglas a aplicar
```

## Integración con CI

En el pipeline de CI, `ruff check .` corre automáticamente:

```yaml
lint:
    steps:
      - run: pip install ruff
      - run: ruff check .
```

Si hay errores de estilo, el job falla y vos tenés que arreglarlos
antes de mergear.

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **Ruff rules** | Todas las reglas disponibles | https://docs.astral.sh/ruff/rules/ |
| **Ruff formatter** | Alternativa a Black | `ruff format --check .` |
| **pre-commit** | Correr ruff antes de cada commit | https://pre-commit.com/ |
| **mypy** | Type checking estático | https://mypy-lang.org/ |
| **EditorConfig** | Consistencia entre editores | https://editorconfig.org/ |
