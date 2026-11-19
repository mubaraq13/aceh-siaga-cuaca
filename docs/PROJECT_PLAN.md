# RENCANA PENGEMBANGAN PROYEK (PROJECT PLAN)
## ACEH SIAGA CUACA

**Judul Penelitian:**  
Analisis Spasial-Temporal dan Prediksi Potensi Cuaca Ekstrem Berbasis Data BMKG Menggunakan Pendekatan Data Science dan Machine Learning untuk Mendukung Kesiapsiagaan Bencana Hidrometeorologi di Provinsi Aceh.

**Lokasi Fokus:** Provinsi Aceh, Indonesia (Kode Kemendagri: `11`)  
**Zona Waktu Standar:** `Asia/Jakarta` (WIB / UTC+7)

---

## 1. Latar Belakang dan Urgensi
Provinsi Aceh memiliki karakteristik topografi dan meteorologi yang sangat kompleks, diapit oleh Samudra Hindia di barat, Selat Malaka di timur-utara, dan dibelah oleh gugusan Pegunungan Bukit Barisan. Kondisi ini menyebabkan variasi pola curah hujan lokal (monsunal di pesisir timur-utara dan ekuatorial/samudra di pesisir barat-selatan) yang memicu tingginya frekuensi bencana hidrometeorologi seperti banjir, banjir bandang, tanah longsor, dan angin ekstrem.

Proyek **ACEH SIAGA CUACA** dibangun untuk menjembatani kesenjangan antara data meteorologi teknis, analisis ilmiah berbasis *Data Science* & *Machine Learning*, dan kebutuhan informasi kesiapsiagaan publik yang mudah dipahami oleh masyarakat, BPBA/BPBD, serta pemerintah daerah.

---

## 2. Prinsip Utama Rekayasa & Integritas Ilmiah
1. **Keaslian Data (Zero Fabricated Data):** Seluruh analisis historis dan pelatihan model hanya boleh dijalankan di atas data observasi terverifikasi. Data tiruan (*mock data*) hanya diizinkan pada mode `DEMO_MODE=true` untuk pengujian antarmuka dan wajib diberi watermark/label eksplisit.
2. **Pemisahan Entitas Data:**
   - **Data Observasi Aktual:** Hasil pengukuran instrumen stasiun BMKG.
   - **Data Prakiraan Resmi:** Hasil luaran API prakiraan BMKG (horizon 3 hari, resolusi 3 jam).
   - **Peringatan Dini Resmi:** Dokumen Common Alerting Protocol (CAP) BMKG.
   - **Prediksi Eksperimental ML:** Luaran model *Machine Learning* internal yang wajib diberi label: *"Analisis model eksperimental, bukan peringatan resmi BMKG."*
3. **Kepatuhan Rate Limit:** Menghormati kuota server publik BMKG (maksimum 60 request/menit/IP) menggunakan *token bucket rate limiter*, *exponential backoff*, dan *caching layer*.

---

## 3. Tahapan Eksekusi (Roadmap & Milestones)

### PHASE 0 — PROJECT DISCOVERY (Selesai)
- Audit endpoint API Prakiraan Cuaca BMKG (`adm4`) dan RSS/CAP Nowcasting BMKG.
- Pemetaan stasiun pengamatan meteorologi/klimatologi BMKG di Provinsi Aceh.
- Identifikasi aturan pembersihan kode khusus BMKG (`8888` untuk *trace rainfall*, `9999` untuk *missing value*).
- Penyusunan 5 dokumen fondasi (`PROJECT_PLAN.md`, `DATA_SOURCE_CATALOG.md`, `DATA_DICTIONARY.md`, `SYSTEM_ARCHITECTURE.md`, `RESEARCH_METHODOLOGY.md`).

### PHASE 1 — DATA FOUNDATION
- Inisialisasi struktur folder proyek standar produksi.
- Pembuatan skema database PostgreSQL + PostGIS (`database/schema.sql`).
- Implementasi modul pengumpulan data:
  - `src/data_collection/bmkg_forecast.py` (Pengambilan prakiraan cuaca dengan rate limiter & cache).
  - `src/data_collection/bmkg_alerts.py` (Parser RSS XML dan ekstraktor poligon CAP XML).
  - `src/data_collection/bmkg_historical_import.py` (Pipeline validasi dan impor CSV/XLSX Data Online BMKG).
  - `src/data_collection/disaster_import.py` (Pipeline impor data bencana BPBA/BNPB).
- Implementasi modul pembersihan data `src/data_processing/data_cleaning.py` beserta *unit test* (`pytest`).

### PHASE 2 — DATA ANALYSIS (EDA & SPATIO-TEMPORAL)
- Pembuatan Jupyter Notebooks (`01` s.d. `04`) yang dapat dieksekusi secara deterministik.
- Statistik deskriptif parameter cuaca Aceh (mean, median, std, IQR, kuantil ekstrem P90, P95, P99).
- Analisis pola temporal (siklus diurnal 3-jaman dari prakiraan, pola bulanan/musiman monsun barat vs timur, tren tahunan 2021–2026).
- Analisis korelasi non-parametrik (Spearman/Kendall) dan parametrik (Pearson) antarvariabel cuaca.
- Analisis spasial berbasis GIS: pemetaan distribusi stasiun, poligon peringatan dini, dan *overlay* frekuensi kejadian bencana banjir/longsor per kabupaten/kota tanpa melakukan interpolasi buta di area minim stasiun.

