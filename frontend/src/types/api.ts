export type DataCategory =
  | "OFFICIAL_BMKG_FORECAST"
  | "OFFICIAL_BMKG_ALERT"
  | "HISTORICAL_OBSERVATION"
  | "SPATIOTEMPORAL_GIS"
  | "EXPERIMENTAL_ML_PREDICTION"
  | "DISASTER_AND_PREPAREDNESS"
  | "DASHBOARD_OVERVIEW"
  | "GEOSPATIAL_REFERENCE"
  | "SYSTEM_HEALTH";

export interface StandardAPIEnvelope<T> {
  status: string;
  data_category: DataCategory;
  source_attribution: string;
  disclaimer: string;
  last_updated_wib: string;
  api_health: string;
  is_demo_mode: boolean;
  data: T;
}

export interface RegencyItem {
  region_code: string;
  region_name: string;
  representative_adm4: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  topography_zone: string;
  nearest_bmkg_station_wmo: string;
}

export interface ForecastSlot {
  forecast_time_utc: string;
  forecast_time_local: string;
  analysis_time: string;
  temperature_c: number;
  humidity_pct: number;
  weather_code: number | null;
  weather_desc_id: string;
  weather_desc_en: string | null;
  wind_speed_kmh: number;
  wind_speed_ms: number;
  wind_dir_cardinal: string | null;
  wind_dir_deg: number | null;
  cloud_cover_pct: number | null;
  visibility_text: string | null;
}

export interface ActiveAlertItem {
  cap_identifier: string;
  sender: string;
  sent_time: string;
  status: string;
  msg_type: string;
  event_type: string;
  urgency: string;
  severity: string;
  certainty: string;
  effective_time: string;
  onset_time: string | null;
  expires_time: string;
  headline: string;
  description: string;
  instruction: string | null;
  official_web_url: string;
  cap_xml_url: string;
  affected_areas_text: string;
  polygons_geojson: number[][][];
  source_attribution: string;
}

export interface StationPredictionItem {
  wmo_id: string;
  station_name: string;
  region_code: string;
  last_observation_date: string;
  target_prediction_date: string;
  horizon_days: number;
  predicted_rainfall_mm: number;
  predicted_extreme_probability: number;
  decision_threshold: number;
  is_potential_heavy_rain: boolean;
  predicted_category: string;
  regression_model_used: string;
  classification_model_used: string;
  model_version: string;
  dataset_version: string;
  predicted_at_wib: string;
  top_contributing_features: Array<{ feature: string; importance: number }>;
  is_experimental: boolean;
  disclaimer_label: string;
}
