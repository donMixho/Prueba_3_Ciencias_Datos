"""Vista Operativa — datos detallados y exportación para equipos operativos."""

from __future__ import annotations

import streamlit as st

from data_access import prevalence, state_obesity, summary

st.set_page_config(page_title="Operativa", page_icon="🛠️", layout="wide")
st.title("🛠️ Vista Operativa")
st.caption("Tablas completas y descarga de datos")

datasets = {
    "Prevalencia por edad": prevalence(),
    "Resumen por demografía": summary(),
    "Obesidad por estado (CDC API)": state_obesity(),
}

choice = st.selectbox("Dataset", list(datasets.keys()))
df = datasets[choice]

if df.empty:
    st.warning("No hay datos. Ejecuta el pipeline (`kedro run`).")
    st.stop()

st.dataframe(df, use_container_width=True, height=500)

st.download_button(
    "⬇️ Descargar CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"{choice.lower().replace(' ', '_')}.csv",
    mime="text/csv",
)
