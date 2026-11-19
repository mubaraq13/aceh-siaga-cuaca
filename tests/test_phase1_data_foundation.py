"""
Unit Tests for PHASE 1 — DATA FOUNDATION (ACEH SIAGA CUACA)
File: tests/test_phase1_data_foundation.py
Jalankan dengan: pytest tests/test_phase1_data_foundation.py -v
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data_collection.bmkg_alerts import BMKGAlertCollector
from src.data_collection.bmkg_forecast import BMKGForecastCollector
from src.data_collection.disaster_import import DisasterDataImporter
from src.data_processing.data_cleaning import (
    classify_bmkg_daily_rainfall,
    clean_bmkg_observation_dataframe,
)


def test_adm4_validation_accepts_aceh_and_rejects_non_aceh() -> None:
    assert BMKGForecastCollector.validate_adm4_code("11.71.01.2001") == "11.71.01.2001"
    with pytest.raises(ValueError, match="Wajib menggunakan format Aceh"):
        BMKGForecastCollector.validate_adm4_code("12.71.01.1001")  # Sumatera Utara (12) ditolak


def test_parse_bmkg_forecast_payload() -> None:
    sample_payload = {
        "lokasi": {
            "adm1": "11",
            "adm2": "11.71",
            "adm3": "11.71.01",
            "adm4": "11.71.01.2001",
            "provinsi": "Aceh",
            "kotkab": "Kota Banda Aceh",
            "kecamatan": "Baiturrahman",
            "desa": "Kampung Baru",
            "lon": 95.3175,
            "lat": 5.5540,
            "timezone": "Asia/Jakarta",
        },
        "data": [
            {
                "lokasi": {
                    "adm1": "11",
                    "adm2": "11.71",
                    "adm3": "11.71.01",
                    "adm4": "11.71.01.2001",
                    "provinsi": "Aceh",
                    "kotkab": "Kota Banda Aceh",
                    "kecamatan": "Baiturrahman",
                    "desa": "Kampung Baru",
                    "lon": 95.3175,
                    "lat": 5.5540,
                },
                "cuaca": [
                    [
                        {
                            "utc_datetime": "2026-11-18 15:00:00",
                            "local_datetime": "2026-11-18 22:00:00",
                            "t": 26,
                            "hu": 88,
                            "weather": 61,
                            "weather_desc": "Hujan Ringan",
                            "weather_desc_en": "Light Rain",
                            "ws": 18.0,
                            "wd": "SW",
                            "wd_deg": 225,
                            "tcc": 85,
                            "vs": 8000,
                            "vs_text": "< 8 km",
                            "analysis_date": "2026-11-18T12:00:00",
                        }
                    ]
                ],
            }
        ],
    }

    records = BMKGForecastCollector.parse_forecast_payload(sample_payload)
    assert len(records) == 1
    rec = records[0]
    assert rec.region_code == "11.71.01.2001"
    assert rec.kotkab_name == "Kota Banda Aceh"
    assert rec.temperature_c == 26.0
    assert rec.humidity_pct == 88.0
    assert rec.weather_desc_id == "Hujan Ringan"
    assert rec.wind_speed_kmh == 18.0
    assert rec.wind_speed_ms == 5.0
    assert rec.data_nature == "OFFICIAL_FORECAST"


def test_parse_rss_and_cap_xml_with_polygon_reversal() -> None:
    sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>BMKG Nowcast Alerts</title>
        <item>
          <title>Peringatan Dini Cuaca Aceh</title>
          <link>https://www.bmkg.go.id/alerts/nowcast/id/ACAC20261118001_alert.xml</link>
          <pubDate>Wed, 18 Nov 2026 16:00:00 +0000</pubDate>
          <description>Berpotensi hujan sedang-lebat di wilayah Aceh Besar dan Kota Banda Aceh.</description>
        </item>
        <item>
          <title>Peringatan Dini Cuaca Jawa Barat</title>
          <link>https://www.bmkg.go.id/alerts/nowcast/id/JBJB20261118002_alert.xml</link>
          <description>Hujan lebat di Bandung.</description>
        </item>
      </channel>
    </rss>
    """
    aceh_items = BMKGAlertCollector.parse_rss_xml(sample_rss, filter_aceh_only=True)
    assert len(aceh_items) == 1
    assert aceh_items[0].cap_url == "https://www.bmkg.go.id/alerts/nowcast/id/ACAC20261118001_alert.xml"

    sample_cap = """<?xml version="1.0" encoding="UTF-8"?>
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <identifier>BMKG-CAP-ACEH-20261118-01</identifier>
      <sender>pusat@bmkg.go.id</sender>
      <sent>2026-11-18T22:00:00+07:00</sent>
      <status>Actual</status>
      <msgType>Alert</msgType>
      <info>
        <language>id-ID</language>
        <category>Met</category>
        <event>Hujan Lebat disertai Kilat/Petir dan Angin Kencang</event>
        <urgency>Immediate</urgency>
        <severity>Severe</severity>
        <certainty>Observed</certainty>
        <effective>2026-11-18T22:15:00+07:00</effective>
        <expires>2026-11-19T01:15:00+07:00</expires>
        <headline>Peringatan Dini Cuaca Wilayah Aceh</headline>
        <description>Berpotensi terjadi hujan sedang hingga lebat di Kota Banda Aceh dan Aceh Besar.</description>
        <instruction>Waspada potensi genangan dan pohon tumbang.</instruction>
        <web>https://www.bmkg.go.id/cuaca/peringatan-dini</web>
        <area>
          <areaDesc>Kota Banda Aceh, Kabupaten Aceh Besar</areaDesc>
          <polygon>5.50,95.30 5.60,95.30 5.60,95.45 5.50,95.45 5.50,95.30</polygon>
        </area>
      </info>
    </alert>
    """
    parsed_cap = BMKGAlertCollector.parse_cap_xml(sample_cap, cap_xml_url=aceh_items[0].cap_url)
    assert parsed_cap.cap_identifier == "BMKG-CAP-ACEH-20261118-01"
    assert parsed_cap.severity == "Severe"
    assert "Kota Banda Aceh" in parsed_cap.affected_areas_text
    # Verifikasi koordinat CAP (lat=5.50, lon=95.30) telah dibalik menjadi [lon=95.3, lat=5.5]
    assert len(parsed_cap.polygons_geojson) == 1
    first_point = parsed_cap.polygons_geojson[0][0]
    assert first_point == [95.3, 5.5]
    assert parsed_cap.multipolygon_wkt is not None
    assert parsed_cap.multipolygon_wkt.startswith("MULTIPOLYGON(((95.3 5.5,")


