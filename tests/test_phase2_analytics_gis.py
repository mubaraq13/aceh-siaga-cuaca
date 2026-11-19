"""
Unit Tests for PHASE 2 — DATA ANALYSIS & SPATIO-TEMPORAL GIS (ACEH SIAGA CUACA)
File: tests/test_phase2_analytics_gis.py
Jalankan dengan: python -m pytest tests\test_phase2_analytics_gis.py -v
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analytics.eda_statistics import (
    classify_aceh_season,
    compute_correlation_analysis,
    compute_data_quality_report,
    compute_descriptive_statistics,
    compute_etccdi_extreme_indices,
    compute_temporal_patterns,
)
from src.analytics.eda_visualizations import generate_all_eda_figures
from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter
from src.data_collection.disaster_import import DisasterDataImporter
from src.geospatial.aceh_gis_analyzer import AcehGISAnalyzer


def _build_sample_cleaned_observations() -> pd.DataFrame:
    raw = pd.DataFrame(
        [
            {"wmo_id": "96001", "Tanggal": "01-10-2025", "Tn": 23.0, "Tx": 31.0, "Tavg": 26.8, "RH_avg": 86.0, "RR": 0.0, "ss": 7.5, "ff_x": 6.0, "ddd_x": 200, "ff_avg": 2.5, "ddd_car": "SW"},
            {"wmo_id": "96001", "Tanggal": "02-10-2025", "Tn": 23.2, "Tx": 30.5, "Tavg": 26.5, "RH_avg": 89.0, "RR": 8888, "ss": 5.0, "ff_x": 7.0, "ddd_x": 210, "ff_avg": 3.0, "ddd_car": "SW"},
            {"wmo_id": "96001", "Tanggal": "03-10-2025", "Tn": 22.8, "Tx": 29.0, "Tavg": 25.4, "RH_avg": 93.0, "RR": 25.0, "ss": 3.2, "ff_x": 9.5, "ddd_x": 220, "ff_avg": 4.1, "ddd_car": "W"},
            {"wmo_id": "96001", "Tanggal": "04-10-2025", "Tn": 22.5, "Tx": 28.2, "Tavg": 24.9, "RH_avg": 96.0, "RR": 68.5, "ss": 1.1, "ff_x": 13.0, "ddd_x": 230, "ff_avg": 5.8, "ddd_car": "W"},
            {"wmo_id": "96001", "Tanggal": "05-10-2025", "Tn": 22.6, "Tx": 28.5, "Tavg": 25.1, "RH_avg": 95.0, "RR": 112.0, "ss": 0.5, "ff_x": 14.0, "ddd_x": 225, "ff_avg": 6.2, "ddd_car": "W"},
            {"wmo_id": "96011", "Tanggal": "01-10-2025", "Tn": 23.1, "Tx": 30.8, "Tavg": 26.7, "RH_avg": 87.0, "RR": 5.0, "ss": 6.2, "ff_x": 6.5, "ddd_x": 190, "ff_avg": 2.8, "ddd_car": "S"},
            {"wmo_id": "96011", "Tanggal": "02-10-2025", "Tn": 22.9, "Tx": 29.5, "Tavg": 25.8, "RH_avg": 91.0, "RR": 42.0, "ss": 3.0, "ff_x": 8.5, "ddd_x": 195, "ff_avg": 3.5, "ddd_car": "S"},
            {"wmo_id": "96011", "Tanggal": "03-10-2025", "Tn": 22.4, "Tx": 28.0, "Tavg": 24.8, "RH_avg": 97.0, "RR": 85.0, "ss": 0.8, "ff_x": 12.5, "ddd_x": 205, "ff_avg": 5.2, "ddd_car": "SW"},
            {"wmo_id": "96011", "Tanggal": "04-10-2025", "Tn": 23.0, "Tx": 31.2, "Tavg": 27.0, "RH_avg": 84.0, "RR": 0.0, "ss": 8.0, "ff_x": 5.5, "ddd_x": 180, "ff_avg": 2.1, "ddd_car": "S"},
            {"wmo_id": "96011", "Tanggal": "05-10-2025", "Tn": 23.4, "Tx": 31.5, "Tavg": 27.3, "RH_avg": 82.0, "RR": 0.0, "ss": 8.4, "ff_x": 5.0, "ddd_x": 175, "ff_avg": 2.0, "ddd_car": "S"},
        ]
    )
    from src.data_processing.data_cleaning import clean_bmkg_observation_dataframe
    return clean_bmkg_observation_dataframe(raw)


def test_data_quality_and_descriptive_statistics() -> None:
    df = _build_sample_cleaned_observations()
    q_report = compute_data_quality_report(df)
    assert q_report["total_records"] == 10
    assert q_report["stations_count"] == 2
    assert q_report["trace_rainfall_8888_count"] == 1

    desc = compute_descriptive_statistics(df)
    assert "rainfall_mm" in desc["variable"].values
    rain_row = desc.loc[desc["variable"] == "rainfall_mm"].iloc[0]
    assert rain_row["max"] == 112.0
    assert rain_row["min"] == 0.0
    assert rain_row["iqr"] >= 0.0


def test_etccdi_extreme_indices_calculation() -> None:
    df = _build_sample_cleaned_observations()
    etccdi = compute_etccdi_extreme_indices(df)
    assert len(etccdi) == 2

    st_96001 = etccdi.loc[etccdi["wmo_id"] == "96001"].iloc[0]
    # Pada stasiun 96001: RR = [0.0, 0.0 (trace), 25.0, 68.5, 112.0]
    assert st_96001["R20mm_days"] == 3
    assert st_96001["R50mm_extreme_days"] == 2
    assert st_96001["R100mm_very_heavy_days"] == 1
    assert st_96001["Rx1day_max_mm"] == 112.0
    assert st_96001["CDD_max_dry_spell_days"] == 2
    assert st_96001["CWD_max_wet_spell_days"] == 3


def test_temporal_patterns_and_aceh_season_classification() -> None:
    assert classify_aceh_season(11) == "SON_PUNCAK_HUJAN_UTAMA"
    assert classify_aceh_season(1) == "DJF_MONSUN_BARAT"
    assert classify_aceh_season(4) == "MAM_TRANSISI_EKUATORIAL"
    assert classify_aceh_season(7) == "JJA_KEMARAU_RELATIF"

    df = _build_sample_cleaned_observations()
    temporal = compute_temporal_patterns(df)
    assert "monthly_climatology" in temporal
    assert "seasonal_summary" in temporal
    assert not temporal["monthly_climatology"].empty


def test_correlation_analysis_includes_non_causality_note() -> None:
    df = _build_sample_cleaned_observations()
    corr = compute_correlation_analysis(df)
    assert "TIDAK membuktikan hubungan kausalitas" in corr["methodology_note"]
    assert len(corr["rainfall_associations"]) > 0


def test_gis_geojson_layers_and_spatial_limitation_note(tmp_path: Path) -> None:
    df_obs = _build_sample_cleaned_observations()
    stations_geojson = AcehGISAnalyzer.build_stations_geojson(df_obs)
    assert stations_geojson["type"] == "FeatureCollection"
    assert len(stations_geojson["features"]) == 5
    assert "TIDAK melakukan interpolasi permukaan kontinu" in stations_geojson["metadata"]["spatial_limitation_note"]

    dis_csv = AcehGISAnalyzer.generate_demo_disaster_dataset(tmp_path / "demo_disasters.csv")
    df_dis = DisasterDataImporter.import_file(dis_csv)
    dis_geojson = AcehGISAnalyzer.build_disaster_density_geojson(df_dis)
    assert dis_geojson["type"] == "FeatureCollection"
    assert len(dis_geojson["features"]) == 23

    link_report = AcehGISAnalyzer.analyze_spatiotemporal_weather_disaster_link(df_obs, df_dis)
    assert "spatial_limitation_statement" in link_report
    assert len(link_report["disasters_by_topography_zone"]) > 0


def test_eda_visualizations_generates_all_7_charts(tmp_path: Path) -> None:
    df_obs = _build_sample_cleaned_observations()
    figs = generate_all_eda_figures(df_obs, output_dir=tmp_path / "figures")
    assert len(figs) == 7
    for name, fpath in figs.items():
        assert fpath.exists(), f"Grafik {name} gagal dibuat di {fpath}"
        assert fpath.stat().st_size > 1000
