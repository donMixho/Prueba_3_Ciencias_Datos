"""Nodos de ingestión.

La mayoría de las fuentes (CSV y SQL) las resuelve directamente el Data Catalog
de Kedro. Aquí solo vive la lógica de la **fuente 3 (API REST)**, que requiere
una llamada HTTP, y un nodo de validación inicial reutilizable.
"""

from __future__ import annotations

import logging

import pandas as pd

from prueba.utils.io_sources import fetch_cdc_dataset
from prueba.utils.validation import validate_min_rows

log = logging.getLogger(__name__)


def extract_cdc_api(cdc_api: dict) -> pd.DataFrame:
    """Fuente 3: descarga indicadores de obesidad por estado desde data.cdc.gov.

    Args:
        cdc_api: bloque de parámetros ``cdc_api`` (base_url, dataset_id, ...).

    Returns:
        DataFrame con el snapshot de la API (se persiste como Parquet).
    """
    df = fetch_cdc_dataset(
        base_url=cdc_api["base_url"],
        dataset_id=cdc_api["dataset_id"],
        limit=cdc_api.get("limit", 5000),
        where=cdc_api.get("where"),
    )
    if df.empty:
        log.warning("La API CDC devolvió 0 filas; revisa el filtro 'where'.")
    return df


def validate_raw_sources(
    demographics: pd.DataFrame,
    body_measures: pd.DataFrame,
    blood_pressure: pd.DataFrame,
    validation: dict,
) -> pd.DataFrame:
    """Valida un mínimo de filas en las fuentes base y devuelve un reporte.

    Sirve como "puerta de calidad" temprana del pipeline.
    """
    min_rows = validation.get("min_rows", 1000)
    validate_min_rows(demographics, min_rows, "raw_demographics")
    validate_min_rows(body_measures, min_rows, "raw_body_measures")
    validate_min_rows(blood_pressure, min_rows, "raw_blood_pressure")

    report = pd.DataFrame(
        {
            "dataset": ["demographics", "body_measures", "blood_pressure"],
            "rows": [len(demographics), len(body_measures), len(blood_pressure)],
        }
    )
    log.info("Validación de fuentes base OK:\n%s", report.to_string(index=False))
    return report
