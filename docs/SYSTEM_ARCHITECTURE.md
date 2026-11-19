# ARSITEKTUR SISTEM (SYSTEM ARCHITECTURE)
## ACEH SIAGA CUACA

Dokumen ini menjelaskan arsitektur perangkat lunak, alur data (*data pipeline*), skema relasional database PostGIS, pemisahan layanan (*microservices/containers*), serta mekanisme keamanan dan keandalan platform **ACEH SIAGA CUACA**.

---

## 1. Diagram Arsitektur Tingkat Tinggi (High-Level Architecture)
+-----------------------------------------------------------------------------------+
|                            SUMBER DATA EKSTERNAL RESMI                            |
|  [API Prakiraan BMKG]   [RSS & CAP Nowcast BMKG]   [CSV/XLSX Data Online & BNPB]  |
+-----------+------------------------+-----------------------------+----------------+
| (HTTPS JSON)           | (HTTPS XML/CAP)             | (Batch File)
v                        v                             v
+-----------------------------------------------------------------------------------+
|                     DATA ENGINEERING & INGESTION LAYER (Python)                   |
|  - Rate Limiter (Max 45 req/min) & Exponential Backoff Retry                      |
|  - XML/CAP Parser (Lat/Lon -> Lon/Lat PostGIS Polygon Converter)                  |
|  - BMKG Special Code Cleaner (8888 -> 0.0 + is_trace, 9999 -> NULL)               |
|  - Ingestion Logger & Deduplication Engine                                        |
+------------------------------------+----------------------------------------------+
|
v
+-----------------------------------------------------------------------------------+
|                  STORAGE & GEOSPATIAL LAYER (PostgreSQL 16 + PostGIS 3.4)         |
|  - Tabel: regions, administrative_boundaries (GEOMETRY), weather_stations (POINT) |
|  - Tabel: weather_forecasts, weather_alerts (MULTIPOLYGON), weather_observations  |
|  - Tabel: disaster_events, disaster_impacts, model_predictions                    |
|  - Tabel: data_sources, data_ingestion_logs                                       |
+----------------+-------------------------------------------------+----------------+
|                                                 |
v                                                 v
+----------------------------------------+       +----------------------------------+
|   ANALYTICS & ML PIPELINE (Python)     |       |    BACKEND API (FastAPI)         |
|  - Exploratory Data Analysis (Jupyter) |       |  - RESTful Endpoints (/api/v1/*) |
|  - Spatio-Temporal GIS Processing      |       |  - Pydantic v2 Schema Validation |
|  - Leakage-Free Feature Engineering    |------>|  - Source Attribution Injector   |
|  - Model Training (Baseline, RF, XGB)  |       |  - Health & Sync Status Monitor  |
|  - Model Registry (/models/trained)    |       |  - Rate Limiting & CORS Security |
+----------------------------------------+       +-----------------+----------------+
| (REST JSON / GeoJSON)
v
+-----------------------------------------------------------------------------------+
|                PUBLIC WEB PLATFORM (Next.js + TypeScript + Tailwind)              |
|  - 7 Halaman Utama (Home, Prakiraan, Peta GIS Leaflet, Analisis, ML, Alert, Edu)  |
|  - Visual Separation Badges (Aktual vs Prakiraan BMKG vs Peringatan vs Model ML)  |
|  - Degraded/Offline Fallback Banner (Menampilkan timestamp sinkronisasi terakhir) |
+-----------------------------------------------------------------------------------+

---

## 2. Desain Database Relasional & Spasial (ERD & Skema Tabel)

Database menggunakan **PostgreSQL 16** dengan ekstensi **PostGIS 3.4**. Seluruh tabel wajib memiliki atribut audit (`created_at`, `updated_at`) dan atribusi sumber data (`source_id` atau `data_source_label`).

### Daftar 11 Tabel Inti:
1. **`data_sources`**: Menyimpan metadata katalog sumber data (`id`, `source_code`, `source_name`, `organization`, `base_url`, `data_nature` [`OBSERVATION`, `OFFICIAL_FORECAST`, `OFFICIAL_ALERT`, `DISASTER_RECORD`, `ML_EXPERIMENTAL`], `is_official`, `license_notes`).
2. **`data_ingestion_logs`**: Mencatat setiap eksekusi pengambilan/impor data (`id`, `source_id`, `job_type`, `started_at`, `finished_at`, `status` [`SUCCESS`, `PARTIAL`, `FAILED`], `records_fetched`, `records_inserted`, `records_updated`, `error_message`).
3. **`regions`**: Hirarki wilayah administratif Provinsi Aceh dari tingkat Provinsi (`ADM1 = 11`), Kabupaten/Kota (`ADM2`), Kecamatan (`ADM3`), hingga Gampong/Desa (`ADM4`), beserta koordinat titik tengah (`latitude`, `longitude`) dan jumlah penduduk (`population`).
4. **`administrative_boundaries`**: Menyimpan poligon batas wilayah (`id`, `region_code` FK -> `regions.region_code`, `admin_level`, `geom GEOMETRY(MultiPolygon, 4326)`, `area_sq_km`).
5. **`weather_stations`**: Menyimpan metadata stasiun pengamatan BMKG di Aceh (`id`, `wmo_id`, `station_name`, `station_type`, `region_code`, `latitude`, `longitude`, `elevation_m`, `geom GEOMETRY(Point, 4326)`, `is_active`).
6. **`weather_observations`**: Menyimpan data observasi historis harian/per-jam dari stasiun BMKG (`id`, `station_id` FK, `source_id` FK, `observation_date`, `temp_min_c`, `temp_max_c`, `temp_avg_c`, `humidity_avg_pct`, `rainfall_mm`, `is_trace_rainfall`, `sunshine_hours`, `wind_speed_max_ms`, `wind_dir_max_deg`, `wind_speed_avg_ms`, `wind_dir_predominant`, `rainfall_category`, `quality_flag`).
   - *Unique Constraint:* `UNIQUE(station_id, observation_date)`.
7. **`weather_forecasts`**: Menyimpan data prakiraan 3-jaman dari API BMKG (`id`, `region_code` FK, `source_id` FK, `analysis_time`, `forecast_time_utc`, `forecast_time_local`, `temperature_c`, `humidity_pct`, `weather_code`, `weather_desc_id`, `weather_desc_en`, `wind_speed_kmh`, `wind_speed_ms`, `wind_dir_cardinal`, `wind_dir_deg`, `cloud_cover_pct`, `visibility_text`, `fetched_at`).
   - *Unique Constraint:* `UNIQUE(region_code, forecast_time_utc)`.
8. **`weather_alerts`**: Menyimpan peringatan dini cuaca resmi CAP BMKG (`id`, `cap_identifier` UNIQUE, `source_id` FK, `sender`, `sent_time`, `status`, `msg_type`, `event_type`, `urgency`, `severity`, `certainty`, `effective_time`, `onset_time`, `expires_time`, `headline`, `description`, `instruction`, `official_web_url`, `affected_areas_text`, `geom GEOMETRY(MultiPolygon, 4326)`, `raw_xml`, `fetched_at`).
9. **`disaster_events`**: Menyimpan riwayat kejadian bencana hidrometeorologi Aceh dari BPBA/BNPB (`id`, `event_code` UNIQUE, `source_id` FK, `region_code` FK, `disaster_type` [`BANJIR`, `BANJIR_BANDANG`, `TANAH_LONGSOR`, `CUACA_EKSTREM`], `event_date`, `location_detail`, `cause_description`, `geom GEOMETRY(Point, 4326)`).
10. **`disaster_impacts`**: Menyimpan rincian dampak dari kejadian bencana (`id`, `disaster_event_id` FK, `casualties_dead`, `casualties_missing`, `casualties_injured`, `displaced_people`, `houses_heavily_damaged`, `houses_moderately_damaged`, `houses_lightly_damaged`, `houses_submerged`, `public_facilities_damaged`).
11. **`model_predictions`**: Menyimpan luaran prediksi model Machine Learning eksperimental (`id`, `station_id` FK, `region_code` FK, `model_name`, `model_version`, `dataset_version`, `predicted_at`, `target_date`, `horizon_days`, `predicted_rainfall_mm`, `predicted_extreme_prob`, `predicted_category`, `disclaimer_label`).
    - *Default `disclaimer_label`:* `'Analisis model eksperimental, bukan peringatan resmi BMKG.'`

---

## 3. Desain Kontrak REST API (FastAPI)

Seluruh respons JSON dari backend wajib dibungkus dalam struktur amplop (*envelope*) standar yang memuat metadata sumber dan waktu pembaruan:

```json
{
  "status": "success",
  "data_category": "OFFICIAL_BMKG_FORECAST",
  "source_attribution": "BMKG - Badan Meteorologi, Klimatologi, dan Geofisika",
  "disclaimer": "Data prakiraan resmi BMKG. Bukan merupakan data observasi historis.",
  "last_updated_wib": "2026-11-18T23:00:00+07:00",
  "is_demo_mode": false,
  "api_health": "ONLINE",
  "data": { ... }
}