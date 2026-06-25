"""Definición del pipeline de procesamiento."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import clean_clinical, engineer_features, merge_clinical


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=merge_clinical,
                inputs=[
                    "raw_demographics",
                    "raw_body_measures",
                    "raw_diet",
                    "raw_blood_pressure",
                    "raw_lab_glucose",
                    "raw_lab_hba1c",
                    "raw_lab_cholesterol",
                    "raw_lab_triglycerides",
                    "raw_diabetes_q",
                    "raw_bloodpressure_q",
                    "raw_smoking_q",
                    "raw_activity_q",
                    "params:columns",
                ],
                outputs="int_clinical_merged",
                name="merge_clinical_node",
            ),
            node(
                func=clean_clinical,
                inputs=["int_clinical_merged", "params:validation"],
                outputs="clinical_clean",
                name="clean_clinical_node",
            ),
            node(
                func=engineer_features,
                inputs=["clinical_clean", "params:thresholds"],
                outputs="prm_cardiometabolic",
                name="engineer_features_node",
            ),
        ]
    )
