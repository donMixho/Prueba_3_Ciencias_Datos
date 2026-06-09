"""Definición del pipeline de ingestión."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import extract_cdc_api, validate_raw_sources


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=extract_cdc_api,
                inputs="params:cdc_api",
                outputs="raw_cdc_obesity_api",
                name="extract_cdc_api_node",
            ),
            node(
                func=validate_raw_sources,
                inputs=[
                    "raw_demographics",
                    "raw_body_measures",
                    "raw_blood_pressure",
                    "params:validation",
                ],
                outputs="ingestion_quality_report",
                name="validate_raw_sources_node",
            ),
        ]
    )
