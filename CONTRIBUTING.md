# Guía de Contribución

Este documento define cómo colabora el equipo en el proyecto. Complementa la
[guía de workflow de Git](repo/git_workflow.md).

## Flujo de trabajo (resumen)

1. **Toma un issue** del tablero (o crea uno).
2. **Crea una rama** desde `main`:
   ```bash
   git switch main && git pull
   git switch -c feature/descripcion-corta
   ```
3. **Trabaja en commits pequeños** siguiendo Conventional Commits:
   ```
   feat(etl): integra fuente de dieta
   fix(api): corrige filtro por sexo
   docs(readme): agrega instrucciones de Docker
   test(reporting): cubre filtro de adultos
   ```
4. **Verifica localmente antes de subir**:
   ```bash
   ruff check src tests api dashboards scripts
   pytest -q
   ```
5. **Abre un Pull Request** hacia `main` (se usa la plantilla automática).
6. **Espera la revisión** de al menos un compañero y que pase la **CI**.
7. **Squash & merge** una vez aprobado.

## Reglas del equipo

- `main` siempre debe quedar **desplegable** (CI verde).
- No se hace `push` directo a `main`: todo entra por PR.
- Cada PR debe cerrar un issue (`Closes #N`).
- Mantener docstrings y nombres descriptivos.
- Las credenciales van solo en `conf/local/` y `.env` (nunca se versionan).

## Roles sugeridos (equipo)

| Rol | Responsabilidad |
|-----|-----------------|
| ETL / Datos | pipelines de ingestion y processing |
| API / Backend | FastAPI y endpoints |
| Dashboard / Viz | Streamlit y visualizaciones |
| DevOps | Docker, docker-compose, CI |

> Los roles son guías; todos revisan PRs de todos.

## Estándares de código

- **Formato y lint:** `ruff` (configurado en `pyproject.toml`).
- **Tests:** `pytest`, ubicados en `tests/`.
- **Tipado:** type hints en funciones públicas.
