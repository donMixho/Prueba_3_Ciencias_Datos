"""Definición del pipeline de reporting."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import prevalence, state_obesity, summary_by_demographics


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=summary_by_demographics,
                inputs="prm_cardiometabolic",
                outputs="rpt_summary_by_demographics",
                name="summary_by_demographics_node",
            ),
            node(
                func=prevalence,
                inputs="prm_cardiometabolic",
                outputs="rpt_prevalence",
                name="prevalence_node",
            ),
            node(
                func=state_obesity,
                inputs="raw_cdc_obesity_api",
                outputs="rpt_state_obesity",
                name="state_obesity_node",
            ),
        ]
    )
