"""Tests del feature engineering del pipeline de processing."""

from __future__ import annotations

import pandas as pd

from prueba.pipelines.processing.nodes import engineer_features

THRESHOLDS = {
    "bmi": {"underweight": 18.5, "normal": 25.0, "overweight": 30.0},
    "hypertension_systolic": 130,
    "hypertension_diastolic": 80,
    "diabetes_fasting_glucose": 126,
    "diabetes_hba1c": 6.5,
    "age_groups": [
        {"label": "18-29", "min": 18, "max": 29},
        {"label": "30-44", "min": 30, "max": 44},
        {"label": "45-64", "min": 45, "max": 64},
        {"label": "65+", "min": 65, "max": 150},
    ],
}


def _sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SEQN": [1, 2],
            "age": [25, 70],
            "bmi": [22.0, 33.0],
            "BPXSY1": [120, 145],
            "BPXSY2": [122, 147],
            "BPXDI1": [78, 92],
            "BPXDI2": [0, 90],  # 0 -> inválido
            "hba1c_pct": [5.0, 7.1],
            "glucose_mgdl": [90, 130],
            "DIQ010": [2, 1],
            "SMQ020": [2, 1],
        }
    )


def test_bmi_category_and_obesity_flag():
    out = engineer_features(_sample(), THRESHOLDS)
    assert out.loc[0, "bmi_category"] == "Normal"
    assert out.loc[1, "bmi_category"] == "Obesidad"
    assert out.loc[1, "obesity_flag"] == 1


def test_age_group():
    out = engineer_features(_sample(), THRESHOLDS)
    assert out.loc[0, "age_group"] == "18-29"
    assert out.loc[1, "age_group"] == "65+"


def test_flags_and_risk_score():
    out = engineer_features(_sample(), THRESHOLDS)
    # Sujeto 2: obeso + hipertenso + diabético + fumador = riesgo 4
    assert out.loc[1, "hypertension_flag"] == 1
    assert out.loc[1, "diabetes_flag"] == 1
    assert out.loc[1, "cardiometabolic_risk"] == 4
    # Sujeto 1: sano = riesgo 0
    assert out.loc[0, "cardiometabolic_risk"] == 0


def test_diastolic_zero_ignored():
    out = engineer_features(_sample(), THRESHOLDS)
    # media diastólica del sujeto 1 = 78 (el 0 se ignora)
    assert out.loc[0, "bp_diastolic_mean"] == 78
