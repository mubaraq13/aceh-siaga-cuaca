"""
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
