# Guía de Despliegue

## Opción A — Docker (recomendada)

Requisitos: Docker Desktop / Docker Engine + Docker Compose.

```bash
# 1. Configurar variables de entorno
cp .env.example .env

# 2. Levantar todo el stack (Postgres + seed + ETL + API + Dashboard)
docker compose up --build
```

Orden de arranque (gestionado por `depends_on` + healthchecks):
1. `postgres` arranca y queda *healthy*.
2. `db-seed` carga las tablas de laboratorio y termina.
3. `etl` ejecuta `kedro run` (integra las 3 fuentes → genera reporting).
4. `api` y `dashboard` quedan disponibles.

Acceso:
- API: <http://localhost:8000/docs>
- Dashboard: <http://localhost:8501>

Detener y limpiar:
```bash
docker compose down          # detiene
docker compose down -v       # detiene y borra el volumen de Postgres
```

## Opción B — Local (sin Docker)

```bash
# 1. Entorno e instalación
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Descargar y preparar datos
python scripts/download_nhanes.py
python scripts/xpt_to_csv.py

# 3. Sembrar la fuente SQL (por defecto SQLite, sin servidor)
python docker/seed_db.py
#    (Para usar Postgres en su lugar: exporta DB_URL antes de este paso)

# 4. Ejecutar el pipeline ETL completo (integra las 3 fuentes)
kedro run

# 5. Levantar API y dashboard (en terminales separadas)
uvicorn api.main:app --reload --port 8000
streamlit run dashboards/app.py
```

## Ejecutar solo una parte del pipeline

```bash
kedro run --pipeline ingestion
kedro run --pipeline processing
kedro run --pipeline reporting
kedro run --node merge_clinical_node
```

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| API responde 503 | No se ejecutó el ETL | `kedro run` o esperar al servicio `etl` |
| Dashboard vacío | Reporting no generado | Verificar `data/08_reporting/*.parquet` |
| Error de conexión SQL | Postgres no listo / credenciales | Revisar `.env` y `docker compose logs postgres` |
| API CDC sin datos | Filtro `where` muy estricto | Ajustar `cdc_api.where` en `parameters.yml` |

## Configuración de credenciales locales

Crear el archivo `conf/local/credentials.yml` con el siguiente contenido:

```yaml
db_lab:
  con: postgresql+psycopg2://nhanes:nhanes@postgres:5432/nhanes
```

> Este archivo está en `.gitignore` y no se versiona por seguridad.
