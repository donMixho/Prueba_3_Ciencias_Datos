"""Dashboard NHANES — punto de entrada (Streamlit multipágina).

Ejecutar:
    streamlit run dashboards/app.py

Las vistas diferenciadas por audiencia están en dashboards/pages/:
    1_Ejecutiva.py     — KPIs y mensajes de negocio
    2_Tecnica.py       — distribuciones y correlaciones para analistas
    3_Operativa.py     — tabla detallada y descarga de datos
    4_Prediccion.py    — predicción de riesgo con el modelo de ML
    5_EdadBiologica.py — edad biológica (proxy de longevidad) con ML
    6_Clustering.py    — segmentación en perfiles de salud (clustering)
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

def render_card(col, icon, title, who, desc, page):
    """Renderiza una tarjeta con su botón de navegación dentro de una columna."""
    with col:
        st.markdown(
            f"""<div class="nav-card">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-weight:700;font-size:1.15rem;color:{PRIMARY}">{title}</div>
                <div style="color:{MUTED};font-size:.8rem;font-weight:600;margin-bottom:.5rem">{who}</div>
                <div style="color:#334155;font-size:.92rem">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.page_link(page, label=f"Abrir {title}", icon=icon, use_container_width=True)


section("Elige tu vista según tu rol")
r1, r2, r3 = st.columns(3)
render_card(r1, "📊", "Ejecutiva", "Gerencia / negocio", "KPIs, prevalencias y mensajes clave para decidir.", "pages/1_Ejecutiva.py")
render_card(r2, "🔬", "Técnica", "Analistas / data science", "Distribuciones, métricas clínicas y correlaciones.", "pages/2_Tecnica.py")
render_card(r3, "🛠️", "Operativa", "Equipos operativos", "Tablas detalladas y exportación de datos.", "pages/3_Operativa.py")

st.markdown("")
section("Modelos de Machine Learning")
m1, m2, m3 = st.columns(3)
render_card(m1, "🤖", "Predicción de Riesgo", "Clasificación", "Probabilidad de alto riesgo cardiometabólico de una persona.", "pages/4_Prediccion.py")
render_card(m2, "🧬", "Edad Biológica", "Regresión · longevidad", "Estima cuántos años aparenta tu cuerpo (age gap).", "pages/5_EdadBiologica.py")
render_card(m3, "🧩", "Perfiles de Salud", "Clustering · no supervisado", "Agrupa a una persona en uno de los 4 perfiles de salud (KMeans).", "pages/6_Clustering.py")

st.markdown("")
st.info("Abre una vista con los botones o desde el menú lateral. Si los gráficos salen vacíos, ejecuta el pipeline con `kedro run`.")

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
