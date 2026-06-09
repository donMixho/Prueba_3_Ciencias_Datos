"""Tests del cliente de la API CDC (con mocks, sin red)."""

from __future__ import annotations

import pytest

from prueba.utils.io_sources import CDCApiError, fetch_cdc_dataset


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload


def test_fetch_ok(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        assert url.endswith("hn4x-zwk7.json")
        return _FakeResp([{"state": "CA", "data_value": "25.1"}])

    monkeypatch.setattr("prueba.utils.io_sources.requests.get", fake_get)
    df = fetch_cdc_dataset("https://data.cdc.gov/resource", "hn4x-zwk7", limit=10)
    assert len(df) == 1
    assert df.iloc[0]["state"] == "CA"


def test_fetch_retries_then_fails(monkeypatch):
    import requests

    def fake_get(url, params=None, timeout=None):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr("prueba.utils.io_sources.requests.get", fake_get)
    monkeypatch.setattr("prueba.utils.io_sources.time.sleep", lambda *_: None)
    with pytest.raises(CDCApiError):
        fetch_cdc_dataset("https://data.cdc.gov/resource", "x", max_retries=2)
