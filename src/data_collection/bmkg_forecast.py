"""
BMKG Public Weather Forecast Collector — ACEH SIAGA CUACA
Endpoint resmi: https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={KODE_ADM4}
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import requests
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("aceh_siaga.bmkg_forecast")
WIB_TZ = ZoneInfo("Asia/Jakarta")
ACEH_ADM4_REGEX = re.compile(r"^11\.\d{2}\.\d{2}\.\d{4}$")

ACEH_REPRESENTATIVE_ADM4: Dict[str, Dict[str, str]] = {
    "11.01": {"name": "Kabupaten Aceh Selatan", "adm4": "11.01.02.2001"},
    "11.02": {"name": "Kabupaten Aceh Tenggara", "adm4": "11.02.04.2001"},
    "11.03": {"name": "Kabupaten Aceh Timur", "adm4": "11.03.03.2001"},
    "11.04": {"name": "Kabupaten Aceh Tengah", "adm4": "11.04.01.2001"},
    "11.05": {"name": "Kabupaten Aceh Barat", "adm4": "11.05.01.2001"},
    "11.06": {"name": "Kabupaten Aceh Besar", "adm4": "11.06.08.2001"},
    "11.07": {"name": "Kabupaten Pidie", "adm4": "11.07.16.2001"},
    "11.08": {"name": "Kabupaten Aceh Utara", "adm4": "11.08.02.2001"},
    "11.09": {"name": "Kabupaten Simeulue", "adm4": "11.09.04.2001"},
    "11.10": {"name": "Kabupaten Aceh Singkil", "adm4": "11.10.04.2001"},
    "11.11": {"name": "Kabupaten Bireuen", "adm4": "11.11.13.2001"},
    "11.12": {"name": "Kabupaten Aceh Barat Daya", "adm4": "11.12.01.2001"},
    "11.13": {"name": "Kabupaten Gayo Lues", "adm4": "11.13.01.2001"},
    "11.14": {"name": "Kabupaten Aceh Jaya", "adm4": "11.14.04.2001"},
    "11.15": {"name": "Kabupaten Nagan Raya", "adm4": "11.15.02.2001"},
    "11.16": {"name": "Kabupaten Aceh Tamiang", "adm4": "11.16.03.2001"},
    "11.17": {"name": "Kabupaten Bener Meriah", "adm4": "11.17.05.2001"},
    "11.18": {"name": "Kabupaten Pidie Jaya", "adm4": "11.18.01.2001"},
    "11.71": {"name": "Kota Banda Aceh", "adm4": "11.71.01.2001"},
    "11.72": {"name": "Kota Sabang", "adm4": "11.72.01.2001"},
    "11.73": {"name": "Kota Lhokseumawe", "adm4": "11.73.02.2001"},
    "11.74": {"name": "Kota Langsa", "adm4": "11.74.02.2001"},
    "11.75": {"name": "Kota Subulussalam", "adm4": "11.75.01.2001"},
}


class BMKGLocationSchema(BaseModel):
    adm1: str
    adm2: str
    adm3: str
    adm4: str
    provinsi: str
    kotkab: str
    kecamatan: str
    desa: str
    lon: float
    lat: float
    timezone: str = "Asia/Jakarta"

    @field_validator("adm4")
    @classmethod
    def validate_aceh_adm4(cls, value: str) -> str:
        if not ACEH_ADM4_REGEX.match(value):
            raise ValueError(
                f"Kode ADM4 '{value}' bukan kode administrasi desa/gampong Provinsi Aceh yang valid (11.xx.xx.xxxx)."
            )
        return value


class BMKGForecastPointSchema(BaseModel):
    region_code: str
    adm2_code: str
    adm3_code: str
    desa_name: str
    kecamatan_name: str
    kotkab_name: str
    latitude: float
    longitude: float
    analysis_time: datetime
    forecast_time_utc: datetime
    forecast_time_local: datetime
    temperature_c: float = Field(..., ge=5.0, le=45.0)
    humidity_pct: float = Field(..., ge=0.0, le=100.0)
    weather_code: Optional[int] = None
    weather_desc_id: str
    weather_desc_en: Optional[str] = None
    wind_speed_kmh: float = Field(..., ge=0.0)
    wind_speed_ms: float = Field(..., ge=0.0)
    wind_dir_cardinal: Optional[str] = None
    wind_dir_deg: Optional[float] = None
    cloud_cover_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    visibility_text: Optional[str] = None
    visibility_m: Optional[int] = None
    source_attribution: str = "API Prakiraan Cuaca Publik BMKG (Resmi)"
    data_nature: str = "OFFICIAL_FORECAST"
    fetched_at: datetime


class BMKGForecastCollector:
    """Client pengumpul data prakiraan cuaca BMKG dengan Rate Limiter, Retry, dan Cache."""

    BASE_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

    def __init__(
        self,
        cache_dir: Path = Path("data/raw/bmkg/cache"),
        cache_ttl_seconds: int = 10800,
        requests_per_minute: int = 45,
        timeout_seconds: int = 15,
        max_retries: int = 3,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.min_interval_seconds = 60.0 / max(1, min(requests_per_minute, 55))
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._last_request_ts: float = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "AcehSiagaCuaca-ResearchPlatform/1.0 (Hydrometeorological Disaster Preparedness Aceh)",
                "Accept": "application/json",
            }
        )

    @staticmethod
    def validate_adm4_code(adm4_code: str) -> str:
        cleaned = adm4_code.strip()
        if not ACEH_ADM4_REGEX.match(cleaned):
            raise ValueError(
                f"Kode ADM4 '{cleaned}' tidak valid. Wajib menggunakan format Aceh '11.xx.xx.xxxx'."
            )
        return cleaned

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)
        self._last_request_ts = time.monotonic()

    def _get_cache_file(self, adm4_code: str) -> Path:
        safe_key = hashlib.sha256(adm4_code.encode("utf-8")).hexdigest()[:16]
        return self.cache_dir / f"forecast_{adm4_code}_{safe_key}.json"

    def _read_cache(self, adm4_code: str, allow_stale: bool = False) -> Optional[Dict[str, Any]]:
        cache_file = self._get_cache_file(adm4_code)
        if not cache_file.exists():
            return None
        try:
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_at = payload.get("_cached_at_epoch", 0)
            age_seconds = time.time() - float(cached_at)
            if age_seconds <= self.cache_ttl_seconds or allow_stale:
                payload["_from_cache"] = True
                payload["_is_stale_cache"] = age_seconds > self.cache_ttl_seconds
                return payload
        except (OSError, ValueError, KeyError) as exc:
            logger.warning("Gagal membaca cache untuk %s: %s", adm4_code, exc)
        return None

    def _write_cache(self, adm4_code: str, raw_payload: Dict[str, Any]) -> None:
        cache_file = self._get_cache_file(adm4_code)
        enriched = dict(raw_payload)
        enriched["_cached_at_epoch"] = time.time()
        enriched["_fetched_at_wib"] = datetime.now(WIB_TZ).isoformat()
        cache_file.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    def fetch_raw_forecast(self, adm4_code: str, use_cache: bool = True) -> Dict[str, Any]:
        valid_adm4 = self.validate_adm4_code(adm4_code)
        if use_cache:
            cached = self._read_cache(valid_adm4, allow_stale=False)
            if cached is not None:
                return cached

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            self._respect_rate_limit()
            try:
                response = self.session.get(
                    self.BASE_URL,
                    params={"adm4": valid_adm4},
                    timeout=self.timeout_seconds,
                )
                if response.status_code == 429:
                    time.sleep((2 ** attempt) * 2.5)
                    continue

                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or "lokasi" not in payload or "data" not in payload:
                    raise ValueError(f"Struktur JSON BMKG tidak sesuai spesifikasi untuk {valid_adm4}")

                self._write_cache(valid_adm4, payload)
                payload["_from_cache"] = False
                payload["_is_stale_cache"] = False
                payload["_fetched_at_wib"] = datetime.now(WIB_TZ).isoformat()
                return payload
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep((2 ** (attempt - 1)) * 1.5)

        stale_cache = self._read_cache(valid_adm4, allow_stale=True)
        if stale_cache is not None:
            return stale_cache

        raise RuntimeError(f"Gagal mengambil data prakiraan BMKG untuk {valid_adm4}: {last_error}")

    @staticmethod
    def _parse_datetime(dt_str: str, is_utc: bool = True) -> datetime:
        cleaned = dt_str.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
        except ValueError:
            dt = datetime.strptime(cleaned[:19], "%Y-%m-%d %H:%M:%S")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc if is_utc else WIB_TZ)
        return dt

    @classmethod
    def parse_forecast_payload(cls, payload: Dict[str, Any]) -> List[BMKGForecastPointSchema]:
        if "lokasi" not in payload or "data" not in payload:
            raise ValueError("Payload JSON tidak memiliki kunci wajib 'lokasi' dan 'data'.")

        BMKGLocationSchema(**payload["lokasi"])
        fetched_at_str = payload.get("_fetched_at_wib")
        fetched_at = datetime.fromisoformat(fetched_at_str) if fetched_at_str else datetime.now(WIB_TZ)

        normalized_records: List[BMKGForecastPointSchema] = []
        seen_timestamps: set[tuple[str, str]] = set()

        for data_item in payload.get("data", []):
            item_loc = BMKGLocationSchema(**data_item.get("lokasi", payload["lokasi"]))
            for day_group in data_item.get("cuaca", []):
                if not isinstance(day_group, list):
                    continue
                for slot in day_group:
                    if not isinstance(slot, dict):
                        continue
                    utc_str = str(slot.get("utc_datetime", ""))
                    dedup_key = (item_loc.adm4, utc_str)
                    if not utc_str or dedup_key in seen_timestamps:
                        continue
                    seen_timestamps.add(dedup_key)

                    utc_dt = cls._parse_datetime(utc_str, is_utc=True)
                    local_str = str(slot.get("local_datetime", ""))
                    local_dt = (
                        cls._parse_datetime(local_str, is_utc=False).replace(tzinfo=None)
                        if local_str
                        else utc_dt.astimezone(WIB_TZ).replace(tzinfo=None)
                    )
                    analysis_str = str(slot.get("analysis_date", utc_str))
                    analysis_dt = cls._parse_datetime(analysis_str, is_utc=True)

                    ws_kmh = float(slot.get("ws", 0.0) or 0.0)
                    ws_ms = round(ws_kmh / 3.6, 2)

                    normalized_records.append(
                        BMKGForecastPointSchema(
                            region_code=item_loc.adm4,
                            adm2_code=item_loc.adm2,
                            adm3_code=item_loc.adm3,
                            desa_name=item_loc.desa,
                            kecamatan_name=item_loc.kecamatan,
                            kotkab_name=item_loc.kotkab,
                            latitude=item_loc.lat,
                            longitude=item_loc.lon,
                            analysis_time=analysis_dt,
                            forecast_time_utc=utc_dt,
                            forecast_time_local=local_dt,
                            temperature_c=float(slot["t"]),
                            humidity_pct=float(slot["hu"]),
                            weather_code=int(slot["weather"]) if slot.get("weather") is not None else None,
                            weather_desc_id=str(slot.get("weather_desc", "Tidak Diketahui")).strip(),
                            weather_desc_en=str(slot.get("weather_desc_en", "")).strip() or None,
                            wind_speed_kmh=ws_kmh,
                            wind_speed_ms=ws_ms,
                            wind_dir_cardinal=str(slot.get("wd", "")).strip() or None,
                            wind_dir_deg=float(slot["wd_deg"]) if slot.get("wd_deg") is not None else None,
                            cloud_cover_pct=float(slot["tcc"]) if slot.get("tcc") is not None else None,
                            visibility_text=str(slot.get("vs_text", "")).strip() or None,
                            visibility_m=int(slot["vs"]) if slot.get("vs") is not None else None,
                            fetched_at=fetched_at,
                        )
                    )

        normalized_records.sort(key=lambda r: r.forecast_time_utc)
        return normalized_records

    def fetch_and_parse(self, adm4_code: str, use_cache: bool = True) -> List[BMKGForecastPointSchema]:
        raw_payload = self.fetch_raw_forecast(adm4_code=adm4_code, use_cache=use_cache)
        return self.parse_forecast_payload(raw_payload)
