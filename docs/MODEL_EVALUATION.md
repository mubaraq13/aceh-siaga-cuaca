# LAPORAN EVALUASI MODEL MACHINE LEARNING (MODEL EVALUATION)
## ACEH SIAGA CUACA

> **Label Wajib:** *Analisis model eksperimental, bukan peringatan resmi BMKG.*

- **Waktu Training (WIB):** `2026-11-19T01:53:02.095057+07:00`
- **Versi Model:** `v1.0.0-exp`
- **Versi Dataset:** `aceh_obs_v2026.11`
- **Metode Split:** `Chronological Time-Series Split (Zero Future Data Leakage)`
  - **Train Set:** 7319 baris (`2021-01-02 s.d. 2025-01-29`)
  - **Validation Set:** 1569 baris (`2025-01-30 s.d. 2025-12-14`)
  - **Holdout Test Set:** 1572 baris (`2025-12-15 s.d. 2026-10-30`)

---

## 1. Perbandingan Performa Model Klasifikasi Potensi Hujan Lebat-Ekstrem
Target Klasifikasi: `target_is_extreme_50mm` (Ambang $\ge 50.0	ext{ mm/hari}$)

| Nama Model | Threshold | Precision | Recall | F1-Score | PR-AUC | TP | FP | FN | TN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline_Persistence** | 0.5 | 0.0000 | 0.0000 | **0.0000** | **0.0153** | 0 | 24 | 24 | 1524 |
| **Baseline_Seasonal_Climatology** | 0.15 | 0.0000 | 0.0000 | **0.0000** | **0.0351** | 0 | 0 | 24 | 1548 |
| **Logistic_Regression_Balanced** | 0.65 | 0.0396 | 0.3333 | **0.0708** | **0.0618** | 8 | 194 | 16 | 1354 |
| **Random_Forest_Classifier** | 0.5 | 0.2000 | 0.0417 | **0.0690** | **0.0585** | 1 | 4 | 23 | 1544 |
| **XGBoost_Classifier** | 0.64 | 0.2308 | 0.1250 | **0.1622** | **0.0733** | 3 | 10 | 21 | 1538 |
| **Sequence_Lag_NeuralNet_Classifier** | 0.13 | 0.0270 | 0.2083 | **0.0478** | **0.0192** | 5 | 180 | 19 | 1368 |

- **Model Klasifikasi Terbaik:** `XGBoost_Classifier` (Test F1-Score = `0.1622` pada threshold `0.64`)
- **Walk-Forward Time-Series CV (5 Folds):** Mean PR-AUC = `0.0446`, Mean F1 = `0.1017`

---

## 2. Perbandingan Performa Model Regresi Curah Hujan Harian (H+1)

| Nama Model | MAE (mm) | RMSE (mm) | R² Score | Skill vs Baseline (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline_Persistence** | 8.322 | **17.714** | -0.9784 | Baseline |
| **Baseline_Seasonal_Climatology** | 7.232 | **12.486** | 0.0170 | +29.51% |
| **Linear_Ridge_Regression** | 5.712 | **12.792** | -0.0317 | -2.45% |
| **Random_Forest_Regressor** | 5.782 | **12.782** | -0.0301 | -2.37% |
| **XGBoost_Regressor** | 5.760 | **12.765** | -0.0273 | -2.23% |
| **Sequence_Lag_NeuralNet_Regressor** | 5.693 | **12.794** | -0.0320 | -2.46% |

- **Model Regresi Terbaik:** `XGBoost_Regressor` (Test RMSE = `12.765 mm`)

---

## 3. Top 10 Variabel Prediktor Paling Berpengaruh (Feature Importance)

| Peringkat | Nama Fitur | Bobot Kepentingan |
| :---: | :--- | :---: |
| 1 | `doy_cos` | 0.09103 |
| 2 | `month_cos` | 0.08151 |
| 3 | `rain_roll_sum_14d` | 0.06639 |
| 4 | `doy_sin` | 0.04422 |
| 5 | `rain_roll_mean_7d` | 0.03994 |
| 6 | `rain_roll_max_7d` | 0.03569 |
| 7 | `rain_roll_sum_7d` | 0.03444 |
| 8 | `temp_humidity_interaction` | 0.03381 |
| 9 | `humidity_change_1d` | 0.03347 |
| 10 | `wind_u_zonal` | 0.03208 |

---

## 4. Prediksi Eksperimental H+1 pada 5 Stasiun BMKG Provinsi Aceh

| WMO ID | Stasiun BMKG | Tanggal Target | Estimasi Hujan (mm) | Probabilitas Lebat | Kategori | Disclaimer |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `96003` | Stasiun Klimatologi Aceh (Indrapuri) | 2026-10-31 | 3.11 mm | 17.92% | `LIGHT` | *Analisis model eksperimental, bukan peringatan resmi BMKG.* |
| `96009` | Stasiun Meteorologi Malikussaleh Aceh Utara | 2026-10-31 | 2.31 mm | 5.38% | `LIGHT` | *Analisis model eksperimental, bukan peringatan resmi BMKG.* |
| `96001` | Stasiun Meteorologi Kelas I Sultan Iskandar Muda | 2026-10-31 | 1.57 mm | 42.86% | `LIGHT` | *Analisis model eksperimental, bukan peringatan resmi BMKG.* |
| `96002` | Stasiun Meteorologi Maimun Saleh Sabang | 2026-10-31 | 3.62 mm | 29.61% | `LIGHT` | *Analisis model eksperimental, bukan peringatan resmi BMKG.* |
| `96011` | Stasiun Meteorologi Cut Nyak Dhien Nagan Raya | 2026-10-31 | 2.48 mm | 16.83% | `LIGHT` | *Analisis model eksperimental, bukan peringatan resmi BMKG.* |

---

## 5. Keterbatasan Model (Model Limitations)
- Model dilatih pada titik lokasi 5 stasiun pengamatan BMKG Aceh dan merepresentasikan dinamika cuaca lokal stasiun, bukan pengganti model NWP/satelit BMKG.
- Curah hujan tropis konvektif memiliki variabilitas stokastik harian yang tinggi sehingga prediksi digunakan sebagai indikator kewaspadaan dini pendamping, bukan peringatan resmi.
- Analisis model eksperimental, bukan peringatan resmi BMKG.
