#!/usr/bin/env python3
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
        f"Target Klasifikasi: `{split['classification_target_column']}` (Ambang $\ge {split['classification_threshold_mm']}\text{{ mm/hari}}$)",
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
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
