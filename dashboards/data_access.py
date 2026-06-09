"""Acceso a datos para el dashboard.

Intenta consumir la API REST (FastAPI). Si no está disponible, cae a leer los
parquet de la capa de reporting directamente (modo offline / desarrollo).
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
REPORTING_DIR = Path(os.getenv("REPORTING_DIR", "data/08_reporting"))


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
