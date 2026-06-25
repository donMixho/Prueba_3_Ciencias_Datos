# Diccionario de Datos — NHANES Pre-Pandemic 2017-marzo 2020

Fuente: [CDC / NHANES](https://wwwn.cdc.gov/nchs/nhanes/). Todos los archivos se
unen por la llave **`SEQN`** (identificador único del encuestado).

Dominio de análisis: **factores de riesgo cardiometabólico** (obesidad,
diabetes, hipertensión y dislipidemia) en la población de EE.UU.
(**15.560 personas**).

> 📅 Se usa el dataset **Pre-Pandemic 2017-marzo 2020** (archivos con prefijo
> `P_`), que combina los ciclos 2017-2018 y 2019-2020. El 2019-2020 no se publicó
> por separado por la interrupción del COVID-19. La presión arterial pasó a
> medición **oscilométrica** (`P_BPXO`).

## Archivos y variables seleccionadas

### Demografía — `P_DEMO` (fuente: archivos)
| Variable    | Descripción                                   | Tipo |
|-------------|-----------------------------------------------|------|
| `SEQN`      | ID del encuestado (llave)                     | int  |
| `RIAGENDR`  | Sexo (1=Hombre, 2=Mujer)                       | cat  |
| `RIDAGEYR`  | Edad en años                                  | num  |
| `RIDRETH3`  | Raza/etnia                                     | cat  |
| `DMDEDUC2`  | Nivel educativo (adultos)                      | cat  |
| `INDFMPIR`  | Razón ingreso familiar / línea de pobreza      | num  |

### Examen físico (fuente: archivos)
**`P_BMX` — Medidas corporales**
| Variable   | Descripción                  |
|------------|------------------------------|
| `BMXBMI`   | Índice de masa corporal (kg/m²) |
| `BMXWT`    | Peso (kg)                    |
| `BMXHT`    | Estatura (cm)                |
| `BMXWAIST` | Circunferencia de cintura (cm) |

**`P_BPXO` — Presión arterial (oscilométrica)**
| Variable             | Descripción                            |
|----------------------|----------------------------------------|
| `BPXOSY1`–`BPXOSY3`  | Presión sistólica (mmHg), 3 lecturas   |
| `BPXODI1`–`BPXODI3`  | Presión diastólica (mmHg), 3 lecturas  |

### Dieta / Nutrición — `P_DR1TOT` (fuente: archivos)
Recordatorio dietético de 24 h (Día 1), totales diarios por persona.
| Variable    | Descripción                          |
|-------------|--------------------------------------|
| `DR1TKCAL`  | Energía (kcal)                       |
| `DR1TSUGR`  | Azúcar total (g)                     |
| `DR1TSODI`  | Sodio (mg)                           |
| `DR1TTFAT`  | Grasa total (g)                      |
| `DR1TSFAT`  | Grasa saturada (g)                   |
| `DR1TFIBE`  | Fibra (g)                            |
| `DR1TPROT`  | Proteína (g)                         |
| `DR1TCARB`  | Carbohidratos (g)                    |

### Laboratorio (fuente: **base de datos SQL / Postgres**)
| Archivo     | Variable  | Descripción                       |
|-------------|-----------|-----------------------------------|
| `P_GLU`     | `LBXGLU`  | Glucosa plasmática en ayunas (mg/dL) |
| `P_GHB`     | `LBXGH`   | Hemoglobina glicosilada HbA1c (%) |
| `P_TCHOL`   | `LBXTC`   | Colesterol total (mg/dL)          |
| `P_HDL`     | `LBDHDD`  | Colesterol HDL (mg/dL)            |
| `P_TRIGLY`  | `LBXTR`   | Triglicéridos (mg/dL)             |
| `P_TRIGLY`  | `LBDLDL`  | Colesterol LDL (mg/dL)            |

### Cuestionario (fuente: archivos)
| Archivo  | Variable  | Descripción                                  |
|----------|-----------|----------------------------------------------|
| `P_DIQ`  | `DIQ010`  | ¿Le han dicho que tiene diabetes? (1=Sí)     |
| `P_BPQ`  | `BPQ020`  | ¿Le han dicho que tiene hipertensión? (1=Sí) |
| `P_SMQ`  | `SMQ020`  | ¿Ha fumado ≥100 cigarrillos en su vida?      |
| `P_PAQ`  | `PAQ650`  | ¿Realiza actividad física vigorosa?          |
| `P_MCQ`  | varias    | Condiciones médicas auto-reportadas          |

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
