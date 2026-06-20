# 🎤 Guion de Presentación Individual (15 min)

> Defensa de la Evaluación Parcial N°3 — *Programación para la Ciencia de Datos*.
> Cada diapositiva trae **qué mostrar** y **qué decir** (notas del orador).
> Pesos de la rúbrica: Demo end-to-end (30%), Dashboards por audiencia (30%),
> Trabajo colaborativo (40%).

---

## Slide 1 — Portada (30 seg)
**Mostrar:** título del proyecto, tu nombre, asignatura, logo Duoc.

> "Buenos días. Presento *NHANES — Plataforma de Análisis de Riesgo
> Cardiometabólico*, una solución end-to-end de ciencia de datos que integra
> tres fuentes, las procesa con un pipeline ETL y las expone en una API y un
> dashboard, todo en Docker."

---

## Slide 2 — El problema y los datos (1 min)
**Mostrar:** logo CDC/NHANES, los números (9.254 personas, 13 archivos usados, 3 fuentes).

> "Usamos datos reales de la encuesta de salud NHANES 2017-2018 del CDC de EE.UU.
> El objetivo: medir factores de riesgo cardiometabólico —obesidad, hipertensión
> y diabetes— en la población adulta. Trabajamos con más de 9.000 personas
> integradas desde tres tipos de fuente distintos."

---

## Slide 3 — Arquitectura (2 min) · *cubre indicador Demo (30%)*
**Mostrar:** el diagrama de `docs/architecture.md` (Fuentes → ETL → API → Dashboard).

> "La arquitectura tiene cuatro capas. **Tres fuentes**: archivos CSV con
> demografía y examen; una **base de datos PostgreSQL** con los datos de
> laboratorio; y una **API REST** de data.cdc.gov. Todas se integran por la
> llave SEQN en un **pipeline ETL en Kedro** con tres etapas: ingestión,
> procesamiento y reporting. El resultado lo sirve una **API en FastAPI** que
> consume el **dashboard en Streamlit**. Todo se orquesta con **Docker
> Compose**."

**Decisiones clave a justificar:**
- *¿Por qué Kedro?* → catálogo declarativo, capas y reproducibilidad.
- *¿Por qué Parquet?* → eficiencia y tipado en capas intermedias.
- *¿Por qué API intermedia?* → desacopla el dashboard; degradación elegante.

---

## Slide 4 — DEMO EN VIVO: el pipeline (3 min) · *indicador Demo (30%)*
**Mostrar (en terminal):**
```bash
docker compose up          # o, local: kedro run
```
**Mostrar (Kedro Viz, opcional):** `kedro viz`

> "Levanto el stack. Postgres arranca, se siembran los datos de laboratorio, el
> ETL integra las tres fuentes y genera las tablas de reporting. Aquí vemos el
> grafo del pipeline: cada nodo es una transformación trazable."

**Plan B (si falla Docker):** mostrar `kedro run` local y los parquet generados.

---

## Slide 5 — DEMO EN VIVO: API REST (1.5 min)
**Mostrar:** `http://localhost:8000/docs` → ejecutar `/prevalence` y `/state-obesity`.

> "La API expone los indicadores como JSON, documentada automáticamente con
> OpenAPI. Aquí pido la prevalencia por edad… y la obesidad por estado, que
> viene de la fuente API del CDC."

---

## Slide 6 — DEMO EN VIVO: Dashboard por audiencia (3 min) · *indicador Dashboards (30%)*
**Mostrar:** `http://localhost:8501`, recorrer las 3 vistas.

> "El dashboard está diseñado para **tres audiencias**:
> - **Ejecutiva**: KPIs y el mensaje de negocio —el riesgo se concentra en
>   adultos de 45+.
> - **Técnica**: distribuciones y métricas clínicas filtrables, para analistas.
> - **Operativa**: tablas detalladas y descarga en CSV para el día a día.
> La misma data, comunicada distinto según quién la consume y qué decisión toma."

**Valor de negocio a mencionar:** focalizar prevención en mayores de 45;
priorizar estados con mayor obesidad.

---

## Slide 7 — Trabajo colaborativo (2.5 min) · *indicador Colaboración (40% — el que más pesa)*
**Mostrar:** GitHub → grafo de ramas, un Pull Request con revisión, los issues, la CI en verde.

> "Trabajamos con **GitHub Flow**: rama `main` siempre desplegable y una rama por
> funcionalidad. Cada cambio entró por **Pull Request** con revisión de un
> compañero y **CI automática** que corre lint y tests. Usamos **issues** con
> etiquetas y **Conventional Commits** para un historial limpio. Aquí se ve un
> PR real con sus comentarios y la resolución de un conflicto."

**Metodología:** roles (ETL, API, Dashboard, DevOps), tablero de issues.

---

## Slide 8 — Calidad: testing, Docker, configuración (1 min)
**Mostrar:** salida de `pytest` (11 tests verdes), `docker-compose.yml`, `.env.example`.

> "La calidad se sostiene en **tests automatizados**, **contenedores Docker**
> con docker-compose y healthchecks, configuración por **variables de entorno**
> y **logging** en cada módulo."

---

## Slide 9 — Lecciones aprendidas y mejoras (1 min) · *indicador Colaboración (40%)*
**Mostrar:** lista breve.

> "Aprendimos que **desacoplar con una API** facilita el trabajo en paralelo.
> Un desafío fue **integrar fuentes heterogéneas** unificándolas por SEQN.
> Como mejoras futuras: añadir más fuentes (dieta), un modelo predictivo de
> riesgo y despliegue en la nube con CI/CD."

---

## Slide 10 — Cierre (30 seg)
**Mostrar:** links al repo y resumen de la arquitectura.

> "En resumen: una solución end-to-end, reproducible y colaborativa, desde el
> dato crudo del CDC hasta una visualización lista para decidir. Gracias,
> quedo atento a sus preguntas."

---

## ⏱️ Control de tiempo
| Bloque | Min |
|--------|-----|
| Intro + datos + arquitectura | 3.5 |
| Demo (pipeline + API + dashboard) | 7.5 |
| Colaboración + calidad + lecciones | 4.5 |
| **Total** | **~15** |

## ✅ Checklist antes de presentar
- [ ] Docker corriendo y `docker compose up` probado **antes** de la defensa
- [ ] Dashboard y API abiertos en pestañas
- [ ] GitHub abierto en el grafo de ramas y un PR
- [ ] `pytest` ejecutado para mostrar verde
- [ ] Plan B listo (capturas) por si falla el internet/Docker
