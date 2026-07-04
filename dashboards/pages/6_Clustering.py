"""Vista Clustering — modelo de ML que segmenta perfiles de salud.

Agrupa a una persona en uno de los **4 perfiles de salud** (clustering *no
supervisado*, ``KMeans`` k=4) a partir de sus biomarcadores cardiometabólicos.
Consume la API (``/predict-cluster``) y, si no está, el modelo local.
"""

from __future__ import annotations

import streamlit as st
from data_access import CLUSTER_PROFILES, cluster_summary, predict_cluster
from theme import MUTED, footer, kpi_card, page_header, section, setup_page

# Color por perfil según severidad clínica (verde → amarillo → naranja → rojo).
CLUSTER_COLORS = {
    2: "#10B981",  # verde   — jóvenes/menores sanos
    0: "#F59E0B",  # amarillo — obesos metabólicamente estables
    3: "#F97316",  # naranja  — hipertensos con dislipidemia
    1: "#EF4444",  # rojo     — diabéticos descompensados (crítico)
}

setup_page("Clustering", "🧩")
page_header(
    "Perfiles de Salud (ML · Clustering)",
    "Modelo KMeans (k=4) que agrupa a una persona en su perfil de salud cardiometabólico",
)

st.markdown(
    "Ingresa los datos de una persona y el modelo la asignará a uno de los **4 "
    "perfiles de salud** aprendidos de la población (aprendizaje *no supervisado*). "
    "Los campos sin datos se imputan con la mediana del entrenamiento."
)

# --- Formulario de entrada (8 features del clustering) ---
section("Datos de la persona")
c1, c2, c3 = st.columns(3)
age = c1.number_input("Edad (años)", min_value=2, max_value=100, value=50)
bmi = c1.number_input("IMC (kg/m²)", min_value=10.0, max_value=60.0, value=28.0, step=0.1)
waist = c1.number_input("Cintura (cm)", min_value=40.0, max_value=200.0, value=95.0, step=0.5)
sys_bp = c2.number_input("Presión sistólica (mmHg)", min_value=80, max_value=220, value=130)
dia_bp = c2.number_input("Presión diastólica (mmHg)", min_value=40, max_value=140, value=82)
hba1c = c2.number_input("HbA1c (%)", min_value=3.0, max_value=15.0, value=5.6, step=0.1)
glucose = c3.number_input("Glucosa (mg/dL)", min_value=50, max_value=400, value=100)
chol_total = c3.number_input("Colesterol total (mg/dL)", min_value=80, max_value=450, value=190)

st.markdown("")
go_predict = st.button("🧩 Identificar perfil", type="primary", use_container_width=True)

if go_predict:
    payload = {
        "bmi": bmi,
        "age": age,
        "bp_systolic_mean": sys_bp,
        "bp_diastolic_mean": dia_bp,
        "hba1c_pct": hba1c,
        "glucose_mgdl": glucose,
        "cholesterol_total": chol_total,
        "waist_cm": waist,
    }
    result = predict_cluster(payload)

    if result is None:
        st.error("Modelo no disponible. Ejecuta el pipeline con `kedro run`.")
        st.stop()

    cluster = result["cluster"]
    color = CLUSTER_COLORS.get(cluster, MUTED)
    share = CLUSTER_PROFILES.get(cluster, {}).get("share")

    section("Resultado")
    st.markdown(
        f"""<div style="background:#fff;border:1px solid #E2E8F0;
            border-left:6px solid {color};border-radius:14px;padding:1.2rem 1.4rem;
            box-shadow:0 1px 3px rgba(15,23,42,.06)">
            <div style="font-size:.85rem;font-weight:700;color:{MUTED};
                text-transform:uppercase;letter-spacing:.04em">
                Cluster {cluster} · perfil asignado</div>
            <div style="font-size:1.5rem;font-weight:800;color:{color};
                margin:.2rem 0 .4rem">{result['profile']}</div>
            <div style="color:#334155;font-size:.95rem">{result['description']}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("")
    k1, k2, k3 = st.columns(3)
    kpi_card(k1, "Cluster asignado", f"#{cluster}", "🧩", color)
    kpi_card(k2, "Peso poblacional", f"{share}%" if share is not None else "—", "👥", color)
    kpi_card(k3, "Total de perfiles", "4", "🗂️", color)

    st.caption(
        "🧩 Segmentación estadística **no supervisada** con fines educativos; la "
        "etiqueta numérica (0-3) no implica un orden de gravedad y **no** constituye "
        "un diagnóstico médico."
    )

# --- Tabla resumen de los 4 perfiles (valores reales del pipeline) ---
section("Los 4 perfiles de salud")
tabla = cluster_summary()

if tabla is None:
    st.info("Modelo no disponible. Ejecuta el pipeline con `kedro run` para ver los perfiles.")
else:
    def _row_bg(row):
        """Tiñe cada fila con el color de severidad de su cluster."""
        color = CLUSTER_COLORS.get(row.name, "#94A3B8")
        return [f"background-color:{color}1A"] * len(row)

    st.dataframe(
        tabla.style.apply(_row_bg, axis=1).format(precision=1),
        use_container_width=True,
    )
    st.caption(
        "Valores medios (centroides) de cada perfil en su escala clínica original, "
        "recuperados del modelo entrenado."
    )

footer()
