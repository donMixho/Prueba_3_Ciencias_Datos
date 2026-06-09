"""Vista Técnica — distribuciones y relaciones para analistas/data scientists."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from data_access import summary

st.set_page_config(page_title="Técnica", page_icon="🔬", layout="wide")
st.title("🔬 Vista Técnica")
st.caption("Métricas clínicas por demografía — para análisis detallado")

df = summary()
if df.empty:
    st.warning("No hay datos. Ejecuta el pipeline (`kedro run`).")
    st.stop()

# Filtros
sexes = sorted(df["sex"].dropna().unique()) if "sex" in df.columns else []
sel = st.multiselect("Sexo", sexes, default=sexes)
fdf = df[df["sex"].isin(sel)] if sel else df

metric_cols = [c for c in ["bmi", "bp_systolic_mean", "bp_diastolic_mean", "glucose_mgdl", "hba1c_pct"] if c in fdf.columns]
metric = st.selectbox("Métrica", metric_cols, index=0 if metric_cols else None)

if metric:
    st.subheader(f"{metric} por grupo etario y sexo")
    fig = px.bar(fdf, x="age_group", y=metric, color="sex", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Tabla resumen")
st.dataframe(fdf, use_container_width=True)

with st.expander("ℹ️ Notas metodológicas"):
    st.markdown(
        """
        - Presión arterial: media de hasta 4 lecturas válidas (diastólica = 0 tratada como nula).
        - Diabetes: HbA1c ≥ 6.5% **o** glucosa en ayunas ≥ 126 mg/dL **o** autoreporte (DIQ010).
        - Hipertensión: ≥ 130/80 mmHg (criterio ACC/AHA 2017).
        - Los códigos NHANES de "no sabe/rehúsa" (7/9/77/99/...) se convierten a nulos.
        """
    )
