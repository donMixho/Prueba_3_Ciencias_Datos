# Informe de Pruebas (Testing)

El proyecto usa **pytest** con cobertura (`pytest-cov`). La configuración está en
`pyproject.toml` (`[tool.pytest.ini_options]` y `[tool.coverage.report]`).

## Cómo ejecutar

```bash
pytest                       # toda la suite con reporte de cobertura
pytest tests/test_processing.py -q   # un archivo
pytest -k features           # por palabra clave
```

> En entorno local sin instalar el paquete: `PYTHONPATH=src pytest`.

## Resultado actual

```
18 passed
Cobertura total: 59%  (núcleo de transformación > 84%)
```

## Cobertura por módulo (núcleo del pipeline)

| Módulo | Cobertura | Qué valida |
|--------|-----------|------------|
| `utils/io_sources.py` | 97% | Cliente API CDC: éxito y reintentos |
| `utils/validation.py` | 84% | Esquemas, llaves únicas, códigos faltantes |
| `pipelines/processing/nodes.py` | 97% | Merge, limpieza, feature engineering |
| `pipelines/reporting/nodes.py` | 100% | Agregaciones y filtro de adultos |

## Suite de pruebas

| Archivo | Tests | Foco |
|---------|-------|------|
| `tests/test_validation.py` | 5 | Validación de esquemas y limpieza de códigos NHANES |
| `tests/test_processing.py` | 4 | Categorías de IMC, grupos etarios, banderas clínicas y score de riesgo |
| `tests/test_io_sources.py` | 2 | Cliente de la API REST (con mocks, sin red) |
| `tests/test_run.py` | 3 | Estructura y conexiones de los pipelines |
| `tests/test_api.py` | 4 | Endpoints de la API REST (TestClient) |
| **Total** | **18** | |

## Tipos de prueba aplicados

- **Unitarias**: funciones de transformación y validación (entradas controladas).
- **De contrato/mocks**: la llamada a la API externa se prueba sin red usando
  `monkeypatch`, verificando el manejo de errores y reintentos.
- **Estructurales**: que los pipelines se construyan y conecten los datasets
  esperados (`prm_cardiometabolic`, `raw_cdc_obesity_api`).

## Integración continua (CI)

Cada *push* y *pull request* dispara el workflow `.github/workflows/ci.yml`, que:
1. Instala dependencias en Python 3.10 y 3.11.
2. Corre `ruff check` (lint).
3. Ejecuta `pytest` con cobertura.

Un PR no se mergea a `main` si la CI falla.

## Próximas pruebas sugeridas

- Test de integración end-to-end del `merge_clinical` con datos de muestra.
- Tests de los endpoints de la API con `TestClient` de FastAPI.
- Validación de contrato del esquema de salida (`prm_cardiometabolic`).
