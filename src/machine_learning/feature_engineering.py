"""
Leakage-Free Spatio-Temporal Feature Engineering Engine — ACEH SIAGA CUACA
File: src/machine_learning/feature_engineering.py

Aturan Ketat Anti Data Leakage:
1. Seluruh lag dan rolling window dihitung per stasiun (groupby 'wmo_id') setelah diurutkan
   secara kronologis berdasarkan 'observation_date'.
2. Semua fitur pada baris ke-t hanya menggunakan observasi dari waktu <= t.
3. Variabel target (H+1 / besok) dibentuk menggunakan shift(-1) per stasiun, dan baris dengan
   target NaN (missing observation) WAJIB dihapus (tidak boleh diimputasi).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

STATION_SPATIAL_META: Dict[str, Dict[str, float]] = {
    "96001": {"latitude": 5.5225, "longitude": 95.4170, "elevation_m": 20.0, "is_west_coast": 0.0},
    "96002": {"latitude": 5.8742, "longitude": 95.3397, "elevation_m": 126.0, "is_west_coast": 0.0},
    "96003": {"latitude": 5.4045, "longitude": 95.4472, "elevation_m": 45.0, "is_west_coast": 0.0},
    "96009": {"latitude": 5.2286, "longitude": 96.9475, "elevation_m": 8.0, "is_west_coast": 0.0},
    "96011": {"latitude": 4.0450, "longitude": 96.2483, "elevation_m": 4.0, "is_west_coast": 1.0},
}

FEATURE_COLUMNS: List[str] = [
    # Lag Rainfall Features (t, t-1, t-2, t-3, t-7)
    "rain_lag_0",
    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",
    # Rolling Window Rainfall Features (using data <= t)
    "rain_roll_mean_3d",
    "rain_roll_sum_3d",
    "rain_roll_mean_7d",
    "rain_roll_sum_7d",
    "rain_roll_max_7d",
    "rain_roll_sum_14d",
    "wet_days_count_7d",
    # Thermodynamic & Atmospheric Features at time t
    "temp_min_c",
    "temp_max_c",
    "temp_avg_c",
    "diurnal_temp_range_c",
    "humidity_avg_pct",
    "humidity_change_1d",
    "humidity_roll_mean_3d",
    "temp_humidity_interaction",
    "sunshine_hours",
    "sunshine_roll_mean_3d",
    # Wind Dynamics Features at time t
    "wind_speed_avg_ms",
    "wind_speed_max_ms",
    "wind_u_zonal",
    "wind_v_meridional",
    # Temporal Cyclical Features
    "doy_sin",
    "doy_cos",
    "month_sin",
    "month_cos",
    "month_num",
    # Spatial & Station Features
    "latitude",
    "longitude",
    "elevation_m",
    "is_west_coast",
    "station_code_num",
]


def build_supervised_dataset(
    df_cleaned: pd.DataFrame,
    extreme_threshold_mm: float = 50.0,
    moderate_threshold_mm: float = 20.0,
    drop_missing_target: bool = True,
) -> pd.DataFrame:
    """
    Membentuk dataset supervised learning (fitur waktu <= t untuk memprediksi target waktu t+1).
    """
    if df_cleaned.empty:
        raise ValueError("DataFrame input kosong.")

    df = df_cleaned.copy()
    df["obs_dt"] = pd.to_datetime(df["observation_date"])
    df = df.sort_values(["wmo_id", "obs_dt"]).reset_index(drop=True)
    df["wmo_id"] = df["wmo_id"].astype(str)

    station_Ids = sorted(df["wmo_id"].unique())
    station_map = {wmo: float(idx) for idx, wmo in enumerate(station_Ids)}

    processed_groups: List[pd.DataFrame] = []

    for wmo_id, grp in df.groupby("wmo_id", sort=False):
        g = grp.sort_values("obs_dt").copy()
        rr = pd.to_numeric(g["rainfall_mm"], errors="coerce")

        # 1. Fitur Lag Curah Hujan (hanya menggunakan masa lalu <= t)
        g["rain_lag_0"] = rr
        g["rain_lag_1"] = rr.shift(1)
        g["rain_lag_2"] = rr.shift(2)
        g["rain_lag_3"] = rr.shift(3)
        g["rain_lag_7"] = rr.shift(7)

        # 2. Fitur Rolling Window (jendela berakhir di hari t, TIDAK menyertakan t+1)
        g["rain_roll_mean_3d"] = rr.rolling(window=3, min_periods=1).mean()
        g["rain_roll_sum_3d"] = rr.rolling(window=3, min_periods=1).sum()
        g["rain_roll_mean_7d"] = rr.rolling(window=7, min_periods=2).mean()
        g["rain_roll_sum_7d"] = rr.rolling(window=7, min_periods=2).sum()
        g["rain_roll_max_7d"] = rr.rolling(window=7, min_periods=2).max()
        g["rain_roll_sum_14d"] = rr.rolling(window=14, min_periods=3).sum()

        is_wet = (rr >= 1.0).astype(float)
        g["wet_days_count_7d"] = is_wet.rolling(window=7, min_periods=1).sum()

        # 3. Fitur Termodinamika (Suhu, Kelembapan, Penyinaran Matahari)
        g["diurnal_temp_range_c"] = g["temp_max_c"] - g["temp_min_c"]
        g["humidity_change_1d"] = g["humidity_avg_pct"] - g["humidity_avg_pct"].shift(1)
        g["humidity_roll_mean_3d"] = g["humidity_avg_pct"].rolling(window=3, min_periods=1).mean()
        g["temp_humidity_interaction"] = g["temp_avg_c"] * (g["humidity_avg_pct"] / 100.0)
        g["sunshine_roll_mean_3d"] = g["sunshine_hours"].rolling(window=3, min_periods=1).mean()

        # 4. Dekomposisi Vektor Angin (Zonal u & Meridional v)
        rad = np.deg2rad(pd.to_numeric(g["wind_dir_max_deg"], errors="coerce").fillna(0.0))
        ws = pd.to_numeric(g["wind_speed_avg_ms"], errors="coerce").fillna(0.0)
        g["wind_u_zonal"] = -ws * np.sin(rad)
        g["wind_v_meridional"] = -ws * np.cos(rad)

        # 5. Fitur Siklikal Kalender
        doy = g["obs_dt"].dt.dayofyear.astype(float)
        month = g["obs_dt"].dt.month.astype(float)
        g["doy_sin"] = np.sin(2.0 * np.pi * doy / 365.25)
        g["doy_cos"] = np.cos(2.0 * np.pi * doy / 365.25)
        g["month_sin"] = np.sin(2.0 * np.pi * month / 12.0)
        g["month_cos"] = np.cos(2.0 * np.pi * month / 12.0)
        g["month_num"] = month

        # 6. Fitur Spasial Stasiun
        meta = STATION_SPATIAL_META.get(
            str(wmo_id),
            {"latitude": 5.0, "longitude": 96.0, "elevation_m": 20.0, "is_west_coast": 0.0},
        )
        g["latitude"] = meta["latitude"]
        g["longitude"] = meta["longitude"]
        g["elevation_m"] = meta["elevation_m"]
        g["is_west_coast"] = meta["is_west_coast"]
        g["station_code_num"] = station_map[str(wmo_id)]

        # 7. Pembentukan Variabel Target pada Hari Berikutnya (t + 1)
        g["target_date"] = g["obs_dt"].shift(-1)
        g["target_rain_next_day_mm"] = rr.shift(-1)

        # Pastikan selisih tanggal menuju target_date adalah tepat 1 hari (mencegah loncatan tanggal)
        day_gap = (g["target_date"] - g["obs_dt"]).dt.days
        g.loc[day_gap != 1, "target_rain_next_day_mm"] = np.nan

        g["target_is_extreme_50mm"] = np.where(
            g["target_rain_next_day_mm"].notna(),
            (g["target_rain_next_day_mm"] >= extreme_threshold_mm).astype(int),
            np.nan,
        )
        g["target_is_heavy_20mm"] = np.where(
            g["target_rain_next_day_mm"].notna(),
            (g["target_rain_next_day_mm"] >= moderate_threshold_mm).astype(int),
            np.nan,
        )

        processed_groups.append(g)

    full_df = pd.concat(processed_groups, ignore_index=True)
    full_df = full_df.sort_values(["obs_dt", "wmo_id"]).reset_index(drop=True)

    # Buang baris pemanasan lag awal (7 hari pertama per stasiun)
    full_df = full_df[full_df["rain_lag_7"].notna() | full_df["rain_roll_mean_7d"].notna()].copy()

    if drop_missing_target:
        full_df = full_df[full_df["target_rain_next_day_mm"].notna()].copy()
        full_df["target_is_extreme_50mm"] = full_df["target_is_extreme_50mm"].astype(int)
        full_df["target_is_heavy_20mm"] = full_df["target_is_heavy_20mm"].astype(int)

    return full_df.reset_index(drop=True)


def chronological_train_val_test_split(
    df_supervised: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Membagi dataset secara KRONOLOGIS murni berdasarkan tanggal unik (tanpa pengacakan / no shuffling)
    untuk mencegah kebocoran data masa depan (future data leakage).
    """
    if df_supervised.empty:
        raise ValueError("DataFrame supervised kosong.")

    unique_dates = np.sort(pd.to_datetime(df_supervised["obs_dt"]).unique())
    n_dates = len(unique_dates)
    if n_dates < 10:
        raise ValueError("Jumlah tanggal unik terlalu sedikit untuk pembagian kronologis.")

    train_cutoff_idx = int(n_dates * train_ratio)
    val_cutoff_idx = int(n_dates * (train_ratio + val_ratio))

    train_end_date = unique_dates[train_cutoff_idx - 1]
    val_end_date = unique_dates[val_cutoff_idx - 1]

    obs_dt = pd.to_datetime(df_supervised["obs_dt"])
    train_df = df_supervised[obs_dt <= train_end_date].copy().reset_index(drop=True)
    val_df = df_supervised[(obs_dt > train_end_date) & (obs_dt <= val_end_date)].copy().reset_index(drop=True)
    test_df = df_supervised[obs_dt > val_end_date].copy().reset_index(drop=True)

    return train_df, val_df, test_df
