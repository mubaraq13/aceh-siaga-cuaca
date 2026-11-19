# ACEH SIAGA CUACA
**Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh.**

Judul Penelitian:
> *"Analisis Spasial-Temporal dan Prediksi Potensi Cuaca Ekstrem Berbasis Data BMKG Menggunakan Pendekatan Data Science dan Machine Learning untuk Mendukung Kesiapsiagaan Bencana Hidrometeorologi di Provinsi Aceh."*

- **Lokasi Fokus:** Provinsi Aceh, Indonesia (23 Kabupaten/Kota, 5 Stasiun BMKG)
- **Zona Waktu Operasional:** `Asia/Jakarta` (WIB / UTC+7)

## 1. Fitur Utama Platform
1. **Prakiraan Cuaca Resmi BMKG (ADM4 Aceh):** Interval 3 jam, horizon 3 hari, rate limiter 45 req/menit, dan caching.
2. **Peringatan Dini Cuaca Resmi BMKG (Nowcasting RSS & CAP v1.2):** Parser XML aman (defusedxml) dan ekstraksi poligon wilayah terdampak.
3. **Pembersihan Data Observasi Historis BMKG:** Penanganan kode khusus 8888 (trace rainfall -> 0.0 mm) dan 9999 (missing -> NULL).
4. **Analisis Spasial-Temporal & EDA:** Statistik deskriptif, indeks ekstrem WMO/ETCCDI, korelasi Spearman/Pearson, 7 grafik PNG, dan 3 layer GeoJSON.
5. **Machine Learning Bebas Data Leakage:** 36 fitur prediktor, Chronological Split, Walk-Forward CV, dan label wajib eksperimental.
6. **Website Publik 7 Halaman (Next.js + TypeScript + Tailwind + Leaflet + Recharts):** Dilengkapi Data Provenance, Data Freshness, dan kontras WCAG AA.

## 2. Cara Menjalankan Secara Lokal (Windows PowerShell)
1. Aktifkan virtual environment: `.\.venv\Scripts\Activate.ps1`
2. Jalankan pipeline data & ML: `python scripts\verify_phase1_live.py`, `python scripts\run_phase2_analysis.py`, `python scripts\run_phase3_ml.py`
3. Jalankan Backend FastAPI (Port 8000): `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload`
4. Jalankan Frontend Next.js (Port 3000): `cd frontend`, `npm install`, `npm run dev`
5. Jalankan seluruh pengujian otomatis: `python -m pytest -v`

## 3. Cara Menjalankan dengan Docker Compose
Jalankan `docker compose up --build -d` untuk mengaktifkan PostGIS, FastAPI, Next.js, dan Nginx Reverse Proxy.
