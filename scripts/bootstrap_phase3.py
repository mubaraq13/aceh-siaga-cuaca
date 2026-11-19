#!/usr/bin/env python3
"""
Phase 3 Automated File Builder — ACEH SIAGA CUACA
Membangun seluruh modul Feature Engineering, Model Training, Walk-Forward Evaluation,
Jupyter Notebooks (05-07), dan Unit Tests untuk Phase 3.
Jalankan dengan: python scripts\bootstrap_phase3.py
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FILES: dict[str, str] = {}

# ==============================================================================
# 1. src/machine_learning/feature_engineering.py
# ==============================================================================
FILES["src/machine_learning/feature_engineering.py"] = '''"""
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
'''

# ==============================================================================
# 2. src/machine_learning/model_evaluation.py
# ==============================================================================
FILES["src/machine_learning/model_evaluation.py"] = '''"""
Machine Learning Evaluation Metrics & Threshold Optimizer — ACEH SIAGA CUACA
File: src/machine_learning/model_evaluation.py

Mencakup:
- Metrik Regresi: MAE, RMSE, R2, dan Skill Score terhadap Baseline.
- Metrik Klasifikasi Data Tidak Seimbang: Precision, Recall, F1-Score, PR-AUC, Confusion Matrix.
- Penentuan ambang probabilitas optimal (Threshold Tuning) pada Validation Set.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


def evaluate_regression_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    baseline_rmse: float | None = None,
) -> Dict[str, Any]:
    """Menghitung MAE, RMSE, R2, dan persentase peningkatan terhadap baseline."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.clip(np.asarray(y_pred, dtype=float), a_min=0.0, a_max=None)

    mae = float(mean_absolute_error(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    r2 = float(r2_score(y_t, y_p))

    skill_pct = None
    if baseline_rmse is not None and baseline_rmse > 0:
        skill_pct = round(((baseline_rmse - rmse) / baseline_rmse) * 100.0, 2)

    return {
        "MAE_mm": round(mae, 3),
        "RMSE_mm": round(rmse, 3),
        "R2_score": round(r2, 4),
        "skill_vs_baseline_pct": skill_pct,
    }


def optimize_probability_threshold(y_val_true: np.ndarray, y_val_prob: np.ndarray) -> float:
    """
    Mencari ambang batas probabilitas (threshold) pada Validation Set yang memaksimalkan F1-Score
    untuk menangani ketimpangan kelas (class imbalance) kejadian cuaca ekstrem.
    """
    y_t = np.asarray(y_val_true, dtype=int)
    y_p = np.asarray(y_val_prob, dtype=float)

    if int(y_t.sum()) == 0:
        return 0.50

    best_th = 0.50
    best_f1 = -1.0
    for th in np.linspace(0.10, 0.85, 76):
        preds = (y_p >= th).astype(int)
        score = float(f1_score(y_t, preds, zero_division=0))
        if score > best_f1:
            best_f1 = score
            best_th = float(th)
    return round(best_th, 3)


def evaluate_classification_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Menghitung Precision, Recall, F1-Score, PR-AUC, dan Confusion Matrix.
    Tidak hanya mengandalkan accuracy karena kejadian hujan ekstrem bersifat imbalanced.
    """
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.asarray(y_prob, dtype=float)
    y_hat = (y_p >= threshold).astype(int)

    prec = float(precision_score(y_t, y_hat, zero_division=0))
    rec = float(recall_score(y_t, y_hat, zero_division=0))
    f1 = float(f1_score(y_t, y_hat, zero_division=0))
    pr_auc = float(average_precision_score(y_t, y_p)) if int(y_t.sum()) > 0 else 0.0

    cm = confusion_matrix(y_t, y_hat, labels=[0, 1])
    tn, fp, fn, tp = (int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1]))

    return {
        "decision_threshold": round(float(threshold), 3),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "positive_support": int(y_t.sum()),
        "total_samples": int(len(y_t)),
        "confusion_matrix": {
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "true_positive": tp,
        },
    }
'''

# ==============================================================================
# 3. src/machine_learning/model_trainer.py
# ==============================================================================
FILES["src/machine_learning/model_trainer.py"] = '''"""
Multi-Model Training, Walk-Forward CV & Artifact Registry — ACEH SIAGA CUACA
File: src/machine_learning/model_trainer.py

Membandingkan 5 keluarga algoritma sesuai Bagian 10 Master Prompt:
1. Baseline Climatology & Persistence.
2. Linear Regression (Ridge) / Logistic Regression.
3. Random Forest (Regressor & Balanced Classifier).
4. XGBoost (atau HistGradientBoosting fallback otomatis jika wheel XGBoost belum terpasang).
5. Sequence Auto-Regressive Neural Network (Temporal Lag MLP / LSTM equivalent untuk Python 3.14).

Seluruh prediksi model diberi label wajib:
"Analisis model eksperimental, bukan peringatan resmi BMKG."
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.data_processing.data_cleaning import classify_bmkg_daily_rainfall
from src.geospatial.aceh_gis_analyzer import ACEH_STATIONS_GIS
from src.machine_learning.feature_engineering import (
    FEATURE_COLUMNS,
    build_supervised_dataset,
    chronological_train_val_test_split,
)
from src.machine_learning.model_evaluation import (
    evaluate_classification_predictions,
    evaluate_regression_predictions,
    optimize_probability_threshold,
)

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    xgb = None
    HAS_XGBOOST = False

logger = logging.getLogger("aceh_siaga.model_trainer")
WIB_TZ = ZoneInfo("Asia/Jakarta")
MANDATORY_ML_DISCLAIMER = "Analisis model eksperimental, bukan peringatan resmi BMKG."


class AcehExtremeWeatherTrainer:
    """Pipeline pelatihan, validasi deret waktu, dan penyimpanan model prediksi cuaca Aceh."""

    def __init__(
        self,
        model_dir: Path = Path("models/trained"),
        eval_dir: Path = Path("models/evaluation"),
        dataset_version: str = "aceh_obs_v2026.11",
        model_version: str = "v1.0.0-exp",
    ) -> None:
        self.model_dir = Path(model_dir)
        self.eval_dir = Path(eval_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_version = dataset_version
        self.model_version = model_version

    @staticmethod
    def _build_regression_candidates() -> Dict[str, Pipeline]:
        candidates: Dict[str, Pipeline] = {
            "Linear_Ridge_Regression": Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("model", Ridge(alpha=10.0, random_state=42)),
                ]
            ),
            "Random_Forest_Regressor": Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=160,
                            max_depth=10,
                            min_samples_leaf=5,
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
        }

        if HAS_XGBOOST and xgb is not None:
            candidates["XGBoost_Regressor"] = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        xgb.XGBRegressor(
                            n_estimators=180,
                            max_depth=5,
                            learning_rate=0.04,
                            subsample=0.85,
                            colsample_bytree=0.85,
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            )
        else:
            candidates["XGBoost_HistGB_Regressor"] = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            max_iter=180,
                            max_depth=6,
                            learning_rate=0.04,
                            min_samples_leaf=15,
                            random_state=42,
                        ),
                    ),
                ]
            )

        candidates["Sequence_Lag_NeuralNet_Regressor"] = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    MLPRegressor(
                        hidden_layer_sizes=(64, 32),
                        activation="relu",
                        alpha=0.1,
                        max_iter=250,
                        early_stopping=True,
                        random_state=42,
                    ),
                ),
            ]
        )
        return candidates

    @staticmethod
    def _build_classification_candidates(pos_weight: float) -> Dict[str, Pipeline]:
        candidates: Dict[str, Pipeline] = {
            "Logistic_Regression_Balanced": Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        LogisticRegression(
                            class_weight="balanced",
                            C=0.5,
                            max_iter=500,
                            random_state=42,
                        ),
                    ),
                ]
            ),
            "Random_Forest_Classifier": Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        RandomForestClassifier(
                            n_estimators=200,
                            max_depth=10,
                            min_samples_leaf=4,
                            class_weight="balanced_subsample",
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
        }

        if HAS_XGBOOST and xgb is not None:
            candidates["XGBoost_Classifier"] = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        xgb.XGBClassifier(
                            n_estimators=180,
                            max_depth=5,
                            learning_rate=0.04,
                            subsample=0.85,
                            colsample_bytree=0.85,
                            scale_pos_weight=max(1.0, pos_weight),
                            eval_metric="logloss",
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            )
        else:
            candidates["XGBoost_HistGB_Classifier"] = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        HistGradientBoostingClassifier(
                            max_iter=180,
                            max_depth=6,
                            learning_rate=0.04,
                            class_weight="balanced",
                            random_state=42,
                        ),
                    ),
                ]
            )

        candidates["Sequence_Lag_NeuralNet_Classifier"] = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    MLPClassifier(
                        hidden_layer_sizes=(64, 32),
                        activation="relu",
                        alpha=0.1,
                        max_iter=250,
                        early_stopping=True,
                        random_state=42,
                    ),
                ),
            ]
        )
        return candidates

    @staticmethod
    def _run_walk_forward_cv(
        df_train_val: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
        n_splits: int = 5,
    ) -> Dict[str, float]:
        """Menjalankan Time-Series Walk-Forward Cross Validation pada model Random Forest."""
        tscv = TimeSeriesSplit(n_splits=n_splits)
        X = df_train_val[feature_cols].to_numpy()
        y = df_train_val[target_col].to_numpy()

        fold_pr_aucs: List[float] = []
        fold_f1s: List[float] = []

        for train_idx, val_idx in tscv.split(X):
            X_tr, y_tr = X[train_idx], y[train_idx]
            X_va, y_va = X[val_idx], y[val_idx]
            if int(y_tr.sum()) < 2 or int(y_va.sum()) < 1:
                continue

            pipe = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "model",
                        RandomForestClassifier(
                            n_estimators=100,
                            max_depth=8,
                            class_weight="balanced_subsample",
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            )
            pipe.fit(X_tr, y_tr)
            probs = pipe.predict_proba(X_va)[:, 1]
            th = optimize_probability_threshold(y_va, probs)
            metrics = evaluate_classification_predictions(y_va, probs, threshold=th)
            fold_pr_aucs.append(metrics["pr_auc"])
            fold_f1s.append(metrics["f1_score"])

        return {
            "cv_folds": n_splits,
            "mean_walk_forward_pr_auc": round(float(np.mean(fold_pr_aucs)), 4) if fold_pr_aucs else 0.0,
            "mean_walk_forward_f1": round(float(np.mean(fold_f1s)), 4) if fold_f1s else 0.0,
        }

    def train_and_evaluate_all(
        self,
        df_cleaned: pd.DataFrame,
        extreme_threshold_mm: float = 20.0,
    ) -> Dict[str, Any]:
        """
        Melatih seluruh model regresi dan klasifikasi, membandingkan dengan Baseline Persistence &
        Climatology, menyimpan model terbaik beserta feature importance dan hasil prediksi terbaru.
        """
        df_sup = build_supervised_dataset(
            df_cleaned,
            extreme_threshold_mm=50.0,
            moderate_threshold_mm=extreme_threshold_mm,
            drop_missing_target=True,
        )
        train_df, val_df, test_df = chronological_train_val_test_split(df_sup)

        X_train = train_df[FEATURE_COLUMNS]
        X_val = val_df[FEATURE_COLUMNS]
        X_test = test_df[FEATURE_COLUMNS]

        y_reg_train = train_df["target_rain_next_day_mm"].to_numpy(dtype=float)
        y_reg_val = val_df["target_rain_next_day_mm"].to_numpy(dtype=float)
        y_reg_test = test_df["target_rain_next_day_mm"].to_numpy(dtype=float)

        # Gunakan target_is_heavy_20mm (>=20mm: Hujan Sedang-Ekstrem) dan target_is_extreme_50mm (>=50mm)
        target_cls_col = (
            "target_is_extreme_50mm"
            if int(test_df["target_is_extreme_50mm"].sum()) >= 10
            else "target_is_heavy_20mm"
        )
        active_threshold_mm = 50.0 if target_cls_col == "target_is_extreme_50mm" else 20.0

        y_cls_train = train_df[target_cls_col].to_numpy(dtype=int)
        y_cls_val = val_df[target_cls_col].to_numpy(dtype=int)
        y_cls_test = test_df[target_cls_col].to_numpy(dtype=int)

        # ---------------------------------------------------------------------
        # A. EVALUASI BASELINE REGRESI (Persistence & Seasonal Climatology)
        # ---------------------------------------------------------------------
        persistence_reg_pred = test_df["rain_lag_0"].fillna(0.0).to_numpy(dtype=float)
        clim_lookup = (
            train_df.groupby(["wmo_id", "month_num"])["target_rain_next_day_mm"]
            .mean()
            .to_dict()
        )
        global_train_mean = float(np.mean(y_reg_train))
        climatology_reg_pred = np.array(
            [
                clim_lookup.get((row["wmo_id"], row["month_num"]), global_train_mean)
                for _, row in test_df.iterrows()
            ],
            dtype=float,
        )

        baseline_persistence_reg = evaluate_regression_predictions(y_reg_test, persistence_reg_pred)
        baseline_climatology_reg = evaluate_regression_predictions(
            y_reg_test,
            climatology_reg_pred,
            baseline_rmse=baseline_persistence_reg["RMSE_mm"],
        )
        ref_baseline_rmse = min(
            baseline_persistence_reg["RMSE_mm"],
            baseline_climatology_reg["RMSE_mm"],
        )

        # ---------------------------------------------------------------------
        # B. PELATIHAN & KOMPARASI MODEL REGRESI (dengan log1p target transform)
        # ---------------------------------------------------------------------
        reg_results: Dict[str, Dict[str, Any]] = {
            "Baseline_Persistence": baseline_persistence_reg,
            "Baseline_Seasonal_Climatology": baseline_climatology_reg,
        }
        best_reg_name = "Baseline_Seasonal_Climatology"
        best_reg_rmse = ref_baseline_rmse
        best_reg_pipeline: Pipeline | None = None

        y_reg_train_log = np.log1p(y_reg_train)
        for name, pipe in self._build_regression_candidates().items():
            pipe.fit(X_train, y_reg_train_log)
            pred_log_val = pipe.predict(X_val)
            pred_log_test = pipe.predict(X_test)

            # Koreksi faktor skala smearing Duan / kalibrasi rata-rata pada validation set
            raw_val_mm = np.expm1(np.clip(pred_log_val, 0.0, 6.5))
            scale_factor = float(np.mean(y_reg_val) / max(np.mean(raw_val_mm), 1e-3))
            scale_factor = float(np.clip(scale_factor, 0.6, 1.8))

            pred_test_mm = np.expm1(np.clip(pred_log_test, 0.0, 6.5)) * scale_factor
            metrics = evaluate_regression_predictions(
                y_reg_test,
                pred_test_mm,
                baseline_rmse=ref_baseline_rmse,
            )
            metrics["calibration_scale_factor"] = round(scale_factor, 4)
            reg_results[name] = metrics

            if metrics["RMSE_mm"] < best_reg_rmse or best_reg_pipeline is None:
                best_reg_rmse = metrics["RMSE_mm"]
                best_reg_name = name
                best_reg_pipeline = pipe

        # ---------------------------------------------------------------------
        # C. EVALUASI BASELINE & PELATIHAN MODEL KLASIFIKASI HUJAN EKSTREM
        # ---------------------------------------------------------------------
        persistence_cls_prob = (test_df["rain_lag_0"].fillna(0.0) >= active_threshold_mm).astype(float).to_numpy()
        clim_prob_lookup = (
            train_df.groupby(["wmo_id", "month_num"])[target_cls_col]
            .mean()
            .to_dict()
        )
        base_rate = float(np.mean(y_cls_train))
        climatology_cls_prob = np.array(
            [
                clim_prob_lookup.get((row["wmo_id"], row["month_num"]), base_rate)
                for _, row in test_df.iterrows()
            ],
            dtype=float,
        )

        cls_results: Dict[str, Dict[str, Any]] = {
            "Baseline_Persistence": evaluate_classification_predictions(
                y_cls_test, persistence_cls_prob, threshold=0.5
            ),
            "Baseline_Seasonal_Climatology": evaluate_classification_predictions(
                y_cls_test, climatology_cls_prob, threshold=max(0.15, round(base_rate * 1.5, 2))
            ),
        }

        pos_count = max(1, int(y_cls_train.sum()))
        neg_count = max(1, len(y_cls_train) - pos_count)
        pos_weight = float(neg_count / pos_count)

        best_cls_name = ""
        best_cls_f1 = -1.0
        best_cls_threshold = 0.50
        best_cls_pipeline: Pipeline | None = None

        for name, pipe in self._build_classification_candidates(pos_weight=pos_weight).items():
            pipe.fit(X_train, y_cls_train)
            val_probs = pipe.predict_proba(X_val)[:, 1]
            opt_th = optimize_probability_threshold(y_cls_val, val_probs)

            test_probs = pipe.predict_proba(X_test)[:, 1]
            metrics = evaluate_classification_predictions(y_cls_test, test_probs, threshold=opt_th)
            cls_results[name] = metrics

            if metrics["f1_score"] > best_cls_f1 or best_cls_pipeline is None:
                best_cls_f1 = metrics["f1_score"]
                best_cls_name = name
                best_cls_threshold = opt_th
                best_cls_pipeline = pipe

        # ---------------------------------------------------------------------
        # D. WALK-FORWARD VALIDATION & EKSTRAKSI FEATURE IMPORTANCE
        # ---------------------------------------------------------------------
        train_val_df = pd.concat([train_df, val_df], ignore_index=True)
        walk_forward_summary = self._run_walk_forward_cv(
            train_val_df, FEATURE_COLUMNS, target_cls_col, n_splits=5
        )

        # Ekstrak Feature Importance dari Random Forest Classifier untuk interpretabilitas
        rf_cls_pipe = self._build_classification_candidates(pos_weight)["Random_Forest_Classifier"]
        rf_cls_pipe.fit(X_train, y_cls_train)
        rf_estimator = rf_cls_pipe.named_steps["model"]
        importances = rf_estimator.feature_importances_

        feature_importance_list: List[Dict[str, Any]] = [
            {"feature": feat, "importance": round(float(imp), 5)}
            for feat, imp in sorted(
                zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True
            )
        ]

        # ---------------------------------------------------------------------
        # E. SIMPAN MODEL TERBAIK & HASIL PREDIKSI EKSPERIMENTAL 5 STASIUN ACEH
        # ---------------------------------------------------------------------
        trained_at_wib = datetime.now(WIB_TZ).isoformat()
        if best_reg_pipeline is not None:
            joblib.dump(best_reg_pipeline, self.model_dir / "best_rainfall_regressor.joblib")
        if best_cls_pipeline is not None:
            joblib.dump(best_cls_pipeline, self.model_dir / "best_extreme_classifier.joblib")

        # Buat prediksi H+1 pada observasi terakhir tiap stasiun BMKG Aceh
        latest_predictions: List[Dict[str, Any]] = []
        station_meta_by_wmo = {s["wmo_id"]: s for s in ACEH_STATIONS_GIS}

        latest_per_station = df_sup.sort_values("obs_dt").groupby("wmo_id").tail(1)
        for _, row in latest_per_station.iterrows():
            wmo = str(row["wmo_id"])
            st_info = station_meta_by_wmo.get(wmo, {"station_name": f"Stasiun {wmo}", "region_code": "11.06"})
            X_single = pd.DataFrame([row[FEATURE_COLUMNS]])

            pred_rain_mm = 0.0
            if best_reg_pipeline is not None:
                scale = reg_results.get(best_reg_name, {}).get("calibration_scale_factor", 1.0)
                pred_rain_mm = float(np.expm1(np.clip(best_reg_pipeline.predict(X_single)[0], 0.0, 6.5)) * scale)
                pred_rain_mm = round(max(0.0, pred_rain_mm), 2)

            pred_prob = 0.0
            if best_cls_pipeline is not None:
                pred_prob = round(float(best_cls_pipeline.predict_proba(X_single)[0, 1]), 4)

            pred_category = classify_bmkg_daily_rainfall(pred_rain_mm)
            if pred_prob >= best_cls_threshold and pred_category in ("NO_RAIN", "LIGHT"):
                pred_category = "MODERATE" if active_threshold_mm == 20.0 else "HEAVY"

            latest_predictions.append(
                {
                    "wmo_id": wmo,
                    "station_name": st_info["station_name"],
                    "region_code": st_info["region_code"],
                    "last_observation_date": str(pd.to_datetime(row["obs_dt"]).date()),
                    "target_prediction_date": str(pd.to_datetime(row["target_date"]).date()),
                    "horizon_days": 1,
                    "predicted_rainfall_mm": pred_rain_mm,
                    "predicted_extreme_probability": pred_prob,
                    "decision_threshold": best_cls_threshold,
                    "is_potential_heavy_rain": bool(pred_prob >= best_cls_threshold),
                    "predicted_category": pred_category,
                    "regression_model_used": best_reg_name,
                    "classification_model_used": best_cls_name,
                    "model_version": self.model_version,
                    "dataset_version": self.dataset_version,
                    "predicted_at_wib": trained_at_wib,
                    "top_contributing_features": feature_importance_list[:5],
                    "is_experimental": True,
                    "disclaimer_label": MANDATORY_ML_DISCLAIMER,
                }
            )

        evaluation_payload: Dict[str, Any] = {
            "project_name": "ACEH SIAGA CUACA",
            "trained_at_wib": trained_at_wib,
            "dataset_version": self.dataset_version,
            "model_version": self.model_version,
            "mandatory_disclaimer": MANDATORY_ML_DISCLAIMER,
            "split_summary": {
                "split_method": "Chronological Time-Series Split (Zero Future Data Leakage)",
                "train_rows": len(train_df),
                "train_period": f"{train_df['obs_dt'].min().date()} s.d. {train_df['obs_dt'].max().date()}",
                "val_rows": len(val_df),
                "val_period": f"{val_df['obs_dt'].min().date()} s.d. {val_df['obs_dt'].max().date()}",
                "test_rows": len(test_df),
                "test_period": f"{test_df['obs_dt'].min().date()} s.d. {test_df['obs_dt'].max().date()}",
                "classification_target_column": target_cls_col,
                "classification_threshold_mm": active_threshold_mm,
            },
            "best_models": {
                "best_regression_model": best_reg_name,
                "best_regression_test_rmse_mm": best_reg_rmse,
                "best_classification_model": best_cls_name,
                "best_classification_test_f1": best_cls_f1,
                "optimal_probability_threshold": best_cls_threshold,
            },
            "walk_forward_cv_summary": walk_forward_summary,
            "regression_comparison": reg_results,
            "classification_comparison": cls_results,
            "feature_importance_top15": feature_importance_list[:15],
            "model_limitations": [
                "Model dilatih pada titik lokasi 5 stasiun pengamatan BMKG Aceh dan merepresentasikan dinamika cuaca lokal stasiun, bukan pengganti model NWP/satelit BMKG.",
                "Curah hujan tropis konvektif memiliki variabilitas stokastik harian yang tinggi sehingga prediksi digunakan sebagai indikator kewaspadaan dini pendamping, bukan peringatan resmi.",
                MANDATORY_ML_DISCLAIMER,
            ],
        }

        (self.eval_dir / "model_evaluation_report.json").write_text(
            json.dumps(evaluation_payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.eval_dir / "latest_station_predictions.json").write_text(
            json.dumps(latest_predictions, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        pd.DataFrame(feature_importance_list).to_csv(
            self.eval_dir / "feature_importance.csv", index=False
        )

        return {
            "evaluation_report": evaluation_payload,
            "latest_predictions": latest_predictions,
        }
'''

# ==============================================================================
# 4. Helper pembentuk 3 Jupyter Notebooks Phase 3 (05, 06, 07)
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


FILES["notebooks/05_feature_engineering.ipynb"] = make_notebook(
    "05 — Leakage-Free Spatio-Temporal Feature Engineering",
    "Notebook ini membangun 36 fitur prediktor meteorologi (lag rainfall, rolling window 3/7/14 hari, interaksi suhu-kelembapan, vektor angin zonal/meridional, dan fitur siklikal waktu) tanpa kebocoran data masa depan.",
    [
        """import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()))

import pandas as pd
from src.machine_learning.feature_engineering import (
    FEATURE_COLUMNS,
    build_supervised_dataset,
    chronological_train_val_test_split,
)""",
        """df_clean = pd.read_csv("data/processed/cleaned_weather_observations_aceh.csv")
df_sup = build_supervised_dataset(df_clean)
train_df, val_df, test_df = chronological_train_val_test_split(df_sup)

print(f"Total fitur prediktor: {len(FEATURE_COLUMNS)}")
print(f"Train Set : {len(train_df)} baris ({train_df['obs_dt'].min()} s.d. {train_df['obs_dt'].max()})")
print(f"Val Set   : {len(val_df)} baris ({val_df['obs_dt'].min()} s.d. {val_df['obs_dt'].max()})")
print(f"Test Set  : {len(test_df)} baris ({test_df['obs_dt'].min()} s.d. {test_df['obs_dt'].max()})")""",
    ],
)

FILES["notebooks/06_machine_learning.ipynb"] = make_notebook(
    "06 — Machine Learning Training & Baseline Comparison",
    "Notebook ini melatih model Baseline (Persistence & Climatology), Linear/Logistic Regression, Random Forest, XGBoost/HistGB, dan Sequence Neural Network untuk prediksi curah hujan ekstrem di Provinsi Aceh.",
    [
        """import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()))

import pandas as pd
from src.machine_learning.model_trainer import AcehExtremeWeatherTrainer""",
        """df_clean = pd.read_csv("data/processed/cleaned_weather_observations_aceh.csv")
trainer = AcehExtremeWeatherTrainer()
results = trainer.train_and_evaluate_all(df_clean)
print("Model Terbaik:", results["evaluation_report"]["best_models"])""",
    ],
)

FILES["notebooks/07_model_evaluation.ipynb"] = make_notebook(
    "07 — Model Evaluation, Feature Importance & Experimental Predictions",
    "Notebook ini mengevaluasi metrik regresi (MAE, RMSE, R2) dan klasifikasi data tidak seimbang (Precision, Recall, F1, PR-AUC, Confusion Matrix) serta menampilkan 15 fitur paling berpengaruh.",
    [
        """import json
from pathlib import Path
import pandas as pd

eval_report = json.loads(Path("models/evaluation/model_evaluation_report.json").read_text(encoding="utf-8"))
print("=== KOMPARASI MODEL KLASIFIKASI POTENSI HUJAN LEBAT ===")
print(pd.DataFrame(eval_report["classification_comparison"]).T.to_string())""",
        """print("=== TOP 15 FEATURE IMPORTANCE ===")
print(pd.DataFrame(eval_report["feature_importance_top15"]).to_string(index=False))""",
    ],
)

# ==============================================================================
# 5. tests/test_phase3_machine_learning.py
# ==============================================================================
FILES["tests/test_phase3_machine_learning.py"] = '''"""
Unit Tests for PHASE 3 — MACHINE LEARNING (ACEH SIAGA CUACA)
File: tests/test_phase3_machine_learning.py
Jalankan dengan: python -m pytest tests\\test_phase3_machine_learning.py -v
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter
from src.machine_learning.feature_engineering import (
    FEATURE_COLUMNS,
    build_supervised_dataset,
    chronological_train_val_test_split,
)
from src.machine_learning.model_evaluation import (
    evaluate_classification_predictions,
    evaluate_regression_predictions,
    optimize_probability_threshold,
)
from src.machine_learning.model_trainer import (
    MANDATORY_ML_DISCLAIMER,
    AcehExtremeWeatherTrainer,
)


def _load_or_create_cleaned_data(tmp_path: Path) -> pd.DataFrame:
    processed_csv = Path("data/processed/cleaned_weather_observations_aceh.csv")
    if processed_csv.exists():
        return pd.read_csv(processed_csv)
    demo_csv = BMKGHistoricalImporter.generate_demo_dataset(tmp_path / "demo_obs.csv")
    return BMKGHistoricalImporter.load_file(demo_csv)


def test_supervised_feature_engineering_has_zero_future_leakage() -> None:
    # Buat deret waktu sintetis 20 hari dengan lonjakan hujan ekstrem hanya pada hari terakhir (hari ke-20)
    dates = pd.date_range("2026-01-01", periods=20, freq="D")
    rain_values = [2.0] * 19 + [250.0]  # Hari ke-20 hujan 250 mm
    df_raw = pd.DataFrame(
        {
            "wmo_id": ["96001"] * 20,
            "observation_date": dates.strftime("%Y-%m-%d"),
            "temp_min_c": [23.0] * 20,
            "temp_max_c": [31.0] * 20,
            "temp_avg_c": [27.0] * 20,
            "humidity_avg_pct": [85.0] * 20,
            "rainfall_mm": rain_values,
            "is_trace_rainfall": [False] * 20,
            "is_missing_rainfall": [False] * 20,
            "sunshine_hours": [6.0] * 20,
            "wind_speed_max_ms": [7.0] * 20,
            "wind_dir_max_deg": [180.0] * 20,
            "wind_speed_avg_ms": [3.0] * 20,
            "wind_dir_predominant": ["S"] * 20,
            "rainfall_category": ["LIGHT"] * 19 + ["EXTREME"],
            "quality_flag": ["VALID"] * 20,
        }
    )

    sup_df = build_supervised_dataset(df_raw)
    # Baris terakhir di sup_df adalah pengamatan hari ke-19 (2026-01-19) yang memprediksi target hari ke-20 (250 mm)
    last_row = sup_df.iloc[-1]
    assert last_row["target_rain_next_day_mm"] == 250.0
    assert last_row["target_is_extreme_50mm"] == 1
    # Verifikasi TIDAK ADA fitur pada hari ke-19 yang bocor memuat angka 250.0 dari hari ke-20!
    assert last_row["rain_lag_0"] == 2.0
    assert last_row["rain_roll_max_7d"] == 2.0
    assert last_row["rain_roll_sum_7d"] == 14.0


def test_chronological_split_strictly_orders_time(tmp_path: Path) -> None:
    df_clean = _load_or_create_cleaned_data(tmp_path)
    df_sup = build_supervised_dataset(df_clean)
    train_df, val_df, test_df = chronological_train_val_test_split(df_sup)

    assert len(train_df) > len(val_df) > 0
    assert len(test_df) > 0
    assert train_df["obs_dt"].max() < val_df["obs_dt"].min()
    assert val_df["obs_dt"].max() < test_df["obs_dt"].min()


def test_evaluation_metrics_and_threshold_optimizer() -> None:
    y_true_reg = np.array([0.0, 10.0, 50.0, 100.0])
    y_pred_reg = np.array([1.0, 12.0, 45.0, 90.0])
    reg_m = evaluate_regression_predictions(y_true_reg, y_pred_reg, baseline_rmse=15.0)
    assert reg_m["MAE_mm"] > 0.0
    assert reg_m["RMSE_mm"] < 15.0
    assert reg_m["skill_vs_baseline_pct"] > 0.0

    y_true_cls = np.array([0, 0, 0, 0, 1, 1])
    y_prob_cls = np.array([0.05, 0.10, 0.22, 0.30, 0.42, 0.85])
    opt_th = optimize_probability_threshold(y_true_cls, y_prob_cls)
    cls_m = evaluate_classification_predictions(y_true_cls, y_prob_cls, threshold=opt_th)
    assert cls_m["f1_score"] >= 0.8
    assert cls_m["pr_auc"] >= 0.8


def test_end_to_end_model_trainer_and_mandatory_disclaimer(tmp_path: Path) -> None:
    df_clean = _load_or_create_cleaned_data(tmp_path)
    # Gunakan subset 2 tahun terakhir agar unit test berjalan cepat (< 4 detik)
    df_clean["obs_dt"] = pd.to_datetime(df_clean["observation_date"])
    df_sub = df_clean[df_clean["obs_dt"] >= "2024-01-01"].copy()

    trainer = AcehExtremeWeatherTrainer(
        model_dir=tmp_path / "trained",
        eval_dir=tmp_path / "evaluation",
    )
    output = trainer.train_and_evaluate_all(df_sub)

    assert (tmp_path / "trained" / "best_rainfall_regressor.joblib").exists()
    assert (tmp_path / "trained" / "best_extreme_classifier.joblib").exists()
    assert (tmp_path / "evaluation" / "model_evaluation_report.json").exists()
    assert (tmp_path / "evaluation" / "latest_station_predictions.json").exists()

    preds = output["latest_predictions"]
    assert len(preds) == 5
    for p in preds:
        assert p["disclaimer_label"] == MANDATORY_ML_DISCLAIMER
        assert p["is_experimental"] is True
        assert len(p["top_contributing_features"]) == 5
'''

# ==============================================================================
# 6. scripts/run_phase3_ml.py
# ==============================================================================
FILES["scripts/run_phase3_ml.py"] = '''#!/usr/bin/env python3
"""
Phase 3 End-to-End Machine Learning Runner — ACEH SIAGA CUACA
Melatih seluruh model, membandingkan dengan Baseline Persistence & Climatology,
menyimpan artefak model (.joblib), hasil prediksi 5 stasiun BMKG Aceh,
dan menghasilkan dokumen penelitian docs/MODEL_EVALUATION.md.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_collection.bmkg_historical_import import BMKGHistoricalImporter
from src.machine_learning.model_trainer import AcehExtremeWeatherTrainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_phase3_ml")


def generate_model_evaluation_markdown(report: dict, predictions: list[dict], out_path: Path) -> None:
    split = report["split_summary"]
    best = report["best_models"]
    wf = report["walk_forward_cv_summary"]

    lines = [
        "# LAPORAN EVALUASI MODEL MACHINE LEARNING (MODEL EVALUATION)",
        "## ACEH SIAGA CUACA",
        "",
        f"> **Label Wajib:** *{report['mandatory_disclaimer']}*",
        "",
        f"- **Waktu Training (WIB):** `{report['trained_at_wib']}`",
        f"- **Versi Model:** `{report['model_version']}`",
        f"- **Versi Dataset:** `{report['dataset_version']}`",
        f"- **Metode Split:** `{split['split_method']}`",
        f"  - **Train Set:** {split['train_rows']} baris (`{split['train_period']}`)",
        f"  - **Validation Set:** {split['val_rows']} baris (`{split['val_period']}`)",
        f"  - **Holdout Test Set:** {split['test_rows']} baris (`{split['test_period']}`)",
        "",
        "---",
        "",
        "## 1. Perbandingan Performa Model Klasifikasi Potensi Hujan Lebat-Ekstrem",
        f"Target Klasifikasi: `{split['classification_target_column']}` (Ambang $\\ge {split['classification_threshold_mm']}\\text{{ mm/hari}}$)",
        "",
        "| Nama Model | Threshold | Precision | Recall | F1-Score | PR-AUC | TP | FP | FN | TN |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for m_name, m_val in report["classification_comparison"].items():
        cm = m_val["confusion_matrix"]
        lines.append(
            f"| **{m_name}** | {m_val['decision_threshold']} | {m_val['precision']:.4f} | "
            f"{m_val['recall']:.4f} | **{m_val['f1_score']:.4f}** | **{m_val['pr_auc']:.4f}** | "
            f"{cm['true_positive']} | {cm['false_positive']} | {cm['false_negative']} | {cm['true_negative']} |"
        )

    lines.extend(
        [
            "",
            f"- **Model Klasifikasi Terbaik:** `{best['best_classification_model']}` (Test F1-Score = `{best['best_classification_test_f1']}` pada threshold `{best['optimal_probability_threshold']}`)",
            f"- **Walk-Forward Time-Series CV ({wf['cv_folds']} Folds):** Mean PR-AUC = `{wf['mean_walk_forward_pr_auc']}`, Mean F1 = `{wf['mean_walk_forward_f1']}`",
            "",
            "---",
            "",
            "## 2. Perbandingan Performa Model Regresi Curah Hujan Harian (H+1)",
            "",
            "| Nama Model | MAE (mm) | RMSE (mm) | R² Score | Skill vs Baseline (%) |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
    )

    for m_name, m_val in report["regression_comparison"].items():
        skill_str = f"{m_val['skill_vs_baseline_pct']:+.2f}%" if m_val["skill_vs_baseline_pct"] is not None else "Baseline"
        lines.append(
            f"| **{m_name}** | {m_val['MAE_mm']:.3f} | **{m_val['RMSE_mm']:.3f}** | {m_val['R2_score']:.4f} | {skill_str} |"
        )

    lines.extend(
        [
            "",
            f"- **Model Regresi Terbaik:** `{best['best_regression_model']}` (Test RMSE = `{best['best_regression_test_rmse_mm']} mm`)",
            "",
            "---",
            "",
            "## 3. Top 10 Variabel Prediktor Paling Berpengaruh (Feature Importance)",
            "",
            "| Peringkat | Nama Fitur | Bobot Kepentingan |",
            "| :---: | :--- | :---: |",
        ]
    )

    for idx, feat in enumerate(report["feature_importance_top15"][:10], start=1):
        lines.append(f"| {idx} | `{feat['feature']}` | {feat['importance']:.5f} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Prediksi Eksperimental H+1 pada 5 Stasiun BMKG Provinsi Aceh",
            "",
            "| WMO ID | Stasiun BMKG | Tanggal Target | Estimasi Hujan (mm) | Probabilitas Lebat | Kategori | Disclaimer |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |",
        ]
    )

    for p in predictions:
        lines.append(
            f"| `{p['wmo_id']}` | {p['station_name']} | {p['target_prediction_date']} | "
            f"{p['predicted_rainfall_mm']} mm | {p['predicted_extreme_probability']:.2%} | "
            f"`{p['predicted_category']}` | *{p['disclaimer_label']}* |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 5. Keterbatasan Model (Model Limitations)",
        ]
    )
    for lim in report["model_limitations"]:
        lines.append(f"- {lim}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")


def main() -> None:
    cleaned_csv = Path("data/processed/cleaned_weather_observations_aceh.csv")
    if not cleaned_csv.exists():
        demo_csv = BMKGHistoricalImporter.generate_demo_dataset()
        df_clean = BMKGHistoricalImporter.load_file(demo_csv)
    else:
        df_clean = pd.read_csv(cleaned_csv)

    logger.info("1. Memulai pelatihan & evaluasi multi-model Machine Learning Aceh Siaga Cuaca...")
    trainer = AcehExtremeWeatherTrainer()
    result = trainer.train_and_evaluate_all(df_clean)

    report = result["evaluation_report"]
    predictions = result["latest_predictions"]

    md_path = Path("docs/MODEL_EVALUATION.md")
    generate_model_evaluation_markdown(report, predictions, md_path)

    best = report["best_models"]
    logger.info("=== RINGKASAN HASIL PHASE 3 — MACHINE LEARNING ===")
    logger.info("Model Klasifikasi Terbaik : %s (F1=%.4f | Threshold=%.3f)", best["best_classification_model"], best["best_classification_test_f1"], best["optimal_probability_threshold"])
    logger.info("Model Regresi Terbaik     : %s (RMSE=%.3f mm)", best["best_regression_model"], best["best_regression_test_rmse_mm"])
    logger.info("Artefak Model Tersimpan   : models/trained/best_rainfall_regressor.joblib & best_extreme_classifier.joblib")
    logger.info("Dokumen Evaluasi Tersimpan: %s", md_path)


if __name__ == "__main__":
    main()
'''


def main() -> None:
    print(f"[PHASE 3 BUILDER] Menuliskan seluruh file Phase 3 ke: {BASE_DIR}")
    for rel_path, content in FILES.items():
        target = BASE_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"  [OK] {rel_path} ({len(content)} bytes)")
    print("\n[PHASE 3 BUILDER] Selesai! Jalankan perintah berikut di PowerShell:")
    print("  1. python -m pytest tests\\test_phase3_machine_learning.py -v")
    print("  2. python scripts\\run_phase3_ml.py")


if __name__ == "__main__":
    main()