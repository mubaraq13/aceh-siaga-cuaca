-- ============================================================================
-- ACEH SIAGA CUACA — POSTGRESQL 16 + POSTGIS 3.4 SCHEMA
-- File: database/schema.sql
-- Zona Waktu Standar: Asia/Jakarta (WIB)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
SET timezone = 'Asia/Jakarta';

-- Fungsi otomatis pembaruan kolom updated_at
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 1. TABEL DATA_SOURCES (Katalog & Atribusi Sumber Data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    source_code VARCHAR(50) UNIQUE NOT NULL,
    source_name VARCHAR(150) NOT NULL,
    organization VARCHAR(150) NOT NULL,
    base_url TEXT,
    data_nature VARCHAR(40) NOT NULL CHECK (
        data_nature IN (
            'OBSERVATION',
            'OFFICIAL_FORECAST',
            'OFFICIAL_ALERT',
            'DISASTER_RECORD',
            'GEOSPATIAL_REFERENCE',
            'ML_EXPERIMENTAL',
            'DEMO_SYNTHETIC'
        )
    ),
    temporal_resolution VARCHAR(50),
    spatial_resolution VARCHAR(50),
    is_official BOOLEAN NOT NULL DEFAULT TRUE,
    disclaimer_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER set_updated_at_data_sources
BEFORE UPDATE ON data_sources
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 2. TABEL DATA_INGESTION_LOGS (Jejak Audit Pengambilan & Impor Data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_ingestion_logs (
    id BIGSERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    job_type VARCHAR(60) NOT NULL,
    target_identifier VARCHAR(100),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED', 'CACHED')),
    http_status_code INTEGER,
    records_fetched INTEGER NOT NULL DEFAULT 0,
    records_inserted INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingestion_logs_source_time
ON data_ingestion_logs(source_id, started_at DESC);

-- ============================================================================
-- 3. TABEL REGIONS (Hirarki Wilayah Administratif Provinsi Aceh ADM1-ADM4)
-- ============================================================================
CREATE TABLE IF NOT EXISTS regions (
    region_code VARCHAR(20) PRIMARY KEY,
    parent_code VARCHAR(20) REFERENCES regions(region_code) ON DELETE RESTRICT,
    admin_level SMALLINT NOT NULL CHECK (admin_level BETWEEN 1 AND 4),
    region_name VARCHAR(150) NOT NULL,
    region_type VARCHAR(30) NOT NULL CHECK (
        region_type IN ('PROVINSI', 'KABUPATEN', 'KOTA', 'KECAMATAN', 'GAMPONG')
    ),
    representative_adm4 VARCHAR(20),
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    elevation_m NUMERIC(7, 2),
    population INTEGER,
    is_coastal BOOLEAN DEFAULT FALSE,
    topography_zone VARCHAR(40) CHECK (
        topography_zone IN ('PESISIR_TIMUR_UTARA', 'PESISIR_BARAT_SELATAN', 'DATARAN_TINGGI_TENGAH', 'KEPULAUAN')
    ),
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'Kemendagri & BPS Provinsi Aceh',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regions_admin_level ON regions(admin_level);
CREATE INDEX IF NOT EXISTS idx_regions_parent_code ON regions(parent_code);

CREATE TRIGGER set_updated_at_regions
BEFORE UPDATE ON regions
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 4. TABEL ADMINISTRATIVE_BOUNDARIES (Geometri Spasial Wilayah PostGIS)
-- ============================================================================
CREATE TABLE IF NOT EXISTS administrative_boundaries (
    id SERIAL PRIMARY KEY,
    region_code VARCHAR(20) UNIQUE NOT NULL REFERENCES regions(region_code) ON DELETE CASCADE,
    admin_level SMALLINT NOT NULL CHECK (admin_level BETWEEN 1 AND 4),
    area_sq_km NUMERIC(10, 2),
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL,
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'BIG - Badan Informasi Geospasial',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_boundaries_geom
ON administrative_boundaries USING GIST (geom);

CREATE TRIGGER set_updated_at_admin_boundaries
BEFORE UPDATE ON administrative_boundaries
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 5. TABEL WEATHER_STATIONS (Stasiun Pengamatan Meteorologi/Klimatologi BMKG)
-- ============================================================================
CREATE TABLE IF NOT EXISTS weather_stations (
    id SERIAL PRIMARY KEY,
    wmo_id VARCHAR(20) UNIQUE NOT NULL,
    station_name VARCHAR(150) NOT NULL,
    station_type VARCHAR(50) NOT NULL CHECK (
        station_type IN ('METEOROLOGI_SINOPTIK', 'KLIMATOLOGI', 'GEOFISIKA', 'AWS', 'ARG', 'POS_HUJAN')
    ),
    region_code VARCHAR(20) NOT NULL REFERENCES regions(region_code) ON DELETE RESTRICT,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    elevation_m NUMERIC(7, 2) NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'BMKG - Pusat Database / UPT Aceh',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weather_stations_geom
ON weather_stations USING GIST (geom);

CREATE TRIGGER set_updated_at_weather_stations
BEFORE UPDATE ON weather_stations
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 6. TABEL WEATHER_OBSERVATIONS (Data Observasi Historis Harian Stasiun BMKG)
-- ============================================================================
CREATE TABLE IF NOT EXISTS weather_observations (
    id BIGSERIAL PRIMARY KEY,
    station_id INTEGER NOT NULL REFERENCES weather_stations(id) ON DELETE RESTRICT,
    source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    observation_date DATE NOT NULL,
    temp_min_c NUMERIC(4, 1) CHECK (temp_min_c IS NULL OR (temp_min_c BETWEEN 5.0 AND 45.0)),
    temp_max_c NUMERIC(4, 1) CHECK (temp_max_c IS NULL OR (temp_max_c BETWEEN 5.0 AND 45.0)),
    temp_avg_c NUMERIC(4, 1) CHECK (temp_avg_c IS NULL OR (temp_avg_c BETWEEN 5.0 AND 45.0)),
    humidity_avg_pct NUMERIC(5, 2) CHECK (humidity_avg_pct IS NULL OR (humidity_avg_pct BETWEEN 0.0 AND 100.0)),
    rainfall_mm NUMERIC(6, 2) CHECK (rainfall_mm IS NULL OR (rainfall_mm >= 0.0 AND rainfall_mm <= 1000.0)),
    is_trace_rainfall BOOLEAN NOT NULL DEFAULT FALSE,
    is_missing_rainfall BOOLEAN NOT NULL DEFAULT FALSE,
    sunshine_hours NUMERIC(4, 1) CHECK (sunshine_hours IS NULL OR (sunshine_hours BETWEEN 0.0 AND 13.0)),
    wind_speed_max_ms NUMERIC(5, 2) CHECK (wind_speed_max_ms IS NULL OR (wind_speed_max_ms >= 0.0)),
    wind_dir_max_deg NUMERIC(5, 1) CHECK (wind_dir_max_deg IS NULL OR (wind_dir_max_deg BETWEEN 0.0 AND 360.0)),
    wind_speed_avg_ms NUMERIC(5, 2) CHECK (wind_speed_avg_ms IS NULL OR (wind_speed_avg_ms >= 0.0)),
    wind_dir_predominant VARCHAR(15),
    rainfall_category VARCHAR(20) NOT NULL CHECK (
        rainfall_category IN ('NO_RAIN', 'LIGHT', 'MODERATE', 'HEAVY', 'VERY_HEAVY', 'EXTREME', 'MISSING')
    ),
    quality_flag VARCHAR(30) NOT NULL DEFAULT 'VALID',
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'BMKG Data Online - Observasi Stasiun',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_station_observation_date UNIQUE (station_id, observation_date)
);

CREATE INDEX IF NOT EXISTS idx_obs_date ON weather_observations(observation_date DESC);
CREATE INDEX IF NOT EXISTS idx_obs_station_date ON weather_observations(station_id, observation_date DESC);
CREATE INDEX IF NOT EXISTS idx_obs_rainfall_cat ON weather_observations(rainfall_category);

CREATE TRIGGER set_updated_at_weather_observations
BEFORE UPDATE ON weather_observations
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 7. TABEL WEATHER_FORECASTS (Data Prakiraan Cuaca 3-Jaman Resmi API BMKG)
-- ============================================================================
CREATE TABLE IF NOT EXISTS weather_forecasts (
    id BIGSERIAL PRIMARY KEY,
    region_code VARCHAR(20) NOT NULL REFERENCES regions(region_code) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    analysis_time TIMESTAMPTZ NOT NULL,
    forecast_time_utc TIMESTAMPTZ NOT NULL,
    forecast_time_local TIMESTAMP NOT NULL,
    temperature_c NUMERIC(4, 1) NOT NULL,
    humidity_pct NUMERIC(5, 2) NOT NULL CHECK (humidity_pct BETWEEN 0.0 AND 100.0),
    weather_code INTEGER,
    weather_desc_id VARCHAR(100) NOT NULL,
    weather_desc_en VARCHAR(100),
    wind_speed_kmh NUMERIC(6, 2) NOT NULL CHECK (wind_speed_kmh >= 0.0),
    wind_speed_ms NUMERIC(6, 2) NOT NULL CHECK (wind_speed_ms >= 0.0),
    wind_dir_cardinal VARCHAR(15),
    wind_dir_deg NUMERIC(5, 1),
    cloud_cover_pct NUMERIC(5, 2) CHECK (cloud_cover_pct IS NULL OR (cloud_cover_pct BETWEEN 0.0 AND 100.0)),
    visibility_text VARCHAR(30),
    visibility_m INTEGER,
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'API Prakiraan Cuaca Publik BMKG (Resmi)',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_region_forecast_time UNIQUE (region_code, forecast_time_utc)
);

CREATE INDEX IF NOT EXISTS idx_forecasts_region_time
ON weather_forecasts(region_code, forecast_time_utc ASC);

CREATE TRIGGER set_updated_at_weather_forecasts
BEFORE UPDATE ON weather_forecasts
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 8. TABEL WEATHER_ALERTS (Peringatan Dini Cuaca Nowcasting CAP BMKG)
-- ============================================================================
CREATE TABLE IF NOT EXISTS weather_alerts (
    id BIGSERIAL PRIMARY KEY,
    cap_identifier VARCHAR(120) UNIQUE NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    sender VARCHAR(150) NOT NULL,
    sent_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(30) NOT NULL,
    msg_type VARCHAR(30) NOT NULL,
    event_type VARCHAR(120) NOT NULL,
    urgency VARCHAR(30) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    certainty VARCHAR(30) NOT NULL,
    effective_time TIMESTAMPTZ NOT NULL,
    onset_time TIMESTAMPTZ,
    expires_time TIMESTAMPTZ NOT NULL,
    headline TEXT NOT NULL,
    description TEXT NOT NULL,
    instruction TEXT,
    official_web_url TEXT,
    cap_xml_url TEXT NOT NULL,
    affected_areas_text TEXT NOT NULL,
    geom GEOMETRY(MultiPolygon, 4326),
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'Peringatan Dini Cuaca Resmi BMKG (CAP v1.2)',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_expires_time ON weather_alerts(expires_time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_geom ON weather_alerts USING GIST (geom);

CREATE TRIGGER set_updated_at_weather_alerts
BEFORE UPDATE ON weather_alerts
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 9. TABEL DISASTER_EVENTS (Riwayat Kejadian Bencana BPBA Aceh / DIBI BNPB)
-- ============================================================================
CREATE TABLE IF NOT EXISTS disaster_events (
    id BIGSERIAL PRIMARY KEY,
    event_code VARCHAR(80) UNIQUE NOT NULL,
    source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    region_code VARCHAR(20) NOT NULL REFERENCES regions(region_code) ON DELETE RESTRICT,
    disaster_type VARCHAR(50) NOT NULL CHECK (
        disaster_type IN (
            'BANJIR',
            'BANJIR_BANDANG',
            'TANAH_LONGSOR',
            'ANGIN_KENCANG',
            'CUACA_EKSTREM',
            'GELOMBANG_PASANG_ABRASI',
            'KEKERINGAN'
        )
    ),
    event_date DATE NOT NULL,
    location_detail TEXT,
    cause_description TEXT,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    geom GEOMETRY(Point, 4326),
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'BPBA Provinsi Aceh / DIBI BNPB',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_disaster_events_date ON disaster_events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_disaster_events_region ON disaster_events(region_code, disaster_type);

CREATE TRIGGER set_updated_at_disaster_events
BEFORE UPDATE ON disaster_events
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 10. TABEL DISASTER_IMPACTS (Dampak Kerusakan & Korban Bencana)
-- ============================================================================
CREATE TABLE IF NOT EXISTS disaster_impacts (
    id BIGSERIAL PRIMARY KEY,
    disaster_event_id BIGINT UNIQUE NOT NULL REFERENCES disaster_events(id) ON DELETE CASCADE,
    casualties_dead INTEGER NOT NULL DEFAULT 0 CHECK (casualties_dead >= 0),
    casualties_missing INTEGER NOT NULL DEFAULT 0 CHECK (casualties_missing >= 0),
    casualties_injured INTEGER NOT NULL DEFAULT 0 CHECK (casualties_injured >= 0),
    affected_people INTEGER NOT NULL DEFAULT 0 CHECK (affected_people >= 0),
    displaced_people INTEGER NOT NULL DEFAULT 0 CHECK (displaced_people >= 0),
    houses_heavily_damaged INTEGER NOT NULL DEFAULT 0 CHECK (houses_heavily_damaged >= 0),
    houses_moderately_damaged INTEGER NOT NULL DEFAULT 0 CHECK (houses_moderately_damaged >= 0),
    houses_lightly_damaged INTEGER NOT NULL DEFAULT 0 CHECK (houses_lightly_damaged >= 0),
    houses_submerged INTEGER NOT NULL DEFAULT 0 CHECK (houses_submerged >= 0),
    public_facilities_damaged INTEGER NOT NULL DEFAULT 0 CHECK (public_facilities_damaged >= 0),
    agricultural_area_damaged_ha NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    source_attribution VARCHAR(150) NOT NULL DEFAULT 'BPBA Provinsi Aceh / DIBI BNPB',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER set_updated_at_disaster_impacts
BEFORE UPDATE ON disaster_impacts
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 11. TABEL MODEL_PREDICTIONS (Luaran Prediksi Eksperimental Machine Learning)
-- ============================================================================
CREATE TABLE IF NOT EXISTS model_predictions (
    id BIGSERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES weather_stations(id) ON DELETE SET NULL,
    region_code VARCHAR(20) NOT NULL REFERENCES regions(region_code) ON DELETE RESTRICT,
    source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    model_name VARCHAR(80) NOT NULL,
    model_version VARCHAR(40) NOT NULL,
    dataset_version VARCHAR(60) NOT NULL,
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_date DATE NOT NULL,
    horizon_days SMALLINT NOT NULL CHECK (horizon_days >= 1),
    predicted_rainfall_mm NUMERIC(6, 2) CHECK (predicted_rainfall_mm >= 0.0),
    predicted_extreme_prob NUMERIC(5, 4) CHECK (predicted_extreme_prob BETWEEN 0.0000 AND 1.0000),
    predicted_category VARCHAR(20) NOT NULL CHECK (
        predicted_category IN ('NO_RAIN', 'LIGHT', 'MODERATE', 'HEAVY', 'VERY_HEAVY', 'EXTREME')
    ),
    top_contributing_features JSONB,
    model_metrics_snapshot JSONB,
    is_experimental BOOLEAN NOT NULL DEFAULT TRUE,
    disclaimer_label TEXT NOT NULL DEFAULT 'Analisis model eksperimental, bukan peringatan resmi BMKG.',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_model_prediction_target UNIQUE (station_id, model_name, model_version, target_date)
);

CREATE INDEX IF NOT EXISTS idx_model_predictions_target_date
ON model_predictions(target_date DESC, region_code);

CREATE TRIGGER set_updated_at_model_predictions
BEFORE UPDATE ON model_predictions
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- SEED DATA RESMI: SUMBER DATA, 23 KABUPATEN/KOTA ACEH, & 5 STASIUN BMKG ACEH
-- ============================================================================

INSERT INTO data_sources (
    source_code, source_name, organization, base_url, data_nature,
    temporal_resolution, spatial_resolution, is_official, disclaimer_text
) VALUES
(
    'BMKG_API_FORECAST',
    'API Prakiraan Cuaca Publik BMKG',
    'Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)',
    'https://api.bmkg.go.id/publik/prakiraan-cuaca',
    'OFFICIAL_FORECAST',
    '3 Jam (Horizon 3 Hari)',
    'Desa / Gampong (ADM4)',
    TRUE,
    'Data prakiraan cuaca resmi BMKG. Bukan merupakan data observasi curah hujan historis.'
),
(
    'BMKG_CAP_NOWCAST',
    'RSS & CAP Peringatan Dini Cuaca BMKG',
    'Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)',
    'https://www.bmkg.go.id/alerts/nowcast/id',
    'OFFICIAL_ALERT',
    'Real-time (Nowcasting 1-6 Jam)',
    'Poligon Wilayah Terdampak',
    TRUE,
    'Informasi peringatan dini cuaca ekstrem resmi dari BMKG.'
),
(
    'BMKG_DATA_ONLINE_OBS',
    'Data Observasi Historis Stasiun BMKG Aceh',
    'Pusat Database BMKG / UPT BMKG Provinsi Aceh',
    'https://dataonline.bmkg.go.id/',
    'OBSERVATION',
    'Harian (24 Jam pukul 07.00 WIB)',
    'Titik Koordinat Stasiun Pengamatan',
    TRUE,
    'Data pengamatan instrumen meteorologi/klimatologi resmi stasiun BMKG.'
),
(
    'BPBA_BNPB_DISASTER',
    'Data Kejadian dan Dampak Bencana Hidrometeorologi Aceh',
    'BPBA Provinsi Aceh & DIBI BNPB',
    'https://dibi.bnpb.go.id/',
    'DISASTER_RECORD',
    'Harian / Per Kejadian',
    'Kabupaten / Kota (ADM2)',
    TRUE,
    'Catatan riwayat kejadian dan dampak bencana resmi BPBA/BNPB.'
),
(
    'ACEH_SIAGA_ML_ENGINE',
    'Model Prediksi Cuaca Ekstrem Aceh Siaga Cuaca',
    'Tim Peneliti Aceh Siaga Cuaca',
    NULL,
    'ML_EXPERIMENTAL',
    'Harian (Horizon H+1 s.d. H+3)',
    'Titik Stasiun / Wilayah Representatif',
    FALSE,
    'Analisis model eksperimental, bukan peringatan resmi BMKG.'
)
ON CONFLICT (source_code) DO NOTHING;

-- Seed Provinsi Aceh (ADM1 = 11) + 23 Kabupaten/Kota (ADM2) beserta kode ADM4 representatif ibukota
INSERT INTO regions (
    region_code, parent_code, admin_level, region_name, region_type,
    representative_adm4, latitude, longitude, elevation_m, is_coastal, topography_zone
) VALUES
('11', NULL, 1, 'Provinsi Aceh', 'PROVINSI', '11.71.01.2001', 4.695135, 96.749399, 120.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.01', '11', 2, 'Kabupaten Aceh Selatan', 'KABUPATEN', '11.01.02.2001', 3.257700, 97.180300, 15.0, TRUE, 'PESISIR_BARAT_SELATAN'),
('11.02', '11', 2, 'Kabupaten Aceh Tenggara', 'KABUPATEN', '11.02.04.2001', 3.491300, 97.810800, 320.0, FALSE, 'DATARAN_TINGGI_TENGAH'),
('11.03', '11', 2, 'Kabupaten Aceh Timur', 'KABUPATEN', '11.03.03.2001', 4.950000, 97.766700, 18.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.04', '11', 2, 'Kabupaten Aceh Tengah', 'KABUPATEN', '11.04.01.2001', 4.624700, 96.849200, 1250.0, FALSE, 'DATARAN_TINGGI_TENGAH'),
('11.05', '11', 2, 'Kabupaten Aceh Barat', 'KABUPATEN', '11.05.01.2001', 4.144900, 96.126400, 8.0, TRUE, 'PESISIR_BARAT_SELATAN'),
('11.06', '11', 2, 'Kabupaten Aceh Besar', 'KABUPATEN', '11.06.08.2001', 5.291700, 95.597200, 35.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.07', '11', 2, 'Kabupaten Pidie', 'KABUPATEN', '11.07.16.2001', 5.384700, 95.960800, 12.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.08', '11', 2, 'Kabupaten Aceh Utara', 'KABUPATEN', '11.08.02.2001', 5.051700, 97.318100, 14.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.09', '11', 2, 'Kabupaten Simeulue', 'KABUPATEN', '11.09.04.2001', 2.478900, 96.376100, 10.0, TRUE, 'KEPULAUAN'),
('11.10', '11', 2, 'Kabupaten Aceh Singkil', 'KABUPATEN', '11.10.04.2001', 2.288900, 97.795000, 7.0, TRUE, 'PESISIR_BARAT_SELATAN'),
('11.11', '11', 2, 'Kabupaten Bireuen', 'KABUPATEN', '11.11.13.2001', 5.201400, 96.701900, 15.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.12', '11', 2, 'Kabupaten Aceh Barat Daya', 'KABUPATEN', '11.12.01.2001', 3.743100, 96.832200, 18.0, TRUE, 'PESISIR_BARAT_SELATAN'),
('11.13', '11', 2, 'Kabupaten Gayo Lues', 'KABUPATEN', '11.13.01.2001', 3.983300, 97.350000, 950.0, FALSE, 'DATARAN_TINGGI_TENGAH'),
('11.14', '11', 2, 'Kabupaten Aceh Jaya', 'KABUPATEN', '11.14.04.2001', 4.631900, 95.581900, 12.0, TRUE, 'PESISIR_BARAT_SELATAN'),
('11.15', '11', 2, 'Kabupaten Nagan Raya', 'KABUPATEN', '11.15.02.2001', 4.168300, 96.321100, 22.0, TRUE, 'PESISIR_BARAT_SELATAN'),
('11.16', '11', 2, 'Kabupaten Aceh Tamiang', 'KABUPATEN', '11.16.03.2001', 4.281900, 98.058300, 15.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.17', '11', 2, 'Kabupaten Bener Meriah', 'KABUPATEN', '11.17.05.2001', 4.726700, 96.861700, 1320.0, FALSE, 'DATARAN_TINGGI_TENGAH'),
('11.18', '11', 2, 'Kabupaten Pidie Jaya', 'KABUPATEN', '11.18.01.2001', 5.241100, 96.246900, 10.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.71', '11', 2, 'Kota Banda Aceh', 'KOTA', '11.71.01.2001', 5.548300, 95.323800, 5.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.72', '11', 2, 'Kota Sabang', 'KOTA', '11.72.01.2001', 5.893300, 95.319200, 85.0, TRUE, 'KEPULAUAN'),
('11.73', '11', 2, 'Kota Lhokseumawe', 'KOTA', '11.73.02.2001', 5.180100, 97.150700, 6.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.74', '11', 2, 'Kota Langsa', 'KOTA', '11.74.02.2001', 4.468300, 97.968300, 10.0, TRUE, 'PESISIR_TIMUR_UTARA'),
('11.75', '11', 2, 'Kota Subulussalam', 'KOTA', '11.75.01.2001', 2.641900, 98.005300, 75.0, FALSE, 'PESISIR_BARAT_SELATAN')
ON CONFLICT (region_code) DO NOTHING;

-- Seed 5 Stasiun Pengamatan Utama BMKG di Provinsi Aceh
INSERT INTO weather_stations (
    wmo_id, station_name, station_type, region_code,
    latitude, longitude, elevation_m, geom, is_active
) VALUES
(
    '96001',
    'Stasiun Meteorologi Kelas I Sultan Iskandar Muda',
    'METEOROLOGI_SINOPTIK',
    '11.06',
    5.522500, 95.417000, 20.0,
    ST_SetSRID(ST_MakePoint(95.417000, 5.522500), 4326),
    TRUE
),
(
    '96002',
    'Stasiun Meteorologi Maimun Saleh Sabang',
    'METEOROLOGI_SINOPTIK',
    '11.72',
    5.874200, 95.339700, 126.0,
    ST_SetSRID(ST_MakePoint(95.339700, 5.874200), 4326),
    TRUE
),
(
    '96003',
    'Stasiun Klimatologi Aceh (Indrapuri)',
    'KLIMATOLOGI',
    '11.06',
    5.404500, 95.447200, 45.0,
    ST_SetSRID(ST_MakePoint(95.447200, 5.404500), 4326),
    TRUE
),
(
    '96009',
    'Stasiun Meteorologi Malikussaleh Aceh Utara',
    'METEOROLOGI_SINOPTIK',
    '11.08',
    5.228600, 96.947500, 8.0,
    ST_SetSRID(ST_MakePoint(96.947500, 5.228600), 4326),
    TRUE
),
(
    '96011',
    'Stasiun Meteorologi Cut Nyak Dhien Nagan Raya',
    'METEOROLOGI_SINOPTIK',
    '11.15',
    4.045000, 96.248300, 4.0,
    ST_SetSRID(ST_MakePoint(96.248300, 4.045000), 4326),
    TRUE
)
ON CONFLICT (wmo_id) DO NOTHING;