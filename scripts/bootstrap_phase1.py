#!/usr/bin/env python3
"""
Phase 1 Automated File Builder — ACEH SIAGA CUACA
Menuliskan seluruh modul Phase 1 (src/*, tests/*, scripts/*, pytest.ini) secara otomatis.
Jalankan dengan: python scripts\bootstrap_phase1.py
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

FILES: dict[str, str] = {}

# 1. pytest.ini agar root directory selalu masuk ke PYTHONPATH
FILES["pytest.ini"] = """[pytest]
pythonpath = .
testpaths = tests
"""

# 2. src/data_collection/bmkg_forecast.py
FILES["src/data_collection/bmkg_forecast.py"] = '''"""
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
ACEH_ADM4_REGEX = re.compile(r"^11\\.\\d{2}\\.\\d{2}\\.\\d{4}$")

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
'''

# 3. src/data_collection/bmkg_alerts.py
FILES["src/data_collection/bmkg_alerts.py"] = '''"""
BMKG Weather Early Warning (Nowcasting RSS & CAP v1.2 XML) Collector — ACEH SIAGA CUACA
Endpoint RSS Resmi: https://www.bmkg.go.id/alerts/nowcast/id
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, List, Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from defusedxml import ElementTree as SafeET
from pydantic import BaseModel, Field

logger = logging.getLogger("aceh_siaga.bmkg_alerts")
WIB_TZ = ZoneInfo("Asia/Jakarta")

ACEH_KEYWORDS = (
    "aceh",
    "banda aceh",
    "sabang",
    "lhokseumawe",
    "langsa",
    "subulussalam",
    "simeulue",
    "singkil",
    "bireuen",
    "pidie",
    "gayo lues",
    "nagan raya",
    "bener meriah",
    "tamiang",
)


class RSSAlertItemSchema(BaseModel):
    title: str
    cap_url: str
    pub_date_raw: Optional[str] = None
    description: Optional[str] = None
    is_aceh_related: bool = False


class CAPAlertSchema(BaseModel):
    cap_identifier: str
    sender: str
    sent_time: datetime
    status: str
    msg_type: str
    event_type: str
    urgency: str
    severity: str
    certainty: str
    effective_time: datetime
    onset_time: Optional[datetime] = None
    expires_time: datetime
    headline: str
    description: str
    instruction: Optional[str] = None
    official_web_url: Optional[str] = None
    cap_xml_url: str
    affected_areas_text: str
    polygons_geojson: List[List[List[float]]] = Field(default_factory=list)
    multipolygon_wkt: Optional[str] = None
    source_attribution: str = "Peringatan Dini Cuaca Resmi BMKG (CAP v1.2)"
    data_nature: str = "OFFICIAL_ALERT"
    fetched_at: datetime


class BMKGAlertCollector:
    """Pengumpul dan parser RSS + CAP XML Peringatan Dini Cuaca BMKG."""

    RSS_URL = "https://www.bmkg.go.id/alerts/nowcast/id"

    def __init__(self, timeout_seconds: int = 15, min_interval_seconds: float = 1.2) -> None:
        self.timeout_seconds = timeout_seconds
        self.min_interval_seconds = min_interval_seconds
        self._last_req_ts = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "AcehSiagaCuaca-ResearchPlatform/1.0 (BMKG CAP Alert Consumer)",
                "Accept": "application/xml, text/xml, application/rss+xml",
            }
        )

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_req_ts
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)
        self._last_req_ts = time.monotonic()

    @staticmethod
    def _is_valid_bmkg_url(url: str) -> bool:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and parsed.netloc.endswith("bmkg.go.id")

    @staticmethod
    def _matches_aceh(text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in ACEH_KEYWORDS)

    @classmethod
    def parse_rss_xml(cls, rss_xml_text: str, filter_aceh_only: bool = True) -> List[RSSAlertItemSchema]:
        root = SafeET.fromstring(rss_xml_text.strip())
        items: List[RSSAlertItemSchema] = []

        for item_elem in root.findall(".//item"):
            title = (item_elem.findtext("title") or "").strip()
            link = (item_elem.findtext("link") or "").strip()
            pub_date = (item_elem.findtext("pubDate") or "").strip() or None
            description = (item_elem.findtext("description") or "").strip() or None

            if not link or not cls._is_valid_bmkg_url(link):
                continue

            combined_text = f"{title} {description or ''} {link}"
            is_aceh = cls._matches_aceh(combined_text)

            if filter_aceh_only and not is_aceh:
                continue

            items.append(
                RSSAlertItemSchema(
                    title=title,
                    cap_url=link,
                    pub_date_raw=pub_date,
                    description=description,
                    is_aceh_related=is_aceh,
                )
            )
        return items

    @staticmethod
    def convert_cap_polygon_to_lonlat_ring(cap_polygon_str: str) -> Optional[List[List[float]]]:
        raw_pairs = cap_polygon_str.strip().split()
        if len(raw_pairs) < 3:
            return None

        ring: List[List[float]] = []
        for pair in raw_pairs:
            parts = pair.split(",")
            if len(parts) != 2:
                continue
            try:
                lat = float(parts[0])
                lon = float(parts[1])
            except ValueError:
                continue
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                continue
            ring.append([round(lon, 6), round(lat, 6)])

        if len(ring) < 3:
            return None

        if ring[0] != ring[-1]:
            ring.append(ring[0])

        return ring if len(ring) >= 4 else None

    @staticmethod
    def rings_to_multipolygon_wkt(rings: List[List[List[float]]]) -> Optional[str]:
        if not rings:
            return None
        poly_strings: List[str] = []
        for ring in rings:
            coord_str = ", ".join(f"{pt[0]} {pt[1]}" for pt in ring)
            poly_strings.append(f"(({coord_str}))")
        return f"MULTIPOLYGON({', '.join(poly_strings)})"

    @staticmethod
    def _parse_cap_timestamp(ts_str: Optional[str], fallback: Optional[datetime] = None) -> datetime:
        if not ts_str:
            return fallback or datetime.now(WIB_TZ)
        cleaned = ts_str.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return fallback or datetime.now(WIB_TZ)

    @classmethod
    def parse_cap_xml(cls, cap_xml_text: str, cap_xml_url: str) -> CAPAlertSchema:
        root = SafeET.fromstring(cap_xml_text.strip())

        def find_text(elem: Any, tag_name: str, default: str = "") -> str:
            for child in elem.iter():
                local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if local_name == tag_name and child.text:
                    return child.text.strip()
            return default

        identifier = find_text(root, "identifier")
        if not identifier:
            raise ValueError("Dokumen CAP XML tidak memiliki elemen <identifier>.")

        sender = find_text(root, "sender", "BMKG")
        sent_time = cls._parse_cap_timestamp(find_text(root, "sent"))
        status = find_text(root, "status", "Actual")
        msg_type = find_text(root, "msgType", "Alert")

        info_blocks = [
            el for el in root.iter()
            if (el.tag.split("}")[-1] if "}" in el.tag else el.tag) == "info"
        ]
        if not info_blocks:
            raise ValueError(f"Dokumen CAP {identifier} tidak memiliki elemen <info>.")

        selected_info = info_blocks[0]
        for info_el in info_blocks:
            lang = find_text(info_el, "language", "").lower()
            if "id" in lang:
                selected_info = info_el
                break

        event_type = find_text(selected_info, "event", "Cuaca Ekstrem")
        urgency = find_text(selected_info, "urgency", "Immediate")
        severity = find_text(selected_info, "severity", "Moderate")
        certainty = find_text(selected_info, "certainty", "Likely")

        effective_time = cls._parse_cap_timestamp(
            find_text(selected_info, "effective") or find_text(selected_info, "onset"),
            fallback=sent_time,
        )
        onset_raw = find_text(selected_info, "onset")
        onset_time = cls._parse_cap_timestamp(onset_raw, fallback=effective_time) if onset_raw else effective_time
        expires_time = cls._parse_cap_timestamp(find_text(selected_info, "expires"), fallback=sent_time)

        headline = find_text(selected_info, "headline", event_type)
        description = find_text(selected_info, "description", headline)
        instruction = find_text(selected_info, "instruction") or None
        official_web_url = find_text(selected_info, "web") or None

        area_descs: List[str] = []
        polygons_geojson: List[List[List[float]]] = []

        for child in selected_info.iter():
            local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local_name == "areaDesc" and child.text:
                text_val = child.text.strip()
                if text_val and text_val not in area_descs:
                    area_descs.append(text_val)
            elif local_name == "polygon" and child.text:
                ring = cls.convert_cap_polygon_to_lonlat_ring(child.text)
                if ring is not None:
                    polygons_geojson.append(ring)

        affected_areas_text = "; ".join(area_descs) if area_descs else "Wilayah Provinsi Aceh"
        multipolygon_wkt = cls.rings_to_multipolygon_wkt(polygons_geojson)

        return CAPAlertSchema(
            cap_identifier=identifier,
            sender=sender,
            sent_time=sent_time,
            status=status,
            msg_type=msg_type,
            event_type=event_type,
            urgency=urgency,
            severity=severity,
            certainty=certainty,
            effective_time=effective_time,
            onset_time=onset_time,
            expires_time=expires_time,
            headline=headline,
            description=description,
            instruction=instruction,
            official_web_url=official_web_url,
            cap_xml_url=cap_xml_url,
            affected_areas_text=affected_areas_text,
            polygons_geojson=polygons_geojson,
            multipolygon_wkt=multipolygon_wkt,
            fetched_at=datetime.now(WIB_TZ),
        )

    def fetch_active_aceh_alerts(self) -> List[CAPAlertSchema]:
        self._throttle()
        rss_resp = self.session.get(self.RSS_URL, timeout=self.timeout_seconds)
        rss_resp.raise_for_status()

        rss_items = self.parse_rss_xml(rss_resp.text, filter_aceh_only=True)
        parsed_alerts: List[CAPAlertSchema] = []

        for item in rss_items:
            try:
                self._throttle()
                cap_resp = self.session.get(item.cap_url, timeout=self.timeout_seconds)
                cap_resp.raise_for_status()
                alert_obj = self.parse_cap_xml(cap_resp.text, cap_xml_url=item.cap_url)
                parsed_alerts.append(alert_obj)
            except (requests.RequestException, ValueError) as exc:
                logger.error("Gagal memproses detail CAP dari %s: %s", item.cap_url, exc)

        return parsed_alerts
'''

# 4. src/data_processing/data_cleaning.py
FILES["src/data_processing/data_cleaning.py"] = '''"""
BMKG Meteorological Data Cleaning & Validation Engine — ACEH SIAGA CUACA
File: src/data_processing/data_cleaning.py
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("aceh_siaga.data_cleaning")

