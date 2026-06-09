"""Validación de esquemas y calidad de datos.

Funciones ligeras (sin dependencias pesadas) para validar los DataFrames que
entran y salen del pipeline. Si el proyecto crece, estas funciones pueden
reemplazarse por ``pandera`` o ``great_expectations`` manteniendo la firma.
"""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)

# Códigos NHANES que representan "rehúsa / no sabe / falta"
NHANES_MISSING_CODES = {7, 9, 77, 99, 777, 999, 7777, 9999, 77777, 99999}


class SchemaValidationError(ValueError):
    """El DataFrame no cumple el esquema esperado."""


def validate_columns(df: pd.DataFrame, required: list[str], name: str) -> pd.DataFrame:
    """Verifica que existan las columnas requeridas; lanza error si faltan."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SchemaValidationError(f"[{name}] faltan columnas: {missing}")
    return df


def validate_min_rows(df: pd.DataFrame, min_rows: int, name: str) -> pd.DataFrame:
    """Verifica una cantidad mínima de filas."""
    if len(df) < min_rows:
        raise SchemaValidationError(
            f"[{name}] tiene {len(df)} filas, se esperaban >= {min_rows}"
        )
    return df


def validate_unique_key(df: pd.DataFrame, key: str, name: str) -> pd.DataFrame:
    """Verifica unicidad de la llave (p.ej. SEQN)."""
    if df[key].duplicated().any():
        n = int(df[key].duplicated().sum())
        raise SchemaValidationError(f"[{name}] {n} valores duplicados en llave '{key}'")
    return df


def replace_missing_codes(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Reemplaza los códigos especiales de NHANES por NaN en columnas dadas."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].where(~df[col].isin(NHANES_MISSING_CODES))
    return df


def quality_report(df: pd.DataFrame) -> dict[str, float]:
    """Resumen de calidad: % de nulos por columna y nº de filas."""
    report = {"n_rows": float(len(df))}
    for col in df.columns:
        report[f"null_pct__{col}"] = float(df[col].isna().mean() * 100)
    return report
