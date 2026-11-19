"""
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