BMKG_COLUMN_ALIASES: Dict[str, str] = {
    "tanggal": "observation_date",
    "date": "observation_date",
    "observation_date": "observation_date",
    "wmo_id": "wmo_id",
    "station_id": "wmo_id",
    "kode_stasiun": "wmo_id",
    "tn": "temp_min_c",
    "temp_min": "temp_min_c",
    "temp_min_c": "temp_min_c",
    "tx": "temp_max_c",
    "temp_max": "temp_max_c",
    "temp_max_c": "temp_max_c",
    "tavg": "temp_avg_c",
    "temp_avg": "temp_avg_c",
    "temp_avg_c": "temp_avg_c",
    "rh_avg": "humidity_avg_pct",
    "humidity_avg": "humidity_avg_pct",
    "humidity_avg_pct": "humidity_avg_pct",
    "rr": "rainfall_mm",
    "curah_hujan": "rainfall_mm",
    "rainfall_mm": "rainfall_mm",
    "ss": "sunshine_hours",
    "sunshine_hours": "sunshine_hours",
    "ff_x": "wind_speed_max_ms",
    "wind_speed_max_ms": "wind_speed_max_ms",
    "ddd_x": "wind_dir_max_deg",
    "wind_dir_max_deg": "wind_dir_max_deg",
    "ff_avg": "wind_speed_avg_ms",
    "wind_speed_avg_ms": "wind_speed_avg_ms",
    "ddd_car": "wind_dir_predominant",
    "wind_dir_predominant": "wind_dir_predominant",
}

