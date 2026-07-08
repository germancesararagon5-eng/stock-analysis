# Git y GitHub

## ¿Qué es Git?

Git es un **control de versiones**. Piensen en él como `rsync` con memoria:
cada cambio que hacés queda registrado con un mensaje, autor y timestamp.
Podés volver atrás, crear ramas paralelas, y fusionar cambios.

## Conceptos Clave

| Concepto | Explicación para Sysadmin |
|----------|---------------------------|
| **repo** | El directorio del proyecto + toda su historia (`./.git/`) |
| **commit** | Un snapshot del código con un mensaje |
| **branch** | Una línea de desarrollo paralela |
| **remote** | Un repo en otro lado (GitHub, GitLab, etc.) |
| **push** | Subir commits locales al remote |
| **pull** | Traer commits del remote a local |
| **clone** | Copiar un repo entero a tu máquina |

## Comandos Esenciales

```bash
# Configuración inicial (solo la primera vez)
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# Trabajo diario
git status              # ¿Qué cambió?
git diff                # ¿Qué cambió exactamente?
git add archivo.py      # Marcá archivo para commit
git commit -m "mensaje" # Creá el snapshot
git push                # Subilo a GitHub
git pull                # Traé los cambios de otros
```

## Token de GitHub (PAT)

Para hacer `git push` desde la terminal necesitás autenticación.
Lo correcto hoy es usar un **Personal Access Token (PAT)**:

1. Andá a https://github.com/settings/tokens
2. "Generate new token" → "Classic"
3. Marcá scopes: `repo` (todo) o `repo:status`, `public_repo`
4. Copiá el token (solo se ve una vez)
5. Usalo como contraseña cuando git te la pida

**Tip:** Los tokens clásicos empiezan con `ghp_` y tienen acceso completo
según los scopes que le asignes. Los **fine-grained PAT** empiezan con
`github_pat_` y se limitan a repos específicos (más seguro).

```bash
# Usar token en el remote URL (para no escribirlo cada vez)
git remote set-url origin https://USUARIO:TOKEN@github.com/USUARIO/REPO.git

# O mejor: usar GH CLI
gh auth login
```

## Ramas (Branches)

```bash
git branch                  # Ver ramas
git checkout -b feature-x   # Crear y moverte a rama nueva
git checkout main           # Volver a main
git merge feature-x         # Fusionar feature-x en main
```

## .gitignore

Archivo que le dice a git "esto no lo trackees":

```gitignore
.env            # Credenciales
__pycache__/    # Caché de Python
node_modules/   # Dependencias JS
*.log           # Logs
```

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **Git Flow** | Estrategia de ramas profesional | https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow |
| **Conventional Commits** | Estandarizar mensajes de commit | https://www.conventionalcommits.org/ |
| **GitHub CLI** | Hacer todo desde terminal | `gh --help` |
| **Merge vs Rebase** | Dos formas de integrar cambios | https://www.atlassian.com/git/tutorials/merging-vs-rebasing |
| **Git Hooks** | Scripts que corren en cada commit/push | Buscar "pre-commit hooks" |
