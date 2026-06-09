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