MISSING_TOKENS = {"9999", "9999.0", "-", "--", "na", "n/a", "null", "none", ""}
TRACE_TOKENS = {"8888", "8888.0"}


def classify_bmkg_daily_rainfall(rr_value: Optional[float]) -> str:
    if rr_value is None or pd.isna(rr_value):
        return "MISSING"
    val = float(rr_value)
    if val < 0.5:
        return "NO_RAIN"
    if val <= 20.0:
        return "LIGHT"
    if val <= 50.0:
        return "MODERATE"
    if val <= 100.0:
        return "HEAVY"
    if val <= 150.0:
        return "VERY_HEAVY"
    return "EXTREME"


def clean_bmkg_observation_dataframe(
    df_raw: pd.DataFrame,
    default_wmo_id: Optional[str] = None,
) -> pd.DataFrame:
    if df_raw.empty:
        raise ValueError("DataFrame input observasi BMKG kosong.")

    df = df_raw.copy()

    renamed_cols: Dict[str, str] = {}
    for col in df.columns:
        normalized_key = str(col).strip().lower()
        if normalized_key in BMKG_COLUMN_ALIASES:
            renamed_cols[col] = BMKG_COLUMN_ALIASES[normalized_key]
    df = df.rename(columns=renamed_cols)

    if "observation_date" not in df.columns:
        raise ValueError("Kolom tanggal ('Tanggal' atau 'observation_date') wajib tersedia.")

    if "wmo_id" not in df.columns:
        if default_wmo_id:
            df["wmo_id"] = str(default_wmo_id)
        else:
            raise ValueError("Kolom 'wmo_id' tidak ditemukan dan default_wmo_id tidak diberikan.")

    df["wmo_id"] = df["wmo_id"].astype(str).str.strip()

    parsed_dates = pd.to_datetime(df["observation_date"], dayfirst=True, errors="coerce")
    if parsed_dates.isna().any():
        fallback_dates = pd.to_datetime(df["observation_date"], format="mixed", errors="coerce")
        parsed_dates = parsed_dates.fillna(fallback_dates)

    if int(parsed_dates.isna().sum()) > 0:
        df = df.loc[parsed_dates.notna()].copy()
        parsed_dates = parsed_dates.loc[parsed_dates.notna()]

    df["observation_date"] = parsed_dates.dt.date

    df["is_trace_rainfall"] = False
    df["is_missing_rainfall"] = False

    if "rainfall_mm" in df.columns:
        raw_rr_str = df["rainfall_mm"].astype(str).str.strip().str.lower().str.replace(",", ".", regex=False)
        trace_mask = raw_rr_str.isin(TRACE_TOKENS)
        missing_mask = raw_rr_str.isin(MISSING_TOKENS) | df["rainfall_mm"].isna()

        rr_numeric = pd.to_numeric(raw_rr_str, errors="coerce")
        trace_mask = trace_mask | (rr_numeric == 8888.0)
        missing_mask = missing_mask | (rr_numeric == 9999.0) | (rr_numeric.isna() & ~trace_mask)

        rr_cleaned = rr_numeric.copy()
        rr_cleaned.loc[trace_mask] = 0.0
        rr_cleaned.loc[missing_mask] = np.nan

        df["rainfall_mm"] = rr_cleaned
        df["is_trace_rainfall"] = trace_mask
        df["is_missing_rainfall"] = df["rainfall_mm"].isna()
    else:
        df["rainfall_mm"] = np.nan
        df["is_missing_rainfall"] = True

    numeric_cols = [
        "temp_min_c",
        "temp_max_c",
        "temp_avg_c",
        "humidity_avg_pct",
        "sunshine_hours",
        "wind_speed_max_ms",
        "wind_dir_max_deg",
        "wind_speed_avg_ms",
    ]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = np.nan
            continue
        col_str = df[col].astype(str).str.strip().str.lower().str.replace(",", ".", regex=False)
        num_series = pd.to_numeric(col_str, errors="coerce")
        invalid_code_mask = col_str.isin(MISSING_TOKENS | TRACE_TOKENS) | (num_series.isin([8888.0, 9999.0]))
        num_series.loc[invalid_code_mask] = np.nan
        df[col] = num_series

    if "wind_dir_predominant" in df.columns:
        dir_str = df["wind_dir_predominant"].astype(str).str.strip().str.upper()
        dir_str = dir_str.replace({t.upper(): None for t in (MISSING_TOKENS | TRACE_TOKENS)})
        df["wind_dir_predominant"] = dir_str
    else:
        df["wind_dir_predominant"] = None

    quality_flags: List[str] = []
    for idx, row in df.iterrows():
        flags: List[str] = []

        rr = row["rainfall_mm"]
        if pd.notna(rr) and (rr < 0.0 or rr > 600.0):
            flags.append("ANOMALY_RAINFALL_RANGE")
            df.at[idx, "rainfall_mm"] = np.nan
            df.at[idx, "is_missing_rainfall"] = True

        tn, tavg, tx = row["temp_min_c"], row["temp_avg_c"], row["temp_max_c"]
        for t_col, t_val in [("temp_min_c", tn), ("temp_avg_c", tavg), ("temp_max_c", tx)]:
            if pd.notna(t_val) and not (10.0 <= float(t_val) <= 42.0):
                flags.append(f"OUT_OF_RANGE_{t_col.upper()}")
                df.at[idx, t_col] = np.nan

        tn, tavg, tx = df.at[idx, "temp_min_c"], df.at[idx, "temp_avg_c"], df.at[idx, "temp_max_c"]
        if pd.notna(tn) and pd.notna(tx) and float(tn) > float(tx):
            flags.append("INCONSISTENT_TN_GT_TX")
            df.at[idx, "temp_min_c"] = np.nan
            df.at[idx, "temp_max_c"] = np.nan

        if pd.notna(tavg):
            if (pd.notna(tn) and float(tavg) < float(tn) - 0.5) or (pd.notna(tx) and float(tavg) > float(tx) + 0.5):
                flags.append("INCONSISTENT_TAVG_BOUNDS")

        rh = row["humidity_avg_pct"]
        if pd.notna(rh) and not (10.0 <= float(rh) <= 100.0):
            flags.append("OUT_OF_RANGE_HUMIDITY")
            df.at[idx, "humidity_avg_pct"] = np.nan

        ss = row["sunshine_hours"]
        if pd.notna(ss) and not (0.0 <= float(ss) <= 12.5):
            flags.append("OUT_OF_RANGE_SUNSHINE")
            df.at[idx, "sunshine_hours"] = np.nan

        for w_col in ("wind_speed_max_ms", "wind_speed_avg_ms"):
            w_val = row[w_col]
            if pd.notna(w_val) and not (0.0 <= float(w_val) <= 60.0):
                flags.append(f"OUT_OF_RANGE_{w_col.upper()}")
                df.at[idx, w_col] = np.nan

        quality_flags.append("VALID" if not flags else ";".join(flags))

    df["quality_flag"] = quality_flags
    df["rainfall_category"] = df["rainfall_mm"].apply(classify_bmkg_daily_rainfall)

    df = df.sort_values(["wmo_id", "observation_date"]).drop_duplicates(
        subset=["wmo_id", "observation_date"], keep="last"
    )

    ordered_columns = [
        "wmo_id",
        "observation_date",
        "temp_min_c",
        "temp_max_c",
        "temp_avg_c",
        "humidity_avg_pct",
        "rainfall_mm",
        "is_trace_rainfall",
        "is_missing_rainfall",
        "sunshine_hours",
        "wind_speed_max_ms",
        "wind_dir_max_deg",
        "wind_speed_avg_ms",
        "wind_dir_predominant",
        "rainfall_category",
        "quality_flag",
    ]
    return df[ordered_columns].reset_index(drop=True)
