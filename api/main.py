"""API REST (FastAPI) que sirve los resultados del pipeline NHANES.

Expone las tablas de la capa de reporting (``data/08_reporting``) como endpoints
JSON consumidos por el dashboard y por integraciones externas.

Ejecutar localmente:
    uvicorn api.main:app --reload --port 8000

Documentación interactiva (OpenAPI/Swagger): http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import os
import pickle
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    BioAgeRequest,
    BioAgeResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    PrevalenceRow,
    StateObesityRow,
    SummaryRow,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("api")

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

app = FastAPI(
    title="NHANES Cardiometabolic API",
    description=(
        "API REST que expone indicadores de riesgo cardiometabólico calculados "
        "por el pipeline ETL a partir de datos NHANES 2017-2020 (CDC)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@lru_cache(maxsize=8)
def _load(name: str) -> pd.DataFrame:
    """Carga (con caché) un parquet de la capa de reporting."""
    fp = REPORTING_DIR / f"{name}.parquet"
    if not fp.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Dataset '{name}' no disponible. Ejecuta el pipeline: 'kedro run'.",
        )
    return pd.read_parquet(fp)


@lru_cache(maxsize=1)
def _load_model():
    """Carga (con caché) el modelo de riesgo entrenado (artefacto pickle)."""
    if not MODEL_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Modelo no disponible. Ejecuta el pipeline: 'kedro run'.",
        )
    with MODEL_PATH.open("rb") as fh:
        return pickle.load(fh)


@lru_cache(maxsize=1)
def _load_bioage_model():
    """Carga (con caché) el modelo de edad biológica (artefacto pickle)."""
    if not BIOAGE_MODEL_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Modelo de edad biológica no disponible. Ejecuta 'kedro run'.",
        )
    with BIOAGE_MODEL_PATH.open("rb") as fh:
        return pickle.load(fh)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"service": "NHANES Cardiometabolic API", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Liveness/readiness: indica qué datasets de reporting están disponibles."""
    datasets = {
        f.stem: round(f.stat().st_size / 1024, 1)
        for f in REPORTING_DIR.glob("*.parquet")
    }
    return HealthResponse(status="ok", reporting_dir=str(REPORTING_DIR), datasets_kb=datasets)


@app.get("/prevalence", response_model=list[PrevalenceRow], tags=["indicadores"])
def get_prevalence() -> list[dict]:
    """Prevalencia (%) de obesidad, hipertensión, diabetes y tabaquismo por edad."""
    return _load("prevalence").to_dict(orient="records")


@app.get("/summary", response_model=list[SummaryRow], tags=["indicadores"])
def get_summary(
    sex: str | None = Query(None, description="Filtrar por sexo: Hombre/Mujer"),
) -> list[dict]:
    """Promedios clínicos por grupo etario y sexo."""
    df = _load("summary_by_demographics")
    if sex:
        df = df[df["sex"] == sex]
    return df.to_dict(orient="records")


@app.get("/state-obesity", response_model=list[StateObesityRow], tags=["indicadores"])
def get_state_obesity(
    top: int = Query(10, ge=1, le=60, description="Top N estados por obesidad"),
) -> list[dict]:
    """Obesidad por estado (fuente API REST data.cdc.gov)."""
    df = _load("state_obesity").sort_values("obesity_pct", ascending=False).head(top)
    return df.to_dict(orient="records")


@app.get("/nutrition", tags=["indicadores"])
def get_nutrition() -> list[dict]:
    """Consumo nutricional promedio (kcal, azúcar, sodio...) por categoría de IMC."""
    return _load("nutrition_by_obesity").to_dict(orient="records")


@app.post("/predict", response_model=PredictResponse, tags=["modelo"])
def predict(payload: PredictRequest) -> PredictResponse:
    """Predice la probabilidad de **alto riesgo** cardiometabólico (score ≥ 2).

    Recibe las variables clínicas de una persona y devuelve la probabilidad
    estimada por el ``RandomForestClassifier`` entrenado en el pipeline. Los
    valores ausentes se imputan automáticamente (mediana del entrenamiento).
    """
    model = _load_model()
    row = {feature: getattr(payload, feature) for feature in MODEL_FEATURES}
    features = pd.DataFrame([row], columns=MODEL_FEATURES).astype(float)
    try:
        probability = float(model.predict_proba(features)[0, 1])
    except Exception as exc:  # noqa: BLE001 - error de inferencia -> 500 controlado
        raise HTTPException(
            status_code=500, detail=f"Error al ejecutar la predicción: {exc}"
        ) from exc
    return PredictResponse(
        high_risk=probability >= 0.5,
        high_risk_probability=round(probability, 4),
    )


@app.post("/predict-age", response_model=BioAgeResponse, tags=["modelo"])
def predict_age(payload: BioAgeRequest) -> BioAgeResponse:
    """Estima la **edad biológica** a partir de biomarcadores (proxy de longevidad).

    Devuelve la edad biológica estimada por el ``RandomForestRegressor`` y, si se
    envía la edad real, el *age gap* (biológica − real): positivo indica
    envejecimiento acelerado; negativo, envejecimiento saludable.
    """
    model = _load_bioage_model()
    row = {feature: getattr(payload, feature) for feature in BIOAGE_FEATURES}
    features = pd.DataFrame([row], columns=BIOAGE_FEATURES).astype(float)
    try:
        bio_age = float(model.predict(features)[0])
    except Exception as exc:  # noqa: BLE001 - error de inferencia -> 500 controlado
        raise HTTPException(
            status_code=500, detail=f"Error al estimar la edad biológica: {exc}"
        ) from exc

    gap = None
    interpretation = (
        f"Edad biológica estimada: {bio_age:.1f} años. Envía 'age' para obtener el age gap."
    )
    if payload.age is not None:
        gap = round(bio_age - payload.age, 1)
        if gap > 0:
            interpretation = (
                f"Envejecimiento ACELERADO: aparenta {gap:.1f} años más que su edad real "
                f"({payload.age:.0f}). Proxy de menor longevidad."
            )
        else:
            interpretation = (
                f"Envejecimiento SALUDABLE: aparenta {abs(gap):.1f} años menos que su edad "
                f"real ({payload.age:.0f}). Proxy de mayor longevidad."
            )

    return BioAgeResponse(
        biological_age=round(bio_age, 1),
        chronological_age=payload.age,
        age_gap=gap,
        interpretation=interpretation,
    )
