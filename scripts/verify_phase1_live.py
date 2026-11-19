#!/usr/bin/env python3
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
