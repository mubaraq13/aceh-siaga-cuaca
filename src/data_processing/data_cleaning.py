"""
BMKG Meteorological Data Cleaning & Validation Engine — ACEH SIAGA CUACA
File: src/data_processing/data_cleaning.py
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("aceh_siaga.data_cleaning")

BMKG_COLUMN_ALIASES: Dict[str, str] = {
    "tanggal": "observation_date",
    "date": "observation_date",
    "observation_date": "observation_date",
    "wmo_id": "wmo_id",
    "station_id": "wmo_id",
    "kode_stasiun": "wmo_id",
    "tn": "temp_min_c",
    "temp_min": "temp_min_c",
    "temp_min_c": "temp_min_c",
    "tx": "temp_max_c",
    "temp_max": "temp_max_c",
    "temp_max_c": "temp_max_c",
    "tavg": "temp_avg_c",
    "temp_avg": "temp_avg_c",
    "temp_avg_c": "temp_avg_c",
    "rh_avg": "humidity_avg_pct",
    "humidity_avg": "humidity_avg_pct",
    "humidity_avg_pct": "humidity_avg_pct",
    "rr": "rainfall_mm",
    "curah_hujan": "rainfall_mm",
    "rainfall_mm": "rainfall_mm",
    "ss": "sunshine_hours",
    "sunshine_hours": "sunshine_hours",
    "ff_x": "wind_speed_max_ms",
    "wind_speed_max_ms": "wind_speed_max_ms",
    "ddd_x": "wind_dir_max_deg",
    "wind_dir_max_deg": "wind_dir_max_deg",
    "ff_avg": "wind_speed_avg_ms",
    "wind_speed_avg_ms": "wind_speed_avg_ms",
    "ddd_car": "wind_dir_predominant",
    "wind_dir_predominant": "wind_dir_predominant",
}

MISSING_TOKENS = {"9999", "9999.0", "-", "--", "na", "n/a", "null", "none", ""}
TRACE_TOKENS = {"8888", "8888.0"}


def classify_bmkg_daily_rainfall(rr_value: Optional[float]) -> str:
    if rr_value is None or pd.isna(rr_value):
        return "MISSING"
    val = float(rr_value)
    if val < 0.5:
        return "NO_RAIN"
    if val <= 20.0:
        return "LIGHT"
    if val <= 50.0:
        return "MODERATE"
    if val <= 100.0:
        return "HEAVY"
    if val <= 150.0:
        return "VERY_HEAVY"
    return "EXTREME"


def clean_bmkg_observation_dataframe(
    df_raw: pd.DataFrame,
    default_wmo_id: Optional[str] = None,
) -> pd.DataFrame:
    if df_raw.empty:
        raise ValueError("DataFrame input observasi BMKG kosong.")

    df = df_raw.copy()

    renamed_cols: Dict[str, str] = {}
    for col in df.columns:
        normalized_key = str(col).strip().lower()
        if normalized_key in BMKG_COLUMN_ALIASES:
            renamed_cols[col] = BMKG_COLUMN_ALIASES[normalized_key]
    df = df.rename(columns=renamed_cols)

    if "observation_date" not in df.columns:
        raise ValueError("Kolom tanggal ('Tanggal' atau 'observation_date') wajib tersedia.")

    if "wmo_id" not in df.columns:
        if default_wmo_id:
            df["wmo_id"] = str(default_wmo_id)
        else:
            raise ValueError("Kolom 'wmo_id' tidak ditemukan dan default_wmo_id tidak diberikan.")

    df["wmo_id"] = df["wmo_id"].astype(str).str.strip()

    parsed_dates = pd.to_datetime(df["observation_date"], dayfirst=True, errors="coerce")
    if parsed_dates.isna().any():
        fallback_dates = pd.to_datetime(df["observation_date"], format="mixed", errors="coerce")
        parsed_dates = parsed_dates.fillna(fallback_dates)

    if int(parsed_dates.isna().sum()) > 0:
        df = df.loc[parsed_dates.notna()].copy()
        parsed_dates = parsed_dates.loc[parsed_dates.notna()]

    df["observation_date"] = parsed_dates.dt.date

    df["is_trace_rainfall"] = False
    df["is_missing_rainfall"] = False

    if "rainfall_mm" in df.columns:
        raw_rr_str = df["rainfall_mm"].astype(str).str.strip().str.lower().str.replace(",", ".", regex=False)
        trace_mask = raw_rr_str.isin(TRACE_TOKENS)
        missing_mask = raw_rr_str.isin(MISSING_TOKENS) | df["rainfall_mm"].isna()

        rr_numeric = pd.to_numeric(raw_rr_str, errors="coerce")
        trace_mask = trace_mask | (rr_numeric == 8888.0)
        missing_mask = missing_mask | (rr_numeric == 9999.0) | (rr_numeric.isna() & ~trace_mask)

        rr_cleaned = rr_numeric.copy()
        rr_cleaned.loc[trace_mask] = 0.0
        rr_cleaned.loc[missing_mask] = np.nan

        df["rainfall_mm"] = rr_cleaned
        df["is_trace_rainfall"] = trace_mask
        df["is_missing_rainfall"] = df["rainfall_mm"].isna()
    else:
        df["rainfall_mm"] = np.nan
        df["is_missing_rainfall"] = True

    numeric_cols = [
        "temp_min_c",
        "temp_max_c",
        "temp_avg_c",
        "humidity_avg_pct",
        "sunshine_hours",
        "wind_speed_max_ms",
        "wind_dir_max_deg",
        "wind_speed_avg_ms",
    ]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = np.nan
            continue
        col_str = df[col].astype(str).str.strip().str.lower().str.replace(",", ".", regex=False)
        num_series = pd.to_numeric(col_str, errors="coerce")
        invalid_code_mask = col_str.isin(MISSING_TOKENS | TRACE_TOKENS) | (num_series.isin([8888.0, 9999.0]))
        num_series.loc[invalid_code_mask] = np.nan
        df[col] = num_series

    if "wind_dir_predominant" in df.columns:
        dir_str = df["wind_dir_predominant"].astype(str).str.strip().str.upper()
        dir_str = dir_str.replace({t.upper(): None for t in (MISSING_TOKENS | TRACE_TOKENS)})
        df["wind_dir_predominant"] = dir_str
    else:
        df["wind_dir_predominant"] = None

    quality_flags: List[str] = []
    for idx, row in df.iterrows():
        flags: List[str] = []

        rr = row["rainfall_mm"]
        if pd.notna(rr) and (rr < 0.0 or rr > 600.0):
            flags.append("ANOMALY_RAINFALL_RANGE")
            df.at[idx, "rainfall_mm"] = np.nan
            df.at[idx, "is_missing_rainfall"] = True

        tn, tavg, tx = row["temp_min_c"], row["temp_avg_c"], row["temp_max_c"]
        for t_col, t_val in [("temp_min_c", tn), ("temp_avg_c", tavg), ("temp_max_c", tx)]:
            if pd.notna(t_val) and not (10.0 <= float(t_val) <= 42.0):
                flags.append(f"OUT_OF_RANGE_{t_col.upper()}")
                df.at[idx, t_col] = np.nan

        tn, tavg, tx = df.at[idx, "temp_min_c"], df.at[idx, "temp_avg_c"], df.at[idx, "temp_max_c"]
        if pd.notna(tn) and pd.notna(tx) and float(tn) > float(tx):
            flags.append("INCONSISTENT_TN_GT_TX")
            df.at[idx, "temp_min_c"] = np.nan
            df.at[idx, "temp_max_c"] = np.nan

        if pd.notna(tavg):
            if (pd.notna(tn) and float(tavg) < float(tn) - 0.5) or (pd.notna(tx) and float(tavg) > float(tx) + 0.5):
                flags.append("INCONSISTENT_TAVG_BOUNDS")

        rh = row["humidity_avg_pct"]
        if pd.notna(rh) and not (10.0 <= float(rh) <= 100.0):
            flags.append("OUT_OF_RANGE_HUMIDITY")
            df.at[idx, "humidity_avg_pct"] = np.nan

        ss = row["sunshine_hours"]
        if pd.notna(ss) and not (0.0 <= float(ss) <= 12.5):
            flags.append("OUT_OF_RANGE_SUNSHINE")
            df.at[idx, "sunshine_hours"] = np.nan

        for w_col in ("wind_speed_max_ms", "wind_speed_avg_ms"):
            w_val = row[w_col]
            if pd.notna(w_val) and not (0.0 <= float(w_val) <= 60.0):
                flags.append(f"OUT_OF_RANGE_{w_col.upper()}")
                df.at[idx, w_col] = np.nan

        quality_flags.append("VALID" if not flags else ";".join(flags))

    df["quality_flag"] = quality_flags
    df["rainfall_category"] = df["rainfall_mm"].apply(classify_bmkg_daily_rainfall)

    df = df.sort_values(["wmo_id", "observation_date"]).drop_duplicates(
        subset=["wmo_id", "observation_date"], keep="last"
    )

    ordered_columns = [
        "wmo_id",
        "observation_date",
        "temp_min_c",
        "temp_max_c",
        "temp_avg_c",
        "humidity_avg_pct",
        "rainfall_mm",
        "is_trace_rainfall",
        "is_missing_rainfall",
        "sunshine_hours",
        "wind_speed_max_ms",
        "wind_dir_max_deg",
        "wind_speed_avg_ms",
        "wind_dir_predominant",
        "rainfall_category",
        "quality_flag",
    ]
    return df[ordered_columns].reset_index(drop=True)
