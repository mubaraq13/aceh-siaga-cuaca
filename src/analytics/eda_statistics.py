"""
Exploratory Data Analysis & Hydrometeorological Statistics Engine — ACEH SIAGA CUACA
File: src/analytics/eda_statistics.py

Mencakup:
A. Data Quality Audit (Missing values, duplicates, physical anomalies, trace counts).
B. Descriptive Statistics (Mean, Median, Std, Variance, Min, Max, Quantiles P25-P99).
C. ETCCDI Extreme Indices (R20mm, R50mm, Rx1day, Rx5day, CDD, CWD).
D. Temporal Analysis (Monthly, Seasonal Aceh Monsoon, Annual trends).
E. Correlation Analysis (Spearman & Pearson with explicit non-causality disclaimer).
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

try:
    from scipy import stats as scipy_stats
except ImportError:
    scipy_stats = None

METEOROLOGICAL_VARIABLES = [
    "rainfall_mm",
    "temp_min_c",
    "temp_max_c",
    "temp_avg_c",
    "humidity_avg_pct",
    "sunshine_hours",
    "wind_speed_avg_ms",
    "wind_speed_max_ms",
]


def compute_data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Memeriksa kualitas data: kelengkapan, kode 8888 (trace), duplikasi, dan flag kualitas."""
    if df.empty:
        raise ValueError("DataFrame observasi kosong.")

    total_rows = int(len(df))
    duplicate_pairs = int(df.duplicated(subset=["wmo_id", "observation_date"]).sum())
    dates = pd.to_datetime(df["observation_date"], errors="coerce")

    missing_by_col: Dict[str, Dict[str, float]] = {}
    for col in METEOROLOGICAL_VARIABLES:
        if col in df.columns:
            miss_cnt = int(df[col].isna().sum())
            missing_by_col[col] = {
                "missing_count": miss_cnt,
                "missing_pct": round((miss_cnt / total_rows) * 100.0, 2),
                "valid_count": total_rows - miss_cnt,
            }

    trace_count = int(df["is_trace_rainfall"].sum()) if "is_trace_rainfall" in df.columns else 0
    anomaly_count = (
        int((df["quality_flag"] != "VALID").sum()) if "quality_flag" in df.columns else 0
    )

    station_coverage: List[Dict[str, Any]] = []
    for wmo_id, grp in df.groupby("wmo_id"):
        g_dates = pd.to_datetime(grp["observation_date"])
        station_coverage.append(
            {
                "wmo_id": str(wmo_id),
                "total_days": int(len(grp)),
                "start_date": str(g_dates.min().date()),
                "end_date": str(g_dates.max().date()),
                "valid_rainfall_days": int(grp["rainfall_mm"].notna().sum()),
                "trace_rainfall_days": int(grp["is_trace_rainfall"].sum())
                if "is_trace_rainfall" in grp.columns
                else 0,
                "missing_rainfall_days": int(grp["rainfall_mm"].isna().sum()),
            }
        )

    return {
        "total_records": total_rows,
        "stations_count": int(df["wmo_id"].nunique()),
        "period_start": str(dates.min().date()),
        "period_end": str(dates.max().date()),
        "duplicate_station_date_count": duplicate_pairs,
        "trace_rainfall_8888_count": trace_count,
        "physical_anomaly_flagged_count": anomaly_count,
        "missing_values_summary": missing_by_col,
        "station_coverage": station_coverage,
    }


