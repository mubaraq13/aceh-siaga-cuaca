"""
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
