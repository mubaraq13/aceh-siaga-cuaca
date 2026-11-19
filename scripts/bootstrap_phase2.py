#!/usr/bin/env python3
"""
Phase 2 Automated File Builder — ACEH SIAGA CUACA
Membangun seluruh modul EDA, Visualisasi, Spatio-Temporal GIS, Jupyter Notebooks (01-04),
dan Unit Tests untuk Phase 2.
Jalankan dengan: python scripts\bootstrap_phase2.py
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FILES: dict[str, str] = {}

# ==============================================================================
# 1. src/analytics/eda_statistics.py
# ==============================================================================
FILES["src/analytics/eda_statistics.py"] = '''"""
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
'''

# ==============================================================================
# 2. src/analytics/eda_visualizations.py
# ==============================================================================
FILES["src/analytics/eda_visualizations.py"] = '''"""
Publication-Grade Meteorological Visualization Generator — ACEH SIAGA CUACA
File: src/analytics/eda_visualizations.py

Menghasilkan 7 grafik utama sesuai spesifikasi Bagian 8.E Master Prompt:
1. Grafik tren curah hujan (01_rainfall_trend.png)
2. Grafik curah hujan bulanan (02_monthly_rainfall.png)
3. Heatmap intensitas hujan (03_rainfall_heatmap.png)
4. Distribusi curah hujan (04_rainfall_distribution.png)
5. Grafik suhu dan kelembapan (05_temp_humidity_dynamics.png)
6. Perbandingan antarwilayah/stasiun (06_regional_station_comparison.png)
7. Kalender kejadian hujan ekstrem >=50mm (07_extreme_rain_calendar.png)

Setiap grafik wajib memuat: Judul, Satuan, Label Sumbu, Sumber Data, dan Periode Analisis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

STATION_NAMES: Dict[str, str] = {
    "96001": "Stamet Sultan Iskandar Muda (Aceh Besar/Banda Aceh)",
    "96002": "Stamet Maimun Saleh (Kota Sabang)",
    "96003": "Staklim Aceh (Indrapuri, Aceh Besar)",
    "96009": "Stamet Malikussaleh (Aceh Utara/Lhokseumawe)",
    "96011": "Stamet Cut Nyak Dhien (Nagan Raya/Pesisir Barat)",
}

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _add_footer_attribution(fig: plt.Figure, source_label: str, period_str: str) -> None:
    fig.text(
        0.01,
        0.01,
        f"Sumber Data: {source_label} | Periode Analisis: {period_str} | Platform: ACEH SIAGA CUACA",
        fontsize=8.5,
        color="#475569",
        style="italic",
    )


def generate_all_eda_figures(
    df: pd.DataFrame,
    output_dir: Path = Path("data/processed/figures"),
    source_label: str = "BMKG Provinsi Aceh (Pipeline Observasi Tervalidasi)",
) -> Dict[str, Path]:
    """Menghasilkan 7 visualisasi analisis cuaca Aceh dan menyimpannya ke output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    work = df.copy()
    work["obs_dt"] = pd.to_datetime(work["observation_date"])
    work["year"] = work["obs_dt"].dt.year
    work["month"] = work["obs_dt"].dt.month
    work["year_month"] = work["obs_dt"].dt.to_period("M").dt.to_timestamp()
    work["station_label"] = work["wmo_id"].astype(str).map(lambda x: STATION_NAMES.get(x, f"Stasiun {x}"))

    period_str = f"{work['obs_dt'].min().strftime('%d %b %Y')} - {work['obs_dt'].max().strftime('%d %b %Y')}"
    saved_files: Dict[str, Path] = {}

    # -------------------------------------------------------------------------
    # 1. Grafik Tren Curah Hujan Bulanan & Moving Average
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=150)
    monthly_ts = (
        work.groupby(["year_month", "wmo_id"], as_index=False)["rainfall_mm"]
        .sum()
        .groupby("year_month", as_index=False)["rainfall_mm"]
        .mean()
    )
    monthly_ts["rolling_6m"] = monthly_ts["rainfall_mm"].rolling(6, min_periods=2).mean()

    ax.plot(
        monthly_ts["year_month"],
        monthly_ts["rainfall_mm"],
        color="#0284C7",
        alpha=0.55,
        linewidth=1.5,
        label="Rata-rata Curah Hujan Bulanan Stasiun (mm/bulan)",
    )
    ax.plot(
        monthly_ts["year_month"],
        monthly_ts["rolling_6m"],
        color="#0F172A",
        linewidth=2.5,
        label="Tren Rata-Rata Bergerak 6 Bulan (mm/bulan)",
    )
    ax.set_title("Tren Curah Hujan Bulanan Provinsi Aceh", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Tahun Pengamatan", fontsize=10.5)
    ax.set_ylabel("Akumulasi Curah Hujan (mm/bulan)", fontsize=10.5)
    ax.legend(loc="upper right")
    _add_footer_attribution(fig, source_label, period_str)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    p1 = output_dir / "01_rainfall_trend.png"
    fig.savefig(p1)
    plt.close(fig)
    saved_files["rainfall_trend"] = p1

    # -------------------------------------------------------------------------
    # 2. Grafik Siklus Musiman Curah Hujan Bulanan (Monsunal vs Ekuatorial)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
    st_ym = work.groupby(["wmo_id", "year", "month"], as_index=False)["rainfall_mm"].sum()
    m_avg = st_ym.groupby("month", as_index=False)["rainfall_mm"].agg(["mean", "median"]).reset_index()

    bars = ax.bar(
        m_avg["month"],
        m_avg["mean"],
        color="#0369A1",
        alpha=0.85,
        label="Rata-rata Akumulasi Bulanan (mm)",
    )
    ax.plot(
        m_avg["month"],
        m_avg["median"],
        color="#F59E0B",
        marker="o",
        linewidth=2.2,
        label="Median Akumulasi Bulanan (mm)",
    )
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_title("Pola Klimatologi Curah Hujan Bulanan di Provinsi Aceh", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Bulan", fontsize=10.5)
    ax.set_ylabel("Curah Hujan Bulanan (mm/bulan)", fontsize=10.5)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
        )
    ax.legend(loc="upper left")
    _add_footer_attribution(fig, source_label, period_str)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    p2 = output_dir / "02_monthly_rainfall.png"
    fig.savefig(p2)
    plt.close(fig)
    saved_files["monthly_rainfall"] = p2

    # -------------------------------------------------------------------------
    # 3. Heatmap Intensitas Curah Hujan Bulanan (Tahun vs Bulan)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
    pivot_rain = (
        st_ym.groupby(["year", "month"], as_index=False)["rainfall_mm"]
        .mean()
        .pivot(index="year", columns="month", values="rainfall_mm")
    )
    pivot_rain.columns = [MONTH_LABELS[c - 1] for c in pivot_rain.columns]
    sns.heatmap(
        pivot_rain,
        annot=True,
        fmt=".0f",
        cmap="YlGnBu",
        cbar_kws={"label": "Curah Hujan Rata-rata (mm/bulan)"},
        ax=ax,
    )
    ax.set_title("Heatmap Intensitas Curah Hujan Bulanan Aceh (mm/bulan)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Bulan", fontsize=10.5)
    ax.set_ylabel("Tahun", fontsize=10.5)
    _add_footer_attribution(fig, source_label, period_str)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    p3 = output_dir / "03_rainfall_heatmap.png"
    fig.savefig(p3)
    plt.close(fig)
    saved_files["rainfall_heatmap"] = p3

    # -------------------------------------------------------------------------
    # 4. Distribusi Curah Hujan Harian (Hari Hujan >= 0.5 mm) & Ambang BMKG
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
    wet_rain = work["rainfall_mm"].dropna()
    wet_rain = wet_rain[wet_rain >= 0.5]
    ax.hist(wet_rain, bins=45, color="#0284C7", edgecolor="white", alpha=0.85)
    ax.axvline(20.0, color="#EAB308", linestyle="--", linewidth=2, label="Ambang Hujan Sedang (20 mm/hari)")
    ax.axvline(50.0, color="#EA580C", linestyle="--", linewidth=2, label="Ambang Hujan Lebat/Ekstrem (50 mm/hari)")
    ax.axvline(100.0, color="#DC2626", linestyle="--", linewidth=2, label="Ambang Hujan Sangat Lebat (100 mm/hari)")
    ax.set_yscale("log")
    ax.set_title(
        "Distribusi Frekuensi Curah Hujan Harian pada Hari Hujan (Skala Logaritmik)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Intensitas Curah Hujan Harian (mm/hari)", fontsize=10.5)
    ax.set_ylabel("Frekuensi Kejadian (Hari - Skala Log)", fontsize=10.5)
    ax.legend(loc="upper right")
    _add_footer_attribution(fig, source_label, period_str)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    p4 = output_dir / "04_rainfall_distribution.png"
    fig.savefig(p4)
    plt.close(fig)
    saved_files["rainfall_distribution"] = p4

    # -------------------------------------------------------------------------
    # 5. Grafik Dinamika Suhu dan Kelembapan Udara Bulanan
    # -------------------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(11, 5.5), dpi=150)
    th_monthly = (
        work.groupby("month", as_index=False)
        .agg(
            temp_min=("temp_min_c", "mean"),
            temp_avg=("temp_avg_c", "mean"),
            temp_max=("temp_max_c", "mean"),
            rh_avg=("humidity_avg_pct", "mean"),
        )
    )
    ax1.plot(th_monthly["month"], th_monthly["temp_max"], color="#DC2626", marker="^", label="Suhu Maksimum Rata-rata (°C)")
    ax1.plot(th_monthly["month"], th_monthly["temp_avg"], color="#EA580C", marker="o", linewidth=2.2, label="Suhu Rata-rata Harian (°C)")
    ax1.plot(th_monthly["month"], th_monthly["temp_min"], color="#0284C7", marker="v", label="Suhu Minimum Rata-rata (°C)")
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(MONTH_LABELS)
    ax1.set_xlabel("Bulan", fontsize=10.5)
    ax1.set_ylabel("Suhu Udara (°C)", fontsize=10.5, color="#EA580C")

    ax2 = ax1.twinx()
    ax2.plot(
        th_monthly["month"],
        th_monthly["rh_avg"],
        color="#0D9488",
        linestyle="--",
        marker="s",
        linewidth=2.2,
        label="Kelembapan Relatif Rata-rata (%)",
    )
    ax2.set_ylabel("Kelembapan Udara Relatif (%)", fontsize=10.5, color="#0D9488")
    ax2.grid(False)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper center", ncol=2, fontsize=8.5)
    ax1.set_title("Profil Klimatologi Suhu Udara dan Kelembapan Relatif Provinsi Aceh", fontsize=13, fontweight="bold", pad=12)
    _add_footer_attribution(fig, source_label, period_str)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    p5 = output_dir / "05_temp_humidity_dynamics.png"
    fig.savefig(p5)
    plt.close(fig)
    saved_files["temp_humidity_dynamics"] = p5

    # -------------------------------------------------------------------------
    # 6. Perbandingan Antarwilayah / Stasiun Pengamatan BMKG di Aceh
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
    st_annual = (
        work.groupby(["station_label", "year"], as_index=False)["rainfall_mm"]
        .sum()
        .groupby("station_label", as_index=False)["rainfall_mm"]
        .mean()
        .sort_values("rainfall_mm", ascending=True)
    )
    bars = ax.barh(st_annual["station_label"], st_annual["rainfall_mm"], color="#1E3A8A", alpha=0.88)
    ax.set_title("Perbandingan Rata-Rata Curah Hujan Tahunan Antar Stasiun BMKG Aceh", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Rata-Rata Curah Hujan Tahunan (mm/tahun)", fontsize=10.5)
    ax.set_ylabel("Stasiun Pengamatan BMKG", fontsize=10.5)
    for bar in bars:
        w = bar.get_width()
        ax.annotate(
            f"{w:.0f} mm/thn",
            xy=(w, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=8.5,
        )
    _add_footer_attribution(fig, source_label, period_str)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    p6 = output_dir / "06_regional_station_comparison.png"
    fig.savefig(p6)
    plt.close(fig)
    saved_files["regional_station_comparison"] = p6

    # -------------------------------------------------------------------------
    # 7. Kalender Kejadian Hujan Ekstrem (>= 50 mm/hari) per Bulan & Stasiun
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
    work["is_extreme"] = (work["rainfall_mm"] >= 50.0).astype(int)
    ext_cal = (
        work.groupby(["station_label", "month"], as_index=False)["is_extreme"]
        .sum()
        .pivot(index="station_label", columns="month", values="is_extreme")
        .fillna(0)
    )
    ext_cal.columns = [MONTH_LABELS[c - 1] for c in ext_cal.columns]
    sns.heatmap(
        ext_cal,
        annot=True,
        fmt=".0f",
        cmap="OrRd",
        cbar_kws={"label": "Jumlah Kejadian Hujan Lebat-Ekstrem (>= 50 mm/hari)"},
        ax=ax,
    )
    ax.set_title(
        "Kalender Frekuensi Kejadian Hujan Lebat-Ekstrem (>= 50 mm/hari) di Aceh",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Bulan", fontsize=10.5)
    ax.set_ylabel("Stasiun BMKG", fontsize=10.5)
    _add_footer_attribution(fig, source_label, period_str)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    p7 = output_dir / "07_extreme_rain_calendar.png"
    fig.savefig(p7)
    plt.close(fig)
    saved_files["extreme_rain_calendar"] = p7

    return saved_files
'''

# ==============================================================================
# 3. src/geospatial/aceh_gis_analyzer.py
# ==============================================================================
FILES["src/geospatial/aceh_gis_analyzer.py"] = '''"""
Spatio-Temporal & GIS Engine — ACEH SIAGA CUACA
File: src/geospatial/aceh_gis_analyzer.py

Mencakup:
1. Metadata & Geometri 23 Kabupaten/Kota Aceh + 5 Stasiun Pengamatan BMKG Aceh.
2. Generator layer GeoJSON standar RFC 7946 untuk Leaflet & PostGIS:
   - Layer Stasiun Cuaca + Statistik Ekstrem.
   - Layer Kabupaten/Kota + Kepadatan Kejadian Bencana Banjir & Tanah Longsor.
   - Layer Poligon Peringatan Dini Cuaca (CAP BMKG).
3. Analisis hubungan spasial zona topografi Aceh (Pesisir Barat-Selatan, Pesisir Timur-Utara,
   Dataran Tinggi Tengah, Kepulauan) dengan frekuensi hujan tinggi dan bencana hidrometeorologi.
4. Dokumentasi eksplisit keterbatasan interpolasi spasial (tidak melakukan interpolasi IDW/Kriging
   buta lintas Pegunungan Bukit Barisan dengan hanya 5 stasiun sinoptik).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.data_collection.bmkg_alerts import CAPAlertSchema

ACEH_REGENCIES_GIS: List[Dict[str, Any]] = [
    {"region_code": "11.01", "name": "Kabupaten Aceh Selatan", "lat": 3.2577, "lon": 97.1803, "elev_m": 15.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.02", "name": "Kabupaten Aceh Tenggara", "lat": 3.4913, "lon": 97.8108, "elev_m": 320.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96009"},
    {"region_code": "11.03", "name": "Kabupaten Aceh Timur", "lat": 4.9500, "lon": 97.7667, "elev_m": 18.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.04", "name": "Kabupaten Aceh Tengah", "lat": 4.6247, "lon": 96.8492, "elev_m": 1250.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96009"},
    {"region_code": "11.05", "name": "Kabupaten Aceh Barat", "lat": 4.1449, "lon": 96.1264, "elev_m": 8.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.06", "name": "Kabupaten Aceh Besar", "lat": 5.2917, "lon": 95.5972, "elev_m": 35.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96003"},
    {"region_code": "11.07", "name": "Kabupaten Pidie", "lat": 5.3847, "lon": 95.9608, "elev_m": 12.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96003"},
    {"region_code": "11.08", "name": "Kabupaten Aceh Utara", "lat": 5.0517, "lon": 97.3181, "elev_m": 14.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.09", "name": "Kabupaten Simeulue", "lat": 2.4789, "lon": 96.3761, "elev_m": 10.0, "zone": "KEPULAUAN", "nearest_wmo": "96011"},
    {"region_code": "11.10", "name": "Kabupaten Aceh Singkil", "lat": 2.2889, "lon": 97.7950, "elev_m": 7.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.11", "name": "Kabupaten Bireuen", "lat": 5.2014, "lon": 96.7019, "elev_m": 15.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.12", "name": "Kabupaten Aceh Barat Daya", "lat": 3.7431, "lon": 96.8322, "elev_m": 18.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.13", "name": "Kabupaten Gayo Lues", "lat": 3.9833, "lon": 97.3500, "elev_m": 950.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96011"},
    {"region_code": "11.14", "name": "Kabupaten Aceh Jaya", "lat": 4.6319, "lon": 95.5819, "elev_m": 12.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96003"},
    {"region_code": "11.15", "name": "Kabupaten Nagan Raya", "lat": 4.1683, "lon": 96.3211, "elev_m": 22.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.16", "name": "Kabupaten Aceh Tamiang", "lat": 4.2819, "lon": 98.0583, "elev_m": 15.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.17", "name": "Kabupaten Bener Meriah", "lat": 4.7267, "lon": 96.8617, "elev_m": 1320.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96009"},
    {"region_code": "11.18", "name": "Kabupaten Pidie Jaya", "lat": 5.2411, "lon": 96.2469, "elev_m": 10.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.71", "name": "Kota Banda Aceh", "lat": 5.5483, "lon": 95.3238, "elev_m": 5.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96001"},
    {"region_code": "11.72", "name": "Kota Sabang", "lat": 5.8933, "lon": 95.3192, "elev_m": 85.0, "zone": "KEPULAUAN", "nearest_wmo": "96002"},
    {"region_code": "11.73", "name": "Kota Lhokseumawe", "lat": 5.1801, "lon": 97.1507, "elev_m": 6.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.74", "name": "Kota Langsa", "lat": 4.4683, "lon": 97.9683, "elev_m": 10.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.75", "name": "Kota Subulussalam", "lat": 2.6419, "lon": 98.0053, "elev_m": 75.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
]

ACEH_STATIONS_GIS: List[Dict[str, Any]] = [
    {"wmo_id": "96001", "station_name": "Stasiun Meteorologi Kelas I Sultan Iskandar Muda", "region_code": "11.06", "lat": 5.5225, "lon": 95.4170, "elev_m": 20.0, "zone": "PESISIR_TIMUR_UTARA"},
    {"wmo_id": "96002", "station_name": "Stasiun Meteorologi Maimun Saleh Sabang", "region_code": "11.72", "lat": 5.8742, "lon": 95.3397, "elev_m": 126.0, "zone": "KEPULAUAN"},
    {"wmo_id": "96003", "station_name": "Stasiun Klimatologi Aceh (Indrapuri)", "region_code": "11.06", "lat": 5.4045, "lon": 95.4472, "elev_m": 45.0, "zone": "PESISIR_TIMUR_UTARA"},
    {"wmo_id": "96009", "station_name": "Stasiun Meteorologi Malikussaleh Aceh Utara", "region_code": "11.08", "lat": 5.2286, "lon": 96.9475, "elev_m": 8.0, "zone": "PESISIR_TIMUR_UTARA"},
    {"wmo_id": "96011", "station_name": "Stasiun Meteorologi Cut Nyak Dhien Nagan Raya", "region_code": "11.15", "lat": 4.0450, "lon": 96.2483, "elev_m": 4.0, "zone": "PESISIR_BARAT_SELATAN"},
]

SPATIAL_LIMITATION_STATEMENT = (
    "KETERBATASAN ANALISIS SPASIAL: Jaringan stasiun pengamatan sinoptik utama BMKG yang terbuka "
    "di Provinsi Aceh terdiri atas 5 stasiun yang terkonsentrasi di wilayah pesisir dan lembah "
    "(Aceh Besar, Sabang, Aceh Utara, dan Nagan Raya). Mengingat topografi Pegunungan Bukit Barisan "
    "di bagian tengah Aceh (elevasi >1.000 mdpl) menciptakan efek orografis yang tajam, sistem ini "
    "TIDAK melakukan interpolasi permukaan kontinu (IDW/Kriging) dari 5 titik stasiun ke seluruh "
    "kabupaten pegunungan untuk menghindari galat estimasi yang menyesatkan. Analisis wilayah "
    "disajikan pada titik lokasi stasiun yang terverifikasi dan agregasi batas administrasi kabupaten/kota."
)


class AcehGISAnalyzer:
    """Mesin analisis geospasial dan pembentuk layer GeoJSON untuk Provinsi Aceh."""

    @staticmethod
    def generate_demo_disaster_dataset(
        output_path: Path = Path("data/demo/demo_bpba_disasters_aceh.csv"),
    ) -> Path:
        """
        Membuat dataset DEMO riwayat kejadian bencana hidrometeorologi Aceh (2021-2026)
        dengan distribusi spasial realistis (banjir tinggi di Aceh Utara, Aceh Timur, Aceh Tamiang,
        Aceh Barat, Nagan Raya; tanah longsor tinggi di Aceh Tengah, Bener Meriah, Gayo Lues).
        Diberi label eksplisit DEMO_SYNTHETIC.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(seed=20261119)

        high_flood_regions = ["11.08", "11.03", "11.16", "11.05", "11.15", "11.01", "11.10", "11.06"]
        high_landslide_regions = ["11.04", "11.17", "11.13", "11.02", "11.14", "11.06"]
        all_codes = [r["region_code"] for r in ACEH_REGENCIES_GIS]

        rows: List[Dict[str, Any]] = []
        dates = pd.date_range("2021-01-05", "2026-10-28", freq="7D")

        event_idx = 1
        for d in dates:
            month = d.month
            # Frekuensi bencana meningkat pada puncak musim hujan Aceh (Okt-Jan & Apr-Mei)
            is_wet_peak = month in (10, 11, 12, 1, 4, 5)
            n_events = int(rng.choice([0, 1, 2, 3], p=[0.25, 0.40, 0.25, 0.10] if is_wet_peak else [0.65, 0.25, 0.08, 0.02]))

            for _ in range(n_events):
                dtype_roll = rng.random()
                if dtype_roll < 0.58:
                    dtype = "BANJIR"
                    reg = str(rng.choice(high_flood_regions if rng.random() < 0.75 else all_codes))
                elif dtype_roll < 0.72:
                    dtype = "BANJIR_BANDANG"
                    reg = str(rng.choice(high_landslide_regions + high_flood_regions[:3]))
                elif dtype_roll < 0.90:
                    dtype = "TANAH_LONGSOR"
                    reg = str(rng.choice(high_landslide_regions if rng.random() < 0.80 else all_codes))
                else:
                    dtype = "ANGIN_KENCANG"
                    reg = str(rng.choice(all_codes))

                rows.append(
                    {
                        "event_code": f"DEMO-BPBA-{d.year}-{event_idx:04d}",
                        "region_code": reg,
                        "disaster_type": dtype,
                        "event_date": d.strftime("%Y-%m-%d"),
                        "casualties_dead": int(rng.choice([0, 0, 0, 1, 2], p=[0.90, 0.04, 0.03, 0.02, 0.01])),
                        "casualties_missing": 0,
                        "casualties_injured": int(rng.integers(0, 6)),
                        "affected_people": int(rng.integers(50, 3500)) if "BANJIR" in dtype else int(rng.integers(10, 300)),
                        "displaced_people": int(rng.integers(0, 800)) if "BANJIR" in dtype else int(rng.integers(0, 80)),
                        "houses_heavily_damaged": int(rng.integers(0, 15)),
                        "houses_moderately_damaged": int(rng.integers(0, 25)),
                        "houses_lightly_damaged": int(rng.integers(0, 45)),
                        "houses_submerged": int(rng.integers(20, 950)) if "BANJIR" in dtype else 0,
                        "public_facilities_damaged": int(rng.integers(0, 5)),
                        "data_mode": "DEMO_SYNTHETIC_DISASTER_RECORD",
                    }
                )
                event_idx += 1

        df_dis = pd.DataFrame(rows)
        df_dis.to_csv(output_path, index=False)
        return output_path

    @staticmethod
    def build_stations_geojson(obs_df: pd.DataFrame) -> Dict[str, Any]:
        """Membentuk GeoJSON FeatureCollection untuk 5 Stasiun BMKG Aceh beserta ringkasan iklim ekstrem."""
        work = obs_df.copy()
        work["is_extreme_50mm"] = (pd.to_numeric(work["rainfall_mm"], errors="coerce") >= 50.0).astype(int)
        work["is_heavy_20mm"] = (pd.to_numeric(work["rainfall_mm"], errors="coerce") >= 20.0).astype(int)

        stats_by_wmo = (
            work.groupby("wmo_id", as_index=False)
            .agg(
                obs_days=("rainfall_mm", "count"),
                mean_daily_rain_mm=("rainfall_mm", "mean"),
                max_daily_rain_mm=("rainfall_mm", "max"),
                r20mm_days=("is_heavy_20mm", "sum"),
                r50mm_extreme_days=("is_extreme_50mm", "sum"),
                mean_temp_c=("temp_avg_c", "mean"),
                mean_humidity_pct=("humidity_avg_pct", "mean"),
            )
            .round(2)
            .set_index("wmo_id")
            .to_dict(orient="index")
        )

        features: List[Dict[str, Any]] = []
        for st in ACEH_STATIONS_GIS:
            wmo = st["wmo_id"]
            st_stat = stats_by_wmo.get(wmo, {})
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(st["lon"]), float(st["lat"])],
                    },
                    "properties": {
                        "wmo_id": wmo,
                        "station_name": st["station_name"],
                        "region_code": st["region_code"],
                        "elevation_m": st["elev_m"],
                        "topography_zone": st["zone"],
                        "obs_days": int(st_stat.get("obs_days", 0)),
                        "mean_daily_rain_mm": float(st_stat.get("mean_daily_rain_mm", 0.0)),
                        "max_daily_rain_mm": float(st_stat.get("max_daily_rain_mm", 0.0)),
                        "r20mm_days": int(st_stat.get("r20mm_days", 0)),
                        "r50mm_extreme_days": int(st_stat.get("r50mm_extreme_days", 0)),
                        "mean_temp_c": float(st_stat.get("mean_temp_c", 0.0)),
                        "mean_humidity_pct": float(st_stat.get("mean_humidity_pct", 0.0)),
                        "data_nature": "OBSERVATION_STATION",
                        "source_attribution": "BMKG Provinsi Aceh",
                    },
                }
            )

        return {
            "type": "FeatureCollection",
            "metadata": {
                "layer_name": "Stasiun Pengamatan Cuaca BMKG Provinsi Aceh",
                "spatial_limitation_note": SPATIAL_LIMITATION_STATEMENT,
            },
            "features": features,
        }

    @staticmethod
    def _create_bounding_box_polygon(lon: float, lat: float, delta: float = 0.18) -> List[List[List[float]]]:
        """Membuat poligon kotak batas representatif kabupaten/kota jika shapefile detail BIG belum dimuat."""
        return [
            [
                [round(lon - delta, 5), round(lat - delta, 5)],
                [round(lon + delta, 5), round(lat - delta, 5)],
                [round(lon + delta, 5), round(lat + delta, 5)],
                [round(lon - delta, 5), round(lat + delta, 5)],
                [round(lon - delta, 5), round(lat - delta, 5)],
            ]
        ]

    @classmethod
    def build_disaster_density_geojson(cls, disaster_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Membentuk GeoJSON 23 Kabupaten/Kota Aceh dengan kepadatan kejadian bencana
        (banjir, banjir bandang, tanah longsor, angin kencang) dan dampak rumah terendam.
        """
        agg = (
            disaster_df.groupby("region_code", as_index=False)
            .agg(
                total_events=("event_code", "count"),
                flood_events=("disaster_type", lambda s: int((s == "BANJIR").sum())),
                flash_flood_events=("disaster_type", lambda s: int((s == "BANJIR_BANDANG").sum())),
                landslide_events=("disaster_type", lambda s: int((s == "TANAH_LONGSOR").sum())),
                wind_events=("disaster_type", lambda s: int((s.isin(["ANGIN_KENCANG", "CUACA_EKSTREM"])).sum())),
                total_affected_people=("affected_people", "sum"),
                total_houses_submerged=("houses_submerged", "sum"),
            )
            .set_index("region_code")
            .to_dict(orient="index")
        )

        features: List[Dict[str, Any]] = []
        for reg in ACEH_REGENCIES_GIS:
            code = reg["region_code"]
            d_stat = agg.get(code, {})
            total_ev = int(d_stat.get("total_events", 0))
            risk_class = "TINGGI" if total_ev >= 20 else ("SEDANG" if total_ev >= 10 else "RENDAH")

            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": cls._create_bounding_box_polygon(reg["lon"], reg["lat"]),
                    },
                    "properties": {
                        "region_code": code,
                        "region_name": reg["name"],
                        "centroid_lat": reg["lat"],
                        "centroid_lon": reg["lon"],
                        "elevation_m": reg["elev_m"],
                        "topography_zone": reg["zone"],
                        "nearest_bmkg_station_wmo": reg["nearest_wmo"],
                        "total_disaster_events": total_ev,
                        "flood_events": int(d_stat.get("flood_events", 0)),
                        "flash_flood_events": int(d_stat.get("flash_flood_events", 0)),
                        "landslide_events": int(d_stat.get("landslide_events", 0)),
                        "wind_events": int(d_stat.get("wind_events", 0)),
                        "total_affected_people": int(d_stat.get("total_affected_people", 0)),
                        "total_houses_submerged": int(d_stat.get("total_houses_submerged", 0)),
                        "hydromet_density_class": risk_class,
                    },
                }
            )

        return {
            "type": "FeatureCollection",
            "metadata": {
                "layer_name": "Peta Kepadatan Kejadian Bencana Hidrometeorologi Kabupaten/Kota Aceh",
                "spatial_limitation_note": SPATIAL_LIMITATION_STATEMENT,
            },
            "features": features,
        }

    @staticmethod
    def build_active_alerts_geojson(alerts: List[CAPAlertSchema]) -> Dict[str, Any]:
        """Membentuk GeoJSON poligon peringatan dini cuaca aktif dari dokumen CAP BMKG."""
        features: List[Dict[str, Any]] = []
        for alert in alerts:
            if alert.polygons_geojson:
                geometry: Dict[str, Any] = {
                    "type": "MultiPolygon",
                    "coordinates": [[ring] for ring in alert.polygons_geojson],
                }
            else:
                # Fallback titik pusat Provinsi Aceh jika dokumen CAP hanya mencantumkan teks wilayah tanpa tag <polygon>
                geometry = {"type": "Point", "coordinates": [96.749399, 4.695135]}

            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "cap_identifier": alert.cap_identifier,
                        "headline": alert.headline,
                        "event_type": alert.event_type,
                        "severity": alert.severity,
                        "urgency": alert.urgency,
                        "certainty": alert.certainty,
                        "effective_time": alert.effective_time.isoformat(),
                        "expires_time": alert.expires_time.isoformat(),
                        "affected_areas_text": alert.affected_areas_text,
                        "official_web_url": alert.official_web_url,
                        "source_attribution": alert.source_attribution,
                        "data_nature": "OFFICIAL_ALERT",
                    },
                }
            )

        return {
            "type": "FeatureCollection",
            "metadata": {
                "layer_name": "Poligon Peringatan Dini Cuaca Aktif BMKG (CAP v1.2)",
                "active_alerts_count": len(features),
            },
            "features": features,
        }

    @staticmethod
    def analyze_spatiotemporal_weather_disaster_link(
        obs_df: pd.DataFrame,
        disaster_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Menganalisis hubungan spasial-temporal antara zona topografi Aceh,
        frekuensi hujan lebat-ekstrem (>= 50 mm/hari), dan kejadian bencana banjir/longsor.
        """
        st_zone_map = {s["wmo_id"]: s["zone"] for s in ACEH_STATIONS_GIS}
        reg_zone_map = {r["region_code"]: r["zone"] for r in ACEH_REGENCIES_GIS}

        obs = obs_df.copy()
        obs["topography_zone"] = obs["wmo_id"].astype(str).map(st_zone_map)
        obs["is_extreme_50mm"] = (pd.to_numeric(obs["rainfall_mm"], errors="coerce") >= 50.0).astype(int)
        obs["month"] = pd.to_datetime(obs["observation_date"]).dt.month

        dis = disaster_df.copy()
        dis["topography_zone"] = dis["region_code"].astype(str).map(reg_zone_map)
        dis["month"] = pd.to_datetime(dis["event_date"]).dt.month

        rain_by_zone = (
            obs.groupby("topography_zone", as_index=False)
            .agg(
                mean_daily_rainfall_mm=("rainfall_mm", "mean"),
                max_daily_rainfall_mm=("rainfall_mm", "max"),
                extreme_50mm_days=("is_extreme_50mm", "sum"),
            )
            .round(2)
            .to_dict(orient="records")
        )

        disaster_by_zone = (
            dis.groupby("topography_zone", as_index=False)
            .agg(
                total_disasters=("event_code", "count"),
                flood_count=("disaster_type", lambda s: int(s.isin(["BANJIR", "BANJIR_BANDANG"]).sum())),
                landslide_count=("disaster_type", lambda s: int((s == "TANAH_LONGSOR").sum())),
                total_affected_people=("affected_people", "sum"),
            )
            .to_dict(orient="records")
        )

        # Korelasi temporal bulanan antara jumlah hari hujan ekstrem Aceh dan jumlah kejadian bencana
        monthly_ext = obs.groupby("month", as_index=False)["is_extreme_50mm"].sum()
        monthly_dis = dis.groupby("month", as_index=False)["event_code"].count().rename(columns={"event_code": "disaster_count"})
        merged_monthly = pd.merge(monthly_ext, monthly_dis, on="month", how="inner")

        monthly_corr = 0.0
        if len(merged_monthly) >= 3:
            monthly_corr = round(float(merged_monthly["is_extreme_50mm"].corr(merged_monthly["disaster_count"], method="spearman")), 4)

        return {
            "spatial_limitation_statement": SPATIAL_LIMITATION_STATEMENT,
            "rainfall_by_topography_zone": rain_by_zone,
            "disasters_by_topography_zone": disaster_by_zone,
            "monthly_extreme_rain_vs_disaster_spearman_rho": monthly_corr,
        }
'''

# ==============================================================================
# 4. Helper pembentuk 4 Jupyter Notebooks (.ipynb)
# ==============================================================================
def make_notebook(title: str, description: str, code_cells: list[str]) -> str:
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"# {title}\n", f"**Proyek:** ACEH SIAGA CUACA\n\n", f"{description}\n"],
        }
    ]
    for code in code_cells:
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in code.strip().splitlines()],
            }
        )
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(nb, indent=2, ensure_ascii=False)


FILES["notebooks/01_data_collection.ipynb"] = make_notebook(
    "01 — Data Collection & Verification (BMKG Forecast, CAP Alerts & Historical Pipeline)",
    "Notebook ini mendemonstrasikan pengambilan data prakiraan cuaca resmi BMKG (ADM4 Aceh), RSS/CAP Peringatan Dini Cuaca BMKG, dan pemuatan dataset observasi stasiun.",
    [
        """import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()))

from src.data_collection.bmkg_forecast import BMKGForecastCollector, ACEH_REPRESENTATIVE_ADM4
from src.data_collection.bmkg_alerts import BMKGAlertCollector
from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter""",
        """# 1. Ambil Prakiraan Cuaca Resmi BMKG untuk Kota Banda Aceh (11.71.01.2001)
collector = BMKGForecastCollector()
forecasts = collector.fetch_and_parse("11.71.01.2001", use_cache=True)
print(f"Total slot waktu 3-jaman diperoleh: {len(forecasts)}")
for f in forecasts[:5]:
    print(f.forecast_time_local, "|", f.weather_desc_id, f"| T={f.temperature_c}C | RH={f.humidity_pct}% | WS={f.wind_speed_kmh} km/jam")""",
        """# 2. Ambil Peringatan Dini Cuaca Aktif BMKG (RSS + CAP v1.2) untuk Wilayah Aceh
alert_collector = BMKGAlertCollector()
active_alerts = alert_collector.fetch_active_aceh_alerts()
print(f"Jumlah peringatan dini aktif di Provinsi Aceh: {len(active_alerts)}")
for a in active_alerts:
    print(a.cap_identifier, "|", a.severity, "|", a.headline, "| Berlaku s.d.", a.expires_time)""",
    ],
)

FILES["notebooks/02_data_cleaning.ipynb"] = make_notebook(
    "02 — Data Cleaning & BMKG Special Codes Handling (8888 Trace & 9999 Missing)",
    "Notebook ini memvalidasi proses pembersihan data observasi BMKG, konversi kode khusus 8888 (curah hujan tidak terukur/trace) menjadi 0.0 mm dengan flag is_trace_rainfall=True, serta kode 9999 menjadi NaN.",
    [
        """import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()))

from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter
from src.analytics.eda_statistics import compute_data_quality_report""",
        """# Muat dataset observasi dan jalankan audit kualitas data
csv_path = BMKGHistoricalImporter.generate_demo_dataset()
df_clean = BMKGHistoricalImporter.load_file(csv_path)
quality_report = compute_data_quality_report(df_clean)
print("Ringkasan Kualitas Data Observasi Aceh:")
for k, v in quality_report.items():
    if k not in ('missing_values_summary', 'station_coverage'):
        print(f"  {k}: {v}")""",
        """df_clean.head(10)""",
    ],
)

FILES["notebooks/03_exploratory_data_analysis.ipynb"] = make_notebook(
    "03 — Exploratory Data Analysis (Descriptive Stats, ETCCDI Extremes, Temporal & Correlation)",
    "Notebook ini menjalankan analisis statistik deskriptif, indeks cuaca ekstrem WMO/ETCCDI (R20mm, R50mm, Rx1day, Rx5day, CDD, CWD), pola musiman Aceh, analisis korelasi Spearman/Pearson, dan menghasilkan 7 grafik utama.",
    [
        """import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()))

from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter
from src.analytics.eda_statistics import (
    compute_descriptive_statistics,
    compute_etccdi_extreme_indices,
    compute_temporal_patterns,
    compute_correlation_analysis,
)
from src.analytics.eda_visualizations import generate_all_eda_figures""",
        """df_clean = BMKGHistoricalImporter.load_file(Path("data/demo/demo_bmkg_historical_aceh.csv"))
desc_stats = compute_descriptive_statistics(df_clean)
print("=== Statistik Deskriptif Parameter Meteorologi Aceh ===")
print(desc_stats.to_string(index=False))""",
        """etccdi_df = compute_etccdi_extreme_indices(df_clean)
print("=== Indeks Cuaca Ekstrem Tahunan (ETCCDI) per Stasiun BMKG Aceh ===")
print(etccdi_df.head(15).to_string(index=False))""",
        """corr_report = compute_correlation_analysis(df_clean)
print(corr_report["methodology_note"])
for item in corr_report["rainfall_associations"]:
    print(item)""",
        """saved_figs = generate_all_eda_figures(df_clean)
for name, path in saved_figs.items():
    print(f"Grafik tersimpan: {name} -> {path}")""",
    ],
)

FILES["notebooks/04_spatiotemporal_analysis.ipynb"] = make_notebook(
    "04 — Spatio-Temporal & GIS Analysis of Extreme Weather and Disasters in Aceh",
    "Notebook ini menganalisis distribusi spasial curah hujan ekstrem dan keterkaitannya dengan kejadian bencana banjir serta tanah longsor di 23 Kabupaten/Kota Provinsi Aceh.",
    [
        """import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()))

from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter
from src.data_collection.disaster_import import DisasterDataImporter
from src.geospatial.aceh_gis_analyzer import AcehGISAnalyzer""",
        """df_obs = BMKGHistoricalImporter.load_file(Path("data/demo/demo_bmkg_historical_aceh.csv"))
demo_dis_path = AcehGISAnalyzer.generate_demo_disaster_dataset()
df_dis = DisasterDataImporter.import_file(demo_dis_path)

spatio_report = AcehGISAnalyzer.analyze_spatiotemporal_weather_disaster_link(df_obs, df_dis)
print(spatio_report["spatial_limitation_statement"])
print("\\nCurah Hujan per Zona Topografi Aceh:", spatio_report["rainfall_by_topography_zone"])
print("\\nKejadian Bencana per Zona Topografi Aceh:", spatio_report["disasters_by_topography_zone"])
print("\\nKorelasi Spearman Bulanan (Hujan Ekstrem >=50mm vs Frekuensi Bencana):", spatio_report["monthly_extreme_rain_vs_disaster_spearman_rho"])""",
    ],
)

# ==============================================================================
# 5. tests/test_phase2_analytics_gis.py
# ==============================================================================
FILES["tests/test_phase2_analytics_gis.py"] = '''"""
Unit Tests for PHASE 2 — DATA ANALYSIS & SPATIO-TEMPORAL GIS (ACEH SIAGA CUACA)
File: tests/test_phase2_analytics_gis.py
Jalankan dengan: python -m pytest tests\\test_phase2_analytics_gis.py -v
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
'''

# ==============================================================================
# 6. scripts/run_phase2_analysis.py
# ==============================================================================
FILES["scripts/run_phase2_analysis.py"] = '''#!/usr/bin/env python3
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
'''


def main() -> None:
    print(f"[PHASE 2 BUILDER] Menuliskan seluruh file Phase 2 ke: {BASE_DIR}")
    for rel_path, content in FILES.items():
        target = BASE_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"  [OK] {rel_path} ({len(content)} bytes)")
    print("\n[PHASE 2 BUILDER] Selesai! Jalankan perintah pengujian di PowerShell:")
    print("  1. python -m pytest tests\\test_phase2_analytics_gis.py -v")
    print("  2. python scripts\\run_phase2_analysis.py")


if __name__ == "__main__":
    main()