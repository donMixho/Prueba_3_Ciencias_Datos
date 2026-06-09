"""Dashboard NHANES — punto de entrada (Streamlit multipágina).

Ejecutar:
    streamlit run dashboards/app.py

Las vistas diferenciadas por audiencia están en dashboards/pages/:
    1_Ejecutiva.py  — KPIs y mensajes de negocio
    2_Tecnica.py    — distribuciones y correlaciones para analistas
    3_Operativa.py  — tabla detallada y descarga de datos
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="NHANES · Riesgo Cardiometabólico",
    page_icon="🩺",
    layout="wide",
)

st.title("🩺 NHANES — Análisis de Riesgo Cardiometabólico")
st.markdown(
    """
    Plataforma de análisis **end-to-end** sobre datos de la encuesta
    **NHANES 2017-2018 (CDC)**. Integra tres fuentes de datos (archivos CSV,
    base de datos SQL y API REST), procesadas mediante un pipeline ETL en Kedro.

    ### Audiencias
    Usa el menú lateral para navegar entre vistas diseñadas por audiencia:

    | Vista | Audiencia | Foco |
    |-------|-----------|------|
    | 📊 **Ejecutiva** | Gerencia / negocio | KPIs, prevalencias, mensajes clave |
    | 🔬 **Técnica** | Analistas / data scientists | Distribuciones, correlaciones |
    | 🛠️ **Operativa** | Equipos operativos | Datos detallados, exportación |

    ---
    **Arquitectura:** Archivos + SQL + API REST → ETL (Kedro) → API (FastAPI) → Dashboard (Streamlit), todo en Docker.
    """
)

st.info("Si los gráficos aparecen vacíos, ejecuta primero el pipeline con `kedro run`.")