'''

# 5. src/data_collection/bmkg_historical_import.py
FILES["src/data_collection/bmkg_historical_import.py"] = '''"""
BMKG Historical Observation CSV/XLSX Importer — ACEH SIAGA CUACA
File: src/data_collection/bmkg_historical_import.py
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.data_processing.data_cleaning import clean_bmkg_observation_dataframe

logger = logging.getLogger("aceh_siaga.bmkg_historical_import")


class BMKGHistoricalImporter:
    """Pipeline untuk memuat, membersihkan, dan mengekspor data observasi historis BMKG."""

    @staticmethod
    def load_file(file_path: Path, default_wmo_id: Optional[str] = None) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File data observasi BMKG tidak ditemukan: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            raw_df = pd.read_csv(path)
        elif suffix in (".xlsx", ".xls"):
            raw_df = pd.read_excel(path)
        else:
            raise ValueError(f"Format file '{suffix}' tidak didukung. Gunakan .csv atau .xlsx.")

        cleaned_df = clean_bmkg_observation_dataframe(raw_df, default_wmo_id=default_wmo_id)
        cleaned_df["source_file"] = path.name
        return cleaned_df

    @staticmethod
    def generate_demo_dataset(output_path: Path = Path("data/demo/demo_bmkg_historical_aceh.csv")) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rng = np.random.default_rng(seed=20261118)
        dates = pd.date_range("2021-01-01", "2026-10-31", freq="D")
        stations = [
            ("96001", 27.2, 1.0),
            ("96002", 27.5, 1.1),
            ("96003", 26.8, 1.05),
            ("96009", 27.4, 0.9),
            ("96011", 26.9, 1.35),
        ]

        rows = []
        for wmo_id, base_temp, rain_multiplier in stations:
            for d in dates:
                doy = d.dayofyear
                seasonal_factor = (
                    1.0
                    + 0.65 * np.cos(2 * np.pi * (doy - 320) / 365.25)
                    + 0.35 * np.cos(2 * np.pi * (doy - 115) / 365.25)
                )
                rain_prob = min(0.75, max(0.18, 0.32 * seasonal_factor))

                u = rng.random()
                if u < 0.015:
                    rr_val = 9999.0
                elif u < 0.08:
                    rr_val = 8888.0
                elif rng.random() < rain_prob:
                    gamma_rain = rng.gamma(shape=1.15, scale=14.0 * seasonal_factor * rain_multiplier)
                    rr_val = round(min(280.0, float(gamma_rain)), 1)
                else:
                    rr_val = 0.0

                is_rainy = rr_val not in (0.0, 8888.0, 9999.0)
                t_avg = round(base_temp - (0.8 if is_rainy else 0.0) + float(rng.normal(0, 0.7)), 1)
                t_min = round(t_avg - abs(float(rng.normal(3.4, 0.6))), 1)
                t_max = round(t_avg + abs(float(rng.normal(4.1, 0.7))), 1)
                rh_avg = round(min(99.0, max(62.0, 79.0 + (8.5 if is_rainy else -3.0) + float(rng.normal(0, 4.0)))), 1)
                ss = round(max(0.0, min(11.5, (4.2 if is_rainy else 8.1) + float(rng.normal(0, 1.5)))), 1)
                ff_avg = round(max(0.5, float(rng.gamma(2.2, 1.1))), 1)
                ff_x = round(ff_avg + abs(float(rng.normal(3.5, 1.4))), 1)
                ddd_x = int(rng.integers(0, 360))
                ddd_car = str(rng.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]))

                rows.append(
                    {
                        "wmo_id": wmo_id,
                        "Tanggal": d.strftime("%d-%m-%Y"),
                        "Tn": t_min,
                        "Tx": t_max,
                        "Tavg": t_avg,
                        "RH_avg": rh_avg,
                        "RR": rr_val,
                        "ss": ss,
                        "ff_x": ff_x,
                        "ddd_x": ddd_x,
                        "ff_avg": ff_avg,
                        "ddd_car": ddd_car,
                        "data_mode": "DEMO_SYNTHETIC_DO_NOT_CLAIM_AS_OFFICIAL_OBSERVATION",
                    }
                )

        demo_df = pd.DataFrame(rows)
        demo_df.to_csv(output_path, index=False)
        return output_path
'''

# 6. src/data_collection/disaster_import.py
FILES["src/data_collection/disaster_import.py"] = '''"""
BPBA Aceh & BNPB DIBI Disaster Event Importer — ACEH SIAGA CUACA
File: src/data_collection/disaster_import.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

