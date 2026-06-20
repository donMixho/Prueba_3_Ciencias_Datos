"""Tests de estructura de los pipelines del proyecto."""

from __future__ import annotations

from prueba.pipelines.ingestion import create_pipeline as ingestion_pipeline
from prueba.pipelines.processing import create_pipeline as processing_pipeline
from prueba.pipelines.reporting import create_pipeline as reporting_pipeline


def test_each_pipeline_has_nodes():
    """Cada pipeline se construye y contiene nodos."""
    assert len(ingestion_pipeline().nodes) >= 1
    assert len(processing_pipeline().nodes) >= 3
    assert len(reporting_pipeline().nodes) >= 3


def test_processing_outputs_primary_dataset():
    """El pipeline de processing produce el dataset primario esperado."""
    outputs = processing_pipeline().all_outputs()
    assert "prm_cardiometabolic" in outputs


def test_reporting_consumes_primary_and_api():
    """El reporting consume el dataset primario y el snapshot de la API."""
    inputs = reporting_pipeline().all_inputs()
    assert "prm_cardiometabolic" in inputs
    assert "raw_cdc_obesity_api" in inputs
