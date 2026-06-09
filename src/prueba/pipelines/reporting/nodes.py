"""Nodos de reporting: tablas agregadas para consumo de negocio."""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)


def summary_by_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """Indicadores promedio por grupo etario y sexo (vista operativa/técnica)."""
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
