"""Nodos de reporting: tablas agregadas para consumo de negocio."""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)

# Grupos etarios adultos (excluye menores y edad desconocida del análisis clínico)
ADULT_GROUPS = ["18-29", "30-44", "45-64", "65+"]


def _adults(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra la cohorte adulta (18+) con grupo etario conocido.

    El análisis cardiometabólico se define sobre adultos; los menores y los
    registros con edad desconocida se excluran para no sesgar las prevalencias.
    """
    if "age_group" not in df.columns:
        return df
    return df[df["age_group"].isin(ADULT_GROUPS)].copy()


def summary_by_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """Indicadores promedio por grupo etario y sexo (vista operativa/técnica)."""
    df = _adults(df)
    metrics = ["bmi", "bp_systolic_mean", "bp_diastolic_mean", "glucose_mgdl", "hba1c_pct"]
    metrics = [m for m in metrics if m in df.columns]
    out = (
        df.groupby(["age_group", "sex"], dropna=False)
        .agg(
            n=("SEQN", "count"),
            **{m: (m, "mean") for m in metrics},
        )
        .round(2)
        .reset_index()
    )
    return out


def prevalence(df: pd.DataFrame) -> pd.DataFrame:
    """Prevalencia (%) de condiciones por grupo etario (vista ejecutiva)."""
    df = _adults(df)
    flags = ["obesity_flag", "hypertension_flag", "diabetes_flag", "smoker_flag"]
    flags = [f for f in flags if f in df.columns]
    out = (
        df.groupby("age_group", dropna=False)[flags]
        .mean()
        .mul(100)
        .round(1)
        .reset_index()
        .rename(columns={f: f.replace("_flag", "_pct") for f in flags})
    )
    out["n"] = df.groupby("age_group", dropna=False)["SEQN"].count().values
    return out


def nutrition_by_obesity(df: pd.DataFrame) -> pd.DataFrame:
    """Consumo nutricional promedio por categoría de IMC (vista técnica/ejecutiva).

    Cuenta la historia 'dieta → obesidad': cuánta energía, azúcar y sodio
    consume cada grupo según su estado de peso.
    """
    df = _adults(df)
    nutrients = ["energy_kcal", "sugar_g", "sodium_mg", "fat_g", "sat_fat_g", "fiber_g", "protein_g"]
    nutrients = [n for n in nutrients if n in df.columns]
    if not nutrients or "bmi_category" not in df.columns:
        return pd.DataFrame()
    order = ["Bajo peso", "Normal", "Sobrepeso", "Obesidad"]
    out = (
        df.groupby("bmi_category")[nutrients]
        .mean()
        .round(1)
        .reindex([c for c in order if c in df["bmi_category"].unique()])
        .reset_index()
    )
    counts = df.groupby("bmi_category")["SEQN"].count()
    out["n"] = out["bmi_category"].map(counts).astype("Int64")
    return out


def state_obesity(cdc_api: pd.DataFrame) -> pd.DataFrame:
    """Normaliza el snapshot de la API CDC: obesidad por estado (vista ejecutiva)."""
    if cdc_api.empty:
        log.warning("snapshot CDC vacío; devuelvo tabla vacía")
        return cdc_api
    cols = {c.lower(): c for c in cdc_api.columns}
    value_col = cols.get("data_value", "data_value")
    state_col = cols.get("locationdesc", cols.get("locationabbr", "locationdesc"))
    keep = [c for c in [state_col, value_col, "question"] if c in cdc_api.columns]
    out = cdc_api[keep].copy()
    if value_col in out.columns:
        out[value_col] = pd.to_numeric(out[value_col], errors="coerce")
    return out.rename(columns={state_col: "state", value_col: "obesity_pct"})
