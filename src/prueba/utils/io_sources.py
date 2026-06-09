"""Clientes de las fuentes de datos externas (API REST).

La fuente 3 del pipeline es la API Socrata de ``data.cdc.gov``. Este módulo
encapsula la llamada HTTP con reintentos y manejo de errores para mantener los
nodos del pipeline limpios y testeables.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
import requests

log = logging.getLogger(__name__)


class CDCApiError(RuntimeError):
    """Error al consultar la API de data.cdc.gov."""


def fetch_cdc_dataset(
    base_url: str,
    dataset_id: str,
    *,
    limit: int = 5000,
    where: str | None = None,
    max_retries: int = 3,
    backoff: float = 2.0,
    timeout: int = 60,
) -> pd.DataFrame:
    """Descarga un dataset de la API Socrata (SODA) de la CDC como DataFrame.

    Args:
        base_url: p.ej. ``https://data.cdc.gov/resource``.
        dataset_id: identificador del recurso (p.ej. ``hn4x-zwk7``).
        limit: número máximo de filas (``$limit``).
        where: cláusula SoQL ``$where`` opcional.
        max_retries: reintentos ante error de red / 5xx.
        backoff: factor de espera exponencial entre reintentos.
        timeout: timeout por request en segundos.

    Returns:
        DataFrame con la respuesta JSON.

    Raises:
        CDCApiError: si se agotan los reintentos.
    """
    url = f"{base_url.rstrip('/')}/{dataset_id}.json"
    params: dict[str, Any] = {"$limit": limit}
    if where:
        params["$where"] = where

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            log.info("GET %s (intento %d/%d)", url, attempt, max_retries)
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            df = pd.DataFrame.from_records(data)
            log.info("API CDC OK: %d filas, %d columnas", len(df), df.shape[1])
            return df
        except (requests.RequestException, ValueError) as exc:  # ValueError = JSON inválido
            last_exc = exc
            wait = backoff ** attempt
            log.warning("fallo API (%s); reintento en %.1fs", exc, wait)
            time.sleep(wait)

    raise CDCApiError(f"No se pudo consultar {url}: {last_exc}")
