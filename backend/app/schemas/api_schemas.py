"""
Pydantic v2 API Response Schemas with Mandatory Source Attribution - ACEH SIAGA CUACA
File: backend/app/schemas/api_schemas.py
"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class StandardAPIEnvelope(BaseModel, Generic[T]):
    """
    Amplop respons standar untuk memisahkan dengan tegas:
    1. Informasi observasi aktual (HISTORICAL_OBSERVATION)
    2. Prakiraan resmi BMKG (OFFICIAL_BMKG_FORECAST)
    3. Peringatan dini resmi BMKG (OFFICIAL_BMKG_ALERT)
    4. Prediksi eksperimental Machine Learning (EXPERIMENTAL_ML_PREDICTION)
    5. Catatan riwayat bencana & edukasi (DISASTER_AND_PREPAREDNESS)
    """

    status: str = "success"
    data_category: str = Field(
        ...,
        description="Kategori data: OFFICIAL_BMKG_FORECAST | OFFICIAL_BMKG_ALERT | HISTORICAL_OBSERVATION | EXPERIMENTAL_ML_PREDICTION | DISASTER_AND_PREPAREDNESS",
    )
    source_attribution: str = Field(..., description="Label sumber data resmi atau modul analisis")
    disclaimer: str = Field(..., description="Pernyataan batas tanggung jawab dan sifat data")
    last_updated_wib: str = Field(..., description="Waktu pembaruan data terakhir dalam zona waktu Asia/Jakarta (WIB)")
    api_health: str = Field(default="ONLINE", description="ONLINE | DEGRADED_USING_CACHE | OFFLINE")
    is_demo_mode: bool = False
    data: T


class HealthStatusSchema(BaseModel):
    service_name: str
    timezone: str
    api_health: str
    processed_observations_available: bool
    geojson_layers_available: bool
    trained_ml_models_available: bool
    last_checked_wib: str
