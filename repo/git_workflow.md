# Evidencia de Trabajo Colaborativo (Git)

Esta carpeta documenta las prácticas profesionales de colaboración exigidas por
la rúbrica (branching, pull requests, revisión de código, issues).

## Estrategia de ramas (GitHub Flow)

```
main ──────────●────────────●───────────●──────►  (siempre desplegable)
                \          /  \         /
   feature/etl-merge ●──●     feature/dashboard ●──●
```

- `main`: rama estable y desplegable. Protegida (no se hace push directo).
- `feature/<área>-<descripción>`: una rama por funcionalidad.
- `fix/<descripción>`: correcciones.
- `docs/<descripción>`: documentación.

## Convención de commits (Conventional Commits)

```
feat(etl): integra fuente SQL de laboratorio
fix(api): maneja 503 cuando no existe el parquet
docs(arch): agrega diagrama mermaid
test(processing): cubre score de riesgo cardiometabólico
chore(docker): optimiza capas de la imagen ETL
```

## Flujo de Pull Request

1. Crear rama desde `main`: `git switch -c feature/mi-cambio`.
2. Commits pequeños y descriptivos.
3. `git push -u origin feature/mi-cambio`.
4. Abrir PR con descripción, checklist y enlace al issue.
5. **Revisión de código** por otro integrante (al menos 1 aprobación).
6. Resolver conflictos y comentarios.
7. *Squash & merge* a `main`.

## Plantilla sugerida de PR

```markdown
## Qué hace
## Por qué
## Cómo probar
- [ ] `pytest` en verde
- [ ] `kedro run` sin errores
## Issues relacionados: #
```

## Uso de Issues
- Etiquetas: `etl`, `api`, `dashboard`, `docker`, `docs`, `bug`.
- Cada feature parte de un issue; el PR lo cierra con `Closes #N`.

## Evidencia a adjuntar para la defensa
Coloca aquí capturas que demuestren la colaboración:
- `repo/screenshots/branches.png` — grafo de ramas y merges.
- `repo/screenshots/pull_request.png` — PR con revisión.
- `repo/screenshots/issues.png` — tablero de issues.

> Comandos útiles para generar evidencia:
> ```bash
> git log --graph --oneline --all
> git branch -a
> ```
