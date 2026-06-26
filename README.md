# 🩺 NHANES — Plataforma de Análisis de Riesgo Cardiometabólico

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Modelos](https://img.shields.io/badge/modelos-2_RandomForest-0E7490)]()
[![Tests](https://img.shields.io/badge/tests-26_passing-2ea44f)]()

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

> El pipeline tiene **11 nodos**. La etapa de **processing** entrena además dos modelos de
> machine learning (riesgo y edad biológica) — ver [Modelos de Machine Learning](#-modelos-de-machine-learning).

## 🤖 Modelos de Machine Learning

El pipeline de **processing** entrena dos modelos (scikit-learn) sobre el dataset primario
`prm_cardiometabolic` y los persiste como artefactos `pickle` en `data/06_models/`,
consumibles tanto por la **API** como por el **dashboard**.

### Modelo 1 — Riesgo Cardiometabólico (clasificación)
- **Tipo:** `RandomForestClassifier` (200 árboles, `max_depth=8`) + imputación por mediana.
- **Predice:** alto (`1`) / bajo (`0`) riesgo, definido como `cardiometabolic_risk >= 2`.
- **Métricas (test):** `accuracy = 0.876` · `AUC = 0.967`.
- **Features:** `bmi`, `age`, `bp_systolic_mean`, `bp_diastolic_mean`, `hba1c_pct`, `glucose_mgdl`.
- **Artefacto:** `data/06_models/risk_model.pkl`
- **Nodo:** `train_risk_model_node`

### Modelo 2 — Edad Biológica (regresión · proxy de longevidad)
- **Tipo:** `RandomForestRegressor` (300 árboles, `max_depth=12`) + imputación por mediana.
- **Predice:** edad biológica estimada (años). El *age gap* (biológica − real) indica
  envejecimiento acelerado (`+`) o saludable (`−`).
- **Métricas (test):** `MAE = 9.8 años` · `R² = 0.54`.
- **Features:** 9 variables clínicas (presión, HbA1c, glucosa, colesterol, IMC, cintura…), solo **adultos 18+**.
- **Artefacto:** `data/06_models/bioage_model.pkl`
- **Nodo:** `train_bioage_model_node`

**Registro en Kedro:**
- `conf/base/catalog.yml` → `risk_model` y `bioage_model` (`pickle.PickleDataset`).
- `conf/base/parameters.yml` → secciones `model` y `bioage_model` (features, umbral e hiperparámetros).

> ⚠️ La "edad biológica" es un **proxy estadístico** de envejecimiento, **no** una predicción de
> años de vida. Además, el IMC y la presión también intervienen en el cálculo del score de
> riesgo, por lo que el AUC del Modelo 1 puede estar parcialmente inflado (fuga de información).

## 📁 Estructura del proyecto

```
.
├── src/prueba/            # Pipeline ETL (Kedro)
│   ├── pipelines/
│   │   ├── ingestion/     #  extracción de las 3 fuentes + validación
│   │   ├── processing/    #  limpieza, merge por SEQN, feature engineering + modelos ML
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
    └── 06_models/         # Artefactos de ML: risk_model.pkl, bioage_model.pkl
```

## 🚀 Inicio rápido (Docker)

```bash
cp .env.example .env
docker compose up --build
```
- API → <http://localhost:8000/docs>
  - Indicadores: `/prevalence` · `/summary` · `/state-obesity` · `/nutrition` · `/health`
  - **Modelos (nuevos):** `POST /predict` · `POST /predict-age`
- Dashboard → <http://localhost:8501>
  - Vistas por rol: 📊 Ejecutiva · 🔬 Técnica · 🛠️ Operativa
  - **Modelos de ML (nuevos):** 🤖 Predicción de Riesgo (`pages/4_Prediccion.py`) · 🧬 Edad Biológica (`pages/5_EdadBiologica.py`)

## 🛠️ Inicio rápido (local)

```bash
pip install -r requirements.txt
python scripts/download_nhanes.py     # descarga los .XPT de la CDC
python scripts/xpt_to_csv.py          # genera los CSV (fuente 1)
python docker/seed_db.py              # carga la fuente 2 en Postgres (opcional)
kedro run                             # ejecuta el ETL completo (11 nodos, entrena ambos modelos)
uvicorn api.main:app --port 8000      # API
streamlit run dashboards/app.py       # Dashboard
```

## 🌐 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET`  | `/prevalence` | Prevalencia de obesidad, hipertensión, diabetes y tabaquismo por edad |
| `GET`  | `/summary` | Promedios clínicos por grupo etario y sexo |
| `GET`  | `/state-obesity` | Obesidad por estado (fuente API REST CDC) |
| `GET`  | `/nutrition` | Consumo nutricional por categoría de IMC |
| `GET`  | `/health` | Datasets de reporting disponibles |
| `POST` | **`/predict`** | Predice la probabilidad de **alto riesgo** cardiometabólico (Modelo 1) |
| `POST` | **`/predict-age`** | Predice la **edad biológica** y el *age gap* (Modelo 2) |

## 📺 Vistas del dashboard

| Vista | Página | Audiencia / propósito |
|-------|--------|------------------------|
| 📊 Ejecutiva | `pages/1_Ejecutiva.py` | KPIs, prevalencias y mensajes de negocio |
| 🔬 Técnica | `pages/2_Tecnica.py` | Distribuciones, métricas clínicas y correlaciones |
| 🛠️ Operativa | `pages/3_Operativa.py` | Tablas detalladas y descarga de datos |
| 🤖 Predicción de Riesgo | `pages/4_Prediccion.py` | Formulario + gauge con la probabilidad de alto riesgo |
| 🧬 Edad Biológica | `pages/5_EdadBiologica.py` | Gauge de edad biológica vs. edad real (*age gap*) |

> La página de inicio agrupa las vistas en **"Elige tu vista según tu rol"** y la nueva sección
> **"Modelos de Machine Learning"**, con tarjetas y botones interactivos.

## 🧪 Testing

```bash
pytest                # ejecuta los tests con cobertura
```
**26 tests** automatizados, todos pasando. Suite por archivo:
- `tests/test_processing.py` — feature engineering y score de riesgo (4)
- `tests/test_model.py` — modelo de riesgo cardiometabólico (4) *(nuevo)*
- `tests/test_bioage.py` — modelo de edad biológica (3) *(nuevo)*
- `tests/test_api.py` (5) · `tests/test_validation.py` (5) · `tests/test_run.py` (3) · `tests/test_io_sources.py` (2)

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

## 📝 Changelog

### 2026-06-26 — Modelos de ML y nuevas vistas del dashboard
- **Machine Learning:** se agregan dos modelos entrenados en el pipeline de *processing*:
  - Modelo 1 **Riesgo Cardiometabólico** (`RandomForestClassifier`, `accuracy=0.876`, `AUC=0.967`).
  - Modelo 2 **Edad Biológica** (`RandomForestRegressor`, `MAE=9.8 años`, `R²=0.54`).
- **Pipeline:** ahora **11 nodos**; nuevos nodos `train_risk_model_node` y `train_bioage_model_node`.
- **Kedro:** nuevos datasets `risk_model` y `bioage_model` (`PickleDataset`) en `catalog.yml`;
  nuevas secciones `model` y `bioage_model` en `parameters.yml`.
- **API:** nuevos endpoints `POST /predict` y `POST /predict-age`.
- **Dashboard:** nuevas vistas 🤖 *Predicción de Riesgo* y 🧬 *Edad Biológica*, sección
  "Modelos de ML" en el inicio y botones/tarjetas interactivos.
- **Tests:** suite ampliada a **26 tests** (nuevos `tests/test_model.py` y `tests/test_bioage.py`).
- **Dependencias:** se añade `scikit-learn`.

---
*Datos: [CDC / NHANES Pre-Pandemic 2017-2020](https://wwwn.cdc.gov/nchs/nhanes/). Uso educativo.*
</content>
</invoke>