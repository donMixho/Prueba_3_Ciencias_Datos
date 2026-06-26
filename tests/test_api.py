"""Tests de los endpoints de la API REST (FastAPI TestClient)."""

from __future__ import annotations

import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)


def test_root_ok():
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_prevalence_returns_rows():
    r = client.get("/prevalence")
    # 200 si el pipeline ya generó datos; 503 si aún no (ambos son válidos)
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, list)
        if data:
            assert "age_group" in data[0]


def test_state_obesity_top_param():
    r = client.get("/state-obesity?top=3")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        assert len(r.json()) <= 3


def test_nutrition_endpoint():
    r = client.get("/nutrition")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, list)
        if data:
            assert "bmi_category" in data[0]
