"""
BMKG Historical Observation CSV/XLSX Importer — ACEH SIAGA CUACA
File: src/data_collection/bmkg_historical_import.py
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.data_processing.data_cleaning import clean_bmkg_observation_dataframe

logger = logging.getLogger("aceh_siaga.bmkg_historical_import")


class BMKGHistoricalImporter:
    """Pipeline untuk memuat, membersihkan, dan mengekspor data observasi historis BMKG."""

    @staticmethod
    def load_file(file_path: Path, default_wmo_id: Optional[str] = None) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File data observasi BMKG tidak ditemukan: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            raw_df = pd.read_csv(path)
        elif suffix in (".xlsx", ".xls"):
            raw_df = pd.read_excel(path)
        else:
            raise ValueError(f"Format file '{suffix}' tidak didukung. Gunakan .csv atau .xlsx.")

        cleaned_df = clean_bmkg_observation_dataframe(raw_df, default_wmo_id=default_wmo_id)
        cleaned_df["source_file"] = path.name
        return cleaned_df

    @staticmethod
    def generate_demo_dataset(output_path: Path = Path("data/demo/demo_bmkg_historical_aceh.csv")) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rng = np.random.default_rng(seed=20261118)
        dates = pd.date_range("2021-01-01", "2026-10-31", freq="D")
        stations = [
            ("96001", 27.2, 1.0),
            ("96002", 27.5, 1.1),
            ("96003", 26.8, 1.05),
            ("96009", 27.4, 0.9),
            ("96011", 26.9, 1.35),
        ]

        rows = []
        for wmo_id, base_temp, rain_multiplier in stations:
            for d in dates:
                doy = d.dayofyear
                seasonal_factor = (
                    1.0
                    + 0.65 * np.cos(2 * np.pi * (doy - 320) / 365.25)
                    + 0.35 * np.cos(2 * np.pi * (doy - 115) / 365.25)
                )
                rain_prob = min(0.75, max(0.18, 0.32 * seasonal_factor))

                u = rng.random()
                if u < 0.015:
                    rr_val = 9999.0
                elif u < 0.08:
                    rr_val = 8888.0
                elif rng.random() < rain_prob:
                    gamma_rain = rng.gamma(shape=1.15, scale=14.0 * seasonal_factor * rain_multiplier)
                    rr_val = round(min(280.0, float(gamma_rain)), 1)
                else:
                    rr_val = 0.0

                is_rainy = rr_val not in (0.0, 8888.0, 9999.0)
                t_avg = round(base_temp - (0.8 if is_rainy else 0.0) + float(rng.normal(0, 0.7)), 1)
                t_min = round(t_avg - abs(float(rng.normal(3.4, 0.6))), 1)
                t_max = round(t_avg + abs(float(rng.normal(4.1, 0.7))), 1)
                rh_avg = round(min(99.0, max(62.0, 79.0 + (8.5 if is_rainy else -3.0) + float(rng.normal(0, 4.0)))), 1)
                ss = round(max(0.0, min(11.5, (4.2 if is_rainy else 8.1) + float(rng.normal(0, 1.5)))), 1)
                ff_avg = round(max(0.5, float(rng.gamma(2.2, 1.1))), 1)
                ff_x = round(ff_avg + abs(float(rng.normal(3.5, 1.4))), 1)
                ddd_x = int(rng.integers(0, 360))
                ddd_car = str(rng.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]))

                rows.append(
                    {
                        "wmo_id": wmo_id,
                        "Tanggal": d.strftime("%d-%m-%Y"),
                        "Tn": t_min,
                        "Tx": t_max,
                        "Tavg": t_avg,
                        "RH_avg": rh_avg,
                        "RR": rr_val,
                        "ss": ss,
                        "ff_x": ff_x,
                        "ddd_x": ddd_x,
                        "ff_avg": ff_avg,
                        "ddd_car": ddd_car,
                        "data_mode": "DEMO_SYNTHETIC_DO_NOT_CLAIM_AS_OFFICIAL_OBSERVATION",
                    }
                )

        demo_df = pd.DataFrame(rows)
        demo_df.to_csv(output_path, index=False)
        return output_path
