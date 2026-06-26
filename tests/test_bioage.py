"""Tests del modelo de edad biológica (nodo train_bioage_model)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from prueba.pipelines.processing.nodes import train_bioage_model

BIO_PARAMS = {
    "target_col": "age",
    "min_age": 18,
    "required_features": ["bmi", "bp_systolic_mean"],
    "features": [
        "bp_systolic_mean",
        "bp_diastolic_mean",
        "hba1c_pct",
        "glucose_mgdl",
        "cholesterol_total",
        "cholesterol_hdl",
        "triglycerides",
        "bmi",
        "waist_cm",
    ],
    "test_size": 0.25,
    "random_state": 0,
    "n_estimators": 60,
    "max_depth": 8,
}


def _synthetic(n: int = 300) -> pd.DataFrame:
    """Genera datos donde los biomarcadores crecen con la edad (señal aprendible)."""
    rng = np.random.default_rng(0)
    age = rng.integers(18, 80, n).astype(float)
    return pd.DataFrame(
        {
            "age": age,
            "bp_systolic_mean": 90 + 0.7 * age + rng.normal(0, 5, n),
            "bp_diastolic_mean": 60 + 0.2 * age + rng.normal(0, 4, n),
            "hba1c_pct": 4.8 + 0.03 * age + rng.normal(0, 0.3, n),
            "glucose_mgdl": 85 + 0.4 * age + rng.normal(0, 8, n),
            "cholesterol_total": 150 + 0.6 * age + rng.normal(0, 15, n),
            "cholesterol_hdl": 60 - 0.1 * age + rng.normal(0, 5, n),
            "triglycerides": 90 + 0.8 * age + rng.normal(0, 20, n),
            "bmi": 24 + 0.08 * age + rng.normal(0, 3, n),
            "waist_cm": 80 + 0.3 * age + rng.normal(0, 6, n),
        }
    )


def test_train_returns_fitted_regressor():
    """El nodo devuelve un regresor entrenado que predice valores numéricos."""
    model = train_bioage_model(_synthetic(), BIO_PARAMS)
    assert hasattr(model, "predict")
    preds = model.predict(_synthetic()[BIO_PARAMS["features"]])
    assert len(preds) == len(_synthetic())
    assert np.issubdtype(np.asarray(preds).dtype, np.floating)


def test_model_learns_age_signal():
    """Un perfil con biomarcadores 'mayores' recibe una edad biológica más alta."""
    model = train_bioage_model(_synthetic(), BIO_PARAMS)
    joven = pd.DataFrame([{
        "bp_systolic_mean": 105, "bp_diastolic_mean": 65, "hba1c_pct": 5.0,
        "glucose_mgdl": 90, "cholesterol_total": 165, "cholesterol_hdl": 58,
        "triglycerides": 100, "bmi": 24, "waist_cm": 82,
    }])[BIO_PARAMS["features"]]
    mayor = pd.DataFrame([{
        "bp_systolic_mean": 150, "bp_diastolic_mean": 90, "hba1c_pct": 6.5,
        "glucose_mgdl": 130, "cholesterol_total": 220, "cholesterol_hdl": 45,
        "triglycerides": 200, "bmi": 32, "waist_cm": 108,
    }])[BIO_PARAMS["features"]]
    assert model.predict(mayor)[0] > model.predict(joven)[0]


def test_filters_minors_and_raises_when_empty():
    """Si no quedan adultos usables tras el filtro, lanza ValueError."""
    df = _synthetic()
    df["age"] = 10  # todos menores de edad -> ninguno pasa min_age=18
    with pytest.raises(ValueError):
        train_bioage_model(df, BIO_PARAMS)
