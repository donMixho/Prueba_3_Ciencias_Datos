# Manual de Usuario — Dashboard NHANES

## Acceso
Abre <http://localhost:8501> tras levantar el stack (ver `deployment.md`).

## Navegación
El menú lateral izquierdo ofrece tres vistas según tu rol:

### 📊 Ejecutiva
Para gerencia y toma de decisiones. Muestra:
- **KPIs** de prevalencia (obesidad, hipertensión, diabetes, tabaquismo).
- Gráfico de prevalencia por grupo etario.
- Ranking de obesidad por estado.
- Un **mensaje de negocio** que sintetiza el hallazgo principal.

### 🔬 Técnica
Para analistas y científicos de datos. Permite:
- Filtrar por sexo.
- Elegir la métrica clínica a visualizar (IMC, presión, glucosa, HbA1c).
- Ver la tabla resumen y notas metodológicas.

### 🛠️ Operativa
Para equipos operativos. Permite:
- Seleccionar cualquier dataset de reporting.
- Explorar la tabla completa.
- **Descargar** los datos en CSV.

## Interpretación de indicadores

| Indicador | Criterio |
|-----------|----------|
| Obesidad | IMC ≥ 30 kg/m² |
| Hipertensión | ≥ 130/80 mmHg (ACC/AHA) |
| Diabetes | HbA1c ≥ 6.5% o glucosa ≥ 126 mg/dL o autoreporte |
| Score de riesgo | Suma de banderas: 0 (bajo) a 4 (muy alto) |

## Preguntas frecuentes
- **Veo todo vacío.** El pipeline aún no generó datos: ejecuta `kedro run`.
- **¿Los datos son en tiempo real?** No; corresponden al ciclo NHANES 2017-2018
  más un snapshot de la API CDC tomado al ejecutar el pipeline.
