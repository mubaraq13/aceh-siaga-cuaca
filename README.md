# ACEH SIAGA CUACA

**Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh.**

Platform web informasi meteorologi, analisis spasial-temporal (GIS), evaluasi *Machine Learning*, dan kesiapsiagaan bencana hidrometeorologi untuk 23 Kabupaten/Kota di Provinsi Aceh.

> **Judul Penelitian:**  
> *"Analisis Spasial-Temporal dan Prediksi Potensi Cuaca Ekstrem Berbasis Data BMKG Menggunakan Pendekatan Data Science dan Machine Learning untuk Mendukung Kesiapsiagaan Bencana Hidrometeorologi di Provinsi Aceh."*

- **Cakupan Wilayah:** Provinsi Aceh (23 Kabupaten/Kota, 5 Stasiun Pengamatan BMKG)
- **Zona Waktu Operasional:** `Asia/Jakarta` (WIB / UTC+7)
- **Standar Aksesibilitas:** WCAG AA (*Mobile-First*, Mode Terang & Gelap)

---

## Fitur Utama

1. **Prakiraan Cuaca Resmi BMKG (ADM4 Aceh)**  
   Mengambil prakiraan cuaca 3 harian (interval 3 jam) dari API Publik BMKG dengan *rate limiter* (45 req/menit), *retry* otomatis, dan *local caching*.
2. **Peringatan Dini Cuaca Resmi BMKG (Nowcasting RSS & CAP v1.2)**  
   Parser XML aman (`defusedxml`) dengan filter ketat khusus Provinsi Aceh serta ekstraksi poligon wilayah terdampak ke format GeoJSON.
3. **Pembersihan Data Observasi Historis BMKG**  
   Standarisasi otomatis kode khusus BMKG: `8888` (*trace rainfall* $\rightarrow$ `0.0 mm` dengan penanda `is_trace_rainfall`) dan `9999` (*missing value* $\rightarrow$ `NULL`).
4. **Analisis Eksploratif (EDA) & Spasial-Temporal (GIS)**  
   Statistik deskriptif, indeks iklim ekstrem WMO/ETCCDI, korelasi Spearman/Pearson, 7 grafik publikasi (`.png`), dan 3 layer GeoJSON interaktif.
5. **Prediksi Cuaca Ekstrem Berbasis Machine Learning**  
   36 fitur prediktor bebas *data leakage*, *Chronological Train-Val-Test Split*, *Walk-Forward Cross-Validation*, dan komparasi terhadap *baseline*.
6. **Website Publik 7 Halaman**  
   Beranda, Prakiraan Cuaca, Peta Interaktif, Analisis Cuaca, Machine Learning, Peringatan Dini, dan Edukasi Kesiapsiagaan—dilengkapi pita *Data Provenance* dan *Data Freshness*.

---

## Teknologi yang Digunakan

| Lapisan | Teknologi |
| :--- | :--- |
| **Frontend** | Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Leaflet, Recharts |
| **Backend** | FastAPI, Uvicorn, Pydantic v2, Requests, DefusedXML |
| **Data Science & ML** | Python, Pandas, NumPy, Scikit-Learn, Joblib, Matplotlib, Seaborn |
| **Database & Spasial** | PostgreSQL 16 + PostGIS 3.4 |
| **Deployment** | Docker, Docker Compose, Nginx Reverse Proxy |

---

## Struktur Direktori

```text
aceh-siaga-cuaca/
├── backend/              # REST API FastAPI & Dockerfile backend
├── database/             # Skema PostgreSQL/PostGIS (schema.sql) & migrasi
├── data/                 # Data mentah (raw), cache BMKG, hasil olahan (processed), GeoJSON, & grafik
├── docs/                 # Dokumentasi arsitektur, kamus data, metodologi, & OPENAPI_SPEC.json
├── frontend/             # Aplikasi web publik Next.js (7 halaman) & Dockerfile frontend
├── models/               # Model ML terlatih (.joblib) & laporan evaluasi
├── nginx/                # Konfigurasi reverse proxy (nginx.conf)
├── notebooks/            # 7 Jupyter Notebooks (01_data_collection s.d. 07_model_evaluation)
├── scripts/              # Skrip otomasi pipeline data, analisis, ML, & bootstrap
├── src/                  # Modul inti Python (data_collection, geospatial, machine_learning)
├── tests/                # Suite pengujian otomatis (pytest)
├── DESIGN.md             # Panduan sistem desain & palet warna WCAG AA
└── docker-compose.yml    # Orkestrasi full-stack (PostGIS, Backend, Frontend, Nginx)
