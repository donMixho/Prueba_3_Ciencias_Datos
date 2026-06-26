"""Vista Técnica — distribuciones y relaciones para analistas/data scientists."""

from __future__ import annotations

import plotly.express as px
import streamlit as st
from data_access import nutrition, summary
from theme import footer, page_header, section, setup_page, style_fig

setup_page("Técnica", "🔬")
page_header(
    "Vista Técnica",
    "Métricas clínicas por demografía para análisis detallado",
)

df = summary()
if df.empty:
    st.warning("No hay datos. Ejecuta el pipeline (`kedro run`).")
    st.stop()

# --- Filtros ---
section("Filtros")
fc1, fc2 = st.columns([1, 2])
sexes = sorted(df["sex"].dropna().unique()) if "sex" in df.columns else []
sel = fc1.multiselect("Sexo", sexes, default=sexes)
metric_cols = [c for c in ["bmi", "bp_systolic_mean", "bp_diastolic_mean", "glucose_mgdl", "hba1c_pct"] if c in df.columns]
labels = {
    "bmi": "IMC (kg/m²)", "bp_systolic_mean": "Presión sistólica",
    "bp_diastolic_mean": "Presión diastólica", "glucose_mgdl": "Glucosa (mg/dL)",
    "hba1c_pct": "HbA1c (%)",
}
metric = fc2.selectbox("Métrica clínica", metric_cols,
                       format_func=lambda c: labels.get(c, c), index=0 if metric_cols else None)
fdf = df[df["sex"].isin(sel)] if sel else df

# --- Gráfico principal ---
if metric:
    section(f"{labels.get(metric, metric)} por grupo etario y sexo")
    fig = px.bar(fdf, x="age_group", y=metric, color="sex", barmode="group")
    fig.update_layout(xaxis_title="", yaxis_title=labels.get(metric, metric), legend_title="Sexo")
    st.plotly_chart(style_fig(fig, height=420), use_container_width=True)

# --- Nutrición por categoría de IMC (datos de dieta) ---
section("Consumo nutricional por categoría de IMC")
nut = nutrition()
if not nut.empty:
    nut_cols = {
        "energy_kcal": "Energía (kcal)", "sugar_g": "Azúcar (g)",
        "sodium_mg": "Sodio (mg)", "fat_g": "Grasa (g)",
        "sat_fat_g": "Grasa sat. (g)", "fiber_g": "Fibra (g)", "protein_g": "Proteína (g)",
    }
    avail = [c for c in nut_cols if c in nut.columns]
    nut_metric = st.selectbox("Nutriente", avail, format_func=lambda c: nut_cols.get(c, c))
    fign = px.bar(nut, x="bmi_category", y=nut_metric, color="bmi_category")
    fign.update_layout(xaxis_title="", yaxis_title=nut_cols.get(nut_metric, nut_metric),
                       showlegend=False)
    st.plotly_chart(style_fig(fign, height=360), use_container_width=True)
    st.caption("Fuente: NHANES dieta (P_DR1TOT), recordatorio de 24 h del Día 1.")
else:
    st.info("Datos de nutrición no disponibles. Ejecuta `kedro run`.")

# --- Tabla ---
section("Tabla resumen")
st.dataframe(fdf, use_container_width=True)

with st.expander("ℹ️ Notas metodológicas"):
    st.markdown(
        """
        - **Cohorte:** adultos 18+ (se excluyen menores y edad desconocida).
        - **Presión arterial:** media de hasta 4 lecturas válidas (diastólica = 0 → nula).
        - **Diabetes:** HbA1c ≥ 6.5% **o** glucosa en ayunas ≥ 126 mg/dL **o** autoreporte (DIQ010).
        - **Hipertensión:** ≥ 130/80 mmHg (criterio ACC/AHA 2017).
        - Los códigos NHANES de "no sabe/rehúsa" (7/9/77/99/...) se convierten a nulos.
        """
    )

footer()
