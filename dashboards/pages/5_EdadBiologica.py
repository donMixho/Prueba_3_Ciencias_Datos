"""Vista Edad Biológica — modelo de ML como proxy de longevidad.

Estima la edad biológica de una persona a partir de sus biomarcadores y la
compara con su edad real (*age gap*): un proxy de envejecimiento acelerado o
saludable. Consume la API (``/predict-age``) y, si no está, el modelo local.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from data_access import predict_bioage
from theme import MUTED, PRIMARY, RISK, footer, page_header, section, setup_page, style_fig

setup_page("Edad Biológica", "🧬")
page_header(
    "Edad Biológica (ML)",
    "Estima cuántos años 'aparenta' tu cuerpo según tus biomarcadores — proxy de longevidad",
)

st.markdown(
    "El modelo predice tu **edad biológica** a partir de marcadores clínicos y la "
    "compara con tu **edad real**. Un *age gap* positivo sugiere envejecimiento "
    "acelerado; uno negativo, envejecimiento saludable."
)

# --- Formulario ---
section("Tus datos")
c1, c2, c3 = st.columns(3)
age = c1.number_input("Edad real (años)", min_value=18, max_value=100, value=45)
bmi = c1.number_input("IMC (kg/m²)", min_value=10.0, max_value=60.0, value=28.0, step=0.1)
waist = c1.number_input("Cintura (cm)", min_value=50.0, max_value=200.0, value=95.0, step=0.5)
sys_bp = c2.number_input("Presión sistólica (mmHg)", min_value=80, max_value=220, value=130)
dia_bp = c2.number_input("Presión diastólica (mmHg)", min_value=40, max_value=140, value=82)
hba1c = c2.number_input("HbA1c (%)", min_value=3.0, max_value=15.0, value=5.6, step=0.1)
glucose = c3.number_input("Glucosa (mg/dL)", min_value=50, max_value=400, value=100)
chol_total = c3.number_input("Colesterol total (mg/dL)", min_value=80, max_value=450, value=190)
chol_hdl = c3.number_input("Colesterol HDL (mg/dL)", min_value=10, max_value=150, value=50)
trig = c3.number_input("Triglicéridos (mg/dL)", min_value=20, max_value=1000, value=130)

st.markdown("")
go_predict = st.button("🧬 Estimar mi edad biológica", type="primary", use_container_width=True)

if go_predict:
    payload = {
        "bp_systolic_mean": sys_bp,
        "bp_diastolic_mean": dia_bp,
        "hba1c_pct": hba1c,
        "glucose_mgdl": glucose,
        "cholesterol_total": chol_total,
        "cholesterol_hdl": chol_hdl,
        "triglycerides": trig,
        "bmi": bmi,
        "waist_cm": waist,
        "age": age,
    }
    result = predict_bioage(payload)

    if result is None:
        st.error("Modelo no disponible. Ejecuta el pipeline con `kedro run`.")
        st.stop()

    bio_age = result["biological_age"]
    gap = result.get("age_gap")
    acelerado = gap is not None and gap > 0

    section("Resultado")
    col_gauge, col_msg = st.columns([3, 2])

    with col_gauge:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=bio_age,
                number={"suffix": " años", "font": {"size": 36}},
                delta={"reference": age, "increasing": {"color": RISK["high"]},
                       "decreasing": {"color": RISK["low"]}, "suffix": " vs real"},
                title={"text": "Edad biológica estimada"},
                gauge={
                    "axis": {"range": [18, 90]},
                    "bar": {"color": RISK["high"] if acelerado else RISK["low"]},
                    "threshold": {
                        "line": {"color": PRIMARY, "width": 4},
                        "value": age,
                    },
                },
            )
        )
        st.plotly_chart(style_fig(fig, height=340), use_container_width=True)

    with col_msg:
        st.markdown("")
        st.metric("Edad real", f"{age:.0f} años")
        st.metric("Edad biológica", f"{bio_age:.0f} años",
                  delta=f"{gap:+.0f} años" if gap is not None else None,
                  delta_color="inverse")
        if gap is not None:
            if acelerado:
                st.error(
                    f"⚠️ Tu cuerpo aparenta **{gap:.0f} años más**. "
                    "Envejecimiento acelerado → proxy de menor longevidad."
                )
            else:
                st.success(
                    f"✅ Tu cuerpo aparenta **{abs(gap):.0f} años menos**. "
                    "Envejecimiento saludable → proxy de mayor longevidad."
                )

    st.caption(
        "🧬 La 'edad biológica' es un **proxy estadístico** de envejecimiento "
        "(R² ≈ 0.54, error medio ~10 años); **no** es una predicción de años de "
        "vida ni un diagnóstico médico."
    )

footer()
