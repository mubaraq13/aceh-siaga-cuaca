# METODOLOGI PENELITIAN (RESEARCH METHODOLOGY)
## ACEH SIAGA CUACA

**Judul Penelitian:**  
*"Analisis Spasial-Temporal dan Prediksi Potensi Cuaca Ekstrem Berbasis Data BMKG Menggunakan Pendekatan Data Science dan Machine Learning untuk Mendukung Kesiapsiagaan Bencana Hidrometeorologi di Provinsi Aceh."*

---

## 1. Rumusan Masalah & Pertanyaan Penelitian (Research Questions)
1. **RQ1 (Karakteristik Temporal & Ekstrem):** Bagaimana karakteristik distribusi statistik, pola musiman (monsunal vs ekuatorial), dan tren frekuensi curah hujan ekstrem ($\ge 50\text{ mm/hari}$) pada stasiun-stasiun pengamatan BMKG di Provinsi Aceh selama periode 2021–2026?
2. **RQ2 (Distribusi Spasial & Keterkaitan Bencana):** Bagaimana pola spasial parameter cuaca di berbagai zona topografi Aceh (Pesisir Timur-Utara, Pesisir Barat-Selatan, dan Dataran Tinggi Tengah) serta hubungannya dengan distribusi historis kejadian bencana hidrometeorologi (banjir dan tanah longsor)?
3. **RQ3 (Prediktabilitas Machine Learning):** Sejauh mana algoritma *Machine Learning* (Linear/Logistic Regression, Random Forest, XGBoost, dan LSTM) yang dilatih menggunakan fitur *lag* dan *rolling window* parameter meteorologi lokal mampu melampaui model *Baseline* (Persistence & Climatology) dalam memprediksi curah hujan harian dan klasifikasi potensi hujan ekstrem?

---

## 2. Tahapan Pra-Pemrosesan & Pembersihan Data (Data Preprocessing)

### A. Penanganan Kode Khusus BMKG
Berdasarkan standar pencatatan Pusat Database BMKG:
1. **Kode `8888` (Curah Hujan Tidak Terukur / *Trace*):**
   $$RR_{\text{clean}} = \begin{cases} 0.0, & \text{jika } RR_{\text{raw}} = 8888 \quad (\text{dengan flag } I_{\text{trace}} = 1) \\ \text{NULL}, & \text{jika } RR_{\text{raw}} \in \{9999, \text{'-'}, \text{NaN}\} \\ RR_{\text{raw}}, & \text{lainnya} \end{cases}$$
2. **Pemeriksaan Konsistensi Fisik (*Physical Sanity Checks*):**
   - Memastikan $T_{\min} \le T_{\text{avg}} \le T_{\max}$ pada setiap baris observasi harian.
   - Memastikan $0 \le RH_{\text{avg}} \le 100\%$, $0 \le ss \le 12.5\text{ jam}$, dan $RR \ge 0\text{ mm}$.
3. **Aturan Imputasi (*Imputation Policy*):**
   - **Variabel Target ($RR$):** **DILARANG** melakukan imputasi (interpolasi linier atau pengisian rata-rata) pada nilai curah hujan (`RR`) yang hilang (`NULL`) untuk dijadikan label target pelatihan model, karena akan menciptakan kejadian hujan palsu. Baris dengan target $RR = \text{NULL}$ dikeluarkan dari pembentukan label target $y_t$.
   - **Variabel Prediktor Kontinu ($T_{\text{avg}}, RH_{\text{avg}}, ff_{\text{avg}}$):** Celah kosong singkat ($\le 2$ hari berturut-turut) dapat diisi menggunakan *forward-fill* (`ffill`) maksimal 2 langkah atau median historis bulanan stasiun yang sama **hanya di dalam lipatan data latih (*training fold*)** untuk mencegah kebocoran informasi masa depan (*future data leakage*). Celah $> 2$ hari dibiarkan terputus dan segmen deret waktunya dipisahkan.

