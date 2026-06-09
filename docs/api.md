# Documentación de la API REST

Base URL (local): `http://localhost:8000`
Documentación interactiva (OpenAPI/Swagger): `http://localhost:8000/docs`
Esquema OpenAPI (JSON): `http://localhost:8000/openapi.json`

## Endpoints

### `GET /health`
Estado del servicio y datasets de reporting disponibles.
```json
{ "status": "ok", "reporting_dir": "data/08_reporting", "datasets_kb": {"prevalence": 3.1} }
```

### `GET /prevalence`
Prevalencia (%) de obesidad, hipertensión, diabetes y tabaquismo por grupo etario.
```json
[ {"age_group": "45-64", "obesity_pct": 42.3, "hypertension_pct": 55.1, "diabetes_pct": 18.7, "smoker_pct": 47.2, "n": 1820} ]
```

### `GET /summary?sex=Mujer`
Promedios clínicos por grupo etario y sexo.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `sex` | string (opcional) | `Hombre` o `Mujer` |

### `GET /state-obesity?top=10`
Obesidad por estado (fuente API CDC), ordenada de mayor a menor.

| Parámetro | Tipo | Default | Rango |
|-----------|------|---------|-------|
| `top` | int | 10 | 1–60 |

## Códigos de estado

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 422 | Parámetros inválidos |
| 503 | Dataset no disponible (ejecutar `kedro run` primero) |

## Ejemplos

```bash
curl http://localhost:8000/prevalence
curl "http://localhost:8000/summary?sex=Hombre"
curl "http://localhost:8000/state-obesity?top=5"
```
