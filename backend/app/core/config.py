"""
Backend Application Configuration - ACEH SIAGA CUACA
File: backend/app/core/config.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "ACEH SIAGA CUACA"
    app_tagline: str = "Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh."
    app_env: str = "development"
    app_timezone: str = "Asia/Jakarta"
    demo_mode: bool = False

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://aceh_weather_user:change_this_strong_password_in_prod@localhost:5432/aceh_siaga_cuaca",
    )

    bmkg_forecast_api_url: str = "https://api.bmkg.go.id/publik/prakiraan-cuaca"
    bmkg_nowcast_rss_url: str = "https://www.bmkg.go.id/alerts/nowcast/id"
    bmkg_rate_limit_requests_per_minute: int = 45
    bmkg_request_timeout_seconds: int = 15
    bmkg_cache_ttl_seconds: int = 10800

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
