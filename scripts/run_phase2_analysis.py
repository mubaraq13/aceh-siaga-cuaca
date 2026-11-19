#!/usr/bin/env python3
"""
Phase 2 End-to-End Execution Runner — ACEH SIAGA CUACA
Menjalankan seluruh rangkaian EDA, Perhitungan Indeks Ekstrem ETCCDI, Korelasi,
7 Grafik Publikasi Ilmiah, serta Pembuatan Layer GeoJSON Spasial-Temporal Aceh.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analytics.eda_statistics import (
    compute_correlation_analysis,
    compute_data_quality_report,
    compute_descriptive_statistics,
    compute_etccdi_extreme_indices,
    compute_temporal_patterns,
)
from src.analytics.eda_visualizations import generate_all_eda_figures
from src.data_collection.bmkg_alerts import BMKGAlertCollector
from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter
from src.data_collection.disaster_import import DisasterDataImporter
from src.geospatial.aceh_gis_analyzer import AcehGISAnalyzer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_phase2")


def main() -> None:
    processed_dir = Path("data/processed")
    geojson_dir = processed_dir / "geojson"
    figures_dir = processed_dir / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)
    geojson_dir.mkdir(parents=True, exist_ok=True)

    # 1. Cek apakah ada file observasi asli BMKG di data/raw/bmkg/, jika belum gunakan demo dataset berlabel jelas
    raw_bmkg_files = list(Path("data/raw/bmkg").glob("*.csv")) + list(Path("data/raw/bmkg").glob("*.xlsx"))
    if raw_bmkg_files:
        obs_path = raw_bmkg_files[0]
        source_label = f"Observasi Stasiun BMKG Aceh ({obs_path.name})"
    else:
        obs_path = Path("data/demo/demo_bmkg_historical_aceh.csv")
        if not obs_path.exists():
            BMKGHistoricalImporter.generate_demo_dataset(obs_path)
        source_label = "Dataset Observasi Stasiun Aceh (Mode DEMO Tervalidasi)"

    logger.info("1. Memuat & membersihkan data observasi dari: %s", obs_path)
    df_obs = BMKGHistoricalImporter.load_file(obs_path)
    df_obs.to_csv(processed_dir / "cleaned_weather_observations_aceh.csv", index=False)

    # 2. Audit Kualitas Data & Statistik Deskriptif
    logger.info("2. Menghitung laporan kualitas data, statistik deskriptif, dan indeks ekstrem ETCCDI...")
    quality_report = compute_data_quality_report(df_obs)
    desc_df = compute_descriptive_statistics(df_obs)
    etccdi_df = compute_etccdi_extreme_indices(df_obs)
    temporal_dict = compute_temporal_patterns(df_obs)
    corr_report = compute_correlation_analysis(df_obs)

    desc_df.to_csv(processed_dir / "descriptive_statistics_aceh.csv", index=False)
    etccdi_df.to_csv(processed_dir / "etccdi_extreme_indices_aceh.csv", index=False)
    temporal_dict["monthly_climatology"].to_csv(processed_dir / "monthly_climatology_aceh.csv", index=False)
    temporal_dict["seasonal_summary"].to_csv(processed_dir / "seasonal_summary_aceh.csv", index=False)

    # 3. Buat 7 Visualisasi Utama
    logger.info("3. Menghasilkan 7 visualisasi analisis cuaca di %s...", figures_dir)
    saved_figs = generate_all_eda_figures(df_obs, output_dir=figures_dir, source_label=source_label)
    for k, p in saved_figs.items():
        logger.info("   [GRAFIK OK] %s -> %s", k, p)

    # 4. Analisis Spasial-Temporal & Pembuatan Layer GeoJSON
    logger.info("4. Memproses data kejadian bencana dan membangun layer GeoJSON Aceh...")
    raw_dis_files = list(Path("data/raw/bpba").glob("*.csv")) + list(Path("data/raw/bnpb").glob("*.csv"))
    if raw_dis_files:
        dis_path = raw_dis_files[0]
    else:
        dis_path = AcehGISAnalyzer.generate_demo_disaster_dataset()

    df_dis = DisasterDataImporter.import_file(dis_path)
    df_dis.to_csv(processed_dir / "cleaned_disaster_events_aceh.csv", index=False)

    stations_geojson = AcehGISAnalyzer.build_stations_geojson(df_obs)
    disaster_geojson = AcehGISAnalyzer.build_disaster_density_geojson(df_dis)

    try:
        active_alerts = BMKGAlertCollector().fetch_active_aceh_alerts()
    except Exception as exc:
        logger.warning("Tidak dapat mengambil alert live saat ini (%s), menyimpan GeoJSON kosong.", exc)
        active_alerts = []
    alerts_geojson = AcehGISAnalyzer.build_active_alerts_geojson(active_alerts)

    (geojson_dir / "aceh_weather_stations.geojson").write_text(
        json.dumps(stations_geojson, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (geojson_dir / "aceh_disaster_density.geojson").write_text(
        json.dumps(disaster_geojson, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (geojson_dir / "aceh_active_alerts.geojson").write_text(
        json.dumps(alerts_geojson, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    spatio_report = AcehGISAnalyzer.analyze_spatiotemporal_weather_disaster_link(df_obs, df_dis)

    full_summary = {
        "data_source_label": source_label,
        "data_quality": quality_report,
        "descriptive_statistics": desc_df.to_dict(orient="records"),
        "seasonal_summary": temporal_dict["seasonal_summary"].to_dict(orient="records"),
        "correlation_analysis": corr_report,
        "spatiotemporal_analysis": spatio_report,
        "generated_figures": {k: str(v) for k, v in saved_figs.items()},
    }
    summary_path = processed_dir / "phase2_eda_spatiotemporal_report.json"
    summary_path.write_text(json.dumps(full_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("=== RINGKASAN TEMUAN PHASE 2 ===")
    logger.info("Total Observasi Bersih: %d baris (%s s.d. %s)", quality_report["total_records"], quality_report["period_start"], quality_report["period_end"])
    logger.info("Total Kejadian Bencana Teranalisis: %d kejadian di 23 Kabupaten/Kota Aceh", len(df_dis))
    logger.info("Korelasi Spearman Bulanan (Hujan Ekstrem >=50mm vs Kejadian Bencana): %.4f", spatio_report["monthly_extreme_rain_vs_disaster_spearman_rho"])
    logger.info("Laporan JSON lengkap tersimpan di: %s", summary_path)


if __name__ == "__main__":
    main()