### PHASE 3 — MACHINE LEARNING
- Definisi target prediksi berbasis ambang batas meteorologi resmi BMKG:
  - Regresi: Estimasi curah hujan harian ($RR_{t+1}$) dalam mm.
  - Klasifikasi Multi-Kelas / Biner: Potensi Hujan Lebat–Ekstrem ($\ge 50\text{ mm/hari}$).
- Rekayasa fitur bebas kebocoran data (*leakage-free feature engineering*): *lag rainfall* ($t-1, t-2, t-3, t-7$), *rolling sum/mean* (3, 7, 14 hari dengan `.shift(1)`), komponen siklikal waktu ($\sin/\cos$ hari dalam tahun), dan interaksi kelembapan-suhu.
- Komparasi model menggunakan *Chronological Split* & *Time-Series Walk-Forward Validation*:
  1. Baseline Persistence & Historical Climatology.
  2. Linear / Ridge Regression & Logistic Regression.
  3. Random Forest Regressor & Classifier.
  4. XGBoost Regressor & Classifier (dengan `scale_pos_weight` untuk *class imbalance*).
  5. Eksperimen LSTM (hanya jika deret waktu stasiun kontinu dan memenuhi syarat panjang sampel).
- Penyimpanan artefak model, *feature importance* (SHAP / Gain), dan metadata versi dataset.

### PHASE 4 — WEB DEVELOPMENT (BACKEND & PUBLIC DASHBOARD)
- **Backend FastAPI:** Penyediaan REST API terstruktur (`/api/v1/forecasts`, `/api/v1/alerts`, `/api/v1/observations`, `/api/v1/analytics`, `/api/v1/predictions`, `/api/v1/disasters`) dengan validasi Pydantic dan caching.
- **Frontend Next.js (TypeScript + Tailwind CSS + Recharts + Leaflet):**
  - Halaman 1: Home (Ringkasan Eksekutif & Status Peringatan Aktif Aceh).
  - Halaman 2: Prakiraan Cuaca (Filter berjenjang Kabupaten/Kota -> Kecamatan -> Gampong).
  - Halaman 3: Peta Interaktif GIS (Leaflet dengan layer batas wilayah, stasiun, poligon CAP, dan peta risiko).
  - Halaman 4: Analisis Cuaca Historis (Visualisasi EDA & perbandingan wilayah).
  - Halaman 5: Machine Learning (Prediksi eksperimental, metrik evaluasi, *feature importance*, dan disclaimer wajib).
  - Halaman 6: Peringatan Dini Resmi BMKG (Detail CAP aktif & tautan resmi).
  - Halaman 7: Edukasi Kesiapsiagaan (Panduan banjir, longsor, angin kencang, tas siaga bencana, dan kontak darurat BPBA/BPBD/Basarnas Aceh).

### PHASE 5 — TESTING, SECURITY & DEPLOYMENT
- Pengujian menyeluruh (*unit tests*, *integration tests*, validasi parser XML/JSON, uji beban rate limit).
- Konfigurasi kontainerisasi penuh (`docker-compose.yml` mencakup PostgreSQL/PostGIS, FastAPI Backend, Scheduled Worker, Next.js Frontend, dan Nginx Reverse Proxy).
- Dokumentasi operasional dan panduan *deployment*.

---

## 4. Manajemen Risiko Teknis
| Risiko | Dampak | Strategi Mitigasi |
| :--- | :--- | :--- |
| Pemblokiran IP oleh API BMKG akibat melebihi 60 req/menit | Gagal memperbarui prakiraan cuaca | Implementasi *Token Bucket Rate Limiter* (maks 45 req/menit sebagai margin aman), caching PostgreSQL/Redis, dan pengambilan bertahap. |
| Ketidaktersediaan API langsung untuk data historis Data Online BMKG | Pipeline otomatis tidak bisa mengunduh langsung tanpa sesi login/CAPTCHA | Penyediaan modul `bmkg_historical_import.py` yang mendukung berbagai format ekspor CSV/XLSX BMKG, lengkap dengan validasi skema dan dokumen prosedur permohonan data resmi. |
| Kepadatan stasiun pengamatan BMKG yang jarang di wilayah tengah Aceh | Kesalahan tinggi jika dilakukan interpolasi spasial (IDW/Kriging) ke seluruh provinsi | Melarang klaim interpolasi buta; membatasi klaim observasi pada radius representatif stasiun dan menggunakan agregasi tingkat kabupaten untuk data kejadian bencana. |
| Ketimpangan kelas ekstrem (*Class Imbalance*) pada kejadian hujan $>50\text{ mm}$ | Model ML cenderung memprediksi kelas mayoritas (tidak hujan lebat) | Evaluasi wajib menggunakan Precision, Recall, F1-Score, dan PR-AUC (bukan sekadar Accuracy), disertai *cost-sensitive learning* dan *threshold tuning*. |