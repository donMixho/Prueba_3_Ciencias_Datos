"""Acceso a datos para el dashboard.

Intenta consumir la API REST (FastAPI). Si no está disponible, cae a leer los
parquet de la capa de reporting directamente (modo offline / desarrollo).
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
REPORTING_DIR = Path(os.getenv("REPORTING_DIR", "data/08_reporting"))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "data/06_models/risk_model.pkl"))
BIOAGE_MODEL_PATH = Path(os.getenv("BIOAGE_MODEL_PATH", "data/06_models/bioage_model.pkl"))
CLUSTERING_MODEL_PATH = Path(
    os.getenv("CLUSTERING_MODEL_PATH", "data/06_models/clustering_model.pkl")
)

# Orden de features esperado por el modelo de riesgo (coincide con parameters.yml).
MODEL_FEATURES = [
    "bmi",
    "bp_systolic_mean",
    "bp_diastolic_mean",
    "glucose_mgdl",
    "hba1c_pct",
    "age",
]

# Orden de features del modelo de edad biológica (coincide con parameters.yml).
BIOAGE_FEATURES = [
    "bp_systolic_mean",
    "bp_diastolic_mean",
    "hba1c_pct",
    "glucose_mgdl",
    "cholesterol_total",
    "cholesterol_hdl",
    "triglycerides",
    "bmi",
    "waist_cm",
]

# Orden de features del modelo de clustering (coincide con parameters.yml).
CLUSTER_FEATURES = [
    "bmi",
    "age",
    "bp_systolic_mean",
    "bp_diastolic_mean",
    "hba1c_pct",
    "glucose_mgdl",
    "cholesterol_total",
    "waist_cm",
]

# Etiquetas legibles de las features para la tabla resumen de perfiles.
CLUSTER_FEATURE_LABELS = {
    "bmi": "IMC",
    "age": "Edad",
    "bp_systolic_mean": "PA sistólica",
    "bp_diastolic_mean": "PA diastólica",
    "hba1c_pct": "HbA1c (%)",
    "glucose_mgdl": "Glucosa",
    "cholesterol_total": "Colesterol",
    "waist_cm": "Cintura",
}

# Interpretación clínica de los 4 perfiles de salud (obtenida del pipeline de
# segmentación). ``share`` es el peso poblacional de cada cluster.
CLUSTER_PROFILES = {
    0: {
        "profile": "Adultos con obesidad, metabólicamente estables",
        "description": (
            "Adultos con IMC elevado pero presión arterial, glucosa y lípidos en "
            "rangos relativamente controlados. Riesgo moderado a vigilar."
        ),
        "share": 34.7,
    },
    1: {
        "profile": "Diabéticos descompensados",
        "description": (
            "Grupo crítico con HbA1c y glucosa muy elevadas: descompensación "
            "metabólica que requiere atención clínica prioritaria."
        ),
        "share": 2.3,
    },
    2: {
        "profile": "Jóvenes/menores sanos",
        "description": (
            "Población joven con biomarcadores en rangos saludables y bajo riesgo "
            "cardiometabólico."
        ),
        "share": 46.9,
    },
    3: {
        "profile": "Adultos hipertensos con dislipidemia",
        "description": (
            "Adultos con presión arterial elevada y perfil lipídico alterado "
            "(colesterol/triglicéridos); riesgo cardiovascular a controlar."
        ),
        "share": 16.1,
    },
}


@st.cache_data(ttl=300)
def get(endpoint: str, parquet_name: str) -> pd.DataFrame:
    """Obtiene un dataset desde la API o, en su defecto, desde parquet local."""
    try:
        resp = requests.get(f"{API_URL}/{endpoint}", timeout=5)
        resp.raise_for_status()
        return pd.DataFrame(resp.json())
    except Exception:  # noqa: BLE001 - fallback intencional a archivo local
        fp = REPORTING_DIR / f"{parquet_name}.parquet"
        if fp.exists():
            return pd.read_parquet(fp)
        return pd.DataFrame()


def prevalence() -> pd.DataFrame:
    return get("prevalence", "prevalence")


def summary() -> pd.DataFrame:
    return get("summary", "summary_by_demographics")


def state_obesity() -> pd.DataFrame:
    return get("state-obesity?top=60", "state_obesity")


def nutrition() -> pd.DataFrame:
    return get("nutrition", "nutrition_by_obesity")


@st.cache_resource
def _load_model():
    """Carga (con caché) el modelo de riesgo entrenado desde el artefacto local."""
    if MODEL_PATH.exists():
        with MODEL_PATH.open("rb") as fh:
            return pickle.load(fh)
    return None


@st.cache_resource
def _load_bioage_model():
    """Carga (con caché) el modelo de edad biológica desde el artefacto local."""
    if BIOAGE_MODEL_PATH.exists():
        with BIOAGE_MODEL_PATH.open("rb") as fh:
            return pickle.load(fh)
    return None


@st.cache_resource
def _load_clustering_model():
    """Carga (con caché) el modelo de clustering desde el artefacto local."""
    if CLUSTERING_MODEL_PATH.exists():
        with CLUSTERING_MODEL_PATH.open("rb") as fh:
            return pickle.load(fh)
    return None


def _cluster_result(cluster: int) -> dict:
    """Enriquece un número de cluster con su perfil clínico y descripción.

    Args:
        cluster: etiqueta del cluster asignada por el modelo (0-3).

    Returns:
        Dict con ``cluster``, ``profile`` y ``description``.
    """
    info = CLUSTER_PROFILES.get(cluster, {})
    return {
        "cluster": cluster,
        "profile": info.get("profile", f"Cluster {cluster}"),
        "description": info.get("description", ""),
    }


def predict(features: dict) -> dict | None:
    """Predice la probabilidad de alto riesgo cardiometabólico.

    Intenta primero la API REST (``POST /predict``). Si no está disponible, cae
    a cargar el modelo pickle local y predecir en el proceso (modo offline).

    Args:
        features: diccionario con las claves de ``MODEL_FEATURES``.

    Returns:
        Dict con ``high_risk``, ``high_risk_probability`` y ``threshold``, o
        ``None`` si no hay API ni modelo local disponibles.
    """
    try:
        resp = requests.post(f"{API_URL}/predict", json=features, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:  # noqa: BLE001 - fallback intencional al modelo local
        model = _load_model()
        if model is None:
            return None
        row = {f: features.get(f) for f in MODEL_FEATURES}
        x = pd.DataFrame([row], columns=MODEL_FEATURES).astype(float)
        proba = float(model.predict_proba(x)[0, 1])
        return {
            "high_risk": bool(proba >= 0.5),
            "high_risk_probability": round(proba, 4),
            "threshold": 0.5,
        }


def predict_bioage(features: dict) -> dict | None:
    """Estima la edad biológica (proxy de longevidad).

    Intenta la API REST (``POST /predict-age``) y, si no está, cae al modelo
    pickle local. ``features`` puede incluir ``age`` (edad real) para el age gap.

    Returns:
        Dict con ``biological_age``, ``age_gap`` e ``interpretation``, o ``None``
        si no hay API ni modelo local disponibles.
    """
    try:
        resp = requests.post(f"{API_URL}/predict-age", json=features, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:  # noqa: BLE001 - fallback intencional al modelo local
        model = _load_bioage_model()
        if model is None:
            return None
        row = {f: features.get(f) for f in BIOAGE_FEATURES}
        x = pd.DataFrame([row], columns=BIOAGE_FEATURES).astype(float)
        bio_age = round(float(model.predict(x)[0]), 1)
        real_age = features.get("age")
        gap = round(bio_age - real_age, 1) if real_age is not None else None
        return {
            "biological_age": bio_age,
            "chronological_age": real_age,
            "age_gap": gap,
            "interpretation": "",
        }


def predict_cluster(payload: dict) -> dict | None:
    """Asigna a una persona su perfil de salud (clustering no supervisado).

    Intenta primero la API REST (``POST /predict-cluster``). Si no está
    disponible, cae a cargar el modelo pickle local (``KMeans`` dentro de un
    ``Pipeline`` de imputación + estandarización) y etiquetar en el proceso
    (modo offline).

    Args:
        payload: diccionario con las claves de ``CLUSTER_FEATURES``.

    Returns:
        Dict con ``cluster`` (int 0-3), ``profile`` (nombre del perfil) y
        ``description``, o ``None`` si no hay API ni modelo local disponibles.
    """
    try:
        resp = requests.post(f"{API_URL}/predict-cluster", json=payload, timeout=5)
        resp.raise_for_status()
        return _cluster_result(int(resp.json()["cluster"]))
    except Exception:  # noqa: BLE001 - fallback intencional al modelo local
        model = _load_clustering_model()
        if model is None:
            return None
        row = {f: payload.get(f) for f in CLUSTER_FEATURES}
        x = pd.DataFrame([row], columns=CLUSTER_FEATURES).astype(float)
        cluster = int(model.predict(x)[0])
        return _cluster_result(cluster)


def cluster_summary() -> pd.DataFrame | None:
    """Construye la tabla resumen de los 4 perfiles de salud.

    Recupera los centroides del ``KMeans`` entrenado y los devuelve a la escala
    clínica original deshaciendo la estandarización del ``StandardScaler`` del
    pipeline, de modo que cada fila describe el valor medio real de las features
    en ese cluster. Se anexan el nombre del perfil y su peso poblacional.

    Returns:
        DataFrame indexado por número de cluster con el perfil, el porcentaje de
        población y las medias clínicas de cada feature; o ``None`` si el
        artefacto del modelo no está disponible.
    """
    model = _load_clustering_model()
    if model is None:
        return None

    scaler = model.named_steps["scaler"]
    kmeans = model.named_steps["kmeans"]
    centroides = scaler.inverse_transform(kmeans.cluster_centers_)

    tabla = pd.DataFrame(centroides, columns=CLUSTER_FEATURES).round(1)
    tabla = tabla.rename(columns=CLUSTER_FEATURE_LABELS)
    tabla.insert(0, "Perfil", [CLUSTER_PROFILES[i]["profile"] for i in tabla.index])
    tabla.insert(1, "% población", [CLUSTER_PROFILES[i]["share"] for i in tabla.index])
    tabla.index.name = "Cluster"
    return tabla
