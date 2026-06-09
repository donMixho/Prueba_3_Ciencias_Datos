"""Nodos de procesamiento: limpieza, integración y features cardiometabólicas."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from prueba.utils.validation import (
    replace_missing_codes,
    validate_unique_key,
)

log = logging.getLogger(__name__)


def _select(df: pd.DataFrame, cols: list[str], name: str) -> pd.DataFrame:
    """Selecciona columnas existentes y avisa de las ausentes."""
    present = [c for c in cols if c in df.columns]
    missing = set(cols) - set(present)
    if missing:
        log.warning("[%s] columnas ausentes (se omiten): %s", name, missing)
    return df[present].copy()


def merge_clinical(
    demographics: pd.DataFrame,
    body_measures: pd.DataFrame,
    blood_pressure: pd.DataFrame,
    glucose: pd.DataFrame,
    hba1c: pd.DataFrame,
    cholesterol: pd.DataFrame,
    triglycerides: pd.DataFrame,
    diabetes_q: pd.DataFrame,
    bloodpressure_q: pd.DataFrame,
    smoking_q: pd.DataFrame,
    activity_q: pd.DataFrame,
    columns: dict,
) -> pd.DataFrame:
    """Une todas las fuentes por la llave SEQN (left join sobre demografía)."""
    base = _select(demographics, columns["demographics"], "demographics")
    validate_unique_key(base, "SEQN", "demographics")

    parts = {
        "body_measures": _select(body_measures, columns["body_measures"], "body_measures"),
        "blood_pressure": _select(blood_pressure, columns["blood_pressure"], "blood_pressure"),
        "glucose": _select(glucose, columns["glucose"], "glucose"),
        "hba1c": _select(hba1c, columns["hba1c"], "hba1c"),
        "cholesterol": _select(cholesterol, columns["cholesterol_total"] + ["LBDHDD"], "cholesterol"),
        "triglycerides": _select(triglycerides, columns["triglycerides"], "triglycerides"),
        "diabetes_q": _select(diabetes_q, columns["diabetes_q"], "diabetes_q"),
        "bloodpressure_q": _select(bloodpressure_q, columns["bloodpressure_q"], "bloodpressure_q"),
        "smoking_q": _select(smoking_q, columns["smoking_q"], "smoking_q"),
        "activity_q": _select(activity_q, columns["activity_q"], "activity_q"),
    }

    merged = base
    for name, part in parts.items():
        merged = merged.merge(part, on="SEQN", how="left")
        log.info("merge %-16s -> %d filas, %d cols", name, len(merged), merged.shape[1])

    return merged


def clean_clinical(merged: pd.DataFrame, validation: dict) -> pd.DataFrame:
    """Limpia códigos especiales y normaliza nombres de columnas."""
    coded_cols = ["DIQ010", "BPQ020", "SMQ020", "PAQ650", "DMDEDUC2"]
    if validation.get("drop_invalid_codes", True):
        merged = replace_missing_codes(merged, coded_cols)

    rename = {
        "RIAGENDR": "sex",
        "RIDAGEYR": "age",
        "RIDRETH3": "race",
        "DMDEDUC2": "education",
        "INDFMPIR": "income_poverty_ratio",
        "BMXBMI": "bmi",
        "BMXWT": "weight_kg",
        "BMXHT": "height_cm",
        "BMXWAIST": "waist_cm",
        "LBXGLU": "glucose_mgdl",
        "LBXGH": "hba1c_pct",
        "LBXTC": "cholesterol_total",
        "LBDHDD": "cholesterol_hdl",
        "LBXTR": "triglycerides",
        "LBDLDL": "cholesterol_ldl",
    }
    df = merged.rename(columns={k: v for k, v in rename.items() if k in merged.columns})
    df["sex"] = df["sex"].map({1: "Hombre", 2: "Mujer"}).astype("object")
    return df


def _bmi_category(bmi: float, t: dict) -> str:
    if pd.isna(bmi):
        return "Desconocido"
    if bmi < t["underweight"]:
        return "Bajo peso"
    if bmi < t["normal"]:
        return "Normal"
    if bmi < t["overweight"]:
        return "Sobrepeso"
    return "Obesidad"


def _age_group(age: float, groups: list[dict]) -> str:
    if pd.isna(age):
        return "Desconocido"
    for g in groups:
        if g["min"] <= age <= g["max"]:
            return g["label"]
    return "Desconocido"


def engineer_features(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """Crea variables derivadas y banderas clínicas de riesgo."""
    df = df.copy()

    # Presión arterial: media de lecturas válidas
    sys_cols = [c for c in ["BPXSY1", "BPXSY2", "BPXSY3", "BPXSY4"] if c in df.columns]
    dia_cols = [c for c in ["BPXDI1", "BPXDI2", "BPXDI3", "BPXDI4"] if c in df.columns]
    # diastólica 0 = inválida en NHANES
    df[dia_cols] = df[dia_cols].replace(0, np.nan)
    df["bp_systolic_mean"] = df[sys_cols].mean(axis=1, skipna=True)
    df["bp_diastolic_mean"] = df[dia_cols].mean(axis=1, skipna=True)

    # Categorías
    df["bmi_category"] = df["bmi"].apply(lambda b: _bmi_category(b, thresholds["bmi"]))
    df["age_group"] = df["age"].apply(lambda a: _age_group(a, thresholds["age_groups"]))

    # Banderas clínicas
    df["hypertension_flag"] = (
        (df["bp_systolic_mean"] >= thresholds["hypertension_systolic"])
        | (df["bp_diastolic_mean"] >= thresholds["hypertension_diastolic"])
    ).astype("Int64")

    df["diabetes_flag"] = (
        (df.get("hba1c_pct") >= thresholds["diabetes_hba1c"])
        | (df.get("glucose_mgdl") >= thresholds["diabetes_fasting_glucose"])
        | (df.get("DIQ010") == 1)
    ).astype("Int64")

    df["obesity_flag"] = (df["bmi_category"] == "Obesidad").astype("Int64")
    df["smoker_flag"] = (df.get("SMQ020") == 1).astype("Int64")

    # Score compuesto de riesgo cardiometabólico (0-4)
    df["cardiometabolic_risk"] = (
        df[["hypertension_flag", "diabetes_flag", "obesity_flag", "smoker_flag"]]
        .fillna(0)
        .sum(axis=1)
        .astype("Int64")
    )

    log.info("Features generadas: %d filas, %d columnas", len(df), df.shape[1])
    return df
