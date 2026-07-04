# 🩺 NHANES — Plataforma de Análisis de Riesgo Cardiometabólico

> Powered by Kedro · scikit-learn · FastAPI · Streamlit · Docker · AWS EC2

Solución end-to-end de ciencia de datos sobre la encuesta de salud NHANES Pre-Pandemic 2017-marzo 2020 (CDC). Integra tres fuentes de datos, las procesa con un pipeline ETL reproducible y expone los resultados mediante una API REST y un dashboard interactivo, todo orquestado con Docker y desplegado en AWS EC2.

**Evaluación Final Transversal — Programación para la Ciencia de Datos (SCY1101).**

---

## 🎯 Las tres fuentes de datos

| # | Tipo | Datos | Tecnología |
|---|------|-------|------------|
| 1 | Archivos planos (CSV/XPT) | Demografía, examen físico, cuestionarios | pandas.CSVDataset |
| 2 | Base de datos SQL | Resultados de laboratorio | PostgreSQL + SQLQueryDataset |
| 3 | API REST | Obesidad por estado | data.cdc.gov (Socrata) |

Todas se unen por la llave **SEQN** (identificador del encuestado).

---

## 🏗️ Arquitectura

```
Archivos CSV ┐
BD SQL       ├─► ETL (Kedro) ─► reporting (Parquet) ─► API (FastAPI) ─► Dashboard (Streamlit)
API REST     ┘     ingestion → processing → reporting
```

Detalle y diagrama en `docs/architecture.md`.

El pipeline tiene **13 nodos**. La etapa de processing entrena además dos modelos de machine learning (riesgo y edad biológica).

---

## 📁 Estructura del proyecto

```
.
├── src/prueba/                  # Pipeline ETL (Kedro)
│   ├── pipelines/
│   │   ├── ingestion/           # Extracción de las 3 fuentes + validación de esquemas
│   │   ├── processing/          # Limpieza, merge por SEQN, feature engineering + modelos ML
│   │   └── reporting/           # Agregaciones para negocio (prevalencia, nutrición, etc.)
│   └── utils/                   # Cliente API REST, validación de esquemas
├── api/                         # API REST (FastAPI) — endpoints de predicción e indicadores
│   ├── main.py                  # Entrypoint de la API
│   ├── Dockerfile               # Imagen Docker de la API
│   └── requirements.txt
├── dashboards/                  # Dashboard interactivo (Streamlit) con vistas por audiencia
│   ├── app.py                   # Página principal
│   ├── pages/                   # Vistas por rol (Ejecutiva, Técnica, Operativa, ML)
│   ├── Dockerfile
│   └── requirements.txt
├── docker/                      # Dockerfiles auxiliares y seed de Postgres
│   ├── Dockerfile.etl           # Imagen para correr el pipeline Kedro
│   ├── Dockerfile.seed          # Imagen para poblar la base de datos
│   └── seed_db.py               # Script de carga inicial de tablas de laboratorio
├── docker-compose.yml           # Orquestación completa del stack (5 servicios)
├── scripts/                     # Descarga reproducible de datos NHANES desde CDC
│   ├── download_nhanes.py       # Descarga archivos XPT
│   └── xpt_to_csv.py            # Convierte XPT a CSV
├── tests/                       # Tests automatizados (pytest) — 26 tests
│   ├── test_processing.py
│   ├── test_model.py
│   ├── test_bioage.py
│   ├── test_api.py
│   ├── test_validation.py
│   ├── test_run.py
│   └── test_io_sources.py
├── docs/                        # Documentación técnica completa
│   ├── architecture.md
│   ├── api.md
│   ├── deployment.md
│   ├── user_manual.md
│   └── data_dictionary.md
├── conf/                        # Configuración Kedro (catálogo, parámetros, credenciales)
│   ├── base/
│   │   ├── catalog.yml
│   │   └── parameters.yml
│   └── local/                   # Credenciales locales (no versionadas, en .gitignore)
│       └── credentials.yml
├── data/                        # Datos (no versionados; reproducibles vía scripts)
│   ├── 01_raw/                  # Datos crudos NHANES (.xpt y .csv)
│   ├── 06_models/               # Artefactos ML: risk_model.pkl, bioage_model.pkl
│   └── 08_reporting/            # Parquets de reporting para API y dashboard
├── repo/                        # Evidencia de colaboración Git (ramas, PRs, commits)
├── notebooks/                   # Análisis exploratorio
│   └── 01_analisis_exploratorio.ipynb
├── .env.example                 # Plantilla de variables de entorno
├── pyproject.toml               # Configuración del proyecto Python/Kedro
└── requirements.txt             # Dependencias del pipeline ETL
```

