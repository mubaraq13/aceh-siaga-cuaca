"""
BPBA Aceh & BNPB DIBI Disaster Event Importer — ACEH SIAGA CUACA
File: src/data_collection/disaster_import.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

VALID_DISASTER_TYPES: Dict[str, str] = {
    "banjir bandang": "BANJIR_BANDANG",
    "gelombang pasang": "GELOMBANG_PASANG_ABRASI",
    "tanah longsor": "TANAH_LONGSOR",
    "angin kencang": "ANGIN_KENCANG",
    "puting beliung": "CUACA_EKSTREM",
    "cuaca ekstrem": "CUACA_EKSTREM",
    "kekeringan": "KEKERINGAN",
    "longsor": "TANAH_LONGSOR",
    "abrasi": "GELOMBANG_PASANG_ABRASI",
    "banjir": "BANJIR",
}


class DisasterDataImporter:
    """Importer dan validator CSV/XLSX data bencana hidrometeorologi Provinsi Aceh."""

    @staticmethod
    def normalize_disaster_type(raw_type: str) -> str:
        cleaned = str(raw_type).strip().lower()
        for key, canonical in sorted(
            VALID_DISASTER_TYPES.items(), key=lambda item: len(item[0]), reverse=True
        ):
            if key in cleaned:
                return canonical
        return "CUACA_EKSTREM"

    @classmethod
    def clean_disaster_dataframe(cls, df_raw: pd.DataFrame) -> pd.DataFrame:
        if df_raw.empty:
            raise ValueError("DataFrame bencana kosong.")

        df = df_raw.copy()
        col_map = {c.strip().lower(): c for c in df.columns}

        required = {"event_code", "region_code", "disaster_type", "event_date"}
        missing = required - set(col_map.keys())
        if missing:
            raise ValueError(f"Kolom wajib data bencana tidak lengkap: {missing}")

        df = df.rename(columns={col_map[k]: k for k in col_map})
        df["event_code"] = df["event_code"].astype(str).str.strip()
        df["region_code"] = df["region_code"].astype(str).str.strip()
        df = df[df["region_code"].str.startswith("11.")].copy()

        df["disaster_type"] = df["disaster_type"].apply(cls.normalize_disaster_type)
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce").dt.date
        df = df[df["event_date"].notna()].copy()

        impact_cols: List[str] = [
            "casualties_dead",
            "casualties_missing",
            "casualties_injured",
            "affected_people",
            "displaced_people",
            "houses_heavily_damaged",
            "houses_moderately_damaged",
            "houses_lightly_damaged",
            "houses_submerged",
            "public_facilities_damaged",
        ]
        for col in impact_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0).astype(int)

        df = df.sort_values("event_date").drop_duplicates(subset=["event_code"], keep="last")
        return df.reset_index(drop=True)

    @classmethod
    def import_file(cls, file_path: Path) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File data bencana tidak ditemukan: {path}")
        raw_df = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
        return cls.clean_disaster_dataframe(raw_df)