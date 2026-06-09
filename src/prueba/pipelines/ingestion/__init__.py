"""Pipeline de ingestión: extrae datos de las 3 fuentes (archivos, SQL, API)."""

from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