---

## 🤖 Modelos de Machine Learning

El pipeline de processing entrena tres modelos (scikit-learn) sobre el dataset primario `prm_cardiometabolic` y los persiste como artefactos pickle en `data/06_models/`.

### Modelo 1 — Riesgo Cardiometabólico (clasificación)
- **Tipo:** RandomForestClassifier (200 árboles, max_depth=8) + imputación por mediana.
- **Predice:** alto (1) / bajo (0) riesgo, definido como `cardiometabolic_risk >= 2`.
- **Métricas (test):** accuracy = 0.876 · AUC = 0.967.
- **Features:** `bmi`, `age`, `bp_systolic_mean`, `bp_diastolic_mean`, `hba1c_pct`, `glucose_mgdl`.
- **Artefacto:** `data/06_models/risk_model.pkl`

### Modelo 2 — Edad Biológica (regresión · proxy de longevidad)
- **Tipo:** RandomForestRegressor (300 árboles, max_depth=12) + imputación por mediana.
- **Predice:** edad biológica estimada (años). El age gap (biológica − real) indica envejecimiento acelerado (+) o saludable (−).
- **Métricas (test):** MAE = 9.8 años · R² = 0.54.
- **Features:** 9 variables clínicas (presión, HbA1c, glucosa, colesterol, IMC, cintura…), solo adultos 18+.
- **Artefacto:** `data/06_models/bioage_model.pkl`

> ⚠️ La "edad biológica" es un proxy estadístico de envejecimiento, no una predicción de años de vida.

### Modelo 3 — Perfiles de Salud (clustering · no supervisado)
- **Tipo:** KMeans (k=4) + StandardScaler + imputación por mediana.
- **Propósito:** segmentación **no supervisada** de la población en 4 perfiles de salud a partir de features cardiometabólicas, sin variable objetivo.
- **Salida:** columna `health_cluster` (valores 0–3) en la tabla de predicciones (`model_predictions`).
- **Features:** `bmi`, `age`, `bp_systolic_mean`, `bp_diastolic_mean`, `hba1c_pct`, `glucose_mgdl`, `cholesterol_total`, `waist_cm`.
- **Artefacto:** `data/06_models/clustering_model.pkl`
- **Nodo:** `train_clustering_model_node`

> ℹ️ Los perfiles (clusters) son agrupaciones estadísticas; su etiqueta numérica (0–3) no implica un orden de gravedad.

---

## 🚀 Inicio rápido (Docker — recomendado)

```bash
cp .env.example .env
docker compose up --build
```

| Servicio | URL |
|----------|-----|
| API (docs) | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |

---

## 🛠️ Inicio rápido (local)

```bash
pip install -r requirements.txt
python scripts/download_nhanes.py     # descarga los .XPT de la CDC
python scripts/xpt_to_csv.py          # genera los CSV (fuente 1)
python docker/seed_db.py              # carga la fuente 2 en Postgres (opcional)
kedro run                             # ejecuta el ETL completo (13 nodos, entrena ambos modelos)
uvicorn api.main:app --port 8000      # API
streamlit run dashboards/app.py       # Dashboard
```

---

## ☁️ Despliegue en AWS EC2

El proyecto está configurado para desplegarse en una instancia EC2 de AWS Academy (Learner Lab).

