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
from theme import MUTED, PRIMARY, footer, page_header, section, setup_page

setup_page("Inicio", "🩺")

page_header(
    "Análisis de Riesgo Cardiometabólico",
    "Plataforma end-to-end de salud poblacional — obesidad, hipertensión y diabetes",
)

st.markdown(
    "Solución de datos que integra **tres fuentes** (archivos CSV, base de datos SQL "
    "y una API REST), procesadas con un pipeline **ETL en Kedro** y expuestas vía "
    "**API (FastAPI)** y este **dashboard (Streamlit)**."
)

section("Elige tu vista según tu rol")

c1, c2, c3 = st.columns(3)
cards = [
    (c1, "📊", "Ejecutiva", "Gerencia / negocio", "KPIs, prevalencias y mensajes clave para decidir."),
    (c2, "🔬", "Técnica", "Analistas / data science", "Distribuciones, métricas clínicas y correlaciones."),
    (c3, "🛠️", "Operativa", "Equipos operativos", "Tablas detalladas y exportación de datos."),
]
for col, icon, title, who, desc in cards:
    col.markdown(
        f"""<div style="background:#fff;border:1px solid #E2E8F0;border-radius:14px;
            padding:1.3rem;height:100%;box-shadow:0 1px 3px rgba(15,23,42,.06)">
            <div style="font-size:2rem">{icon}</div>
            <div style="font-weight:700;font-size:1.15rem;color:{PRIMARY}">{title}</div>
            <div style="color:{MUTED};font-size:.8rem;font-weight:600;margin-bottom:.5rem">{who}</div>
            <div style="color:#334155;font-size:.92rem">{desc}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("")
st.info("👈 Usa el menú lateral para abrir cada vista. Si los gráficos salen vacíos, ejecuta el pipeline con `kedro run`.")

section("Arquitectura")
st.markdown(
    """
    ```
    Archivos CSV ┐
    BD SQL       ├─► ETL (Kedro) ─► API (FastAPI) ─► Dashboard (Streamlit)
    API REST     ┘
    ```
    """
)

footer()
