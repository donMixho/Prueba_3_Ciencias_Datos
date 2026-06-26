"""Modelos Pydantic para las respuestas de la API."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    reporting_dir: str
    datasets_kb: dict[str, float]


class PrevalenceRow(BaseModel):
    age_group: str | None = None
    obesity_pct: float | None = None
    hypertension_pct: float | None = None
    diabetes_pct: float | None = None
    smoker_pct: float | None = None
    n: int | None = None

    model_config = {"extra": "allow"}


class SummaryRow(BaseModel):
    age_group: str | None = None
    sex: str | None = None
    n: int | None = None

    model_config = {"extra": "allow"}


class StateObesityRow(BaseModel):
    state: str | None = None
    obesity_pct: float | None = None

    model_config = {"extra": "allow"}


class PredictRequest(BaseModel):
    """Features de entrada para predecir el riesgo cardiometabólico.

    Todos los campos son opcionales: los valores ausentes se imputan por
    mediana dentro del modelo, replicando el comportamiento de entrenamiento.
    """

    bmi: float | None = None
    bp_systolic_mean: float | None = None
    bp_diastolic_mean: float | None = None
    glucose_mgdl: float | None = None
    hba1c_pct: float | None = None
    age: float | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "bmi": 33.0,
                "bp_systolic_mean": 146.0,
                "bp_diastolic_mean": 92.0,
                "glucose_mgdl": 140.0,
                "hba1c_pct": 7.1,
                "age": 65,
            }
        }
    }


class PredictResponse(BaseModel):
    """Resultado de la predicción de alto riesgo cardiometabólico."""

    high_risk: bool
    high_risk_probability: float
    threshold: float = 0.5


class BioAgeRequest(BaseModel):
    """Biomarcadores para estimar la edad biológica.

    ``age`` (edad real) es opcional: si se envía, se devuelve también el
    *age gap*. Los biomarcadores ausentes se imputan por mediana.
    """

    bp_systolic_mean: float | None = None
    bp_diastolic_mean: float | None = None
    hba1c_pct: float | None = None
    glucose_mgdl: float | None = None
    cholesterol_total: float | None = None
    cholesterol_hdl: float | None = None
    triglycerides: float | None = None
    bmi: float | None = None
    waist_cm: float | None = None
    age: float | None = None  # edad cronológica real (opcional, para el gap)

    model_config = {
        "json_schema_extra": {
            "example": {
                "bp_systolic_mean": 155,
                "bp_diastolic_mean": 96,
                "hba1c_pct": 7.4,
                "glucose_mgdl": 140,
                "cholesterol_total": 245,
                "cholesterol_hdl": 38,
                "triglycerides": 280,
                "bmi": 35.0,
                "waist_cm": 110,
                "age": 45,
            }
        }
    }


class BioAgeResponse(BaseModel):
    """Resultado de la estimación de edad biológica."""

    biological_age: float
    chronological_age: float | None = None
    age_gap: float | None = None  # biológica - real (>0 envejecimiento acelerado)
    interpretation: str
