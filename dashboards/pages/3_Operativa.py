"""Vista Operativa — datos detallados y exportación para equipos operativos."""

from __future__ import annotations

import streamlit as st
from data_access import prevalence, state_obesity, summary
from theme import footer, kpi_card, page_header, section, setup_page

setup_page("Operativa", "🛠️")
page_header(
    "Vista Operativa",
    "Tablas completas y descarga de datos para el trabajo diario",
)

datasets = {
    "Prevalencia por edad": ("prevalence", prevalence()),
    "Resumen por demografía": ("summary", summary()),
    "Obesidad por estado (CDC API)": ("state_obesity", state_obesity()),
}

section("Selecciona un dataset")
choice = st.selectbox("Dataset", list(datasets.keys()))
key, df = datasets[choice]

if df.empty:
    st.warning("No hay datos. Ejecuta el pipeline (`kedro run`).")
    st.stop()

# --- Métricas rápidas del dataset ---
c1, c2 = st.columns(2)
kpi_card(c1, "Filas", f"{len(df):,}", "📄")
kpi_card(c2, "Columnas", f"{df.shape[1]}", "🧮")
st.markdown("")

section(choice)
st.dataframe(df, use_container_width=True, height=460)

st.download_button(
    "⬇️ Descargar CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"{key}.csv",
    mime="text/csv",
    type="primary",
)

footer()