> ⚠️ **Importante:** AWS Academy reasigna la IP pública cada vez que el laboratorio se reinicia.
> La IP activa debe consultarse en la consola de AWS antes de cada sesión.

### Flujo de reconexión (cada sesión)

**Paso 1 — Iniciar el laboratorio**
1. Ingresar a AWS Academy → Learner Lab → clic en **Start Lab**
2. Esperar hasta que el indicador quede en **verde**
3. Clic en **AWS** para abrir la consola
4. Ir a **EC2 → Instances** y copiar el valor de **Public IPv4 address**

**Paso 2 — Conectarse por SSH**
```bash
ssh -i ~/Downloads/nhanes-key.pem ec2-user@<IP_PUBLICA>
```
> Reemplaza `<IP_PUBLICA>` con la IP copiada en el paso anterior.
> Si aparece error de permisos, ejecuta primero: `chmod 400 ~/Downloads/nhanes-key.pem`

**Paso 3 — Levantar el stack**
```bash
cd Prueba_3_Ciencias_Datos
git pull origin Leandro        # trae los últimos cambios
docker-compose up -d           # levanta los 5 servicios en segundo plano
docker-compose ps              # verifica que api y dashboard estén "Up"
```

**Paso 4 — Verificar servicios**

| Servicio | URL |
|----------|-----|
| Dashboard | `http://<IP_PUBLICA>:8501` |
| API (docs) | `http://<IP_PUBLICA>:8000/docs` |

### Configuración de la instancia

| Parámetro | Valor |
|-----------|-------|
| AMI | Amazon Linux 2023 |
| Tipo | t3.medium (2 vCPU, 4 GB RAM) |
| Almacenamiento | 20 GiB (gp3) |

### Puertos habilitados (Security Group)

| Puerto | Protocolo | Uso |
|--------|-----------|-----|
| 22 | TCP | SSH |
| 8000 | TCP | FastAPI |
| 8501 | TCP | Streamlit |

> ⚠️ **Problema encontrado:** Al crear la instancia, los puertos 8000 y 8501 no quedaron abiertos por defecto. Fue necesario editarlos manualmente en EC2 → Security Groups → Inbound Rules → agregar TCP personalizado para cada puerto con origen `0.0.0.0/0`.

### Primera instalación en EC2 (desde cero)

Solo la primera vez que se aprovisiona la instancia (después basta con el *Flujo de reconexión*):

#### Paso 1 — Instalar dependencias
```bash
sudo yum update -y && sudo yum install -y docker git
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker ec2-user
```

#### Paso 2 — Instalar Docker Compose y buildx
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

mkdir -p ~/.docker/cli-plugins
curl -L https://github.com/docker/buildx/releases/download/v0.17.0/buildx-v0.17.0.linux-amd64 -o ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx
```

> ⚠️ **Problema encontrado:** `docker-compose up --build` falló con el error `compose build requires buildx 0.17.0 or later`. Solución: instalar manualmente el plugin `docker-buildx` desde los releases oficiales de GitHub.

#### Paso 3 — Clonar el repositorio
```bash
git clone -b Leandro https://github.com/donMixho/Prueba_3_Ciencias_Datos.git
cd Prueba_3_Ciencias_Datos
```

#### Paso 4 — Crear credenciales de Kedro
```bash
mkdir -p conf/local
cat > conf/local/credentials.yml << 'EOF'
db_lab:
  con: postgresql+psycopg2://nhanes:nhanes@postgres:5432/nhanes
