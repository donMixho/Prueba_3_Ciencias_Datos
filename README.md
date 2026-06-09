# 🩺 NHANES — Plataforma de Análisis de Riesgo Cardiometabólico

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)

Solución **end-to-end** de ciencia de datos sobre la encuesta de salud
**NHANES 2017-2018 (CDC)**. Integra **tres fuentes de datos**, las procesa con un
pipeline ETL reproducible y expone los resultados mediante una **API REST** y un
**dashboard interactivo**, todo orquestado con **Docker**.

> Evaluación Parcial N°3 — *Programación para la Ciencia de Datos (SCY1101)*.

## 🎯 Las tres fuentes de datos

| # | Tipo | Datos | Tecnología |
|---|------|-------|-----------|
| 1 | **Archivos planos (CSV/XPT)** | Demografía, examen físico, cuestionarios | `pandas.CSVDataset` |
| 2 | **Base de datos SQL** | Resultados de laboratorio | PostgreSQL + `SQLQueryDataset` |
| 3 | **API REST** | Obesidad por estado | `data.cdc.gov` (Socrata) |

Todas se unen por la llave **`SEQN`** (identificador del encuestado).

## 🏗️ Arquitectura

```
Archivos CSV ┐
BD SQL       ├─► ETL (Kedro) ─► reporting (Parquet) ─► API (FastAPI) ─► Dashboard (Streamlit)
API REST     ┘     ingestion → processing → reporting
```
Detalle y diagrama en [docs/architecture.md](docs/architecture.md).

## 📁 Estructura del proyecto

```
.
├── src/prueba/            # Pipeline ETL (Kedro)
│   ├── pipelines/
│   │   ├── ingestion/     #  extracción de las 3 fuentes + validación
│   │   ├── processing/    #  limpieza, merge por SEQN, feature engineering
│   │   └── reporting/     #  agregaciones para negocio
│   └── utils/             #  cliente API REST, validación de esquemas
├── api/                   # API REST (FastAPI)
├── dashboards/            # Dashboard (Streamlit) con vistas por audiencia
├── docker/                # Dockerfiles, seed de Postgres
├── docker-compose.yml     # Orquestación de todo el stack
├── scripts/               # Descarga reproducible de datos NHANES
├── tests/                 # Tests automatizados (pytest)
├── docs/                  # Arquitectura, API, manual, despliegue, diccionario
├── repo/                  # Evidencia de colaboración Git
├── conf/                  # Catálogo, parámetros y credenciales (Kedro)
└── data/                  # Datos (no versionados; reproducibles vía scripts)
```

## 🚀 Inicio rápido (Docker)

```bash
cp .env.example .env
docker compose up --build
```
- API → <http://localhost:8000/docs>
- Dashboard → <http://localhost:8501>

## 🛠️ Inicio rápido (local)

```bash
pip install -r requirements.txt
python scripts/download_nhanes.py     # descarga los .XPT de la CDC
python scripts/xpt_to_csv.py          # genera los CSV (fuente 1)
python docker/seed_db.py              # carga la fuente 2 en Postgres (opcional)
kedro run                             # ejecuta el ETL completo
uvicorn api.main:app --port 8000      # API
streamlit run dashboards/app.py       # Dashboard
```

## 🧪 Testing

```bash
pytest                # ejecuta los tests con cobertura
```

## 📚 Documentación

- [Arquitectura](docs/architecture.md) · [API](docs/api.md) ·
  [Despliegue](docs/deployment.md) · [Manual de usuario](docs/user_manual.md) ·
  [Diccionario de datos](docs/data_dictionary.md)
- [Workflow de Git](repo/git_workflow.md)

## 📊 Dominio de análisis
Factores de riesgo **cardiometabólico** (obesidad, hipertensión, diabetes y
dislipidemia) en la población adulta de EE.UU. El pipeline calcula banderas
clínicas (criterios OMS / ACC-AHA) y un **score de riesgo compuesto (0-4)**.

---
*Datos: [CDC / NHANES 2017-2018](https://wwwn.cdc.gov/nchs/nhanes/). Uso educativo.*
