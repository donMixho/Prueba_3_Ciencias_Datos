"""Vista Ejecutiva — KPIs y mensajes de negocio para audiencia gerencial."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from data_access import prevalence, state_obesity

st.set_page_config(page_title="Ejecutiva", page_icon="📊", layout="wide")
st.title("📊 Vista Ejecutiva")
st.caption("Indicadores clave de salud poblacional — NHANES 2017-2018")

prev = prevalence()
if prev.empty:
    st.warning("No hay datos. Ejecuta el pipeline (`kedro run`).")
    st.stop()

# --- KPIs principales (promedio ponderado simple sobre grupos) ---
def _wmean(col: str) -> float:
    if col not in prev.columns:
        return float("nan")
    return round((prev[col] * prev["n"]).sum() / prev["n"].sum(), 1)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Obesidad", f"{_wmean('obesity_pct')}%")
c2.metric("Hipertensión", f"{_wmean('hypertension_pct')}%")
c3.metric("Diabetes", f"{_wmean('diabetes_pct')}%")
c4.metric("Tabaquismo", f"{_wmean('smoker_pct')}%")

st.divider()

# --- Prevalencia por grupo etario ---
col_left, col_right = st.columns(2)
with col_left:
    st.subheader("Prevalencia por grupo etario")
    melt = prev.melt(
        id_vars="age_group",
        value_vars=[c for c in ["obesity_pct", "hypertension_pct", "diabetes_pct"] if c in prev.columns],
        var_name="Condición",
        value_name="Prevalencia (%)",
    )
    fig = px.bar(melt, x="age_group", y="Prevalencia (%)", color="Condición", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Obesidad por estado (Top 15)")
    states = state_obesity()
    if not states.empty and "obesity_pct" in states.columns:
        top = states.dropna(subset=["obesity_pct"]).sort_values("obesity_pct", ascending=False).head(15)
        fig2 = px.bar(top, x="obesity_pct", y="state", orientation="h")
        fig2.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Datos de la API CDC no disponibles.")

st.success(
    "**Mensaje de negocio:** la prevalencia de obesidad e hipertensión crece de "
    "forma marcada con la edad, concentrando el riesgo cardiometabólico en adultos 45+."
)