EOF
```

> ⚠️ **Problema encontrado:** Kedro falló con `KeyError: 'db_lab'` porque el archivo `conf/local/credentials.yml` está en `.gitignore` y no se clona. Debe crearse manualmente en la EC2.

#### Paso 5 — Primer build del stack
```bash
cp .env.example .env
docker-compose up --build   # primera vez (construye imágenes)
```

---

## 🌐 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /prevalence | Prevalencia de obesidad, hipertensión, diabetes y tabaquismo por edad |
| GET | /summary | Promedios clínicos por grupo etario y sexo |
| GET | /state-obesity | Obesidad por estado (fuente API REST CDC) |
| GET | /nutrition | Consumo nutricional por categoría de IMC |
| GET | /health | Datasets de reporting disponibles |
| POST | /predict | Predice la probabilidad de alto riesgo cardiometabólico (Modelo 1) |
| POST | /predict-age | Predice la edad biológica y el age gap (Modelo 2) |

---

## 📺 Vistas del dashboard

| Vista | Página | Audiencia / propósito |
|-------|--------|-----------------------|
| 📊 Ejecutiva | pages/1_Ejecutiva.py | KPIs, prevalencias y mensajes de negocio |
| 🔬 Técnica | pages/2_Tecnica.py | Distribuciones, métricas clínicas y correlaciones |
| 🛠️ Operativa | pages/3_Operativa.py | Tablas detalladas y descarga de datos |
| 🤖 Predicción de Riesgo | pages/4_Prediccion.py | Formulario + gauge con la probabilidad de alto riesgo |
| 🧬 Edad Biológica | pages/5_EdadBiologica.py | Gauge de edad biológica vs. edad real (age gap) |

---

## 🧪 Testing

```bash
pytest   # ejecuta los 26 tests con cobertura
```

| Archivo | Tests | Descripción |
|---------|-------|-------------|
| test_processing.py | 4 | Feature engineering y score de riesgo |
| test_model.py | 4 | Modelo de riesgo cardiometabólico |
| test_bioage.py | 3 | Modelo de edad biológica |
| test_api.py | 5 | Endpoints de la API |
| test_validation.py | 5 | Validación de esquemas |
| test_run.py | 3 | Ejecución del pipeline |
| test_io_sources.py | 2 | Fuentes de entrada/salida |

---

## 📚 Documentación

Arquitectura · API · Despliegue · Manual de usuario · Diccionario de datos · Informe de pruebas · Guion de presentación · Workflow de Git · Cómo contribuir

Notebook de análisis exploratorio: `notebooks/01_analisis_exploratorio.ipynb`

---

## 📊 Dominio de análisis

Factores de riesgo cardiometabólico (obesidad, hipertensión, diabetes y dislipidemia) en la población adulta de EE.UU. (15.560 personas). El pipeline calcula banderas clínicas (criterios OMS / ACC-AHA) y un score de riesgo compuesto (0-4).

**Periodo:** dataset Pre-Pandemic 2017-marzo 2020 (prefijo `P_`), que combina los ciclos 2017-2018 y 2019-2020.

---

## 📝 Changelog

### 2026-07-03 — Despliegue en AWS EC2
- Instancia EC2 `t3.medium` con Amazon Linux 2023 levantada en AWS Academy Learner Lab.
- Stack completo desplegado vía `docker-compose` (Postgres + ETL + API + Dashboard).
- Security Group configurado con puertos 8000 y 8501 abiertos públicamente.
- Credenciales de Kedro (`conf/local/credentials.yml`) creadas manualmente en la instancia.
- Plugin `docker-buildx` instalado manualmente para compatibilidad con Docker Compose v5.
- URLs públicas activas: Dashboard `:8501` · API `:8000/docs`.

### 2026-06-26 — Modelos de ML y nuevas vistas del dashboard
- Machine Learning: dos modelos entrenados en el pipeline de processing.
- Modelo 1: Riesgo Cardiometabólico (RandomForestClassifier, accuracy=0.876, AUC=0.967).
- Modelo 2: Edad Biológica (RandomForestRegressor, MAE=9.8 años, R²=0.54).
- Pipeline: ahora 13 nodos; nuevos nodos `train_risk_model_node` y `train_bioage_model_node`.
- API: nuevos endpoints `POST /predict` y `POST /predict-age`.
- Dashboard: nuevas vistas Predicción de Riesgo y Edad Biológica.
- Tests: suite ampliada a 26 tests.
- Dependencias: se añade `scikit-learn`.

---

> Datos: CDC / NHANES Pre-Pandemic 2017-2020. Uso educativo.