VALID_DISASTER_TYPES: Dict[str, str] = {
    "banjir": "BANJIR",
    "banjir bandang": "BANJIR_BANDANG",
    "tanah longsor": "TANAH_LONGSOR",
    "longsor": "TANAH_LONGSOR",
    "angin kencang": "ANGIN_KENCANG",
    "puting beliung": "CUACA_EKSTREM",
    "cuaca ekstrem": "CUACA_EKSTREM",
    "gelombang pasang": "GELOMBANG_PASANG_ABRASI",
    "abrasi": "GELOMBANG_PASANG_ABRASI",
    "kekeringan": "KEKERINGAN",
}


class DisasterDataImporter:
    """Importer dan validator CSV/XLSX data bencana hidrometeorologi Provinsi Aceh."""

    @staticmethod
    def normalize_disaster_type(raw_type: str) -> str:
        cleaned = str(raw_type).strip().lower()
        for key, canonical in VALID_DISASTER_TYPES.items():
            if key in cleaned:
                return canonical
        return "CUACA_EKSTREM"

    @classmethod
    def clean_disaster_dataframe(cls, df_raw: pd.DataFrame) -> pd.DataFrame:
        if df_raw.empty:
            raise ValueError("DataFrame bencana kosong.")

        df = df_raw.copy()
        col_map = {c.strip().lower(): c for c in df.columns}

        required = {"event_code", "region_code", "disaster_type", "event_date"}
        missing = required - set(col_map.keys())
        if missing:
            raise ValueError(f"Kolom wajib data bencana tidak lengkap: {missing}")

        df = df.rename(columns={col_map[k]: k for k in col_map})
        df["event_code"] = df["event_code"].astype(str).str.strip()
        df["region_code"] = df["region_code"].astype(str).str.strip()
        df = df[df["region_code"].str.startswith("11.")].copy()

        df["disaster_type"] = df["disaster_type"].apply(cls.normalize_disaster_type)
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce").dt.date
        df = df[df["event_date"].notna()].copy()

        impact_cols: List[str] = [
            "casualties_dead",
            "casualties_missing",
            "casualties_injured",
            "affected_people",
            "displaced_people",
            "houses_heavily_damaged",
            "houses_moderately_damaged",
            "houses_lightly_damaged",
            "houses_submerged",
            "public_facilities_damaged",
        ]
        for col in impact_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0).astype(int)

        df = df.sort_values("event_date").drop_duplicates(subset=["event_code"], keep="last")
        return df.reset_index(drop=True)

    @classmethod
    def import_file(cls, file_path: Path) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File data bencana tidak ditemukan: {path}")
        raw_df = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
        return cls.clean_disaster_dataframe(raw_df)
