"""Definición del pipeline de procesamiento."""

from __future__ import annotations

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    build_predictions,
    clean_clinical,
    engineer_features,
    merge_clinical,
    store_models_in_db,
    train_bioage_model,
    train_clustering_model,
    train_risk_model,
)


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
            node(
                func=train_risk_model,
                inputs=["prm_cardiometabolic", "params:model"],
                outputs="risk_model",
                name="train_risk_model_node",
            ),
            node(
                func=train_bioage_model,
                inputs=["prm_cardiometabolic", "params:bioage_model"],
                outputs="bioage_model",
                name="train_bioage_model_node",
            ),
            node(
                func=train_clustering_model,
                inputs=["prm_cardiometabolic", "params:clustering_model"],
                outputs="clustering_model",
                name="train_clustering_model_node",
            ),
            node(
                func=build_predictions,
                inputs=[
                    "prm_cardiometabolic",
                    "risk_model",
                    "bioage_model",
                    "clustering_model",
                    "params:model",
                    "params:bioage_model",
                    "params:clustering_model",
                ],
                outputs="model_predictions",
                name="build_predictions_node",
            ),
            node(
                func=store_models_in_db,
                inputs=[
                    "risk_model",
                    "bioage_model",
                    "clustering_model",
                    "params:db",
                ],
                outputs="store_models_report",
                name="store_models_in_db_node",
            ),
        ]
    )
