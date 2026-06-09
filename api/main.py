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
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import HealthResponse, PrevalenceRow, StateObesityRow, SummaryRow

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("api")

REPORTING_DIR = Path(os.getenv("REPORTING_DIR", "data/08_reporting"))

app = FastAPI(
    title="NHANES Cardiometabolic API",
    description=(
        "API REST que expone indicadores de riesgo cardiometabólico calculados "
        "por el pipeline ETL a partir de datos NHANES 2017-2018 (CDC)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
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
