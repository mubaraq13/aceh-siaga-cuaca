from __future__ import annotations

import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from src.machine_learning.model_trainer import MANDATORY_ML_DISCLAIMER

ROOT_DIR = Path(__file__).resolve().parents[1]
client = TestClient(app)

def test_01_database_schema_and_docker_configs_exist() -> None:
    schema_sql = (ROOT_DIR / "database" / "schema.sql").read_text(encoding="utf-8")
    required_tables = [
        "data_sources",
        "data_ingestion_logs",
        "regions",
        "administrative_boundaries",
        "weather_stations",
        "weather_observations",
        "weather_forecasts",
        "weather_alerts",
        "disaster_events",
        "disaster_impacts",
        "model_predictions",
    ]
    for table in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema_sql
    assert (ROOT_DIR / "docker-compose.yml").exists()
    assert (ROOT_DIR / "backend" / "Dockerfile").exists()
    assert (ROOT_DIR / "frontend" / "Dockerfile").exists()
    assert (ROOT_DIR / "nginx" / "nginx.conf").exists()

def test_02_openapi_contract_and_data_provenance_envelopes() -> None:
    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})
    expected_endpoints = [
        "/api/v1/health",
        "/api/v1/regions",
        "/api/v1/forecasts",
        "/api/v1/alerts/active",
        "/api/v1/analytics/historical",
        "/api/v1/gis/layers",
        "/api/v1/ml/predictions",
        "/api/v1/education/preparedness",
        "/api/v1/dashboard/summary",
    ]
    for ep in expected_endpoints:
        assert ep in paths
    openapi_file = ROOT_DIR / "docs" / "OPENAPI_SPEC.json"
    assert openapi_file.exists()
    saved_spec = json.loads(openapi_file.read_text(encoding="utf-8"))
    assert saved_spec["info"]["title"] == "ACEH SIAGA CUACA"

def test_03_frontend_7_pages_and_design_direction_compliance() -> None:
    design_md = ROOT_DIR / "DESIGN.md"
    assert design_md.exists()
    design_text = design_md.read_text(encoding="utf-8")
    for color in ["#102A43", "#173F5F", "#DCEEFF", "#F5F8FC", "#FFFFFF", "#B54708", "#B42318", "#18794E"]:
        assert color in design_text
    frontend_pages = [
        "frontend/src/app/page.tsx",
        "frontend/src/app/prakiraan/page.tsx",
        "frontend/src/app/peta/page.tsx",
        "frontend/src/app/analisis/page.tsx",
        "frontend/src/app/machine-learning/page.tsx",
        "frontend/src/app/peringatan-dini/page.tsx",
        "frontend/src/app/edukasi/page.tsx",
    ]
    em_dash = "\u2014"
    for page_rel in frontend_pages:
        page_path = ROOT_DIR / page_rel
        assert page_path.exists()
        content = page_path.read_text(encoding="utf-8")
        assert em_dash not in content
        assert "ProvenanceHeader" in content
        assert "DataStateWrapper" in content

def test_04_ml_artifacts_and_experimental_separation() -> None:
    reg_model = ROOT_DIR / "models" / "trained" / "best_rainfall_regressor.joblib"
    cls_model = ROOT_DIR / "models" / "trained" / "best_extreme_classifier.joblib"
    eval_json = ROOT_DIR / "models" / "evaluation" / "model_evaluation_report.json"
    assert reg_model.exists()
    assert cls_model.exists()
    assert eval_json.exists()
    report = json.loads(eval_json.read_text(encoding="utf-8"))
    assert report["mandatory_disclaimer"] == MANDATORY_ML_DISCLAIMER