### B. Penyelarasan Resolusi Waktu (*Temporal Alignment*)
- Data observasi historis BMKG memiliki resolusi **harian (24 jam, dipotong pukul 07.00 WIB)**.
- Data prakiraan API BMKG memiliki resolusi **3 jam (8 titik per hari)**.
- **Aturan Ketat:** Kedua dataset ini **tidak boleh digabungkan secara langsung** ke dalam satu tabel pelatihan. Analisis perbandingan antara prakiraan dan observasi hanya dapat dilakukan setelah data prakiraan 3-jaman diagregasi ke jendela waktu 24 jam yang sejajar (07.00 WIB hari $t-1$ hingga 07.00 WIB hari $t$).

---

## 3. Metodologi Analisis Eksploratif & Spasial-Temporal (EDA & GIS)

1. **Statistik Deskriptif & Indeks Iklim Ekstrem (ETCCDI):**
   - Menghitung Mean, Median, Standard Deviation, Interquartile Range (IQR), Skewness, dan Kurtosis.
   - Menghitung indeks ekstrem tahunan/bulanan per stasiun:
     - **R20mm:** Jumlah hari hujan sedang-lebat ($RR \ge 20\text{ mm}$).
     - **R50mm:** Jumlah hari hujan lebat-ekstrem ($RR \ge 50\text{ mm}$).
     - **Rx1day:** Curah hujan harian maksimum dalam satu bulan/tahun.
     - **Rx5day:** Akumulasi curah hujan 5 hari berturut-turut maksimum.
     - **CDD (Consecutive Dry Days) & CWD (Consecutive Wet Days).**
2. **Analisis Korelasi:**
   - Karena distribusi curah hujan harian memiliki kemencengan positif yang tinggi (*highly right-skewed* dan *zero-inflated*), analisis hubungan antarvariabel wajib melaporkan korelasi peringkat **Spearman ($\rho$)** di samping korelasi linier **Pearson ($r$)** beserta nilai signifikansi ($p\text{-value}$).
   - Setiap temuan korelasi disajikan sebagai asosiasi statistik, bukan klaim hubungan sebab-akibat langsung.
3. **Keterbatasan Analisis Spasial (Spatial Limitations):**
   - Mengingat jumlah stasiun sinoptik BMKG yang terbuka di Aceh berjumlah 5–6 titik dengan jarak antarstasiun $>50-150\text{ km}$ yang dipisahkan oleh pegunungan, **sistem ini tidak melakukan interpolasi permukaan kontinu (seperti IDW atau Kriging) dari 5 titik stasiun ke seluruh daratan Aceh** karena akan menghasilkan estimasi yang secara meteorologis tidak valid di wilayah pegunungan tengah (Aceh Tengah, Bener Meriah, Gayo Lues).
   - Visualisasi spasial menyajikan: (a) nilai tepat pada titik stasiun dengan radius keterwakilan lokal, (b) peta choropleth prakiraan resmi BMKG berbasis kode wilayah administrasi, dan (c) peta kepadatan kejadian bencana per kabupaten/kota.

---

## 4. Metodologi Eksperimen Machine Learning

### A. Formulasi Masalah Prediksi
Diberikan vektor fitur historis pada stasiun $s$ hingga hari ke-$t$, $\mathbf{x}_{s, t}$, model memprediksi kondisi pada hari ke-$(t+1)$:
1. **Tugas Regresi:** Memprediksi jumlah curah hujan besok, $\hat{y}_{s, t+1} = \widehat{RR}_{s, t+1} \in [0, \infty)\text{ mm}$ (serta evaluasi transformasi $\log(1 + RR)$ untuk menangani kemencengan distribusi).
2. **Tugas Klasifikasi Potensi Hujan Lebat/Ekstrem:** Memprediksi probabilitas $P(RR_{s, t+1} \ge \tau)$, dengan dua skenario ambang batas resmi BMKG:
   - Ambang Waspada ($\tau_1 = 20\text{ mm/hari}$: Hujan Sedang – Ekstrem).
   - Ambang Siaga Ekstrem ($\tau_2 = 50\text{ mm/hari}$: Hujan Lebat – Ekstrem).

