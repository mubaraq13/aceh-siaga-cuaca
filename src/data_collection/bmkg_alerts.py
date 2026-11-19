"""
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
