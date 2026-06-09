# Diccionario de Datos — NHANES 2017-2018

Fuente: [CDC / NHANES](https://wwwn.cdc.gov/nchs/nhanes/). Todos los archivos se
unen por la llave **`SEQN`** (identificador único del encuestado).

Dominio de análisis: **factores de riesgo cardiometabólico** (obesidad,
diabetes, hipertensión y dislipidemia) en la población de EE.UU.

## Archivos y variables seleccionadas

### Demografía — `DEMO_J` (fuente: archivos)
| Variable    | Descripción                                   | Tipo |
|-------------|-----------------------------------------------|------|
| `SEQN`      | ID del encuestado (llave)                     | int  |
| `RIAGENDR`  | Sexo (1=Hombre, 2=Mujer)                       | cat  |
| `RIDAGEYR`  | Edad en años                                  | num  |
| `RIDRETH3`  | Raza/etnia                                     | cat  |
| `DMDEDUC2`  | Nivel educativo (adultos)                      | cat  |
| `INDFMPIR`  | Razón ingreso familiar / línea de pobreza      | num  |

### Examen físico (fuente: archivos)
**`BMX_J` — Medidas corporales**
| Variable   | Descripción                  |
|------------|------------------------------|
| `BMXBMI`   | Índice de masa corporal (kg/m²) |
| `BMXWT`    | Peso (kg)                    |
| `BMXHT`    | Estatura (cm)                |
| `BMXWAIST` | Circunferencia de cintura (cm) |

**`BPX_J` — Presión arterial**
| Variable           | Descripción                          |
|--------------------|--------------------------------------|
| `BPXSY1`–`BPXSY4`  | Presión sistólica (mmHg), 4 lecturas |
| `BPXDI1`–`BPXDI4`  | Presión diastólica (mmHg), 4 lecturas|

### Laboratorio (fuente: **base de datos SQL / Postgres**)
| Archivo     | Variable  | Descripción                       |
|-------------|-----------|-----------------------------------|
| `GLU_J`     | `LBXGLU`  | Glucosa plasmática en ayunas (mg/dL) |
| `GHB_J`     | `LBXGH`   | Hemoglobina glicosilada HbA1c (%) |
| `TCHOL_J`   | `LBXTC`   | Colesterol total (mg/dL)          |
| `HDL_J`     | `LBDHDD`  | Colesterol HDL (mg/dL)            |
| `TRIGLY_J`  | `LBXTR`   | Triglicéridos (mg/dL)             |
| `TRIGLY_J`  | `LBDLDL`  | Colesterol LDL (mg/dL)            |

### Cuestionario (fuente: archivos)
| Archivo  | Variable  | Descripción                                  |
|----------|-----------|----------------------------------------------|
| `DIQ_J`  | `DIQ010`  | ¿Le han dicho que tiene diabetes? (1=Sí)     |
| `BPQ_J`  | `BPQ020`  | ¿Le han dicho que tiene hipertensión? (1=Sí) |
| `SMQ_J`  | `SMQ020`  | ¿Ha fumado ≥100 cigarrillos en su vida?      |
| `PAQ_J`  | `PAQ650`  | ¿Realiza actividad física vigorosa?          |
| `MCQ_J`  | varias    | Condiciones médicas auto-reportadas          |

### Fuente API REST — `data.cdc.gov` (Socrata)
Enriquecimiento poblacional a nivel estatal: indicadores de obesidad y
actividad física (dataset *Nutrition, Physical Activity, and Obesity*).
Endpoint JSON: `https://data.cdc.gov/resource/hn4x-zwk7.json`

## Variables derivadas (feature engineering)
| Variable derivada     | Definición                                              |
|-----------------------|--------------------------------------------------------|
| `bmi_category`        | Bajo peso / Normal / Sobrepeso / Obesidad (OMS)        |
| `bp_systolic_mean`    | Media de las lecturas sistólicas válidas               |
| `bp_diastolic_mean`   | Media de las lecturas diastólicas válidas              |
| `hypertension_flag`   | ≥130/80 mmHg (criterio ACC/AHA)                        |
| `diabetes_flag`       | HbA1c ≥6.5% o glucosa ayunas ≥126 o DIQ010=1           |
| `age_group`           | Grupos etarios (18-29, 30-44, 45-64, 65+)              |
| `cardiometabolic_risk`| Score compuesto (0-4) de factores de riesgo            |