def compute_descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung statistik deskriptif lengkap:
    Mean, Median, Std, Variance, Min, Max, Quantiles (P25, P75, IQR, P90, P95, P99), Skewness.
    """
    rows: List[Dict[str, Any]] = []
    for col in METEOROLOGICAL_VARIABLES:
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue

        q25 = float(series.quantile(0.25))
        q50 = float(series.quantile(0.50))
        q75 = float(series.quantile(0.75))
        q90 = float(series.quantile(0.90))
        q95 = float(series.quantile(0.95))
        q99 = float(series.quantile(0.99))

        rows.append(
            {
                "variable": col,
                "count": int(series.count()),
                "mean": round(float(series.mean()), 3),
                "std": round(float(series.std(ddof=1)), 3),
                "variance": round(float(series.var(ddof=1)), 3),
                "min": round(float(series.min()), 3),
                "q25": round(q25, 3),
                "median": round(q50, 3),
                "q75": round(q75, 3),
                "iqr": round(q75 - q25, 3),
                "q90": round(q90, 3),
                "q95": round(q95, 3),
                "q99": round(q99, 3),
                "max": round(float(series.max()), 3),
                "skewness": round(float(series.skew()), 3),
            }
        )
    return pd.DataFrame(rows)


def _max_consecutive_run(boolean_series: pd.Series) -> int:
    """Menghitung panjang maksimum deret True berturut-turut (untuk CDD dan CWD)."""
    if boolean_series.empty:
        return 0
    arr = boolean_series.to_numpy(dtype=bool)
    max_run = 0
    current_run = 0
    for val in arr:
        if val:
            current_run += 1
            if current_run > max_run:
                max_run = current_run
        else:
            current_run = 0
    return int(max_run)


def compute_etccdi_extreme_indices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung indeks iklim ekstrem standar WMO/ETCCDI per stasiun dan per tahun:
    - R20mm: Jumlah hari hujan sedang-ekstrem (>= 20 mm)
    - R50mm: Jumlah hari hujan lebat-ekstrem (>= 50 mm, ambang batas peringatan BMKG)
    - R100mm: Jumlah hari hujan sangat lebat-ekstrem (>= 100 mm)
    - Rx1day: Curah hujan harian maksimum (mm)
    - Rx5day: Akumulasi curah hujan 5 hari berturut-turut maksimum (mm)
    - CDD: Consecutive Dry Days maksimum (RR < 1.0 mm)
    - CWD: Consecutive Wet Days maksimum (RR >= 1.0 mm)
    - SDII: Simple Daily Intensity Index (rata-rata hujan pada hari basah >= 1.0 mm)
    """
    work = df.copy()
    work["obs_dt"] = pd.to_datetime(work["observation_date"])
    work["year"] = work["obs_dt"].dt.year
    work = work.sort_values(["wmo_id", "obs_dt"])

    results: List[Dict[str, Any]] = []
    for (wmo_id, year), grp in work.groupby(["wmo_id", "year"]):
        rr = pd.to_numeric(grp["rainfall_mm"], errors="coerce")
        valid_rr = rr.dropna()
        if valid_rr.empty:
            continue

        wet_days = valid_rr[valid_rr >= 1.0]
        rx5_series = rr.rolling(window=5, min_periods=3).sum()

        results.append(
            {
                "wmo_id": str(wmo_id),
                "year": int(year),
                "valid_days": int(len(valid_rr)),
                "annual_rainfall_mm": round(float(valid_rr.sum()), 2),
                "wet_days_ge_1mm": int(len(wet_days)),
                "R20mm_days": int((valid_rr >= 20.0).sum()),
                "R50mm_extreme_days": int((valid_rr >= 50.0).sum()),
                "R100mm_very_heavy_days": int((valid_rr >= 100.0).sum()),
                "Rx1day_max_mm": round(float(valid_rr.max()), 2),
                "Rx5day_max_mm": round(float(rx5_series.max()), 2) if not rx5_series.dropna().empty else 0.0,
                "SDII_mm_per_wet_day": round(float(wet_days.mean()), 2) if not wet_days.empty else 0.0,
                "CDD_max_dry_spell_days": _max_consecutive_run(valid_rr < 1.0),
                "CWD_max_wet_spell_days": _max_consecutive_run(valid_rr >= 1.0),
            }
        )
    return pd.DataFrame(results)


def classify_aceh_season(month: int) -> str:
    """
    Mengklasifikasikan musim klimatologis Provinsi Aceh:
    - Sept-Nov (9, 10, 11) & Des-Feb (12, 1, 2): Puncak Hujan Utama / Monsun Barat-Utara (SON-DJF)
    - Mar-Mei (3, 4, 5): Transisi / Puncak Hujan Kedua Ekuatorial (MAM)
    - Jun-Agu (6, 7, 8): Musim Kemarau Relatif / Monsun Barat Daya-Timur (JJA)
    """
    if month in (9, 10, 11):
        return "SON_PUNCAK_HUJAN_UTAMA"
    if month in (12, 1, 2):
        return "DJF_MONSUN_BARAT"
    if month in (3, 4, 5):
        return "MAM_TRANSISI_EKUATORIAL"
    return "JJA_KEMARAU_RELATIF"


