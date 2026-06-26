"""Vista Predicción — modelo de ML que estima el riesgo cardiometabólico.

Permite ingresar los datos clínicos de una persona y obtener la probabilidad
de **alto riesgo** (score >= 2) según el ``RandomForestClassifier`` entrenado
en el pipeline. Consume la API (``/predict``) y, si no está, el modelo local.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from data_access import predict
from theme import MUTED, RISK, footer, page_header, section, setup_page, style_fig

setup_page("Predicción", "🤖")
page_header(
    "Predicción de Riesgo (ML)",
    "Modelo RandomForest que estima la probabilidad de alto riesgo cardiometabólico",
)

st.markdown(
    "Ingresa los datos de una persona y el modelo estimará su **probabilidad de "
    "alto riesgo** (score clínico ≥ 2). Los campos sin datos se imputan "
    "automáticamente con la mediana del entrenamiento."
)

# --- Formulario de entrada ---
section("Datos de la persona")
c1, c2, c3 = st.columns(3)
age = c1.number_input("Edad (años)", min_value=18, max_value=100, value=50)
bmi = c1.number_input("IMC (kg/m²)", min_value=10.0, max_value=60.0, value=28.0, step=0.1)
sys_bp = c2.number_input("Presión sistólica (mmHg)", min_value=80, max_value=220, value=130)
dia_bp = c2.number_input("Presión diastólica (mmHg)", min_value=40, max_value=140, value=82)
glucose = c3.number_input("Glucosa (mg/dL)", min_value=50, max_value=400, value=100)
hba1c = c3.number_input("HbA1c (%)", min_value=3.0, max_value=15.0, value=5.6, step=0.1)

st.markdown("")
go_predict = st.button("🔮 Predecir riesgo", type="primary", use_container_width=True)

if go_predict:
    payload = {
        "bmi": bmi,
        "bp_systolic_mean": sys_bp,
        "bp_diastolic_mean": dia_bp,
        "glucose_mgdl": glucose,
        "hba1c_pct": hba1c,
        "age": age,
    }
    result = predict(payload)

    if result is None:
        st.error("Modelo no disponible. Ejecuta el pipeline con `kedro run`.")
        st.stop()

    prob_pct = result["high_risk_probability"] * 100
    is_high = result["high_risk"]

    section("Resultado")
    col_gauge, col_msg = st.columns([3, 2])

    with col_gauge:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=prob_pct,
                number={"suffix": "%", "font": {"size": 40}},
                title={"text": "Probabilidad de alto riesgo"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": RISK["high"] if is_high else RISK["low"]},
                    "steps": [
                        {"range": [0, 33], "color": "#DCFCE7"},
                        {"range": [33, 66], "color": "#FEF9C3"},
                        {"range": [66, 100], "color": "#FEE2E2"},
                    ],
                    "threshold": {
                        "line": {"color": MUTED, "width": 3},
                        "value": 50,
                    },
                },
            )
        )
        st.plotly_chart(style_fig(fig, height=320), use_container_width=True)

    with col_msg:
        st.markdown("")
        if is_high:
            st.error(f"⚠️ **ALTO RIESGO** — probabilidad estimada: **{prob_pct:.1f}%**")
            st.markdown(
                "El perfil supera el umbral del modelo (50%). Recomendación: "
                "evaluación clínica y control de factores de riesgo."
            )
        else:
            st.success(f"✅ **BAJO RIESGO** — probabilidad estimada: **{prob_pct:.1f}%**")
            st.markdown(
                "El perfil está por debajo del umbral del modelo (50%). "
                "Mantener hábitos saludables y controles periódicos."
            )

    st.caption(
        "⚕️ Estimación estadística con fines educativos; **no** constituye un "
        "diagnóstico médico."
    )

footer()
