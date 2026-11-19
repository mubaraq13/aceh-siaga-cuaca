"""
Unit Tests for PHASE 3 — MACHINE LEARNING (ACEH SIAGA CUACA)
File: tests/test_phase3_machine_learning.py
Jalankan dengan: python -m pytest tests\test_phase3_machine_learning.py -v
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