def compute_temporal_patterns(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Menganalisis pola temporal curah hujan dan suhu di Provinsi Aceh:
    - Agregasi bulanan lintas stasiun (monthly_climatology).
    - Agregasi musiman Aceh (seasonal_summary).
    - Matriks Tahun x Bulan untuk heatmap intensitas hujan (year_month_matrix).
    """
    work = df.copy()
    work["obs_dt"] = pd.to_datetime(work["observation_date"])
    work["year"] = work["obs_dt"].dt.year
    work["month"] = work["obs_dt"].dt.month
    work["aceh_season"] = work["month"].apply(classify_aceh_season)
    work["is_extreme_50mm"] = (pd.to_numeric(work["rainfall_mm"], errors="coerce") >= 50.0).astype(int)

    # 1. Rata-rata akumulasi bulanan per stasiun terlebih dahulu, lalu rata-rata per bulan
    station_year_month = (
        work.groupby(["wmo_id", "year", "month"], as_index=False)
        .agg(
            monthly_rainfall_mm=("rainfall_mm", "sum"),
            max_daily_rainfall_mm=("rainfall_mm", "max"),
            extreme_days_count=("is_extreme_50mm", "sum"),
            mean_temp_c=("temp_avg_c", "mean"),
            mean_humidity_pct=("humidity_avg_pct", "mean"),
        )
    )

    monthly_climatology = (
        station_year_month.groupby("month", as_index=False)
        .agg(
            avg_monthly_rainfall_mm=("monthly_rainfall_mm", "mean"),
            median_monthly_rainfall_mm=("monthly_rainfall_mm", "median"),
            max_daily_rainfall_mm=("max_daily_rainfall_mm", "max"),
            total_extreme_days=("extreme_days_count", "sum"),
            avg_temp_c=("mean_temp_c", "mean"),
            avg_humidity_pct=("mean_humidity_pct", "mean"),
        )
        .round(2)
    )

    seasonal_summary = (
        work.groupby("aceh_season", as_index=False)
        .agg(
            obs_days=("rainfall_mm", "count"),
            mean_daily_rainfall_mm=("rainfall_mm", "mean"),
            max_daily_rainfall_mm=("rainfall_mm", "max"),
            extreme_50mm_events=("is_extreme_50mm", "sum"),
            mean_temp_c=("temp_avg_c", "mean"),
            mean_humidity_pct=("humidity_avg_pct", "mean"),
        )
        .round(2)
    )

    year_month_matrix = (
        station_year_month.groupby(["year", "month"], as_index=False)
        .agg(
            mean_station_monthly_rain_mm=("monthly_rainfall_mm", "mean"),
            extreme_events_total=("extreme_days_count", "sum"),
        )
        .round(2)
    )

    return {
        "station_year_month": station_year_month,
        "monthly_climatology": monthly_climatology,
        "seasonal_summary": seasonal_summary,
        "year_month_matrix": year_month_matrix,
    }


def compute_correlation_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Menghitung matriks korelasi Spearman (non-parametrik, tahan terhadap skewness curah hujan)
    dan Pearson (linier) antarvariabel meteorologi.
    Menyertakan catatan metodologis bahwa korelasi tidak sama dengan kausalitas.
    """
    cols = [c for c in METEOROLOGICAL_VARIABLES if c in df.columns]
    clean_sub = df[cols].apply(pd.to_numeric, errors="coerce")

    spearman_corr = clean_sub.corr(method="spearman").round(4)
    pearson_corr = clean_sub.corr(method="pearson").round(4)

    pairwise_with_rainfall: List[Dict[str, Any]] = []
    if "rainfall_mm" in cols:
        for other_col in cols:
            if other_col == "rainfall_mm":
                continue
            pair_df = clean_sub[["rainfall_mm", other_col]].dropna()
            n_samples = int(len(pair_df))
            if n_samples < 10:
                continue

            r_spearman = float(spearman_corr.loc["rainfall_mm", other_col])
            r_pearson = float(pearson_corr.loc["rainfall_mm", other_col])
            p_val_spearman = None
            if scipy_stats is not None:
                res = scipy_stats.spearmanr(pair_df["rainfall_mm"], pair_df[other_col])
                p_val_spearman = float(res.pvalue)

            pairwise_with_rainfall.append(
                {
                    "variable": other_col,
                    "sample_size": n_samples,
                    "spearman_rho": round(r_spearman, 4),
                    "pearson_r": round(r_pearson, 4),
                    "spearman_p_value": round(p_val_spearman, 6) if p_val_spearman is not None else None,
                    "direction": "POSITIF" if r_spearman > 0 else "NEGATIF",
                }
            )

    return {
        "methodology_note": (
            "Korelasi mengukur derajat asosiasi statistik antarvariabel meteorologi "
            "(Spearman rho digunakan sebagai rujukan utama karena distribusi curah hujan "
            "menceng kanan/zero-inflated). Korelasi TIDAK membuktikan hubungan kausalitas langsung."
        ),
        "spearman_matrix": spearman_corr.to_dict(),
        "pearson_matrix": pearson_corr.to_dict(),
        "rainfall_associations": pairwise_with_rainfall,
    }