def test_bmkg_special_codes_8888_and_9999_cleaning() -> None:
    raw_df = pd.DataFrame(
        [
            {
                "wmo_id": "96001",
                "Tanggal": "01-11-2026",
                "Tn": 23.5,
                "Tx": 31.2,
                "Tavg": 27.1,
                "RH_avg": 84.0,
                "RR": 8888,  # Kode BMKG Trace Rainfall (<0.05 mm)
                "ss": 6.5,
                "ff_x": 8.0,
                "ddd_x": 240,
                "ff_avg": 3.2,
                "ddd_car": "SW",
            },
            {
                "wmo_id": "96001",
                "Tanggal": "02-11-2026",
                "Tn": 24.0,
                "Tx": 30.0,
                "Tavg": 26.5,
                "RH_avg": 88.0,
                "RR": 9999,  # Kode BMKG Missing Value
                "ss": 9999,
                "ff_x": 7.0,
                "ddd_x": 210,
                "ff_avg": 2.8,
                "ddd_car": "-",
            },
            {
                "wmo_id": "96001",
                "Tanggal": "03-11-2026",
                "Tn": 33.0,  # Anomali fisik: Tn > Tx
                "Tx": 25.0,
                "Tavg": 27.0,
                "RH_avg": 91.0,
                "RR": 65.4,  # Hujan Lebat (HEAVY)
                "ss": 2.1,
                "ff_x": 12.0,
                "ddd_x": 180,
                "ff_avg": 5.0,
                "ddd_car": "S",
            },
        ]
    )

    cleaned = clean_bmkg_observation_dataframe(raw_df)
    assert len(cleaned) == 3

    # Baris 1: RR = 8888 -> rainfall_mm = 0.0, is_trace_rainfall = True, category = NO_RAIN
    row1 = cleaned.iloc[0]
    assert row1["rainfall_mm"] == 0.0
    assert bool(row1["is_trace_rainfall"]) is True
    assert bool(row1["is_missing_rainfall"]) is False
    assert row1["rainfall_category"] == "NO_RAIN"

    # Baris 2: RR = 9999 -> rainfall_mm = NaN, is_missing_rainfall = True, category = MISSING
    row2 = cleaned.iloc[1]
    assert pd.isna(row2["rainfall_mm"])
    assert bool(row2["is_trace_rainfall"]) is False
    assert bool(row2["is_missing_rainfall"]) is True
    assert row2["rainfall_category"] == "MISSING"
    assert pd.isna(row2["sunshine_hours"])

    # Baris 3: Tn > Tx terdeteksi dan RR = 65.4 mm diklasifikasikan sebagai HEAVY
    row3 = cleaned.iloc[2]
    assert "INCONSISTENT_TN_GT_TX" in row3["quality_flag"]
    assert pd.isna(row3["temp_min_c"]) and pd.isna(row3["temp_max_c"])
    assert row3["rainfall_category"] == "HEAVY"


def test_rainfall_intensity_thresholds() -> None:
    assert classify_bmkg_daily_rainfall(None) == "MISSING"
    assert classify_bmkg_daily_rainfall(0.0) == "NO_RAIN"
    assert classify_bmkg_daily_rainfall(12.5) == "LIGHT"
    assert classify_bmkg_daily_rainfall(35.0) == "MODERATE"
    assert classify_bmkg_daily_rainfall(75.0) == "HEAVY"
    assert classify_bmkg_daily_rainfall(120.0) == "VERY_HEAVY"
    assert classify_bmkg_daily_rainfall(180.0) == "EXTREME"


def test_disaster_importer_normalizes_aceh_records() -> None:
    raw_disasters = pd.DataFrame(
        [
            {
                "event_code": "BPBA-2026-001",
                "region_code": "11.08",
                "disaster_type": "Banjir Bandang",
                "event_date": "2026-01-15",
                "affected_people": 1450,
                "houses_submerged": 320,
            },
            {
                "event_code": "NON-ACEH-002",
                "region_code": "12.01",  # Luar Aceh, harus terfilter otomatis
                "disaster_type": "Banjir",
                "event_date": "2026-01-16",
                "affected_people": 100,
                "houses_submerged": 20,
            },
        ]
    )
    cleaned = DisasterDataImporter.clean_disaster_dataframe(raw_disasters)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["region_code"] == "11.08"
    assert cleaned.iloc[0]["disaster_type"] == "BANJIR_BANDANG"
    assert cleaned.iloc[0]["houses_submerged"] == 320