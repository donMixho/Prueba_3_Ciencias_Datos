"""Vista Ejecutiva — KPIs y mensajes de negocio para audiencia gerencial."""

from __future__ import annotations

import plotly.express as px
import streamlit as st
from data_access import prevalence, state_obesity
from theme import RISK, footer, kpi_card, page_header, section, setup_page, style_fig

setup_page("Ejecutiva", "📊")
page_header(
    "Vista Ejecutiva",
    "Indicadores clave de salud poblacional para la toma de decisiones",
)

prev = prevalence()
if prev.empty:
    st.warning("No hay datos. Ejecuta el pipeline (`kedro run`).")
    st.stop()


def _wmean(col: str) -> float:
    if col not in prev.columns:
        return float("nan")
    return round((prev[col] * prev["n"]).sum() / prev["n"].sum(), 1)


# --- KPIs principales ---
section("Prevalencia poblacional (adultos 18+)")
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Obesidad", f"{_wmean('obesity_pct')}%", "⚖️", RISK["high"])
kpi_card(c2, "Hipertensión", f"{_wmean('hypertension_pct')}%", "❤️", RISK["high"])
kpi_card(c3, "Diabetes", f"{_wmean('diabetes_pct')}%", "🩸", RISK["mid"])
kpi_card(c4, "Tabaquismo", f"{_wmean('smoker_pct')}%", "🚬", RISK["mid"])

st.markdown("")

# --- Gráficos ---
col_left, col_right = st.columns(2)
with col_left:
    section("Prevalencia por grupo etario")
    melt = prev.melt(
        id_vars="age_group",
        value_vars=[c for c in ["obesity_pct", "hypertension_pct", "diabetes_pct"] if c in prev.columns],
        var_name="Condición",
        value_name="Prevalencia (%)",
    )
    melt["Condición"] = melt["Condición"].map(
        {"obesity_pct": "Obesidad", "hypertension_pct": "Hipertensión", "diabetes_pct": "Diabetes"}
    )
    fig = px.bar(melt, x="age_group", y="Prevalencia (%)", color="Condición", barmode="group")
    fig.update_layout(xaxis_title="", legend_title="")
    st.plotly_chart(style_fig(fig, height=380), use_container_width=True)

with col_right:
    section("Obesidad por estado · Top 15")
    states = state_obesity()
    if not states.empty and "obesity_pct" in states.columns:
        top = states.dropna(subset=["obesity_pct"]).sort_values("obesity_pct", ascending=False).head(15)
        fig2 = px.bar(top, x="obesity_pct", y="state", orientation="h",
                      color="obesity_pct", color_continuous_scale="Teal")
        fig2.update_layout(yaxis={"categoryorder": "total ascending"},
                           xaxis_title="% obesidad", yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig2, height=380), use_container_width=True)
    else:
        st.info("Datos de la API CDC no disponibles.")

# --- Mensaje de negocio ---
section("Conclusión de negocio")
st.success(
    "La prevalencia de **obesidad** e **hipertensión** crece de forma marcada con la "
    "edad, concentrando el riesgo cardiometabólico en **adultos de 45+ años**. "
    "Recomendación: focalizar campañas de prevención en este grupo y en los estados "
    "con mayor obesidad."
)

footer()
