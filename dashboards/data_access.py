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