'''

# 7. scripts/verify_phase1_live.py
FILES["scripts/verify_phase1_live.py"] = '''#!/usr/bin/env python3
"""
Phase 1 Live Verification Script — ACEH SIAGA CUACA
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_collection.bmkg_alerts import BMKGAlertCollector
from src.data_collection.bmkg_forecast import BMKGForecastCollector
from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("verify_phase1")


def run_phase1_verification() -> None:
    logger.info("=== 1. Menguji Pengambilan Data Prakiraan Cuaca Nyata BMKG (Kota Banda Aceh) ===")
    forecast_collector = BMKGForecastCollector()
    try:
        records = forecast_collector.fetch_and_parse("11.71.01.2001", use_cache=True)
        logger.info(
            "BERHASIL: Diperoleh %d titik waktu prakiraan untuk %s, %s.",
            len(records),
            records[0].desa_name if records else "-",
            records[0].kotkab_name if records else "-",
        )
        if records:
            first = records[0]
            logger.info(
                "Contoh Slot Terdekat (%s WIB): %s | Suhu=%.1fC | RH=%.0f%% | Angin=%.1f km/jam (%s)",
                first.forecast_time_local,
                first.weather_desc_id,
                first.temperature_c,
                first.humidity_pct,
                first.wind_speed_kmh,
                first.wind_dir_cardinal,
            )
    except Exception as exc:
        logger.warning("Kendala jaringan saat mengakses API prakiraan BMKG: %s", exc)

    logger.info("=== 2. Menguji Pengambilan RSS & CAP Peringatan Dini Cuaca BMKG (Filter Aceh) ===")
    alert_collector = BMKGAlertCollector()
    try:
        active_alerts = alert_collector.fetch_active_aceh_alerts()
        logger.info("BERHASIL: Ditemukan %d peringatan dini aktif untuk wilayah Aceh.", len(active_alerts))
        for alert in active_alerts:
            logger.info(
                "ALERT AKTIF [%s]: %s | Wilayah: %s | Berlaku s.d. %s",
                alert.severity,
                alert.headline,
                alert.affected_areas_text,
                alert.expires_time,
            )
    except Exception as exc:
        logger.warning("Kendala jaringan saat mengakses RSS Nowcast BMKG: %s", exc)

    logger.info("=== 3. Memverifikasi Pipeline Impor & Pembersihan Observasi Historis ===")
    demo_csv = BMKGHistoricalImporter.generate_demo_dataset()
    cleaned_df = BMKGHistoricalImporter.load_file(demo_csv)
    trace_count = int(cleaned_df["is_trace_rainfall"].sum())
    missing_count = int(cleaned_df["is_missing_rainfall"].sum())
    extreme_count = int(cleaned_df["rainfall_category"].isin(["HEAVY", "VERY_HEAVY", "EXTREME"]).sum())
    logger.info(
        "BERHASIL: Total baris bersih=%d | Kode 8888 (Trace->0.0mm)=%d | Kode 9999 (Missing->NaN)=%d | Hujan Lebat-Ekstrem (>=50mm)=%d",
        len(cleaned_df),
        trace_count,
        missing_count,
        extreme_count,
    )


if __name__ == "__main__":
    run_phase1_verification()
'''


def main() -> None:
    print(f"[PHASE 1 BUILDER] Menuliskan file-file Phase 1 ke: {BASE_DIR}")
    for rel_path, content in FILES.items():
        target = BASE_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"  [OK] {rel_path} ({len(content)} bytes)")
    print("[PHASE 1 BUILDER] Selesai! Sekarang jalankan: python -m pytest tests\\test_phase1_data_foundation.py -v")


if __name__ == "__main__":
    main()