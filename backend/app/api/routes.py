"""
FastAPI REST API Router (/api/v1/*) - ACEH SIAGA CUACA
File: backend/app/api/routes.py
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.api_schemas import StandardAPIEnvelope
from backend.app.services.weather_service import AcehWeatherPlatformService
from src.machine_learning.model_trainer import MANDATORY_ML_DISCLAIMER

router = APIRouter(prefix="/api/v1", tags=["Aceh Siaga Cuaca API v1"])
service = AcehWeatherPlatformService()


@router.get("/health", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_health() -> StandardAPIEnvelope[dict[str, Any]]:
    data = service.get_health_status()
    return StandardAPIEnvelope(
        data_category="SYSTEM_HEALTH",
        source_attribution="Aceh Siaga Cuaca System Monitor",
        disclaimer="Status operasional layanan platform Aceh Siaga Cuaca.",
        last_updated_wib=data["last_checked_wib"],
        api_health=data["api_health"],
        data=data,
    )


@router.get("/regions", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_regions() -> StandardAPIEnvelope[dict[str, Any]]:
    data = service.get_regions_catalog()
    return StandardAPIEnvelope(
        data_category="GEOSPATIAL_REFERENCE",
        source_attribution="Kemendagri, BPS Provinsi Aceh, dan UPT BMKG Aceh",
        disclaimer="Daftar resmi 23 Kabupaten/Kota dan 5 Stasiun Pengamatan BMKG di Provinsi Aceh.",
        last_updated_wib=service.now_wib_iso(),
        data=data,
    )


@router.get("/forecasts", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_forecasts(
    adm4: Optional[str] = Query(default=None, description="Kode Desa/Gampong ADM4 Aceh (contoh: 11.71.01.2001)"),
    region_code: Optional[str] = Query(default="11.71", description="Kode Kabupaten/Kota ADM2 Aceh (contoh: 11.71)"),
) -> StandardAPIEnvelope[dict[str, Any]]:
    try:
        data = service.get_forecast_for_area(adm4_code=adm4, region_code=region_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Gagal mengambil data prakiraan BMKG: {exc}") from exc

    return StandardAPIEnvelope(
        data_category="OFFICIAL_BMKG_FORECAST",
        source_attribution="API Prakiraan Cuaca Publik BMKG (https://api.bmkg.go.id)",
        disclaimer="Data prakiraan cuaca resmi BMKG (interval 3 jam, horizon 3 hari). Bukan merupakan data observasi curah hujan historis.",
        last_updated_wib=data["fetched_at_wib"],
        api_health=data["api_health"],
        data=data,
    )


@router.get("/alerts/active", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_active_alerts() -> StandardAPIEnvelope[dict[str, Any]]:
    data = service.get_active_alerts()
    return StandardAPIEnvelope(
        data_category="OFFICIAL_BMKG_ALERT",
        source_attribution="Peringatan Dini Cuaca Resmi BMKG (Nowcasting RSS & CAP v1.2)",
        disclaimer="Informasi peringatan dini cuaca ekstrem resmi dari BMKG. Rujuk tautan resmi BMKG untuk pembaruan darurat.",
        last_updated_wib=data["last_updated_wib"],
        api_health=data["api_health"],
        data=data,
    )


@router.get("/analytics/historical", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_historical_analytics() -> StandardAPIEnvelope[dict[str, Any]]:
    try:
        data = service.get_historical_analytics()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return StandardAPIEnvelope(
        data_category="HISTORICAL_OBSERVATION",
        source_attribution=str(data.get("data_source_label", "BMKG Provinsi Aceh")),
        disclaimer="Hasil analisis statistik dan eksplorasi data historis stasiun pengamatan cuaca Aceh. Korelasi statistik tidak menyiratkan hubungan sebab-akibat langsung.",
        last_updated_wib=service.now_wib_iso(),
        is_demo_mode=bool(data.get("is_demo_mode", False)),
        data=data,
    )


@router.get("/gis/layers", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_gis_layers() -> StandardAPIEnvelope[dict[str, Any]]:
    data = service.get_gis_layers()
    return StandardAPIEnvelope(
        data_category="SPATIOTEMPORAL_GIS",
        source_attribution="BMKG Provinsi Aceh, BPBA Aceh, DIBI BNPB, dan BIG",
        disclaimer=data["spatial_limitation_note"],
        last_updated_wib=service.now_wib_iso(),
        data=data,
    )


@router.get("/ml/predictions", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_ml_predictions() -> StandardAPIEnvelope[dict[str, Any]]:
    try:
        data = service.get_ml_predictions_and_evaluation()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return StandardAPIEnvelope(
        data_category="EXPERIMENTAL_ML_PREDICTION",
        source_attribution="Modul Machine Learning Aceh Siaga Cuaca (Eksperimental)",
        disclaimer=MANDATORY_ML_DISCLAIMER,
        last_updated_wib=str(data.get("trained_at_wib") or service.now_wib_iso()),
        data=data,
    )


@router.get("/education/preparedness", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_preparedness_education() -> StandardAPIEnvelope[dict[str, Any]]:
    data = service.get_preparedness_education()
    return StandardAPIEnvelope(
        data_category="DISASTER_AND_PREPAREDNESS",
        source_attribution="BPBA Provinsi Aceh, BNPB, Basarnas Banda Aceh, dan BMKG",
        disclaimer="Panduan edukasi kesiapsiagaan masyarakat dan daftar kontak darurat resmi terverifikasi di Provinsi Aceh.",
        last_updated_wib=service.now_wib_iso(),
        data=data,
    )


@router.get("/dashboard/summary", response_model=StandardAPIEnvelope[dict[str, Any]])
def get_dashboard_summary(
    region_code: str = Query(default="11.71", description="Kode Kabupaten/Kota untuk ringkasan cuaca utama"),
) -> StandardAPIEnvelope[dict[str, Any]]:
    """Endpoint agregat untuk Halaman 1 (Home) agar pemuatan halaman cepat dan hemat bandwidth."""
    forecast_data = service.get_forecast_for_area(region_code=region_code)
    alerts_data = service.get_active_alerts()
    ml_data = service.get_ml_predictions_and_evaluation()

    current_slot = forecast_data["slots"][0] if forecast_data["slots"] else None
    overall_health = (
        "ONLINE"
        if (forecast_data["api_health"] == "ONLINE" and alerts_data["api_health"] == "ONLINE")
        else "DEGRADED_USING_LAST_KNOWN_CACHE"
    )

    summary_payload = {
        "selected_region_code": region_code,
        "location": forecast_data["location"],
        "current_forecast_slot": current_slot,
        "upcoming_24h_slots": forecast_data["slots"][:8],
        "active_alerts_count": alerts_data["active_alerts_count"],
        "active_alerts": alerts_data["alerts"],
        "experimental_ml_highlights": ml_data["station_predictions"],
        "ml_disclaimer": MANDATORY_ML_DISCLAIMER,
    }

    return StandardAPIEnvelope(
        data_category="DASHBOARD_OVERVIEW",
        source_attribution="BMKG Resmi (Prakiraan & Peringatan Dini) + Analisis Internal Aceh Siaga Cuaca",
        disclaimer="Prakiraan dan peringatan dini berasal dari BMKG. Prediksi Machine Learning bersifat eksperimental dan bukan peringatan resmi BMKG.",
        last_updated_wib=forecast_data["fetched_at_wib"],
        api_health=overall_health,
        data=summary_payload,
    )
