# 🩺 NHANES — Plataforma de Análisis de Riesgo Cardiometabólico

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)

Solución **end-to-end** de ciencia de datos sobre la encuesta de salud
**NHANES Pre-Pandemic 2017-marzo 2020 (CDC)**. Integra **tres fuentes de datos**, las procesa con un
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
  [Diccionario de datos](docs/data_dictionary.md) · [Informe de pruebas](docs/testing.md)
- [Guion de presentación](docs/presentation/guion_presentacion.md) ·
  [Workflow de Git](repo/git_workflow.md) · [Cómo contribuir](CONTRIBUTING.md)
- Notebook de análisis exploratorio: [notebooks/01_analisis_exploratorio.ipynb](notebooks/01_analisis_exploratorio.ipynb)

## 📊 Dominio de análisis
Factores de riesgo **cardiometabólico** (obesidad, hipertensión, diabetes y
dislipidemia) en la población adulta de EE.UU. (**15.560 personas**). El pipeline
calcula banderas clínicas (criterios OMS / ACC-AHA) y un **score de riesgo
compuesto (0-4)**.

> 📅 **Periodo:** se usa el dataset **Pre-Pandemic 2017-marzo 2020** (prefijo `P_`),
> que combina los ciclos 2017-2018 y 2019-2020. El ciclo 2019-2020 no se publicó
> por separado debido a la interrupción por COVID-19, por lo que este es el modo
> oficial de incluir datos de 2019-2020.

---
*Datos: [CDC / NHANES Pre-Pandemic 2017-2020](https://wwwn.cdc.gov/nchs/nhanes/). Uso educativo.*
