"""
Integrated Data, GIS, Forecast, Alert & ML Service - ACEH SIAGA CUACA
File: backend/app/services/weather_service.py
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import pandas as pd

from backend.app.core.config import PROJECT_ROOT
from src.data_collection.bmkg_alerts import BMKGAlertCollector
from src.data_collection.bmkg_forecast import (
    ACEH_REPRESENTATIVE_ADM4,
    BMKGForecastCollector,
)
from src.geospatial.aceh_gis_analyzer import (
    ACEH_REGENCIES_GIS,
    ACEH_STATIONS_GIS,
    SPATIAL_LIMITATION_STATEMENT,
)
from src.machine_learning.model_trainer import MANDATORY_ML_DISCLAIMER

logger = logging.getLogger("aceh_siaga.weather_service")
WIB_TZ = ZoneInfo("Asia/Jakarta")


class AcehWeatherPlatformService:
    """Service layer utama yang menyatukan data BMKG, EDA, GIS, ML, dan Edukasi Kesiapsiagaan."""

    def __init__(self, root_dir: Path = PROJECT_ROOT) -> None:
        self.root_dir = Path(root_dir)
        self.processed_dir = self.root_dir / "data" / "processed"
        self.geojson_dir = self.processed_dir / "geojson"
        self.eval_dir = self.root_dir / "models" / "evaluation"
        self.trained_dir = self.root_dir / "models" / "trained"

        self.forecast_collector = BMKGForecastCollector(
            cache_dir=self.root_dir / "data" / "raw" / "bmkg" / "cache"
        )
        self.alert_collector = BMKGAlertCollector()

    @staticmethod
    def now_wib_iso() -> str:
        return datetime.now(WIB_TZ).isoformat()

    def get_health_status(self) -> Dict[str, Any]:
        obs_ok = (self.processed_dir / "cleaned_weather_observations_aceh.csv").exists()
        gis_ok = (self.geojson_dir / "aceh_weather_stations.geojson").exists()
        ml_ok = (self.eval_dir / "model_evaluation_report.json").exists()
        return {
            "service_name": "ACEH SIAGA CUACA REST API",
            "timezone": "Asia/Jakarta (WIB)",
            "api_health": "ONLINE" if (obs_ok and gis_ok and ml_ok) else "PARTIAL_DATA_READY",
            "processed_observations_available": obs_ok,
            "geojson_layers_available": gis_ok,
            "trained_ml_models_available": ml_ok,
            "last_checked_wib": self.now_wib_iso(),
        }

    def get_regions_catalog(self) -> Dict[str, Any]:
        regencies: List[Dict[str, Any]] = []
        for reg in ACEH_REGENCIES_GIS:
            code = reg["region_code"]
            rep_info = ACEH_REPRESENTATIVE_ADM4.get(code, {})
            regencies.append(
                {
                    "region_code": code,
                    "region_name": reg["name"],
                    "representative_adm4": rep_info.get("adm4", f"{code}.01.2001"),
                    "latitude": reg["lat"],
                    "longitude": reg["lon"],
                    "elevation_m": reg["elev_m"],
                    "topography_zone": reg["zone"],
                    "nearest_bmkg_station_wmo": reg["nearest_wmo"],
                }
            )
        return {
            "province_code": "11",
            "province_name": "Provinsi Aceh",
            "total_regencies_cities": len(regencies),
            "regencies": regencies,
            "bmkg_stations": ACEH_STATIONS_GIS,
        }

    def get_forecast_for_area(
        self,
        adm4_code: str | None = None,
        region_code: str | None = None,
    ) -> Dict[str, Any]:
        target_adm4 = adm4_code
        if not target_adm4:
            reg_key = (region_code or "11.71").strip()
            if reg_key not in ACEH_REPRESENTATIVE_ADM4:
                raise ValueError(f"Kode kabupaten/kota '{reg_key}' tidak ditemukan di Provinsi Aceh.")
            target_adm4 = ACEH_REPRESENTATIVE_ADM4[reg_key]["adm4"]

        valid_adm4 = self.forecast_collector.validate_adm4_code(target_adm4)

        api_health = "ONLINE"
        raw_payload = self.forecast_collector.fetch_raw_forecast(valid_adm4, use_cache=True)
        if raw_payload.get("_is_stale_cache"):
            api_health = "DEGRADED_USING_LAST_KNOWN_CACHE"

        points = self.forecast_collector.parse_forecast_payload(raw_payload)
        fetched_at_wib = raw_payload.get("_fetched_at_wib", self.now_wib_iso())

        serialized_slots = [
            {
                "forecast_time_utc": p.forecast_time_utc.isoformat(),
                "forecast_time_local": p.forecast_time_local.strftime("%Y-%m-%d %H:%M:%S"),
                "analysis_time": p.analysis_time.isoformat(),
                "temperature_c": p.temperature_c,
                "humidity_pct": p.humidity_pct,
                "weather_code": p.weather_code,
                "weather_desc_id": p.weather_desc_id,
                "weather_desc_en": p.weather_desc_en,
                "wind_speed_kmh": p.wind_speed_kmh,
                "wind_speed_ms": p.wind_speed_ms,
                "wind_dir_cardinal": p.wind_dir_cardinal,
                "wind_dir_deg": p.wind_dir_deg,
                "cloud_cover_pct": p.cloud_cover_pct,
                "visibility_text": p.visibility_text,
            }
            for p in points
        ]

        location_meta = raw_payload.get("lokasi", {})
        return {
            "api_health": api_health,
            "fetched_at_wib": fetched_at_wib,
            "adm4_code": valid_adm4,
            "location": {
                "provinsi": location_meta.get("provinsi", "Aceh"),
                "kotkab": location_meta.get("kotkab", ""),
                "kecamatan": location_meta.get("kecamatan", ""),
                "desa": location_meta.get("desa", ""),
                "latitude": location_meta.get("lat"),
                "longitude": location_meta.get("lon"),
                "timezone": "Asia/Jakarta",
            },
            "total_slots": len(serialized_slots),
            "forecast_horizon": "3 Hari (Interval 3 Jam)",
            "slots": serialized_slots,
        }

    def get_active_alerts(self) -> Dict[str, Any]:
        api_health = "ONLINE"
        last_updated = self.now_wib_iso()
        alerts_list: List[Dict[str, Any]] = []

        try:
            live_alerts = self.alert_collector.fetch_active_aceh_alerts()
            for a in live_alerts:
                alerts_list.append(
                    {
                        "cap_identifier": a.cap_identifier,
                        "sender": a.sender,
                        "sent_time": a.sent_time.isoformat(),
                        "status": a.status,
                        "msg_type": a.msg_type,
                        "event_type": a.event_type,
                        "urgency": a.urgency,
                        "severity": a.severity,
                        "certainty": a.certainty,
                        "effective_time": a.effective_time.isoformat(),
                        "onset_time": a.onset_time.isoformat() if a.onset_time else None,
                        "expires_time": a.expires_time.isoformat(),
                        "headline": a.headline,
                        "description": a.description,
                        "instruction": a.instruction,
                        "official_web_url": a.official_web_url or "https://www.bmkg.go.id/cuaca/peringatan-dini",
                        "cap_xml_url": a.cap_xml_url,
                        "affected_areas_text": a.affected_areas_text,
                        "polygons_geojson": a.polygons_geojson,
                        "source_attribution": a.source_attribution,
                    }
                )
        except Exception as exc:
            logger.warning("Gangguan koneksi RSS/CAP BMKG (%s). Membaca snapshot lokal.", exc)
            api_health = "DEGRADED_USING_LAST_KNOWN_CACHE"
            cached_geojson = self.geojson_dir / "aceh_active_alerts.geojson"
            if cached_geojson.exists():
                raw_gj = json.loads(cached_geojson.read_text(encoding="utf-8"))
                for feat in raw_gj.get("features", []):
                    props = feat.get("properties", {})
                    alerts_list.append(props)

        return {
            "api_health": api_health,
            "last_updated_wib": last_updated,
            "active_alerts_count": len(alerts_list),
            "has_active_warning": len(alerts_list) > 0,
            "alerts": alerts_list,
        }

    def get_historical_analytics(self) -> Dict[str, Any]:
        report_path = self.processed_dir / "phase2_eda_spatiotemporal_report.json"
        monthly_path = self.processed_dir / "monthly_climatology_aceh.csv"
        etccdi_path = self.processed_dir / "etccdi_extreme_indices_aceh.csv"

        if not report_path.exists():
            raise FileNotFoundError("Laporan analisis Phase 2 belum tersedia. Jalankan scripts/run_phase2_analysis.py.")

        report = json.loads(report_path.read_text(encoding="utf-8"))
        monthly_clim = (
            pd.read_csv(monthly_path).to_dict(orient="records")
            if monthly_path.exists()
            else []
        )
        etccdi_records = (
            pd.read_csv(etccdi_path).to_dict(orient="records")
            if etccdi_path.exists()
            else []
        )

        is_demo = "DEMO" in str(report.get("data_source_label", "")).upper()
        return {
            "is_demo_mode": is_demo,
            "data_source_label": report.get("data_source_label"),
            "data_quality": report.get("data_quality"),
            "descriptive_statistics": report.get("descriptive_statistics"),
            "monthly_climatology": monthly_clim,
            "seasonal_summary": report.get("seasonal_summary"),
            "etccdi_extreme_indices": etccdi_records,
            "correlation_analysis": report.get("correlation_analysis"),
            "spatiotemporal_summary": report.get("spatiotemporal_analysis"),
        }

    def get_gis_layers(self) -> Dict[str, Any]:
        stations_path = self.geojson_dir / "aceh_weather_stations.geojson"
        disasters_path = self.geojson_dir / "aceh_disaster_density.geojson"
        alerts_path = self.geojson_dir / "aceh_active_alerts.geojson"

        stations_gj = (
            json.loads(stations_path.read_text(encoding="utf-8"))
            if stations_path.exists()
            else {"type": "FeatureCollection", "features": []}
        )
        disasters_gj = (
            json.loads(disasters_path.read_text(encoding="utf-8"))
            if disasters_path.exists()
            else {"type": "FeatureCollection", "features": []}
        )
        alerts_gj = (
            json.loads(alerts_path.read_text(encoding="utf-8"))
            if alerts_path.exists()
            else {"type": "FeatureCollection", "features": []}
        )

        return {
            "spatial_limitation_note": SPATIAL_LIMITATION_STATEMENT,
            "map_center": {"latitude": 4.695135, "longitude": 96.749399, "default_zoom": 8},
            "layers": {
                "weather_stations": stations_gj,
                "regency_disaster_density": disasters_gj,
                "active_weather_alerts": alerts_gj,
            },
        }

    def get_ml_predictions_and_evaluation(self) -> Dict[str, Any]:
        eval_path = self.eval_dir / "model_evaluation_report.json"
        preds_path = self.eval_dir / "latest_station_predictions.json"

        if not eval_path.exists() or not preds_path.exists():
            raise FileNotFoundError("Artefak evaluasi ML belum ditemukan. Jalankan scripts/run_phase3_ml.py.")

        eval_report = json.loads(eval_path.read_text(encoding="utf-8"))
        predictions = json.loads(preds_path.read_text(encoding="utf-8"))

        return {
            "mandatory_disclaimer": MANDATORY_ML_DISCLAIMER,
            "trained_at_wib": eval_report.get("trained_at_wib"),
            "model_version": eval_report.get("model_version"),
            "dataset_version": eval_report.get("dataset_version"),
            "split_summary": eval_report.get("split_summary"),
            "best_models": eval_report.get("best_models"),
            "walk_forward_cv_summary": eval_report.get("walk_forward_cv_summary"),
            "regression_comparison": eval_report.get("regression_comparison"),
            "classification_comparison": eval_report.get("classification_comparison"),
            "feature_importance_top15": eval_report.get("feature_importance_top15"),
            "model_limitations": eval_report.get("model_limitations"),
            "station_predictions": predictions,
        }

    @staticmethod
    def get_preparedness_education() -> Dict[str, Any]:
        """Menyajikan panduan kesiapsiagaan bencana hidrometeorologi dan nomor darurat terverifikasi di Aceh."""
        return {
            "guides": [
                {
                    "hazard_type": "BANJIR_DAN_BANJIR_BANDANG",
                    "title": "Kesiapsiagaan Menghadapi Banjir & Banjir Bandang",
                    "before_event": [
                        "Pantau prakiraan cuaca dan peringatan dini resmi BMKG untuk wilayah DAS (Krueng Aceh, Krueng Peusangan, Krueng Pase, Krueng Jambo Aye, Krueng Woyla, Krueng Tripa).",
                        "Kenali jalur evakuasi menuju tempat lebih tinggi (meunasah/masjid bertingkat atau titik kumpul gampong).",
                        "Simpan dokumen penting (KK, KTP, ijazah, surat tanah) di dalam kantong plastik kedap air di dalam Tas Siaga Bencana.",
                        "Bersihkan saluran drainase sekitar rumah dari sumbatan sampah atau ranting.",
                    ],
                    "during_event": [
                        "Segera matikan aliran listrik (MCB utama) dan cabut regulator tabung gas LPG apabila air mulai memasuki rumah.",
                        "Evakuasi warga rentan (lansia, ibu hamil, balita, disabilitas) lebih dahulu sebelum genangan bertambah tinggi.",
                        "Jangan menerobos arus banjir bandang dengan berjalan kaki maupun berkendara karena arus dangkal tetap berisiko menyeret.",
                    ],
                    "after_event": [
                        "Periksa keamanan struktur bangunan, instalasi listrik, dan sumber air bersih sebelum kembali ke rumah.",
                        "Gunakan alas kaki dan sarung tangan saat membersihkan lumpur untuk mencegah infeksi leptospirosis.",
                    ],
                },
                {
                    "hazard_type": "TANAH_LONGSOR",
                    "title": "Kesiapsiagaan Menghadapi Tanah Longsor (Wilayah Perbukitan & Jalan Lintas Tengah/Barat Aceh)",
                    "before_event": [
                        "Waspadai retakan tanah baru berbentuk tapal kuda di lereng, pohon/tiang listrik yang mulai miring, atau rembesan air keruh mendadak dari tebing.",
                        "Hindari membangun hunian tepat di bawah tebing curam atau di mulut alur lembah curam.",
                    ],
                    "during_event": [
                        "Jika terdengar suara gemuruh dari atas lereng saat hujan lebat, segera menjauh tegak lurus dari jalur lintasan longsoran.",
                        "Tunda perjalanan melewati jalur rawan longsor (seperti Geurutee, Tangse, Gunung Salak, Takengon-Blangkejeren) saat peringatan dini hujan lebat aktif.",
                    ],
                    "after_event": [
                        "Jauhi area longsoran karena potensi longsor susulan masih tinggi saat tanah jenuh air.",
                        "Laporkan kejadian penutupan jalan atau korban kepada BPBD setempat atau perangkat gampong.",
                    ],
                },
                {
                    "hazard_type": "ANGIN_KENCANG_DAN_PETIR",
                    "title": "Kesiapsiagaan Menghadapi Angin Kencang & Hujan Petir",
                    "before_event": [
                        "Pangkas dahan pohon besar yang rapuh di dekat atap rumah.",
                        "Periksa kekuatan rangka atap seng dan kencangkan paku/baut penahan.",
                    ],
                    "during_event": [
                        "Berlindung di dalam bangunan permanen yang kokoh; jauhi jendela kaca, pohon besar, papan reklame, dan tiang listrik.",
                        "Bagi nelayan pesisir Aceh, tunda melaut apabila BMKG mengeluarkan peringatan dini angin kencang dan gelombang tinggi.",
                    ],
                    "after_event": [
                        "Waspadai kabel listrik yang terputus di jalanan dan segera lapor ke layanan PLN.",
                    ],
                },
            ],
            "emergency_bag_checklist": [
                {"item": "Dokumen Penting Kedap Air", "detail": "KTP, Kartu Keluarga, buku nikah, akta kelahiran, buku tabungan, dan salinan digital di ponsel."},
                {"item": "Air Minum & Makanan Tahan Lama", "detail": "Minimal persediaan untuk 3 hari (72 jam pertama): air mineral, biskuit padat kalori, makanan kaleng, makanan bayi."},
                {"item": "Kotak P3K & Obat Pribadi", "detail": "Antiseptik, kasa steril, plester, oralit, obat demam, serta obat rutin penyakit kronis."},
                {"item": "Penerangan & Komunikasi Darurat", "detail": "Senter LED, baterai cadangan, powerbank terisi penuh, dan peluit darurat untuk memberi sinyal posisi."},
                {"item": "Pakaian & Perlengkapan Sanitasi", "detail": "Pakaian ganti, jas hujan/ponco, selimut darurat, masker, sabun, dan pembalut."},
                {"item": "Uang Tunai Secukupnya", "detail": "Pecahan kecil untuk kebutuhan darurat apabila jaringan ATM/listrik padam."},
            ],
            "verified_emergency_contacts": [
                {
                    "agency": "Badan Penanggulangan Bencana Aceh (BPBA) - Pusdalops PB Provinsi Aceh",
                    "address": "Jl. Teuku Daud Beureueh No. 18, Kuta Alam, Kota Banda Aceh",
                    "phone": "(0651) 34783",
                    "website": "https://bpba.acehprov.go.id",
                    "verification_status": "Terverifikasi Resmi Pemerintah Aceh",
                },
                {
                    "agency": "Kantor Pencarian dan Pertolongan (BASARNAS) Kelas A Banda Aceh",
                    "address": "Jl. Sultan Malikul Saleh, Lhong Raya, Kota Banda Aceh",
                    "phone": "115 / (0651) 33876",
                    "website": "https://bandaaceh.basarnas.go.id",
                    "verification_status": "Terverifikasi Resmi Basarnas RI",
                },
                {
                    "agency": "Stasiun Meteorologi Kelas I Sultan Iskandar Muda (BMKG Aceh)",
                    "address": "Bandara Sultan Iskandar Muda, Blang Bintang, Aceh Besar",
                    "phone": "(0651) 26947 / Info BMKG 196",
                    "website": "https://www.bmkg.go.id",
                    "verification_status": "Terverifikasi Resmi BMKG",
                },
                {
                    "agency": "Layanan Panggilan Darurat Terpadu Nasional",
                    "address": "Seluruh Kabupaten/Kota",
                    "phone": "112",
                    "website": "https://layanan112.kominfo.go.id",
                    "verification_status": "Nomor Darurat Nasional Bebas Pulsa",
                },
                {
                    "agency": "Pemadam Kebakaran & Penyelamatan (DPKP) Kota Banda Aceh",
                    "address": "Jl. Soekarno-Hatta, Mibo, Banda Raya, Kota Banda Aceh",
                    "phone": "113 / (0651) 113 / (0651) 44123",
                    "website": "https://damkar.bandaacehkota.go.id",
                    "verification_status": "Terverifikasi Resmi Pemko Banda Aceh",
                },
            ],
        }
