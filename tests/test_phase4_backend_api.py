"""
Integration Tests for PHASE 4A - FASTAPI BACKEND REST API (ACEH SIAGA CUACA)
File: tests/test_phase4_backend_api.py
Jalankan dengan: python -m pytest tests\test_phase4_backend_api.py -v
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from src.machine_learning.model_trainer import MANDATORY_ML_DISCLAIMER

client = TestClient(app)


def test_health_endpoint_returns_online() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["processed_observations_available"] is True
    assert body["data"]["trained_ml_models_available"] is True


def test_regions_catalog_contains_23_aceh_regencies_and_5_stations() -> None:
    resp = client.get("/api/v1/regions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["province_code"] == "11"
    assert body["data"]["total_regencies_cities"] == 23
    assert len(body["data"]["bmkg_stations"]) == 5


def test_forecasts_endpoint_validates_aceh_and_rejects_outside_province() -> None:
    # Kota Banda Aceh (11.71) harus berhasil
    resp_ok = client.get("/api/v1/forecasts?region_code=11.71")
    assert resp_ok.status_code == 200
    body_ok = resp_ok.json()
    assert body_ok["data_category"] == "OFFICIAL_BMKG_FORECAST"
    assert body_ok["data"]["total_slots"] > 0

    # Kode ADM4 di luar Aceh (misal 12.71.01.1001) harus ditolak dengan HTTP 400
    resp_bad = client.get("/api/v1/forecasts?adm4=12.71.01.1001")
    assert resp_bad.status_code == 400


def test_ml_predictions_endpoint_enforces_mandatory_experimental_disclaimer() -> None:
    resp = client.get("/api/v1/ml/predictions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_category"] == "EXPERIMENTAL_ML_PREDICTION"
    assert body["disclaimer"] == MANDATORY_ML_DISCLAIMER
    preds = body["data"]["station_predictions"]
    assert len(preds) == 5
    for p in preds:
        assert p["disclaimer_label"] == MANDATORY_ML_DISCLAIMER
        assert p["is_experimental"] is True


def test_gis_layers_historical_and_preparedness_endpoints() -> None:
    resp_gis = client.get("/api/v1/gis/layers")
    assert resp_gis.status_code == 200
    gis_body = resp_gis.json()
    assert len(gis_body["data"]["layers"]["weather_stations"]["features"]) == 5
    assert len(gis_body["data"]["layers"]["regency_disaster_density"]["features"]) == 23

    resp_hist = client.get("/api/v1/analytics/historical")
    assert resp_hist.status_code == 200
    assert resp_hist.json()["data_category"] == "HISTORICAL_OBSERVATION"

    resp_edu = client.get("/api/v1/education/preparedness")
    assert resp_edu.status_code == 200
    edu_data = resp_edu.json()["data"]
    assert len(edu_data["guides"]) == 3
    assert len(edu_data["verified_emergency_contacts"]) >= 4