### B. Rekayasa Fitur Bebas Kebocoran Data (*Leakage-Free Feature Engineering*)
Seluruh fitur untuk memprediksi target hari $t+1$ hanya boleh dihitung dari observasi pada waktu $\le t$:
- **Fitur Lag Curah Hujan:** $RR_{t}, RR_{t-1}, RR_{t-2}, RR_{t-3}, RR_{t-7}$.
- **Fitur Akumulasi & Rata-Rata Bergerak (*Rolling Window*):**
  - `rain_roll_sum_3d`, `rain_roll_sum_7d`, `rain_roll_sum_14d` (merepresentasikan kejenuhan tanah / kelembapan pendahulu).
  - `rain_roll_mean_7d`, `rain_roll_max_7d`, `wet_days_count_7d`.
- **Fitur Termodinamika & Atmosfer Lokal:**
  - $T_{\min, t}, T_{\max, t}, T_{\text{avg}, t}$, serta rentang suhu diurnal $\Delta T_t = T_{\max, t} - T_{\min, t}$.
  - $RH_{\text{avg}, t}$, perubahan kelembapan $\Delta RH_t = RH_{\text{avg}, t} - RH_{\text{avg}, t-1}$.
  - Indeks proksi kelembapan-panas: $T_{\text{avg}, t} \times (RH_{\text{avg}, t} / 100)$.
  - Kecepatan angin $ff_{\text{avg}, t}, ff_{\max, t}$ dan dekomposisi vektor arah angin menjadi komponen Zonal ($u = -ff \cdot \sin(\theta)$) dan Meridional ($v = -ff \cdot \cos(\theta)$).
  - Durasi penyinaran matahari $ss_t$.
- **Fitur Siklikal Kalender:**
  - $\sin\left(\frac{2\pi \cdot \text{doy}}{365.25}\right), \cos\left(\frac{2\pi \cdot \text{doy}}{365.25}\right)$ dan $\sin\left(\frac{2\pi \cdot \text{month}}{12}\right), \cos\left(\frac{2\pi \cdot \text{month}}{12}\right)$.
- **Fitur Spasial Stasiun:** `latitude`, `longitude`, `elevation_m`, dan *one-hot / target encoding* `station_id`.

### C. Strategi Pembagian Data & Validasi Silang Deret Waktu
**DILARANG menggunakan Random K-Fold Split** karena akan membocorkan data masa depan ke masa lalu.
1. **Chronological Train-Validation-Test Split:**
   - **Training Set:** 70% awal periode kronologis (misal: 2021–2024).
   - **Validation Set:** 15% periode berikutnya (misal: 2025) untuk *hyperparameter tuning* dan penentuan *classification threshold*.
   - **Holdout Test Set:** 15% periode terakhir (misal: 2026) untuk evaluasi akhir yang objektif.
2. **Walk-Forward / Expanding Window Time-Series Cross-Validation (5 Folds):**
   - Menguji stabilitas model lintas musim (Monsun Barat vs Monsun Timur).

### D. Model Pembanding & Metrik Evaluasi
1. **Baseline Models (Wajib Dikalahkan oleh Model ML):**
   - *Persistence Baseline:* $\hat{y}_{t+1} = y_t$ (kondisi besok diasumsikan sama dengan hari ini).
   - *Seasonal Climatology Baseline:* Rata-rata historis curah hujan pada bulan dan stasiun yang sama pada data latih.
2. **Model Eksperimen:**
   - Regresi: `Ridge Regression`, `RandomForestRegressor`, `XGBRegressor`, dan `LSTM` (opsional jika data kontinu $>1.000$ hari tanpa celah besar).
   - Klasifikasi: `LogisticRegression(class_weight='balanced')`, `RandomForestClassifier(class_weight='balanced_subsample')`, `XGBClassifier(scale_pos_weight=...)`.
3. **Metrik Evaluasi:**
   - **Regresi:** MAE ($\text{mm}$), RMSE ($\text{mm}$), dan $R^2$ (beserta perbandingan RMSE terhadap Baseline).
   - **Klasifikasi (Fokus Data Tidak Seimbang):** Precision, Recall (Sensitivity / Probability of Detection), F1-Score, PR-AUC (Precision-Recall Area Under Curve), dan Confusion Matrix.