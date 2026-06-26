"""Tests del entrenamiento del modelo de riesgo (nodo train_risk_model)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from prueba.pipelines.processing.nodes import train_risk_model

MODEL_PARAMS = {
    "target_col": "cardiometabolic_risk",
    "target_threshold": 2,
    "features": [
        "bmi",
        "bp_systolic_mean",
        "bp_diastolic_mean",
        "glucose_mgdl",
        "hba1c_pct",
        "age",
    ],
    "test_size": 0.25,
    "random_state": 0,
    "n_estimators": 50,
    "max_depth": 5,
}


def _synthetic(n: int = 80) -> pd.DataFrame:
    """Genera datos sintéticos separables: perfiles sanos vs. de alto riesgo."""
    rng = np.random.default_rng(0)
    low = pd.DataFrame(
        {
            "bmi": rng.normal(23, 2, n),
            "bp_systolic_mean": rng.normal(115, 5, n),
            "bp_diastolic_mean": rng.normal(72, 4, n),
            "glucose_mgdl": rng.normal(90, 5, n),
            "hba1c_pct": rng.normal(5.2, 0.3, n),
            "age": rng.normal(30, 5, n),
            "cardiometabolic_risk": 0,  # bajo riesgo
        }
    )
    high = pd.DataFrame(
        {
            "bmi": rng.normal(34, 2, n),
            "bp_systolic_mean": rng.normal(145, 5, n),
            "bp_diastolic_mean": rng.normal(92, 4, n),
            "glucose_mgdl": rng.normal(140, 10, n),
            "hba1c_pct": rng.normal(7.2, 0.4, n),
            "age": rng.normal(60, 5, n),
            "cardiometabolic_risk": 3,  # alto riesgo (>= 2)
        }
    )
    return pd.concat([low, high], ignore_index=True)


def test_train_returns_fitted_model_with_proba():
    """El nodo devuelve un estimador entrenado capaz de dar probabilidades."""
    model = train_risk_model(_synthetic(), MODEL_PARAMS)
    assert hasattr(model, "predict_proba")

    proba = model.predict_proba(_synthetic()[MODEL_PARAMS["features"]])
    assert proba.shape[1] == 2  # clasificación binaria
    assert ((proba >= 0) & (proba <= 1)).all()


def test_model_learns_separable_signal():
    """Con datos separables, un perfil de alto riesgo recibe mayor probabilidad."""
    model = train_risk_model(_synthetic(), MODEL_PARAMS)

    high_profile = pd.DataFrame(
        [{"bmi": 36, "bp_systolic_mean": 150, "bp_diastolic_mean": 95,
          "glucose_mgdl": 150, "hba1c_pct": 7.5, "age": 65}]
    )[MODEL_PARAMS["features"]]
    low_profile = pd.DataFrame(
        [{"bmi": 22, "bp_systolic_mean": 110, "bp_diastolic_mean": 70,
          "glucose_mgdl": 85, "hba1c_pct": 5.0, "age": 28}]
    )[MODEL_PARAMS["features"]]

    p_high = model.predict_proba(high_profile)[0, 1]
    p_low = model.predict_proba(low_profile)[0, 1]
    assert p_high > p_low
    assert p_high > 0.5


def test_imputes_missing_values():
    """El modelo predice aunque falten features (imputación por mediana)."""
    model = train_risk_model(_synthetic(), MODEL_PARAMS)
    incomplete = pd.DataFrame(
        [{"bmi": 35, "bp_systolic_mean": np.nan, "bp_diastolic_mean": 93,
          "glucose_mgdl": np.nan, "hba1c_pct": 7.0, "age": 62}]
    )[MODEL_PARAMS["features"]]
    proba = model.predict_proba(incomplete)
    assert proba.shape == (1, 2)


def test_raises_on_single_class():
    """Si la variable objetivo tiene una sola clase, debe lanzar ValueError."""
    df = _synthetic()
    df["cardiometabolic_risk"] = 0  # todos bajo riesgo -> una sola clase
    with pytest.raises(ValueError):
        train_risk_model(df, MODEL_PARAMS)
