"""
Spatio-Temporal & GIS Engine — ACEH SIAGA CUACA
File: src/geospatial/aceh_gis_analyzer.py

Mencakup:
1. Metadata & Geometri 23 Kabupaten/Kota Aceh + 5 Stasiun Pengamatan BMKG Aceh.
2. Generator layer GeoJSON standar RFC 7946 untuk Leaflet & PostGIS:
   - Layer Stasiun Cuaca + Statistik Ekstrem.
   - Layer Kabupaten/Kota + Kepadatan Kejadian Bencana Banjir & Tanah Longsor.
   - Layer Poligon Peringatan Dini Cuaca (CAP BMKG).
3. Analisis hubungan spasial zona topografi Aceh (Pesisir Barat-Selatan, Pesisir Timur-Utara,
   Dataran Tinggi Tengah, Kepulauan) dengan frekuensi hujan tinggi dan bencana hidrometeorologi.
4. Dokumentasi eksplisit keterbatasan interpolasi spasial (tidak melakukan interpolasi IDW/Kriging
   buta lintas Pegunungan Bukit Barisan dengan hanya 5 stasiun sinoptik).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.data_collection.bmkg_alerts import CAPAlertSchema

ACEH_REGENCIES_GIS: List[Dict[str, Any]] = [
    {"region_code": "11.01", "name": "Kabupaten Aceh Selatan", "lat": 3.2577, "lon": 97.1803, "elev_m": 15.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.02", "name": "Kabupaten Aceh Tenggara", "lat": 3.4913, "lon": 97.8108, "elev_m": 320.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96009"},
    {"region_code": "11.03", "name": "Kabupaten Aceh Timur", "lat": 4.9500, "lon": 97.7667, "elev_m": 18.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.04", "name": "Kabupaten Aceh Tengah", "lat": 4.6247, "lon": 96.8492, "elev_m": 1250.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96009"},
    {"region_code": "11.05", "name": "Kabupaten Aceh Barat", "lat": 4.1449, "lon": 96.1264, "elev_m": 8.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.06", "name": "Kabupaten Aceh Besar", "lat": 5.2917, "lon": 95.5972, "elev_m": 35.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96003"},
    {"region_code": "11.07", "name": "Kabupaten Pidie", "lat": 5.3847, "lon": 95.9608, "elev_m": 12.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96003"},
    {"region_code": "11.08", "name": "Kabupaten Aceh Utara", "lat": 5.0517, "lon": 97.3181, "elev_m": 14.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.09", "name": "Kabupaten Simeulue", "lat": 2.4789, "lon": 96.3761, "elev_m": 10.0, "zone": "KEPULAUAN", "nearest_wmo": "96011"},
    {"region_code": "11.10", "name": "Kabupaten Aceh Singkil", "lat": 2.2889, "lon": 97.7950, "elev_m": 7.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.11", "name": "Kabupaten Bireuen", "lat": 5.2014, "lon": 96.7019, "elev_m": 15.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.12", "name": "Kabupaten Aceh Barat Daya", "lat": 3.7431, "lon": 96.8322, "elev_m": 18.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.13", "name": "Kabupaten Gayo Lues", "lat": 3.9833, "lon": 97.3500, "elev_m": 950.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96011"},
    {"region_code": "11.14", "name": "Kabupaten Aceh Jaya", "lat": 4.6319, "lon": 95.5819, "elev_m": 12.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96003"},
    {"region_code": "11.15", "name": "Kabupaten Nagan Raya", "lat": 4.1683, "lon": 96.3211, "elev_m": 22.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
    {"region_code": "11.16", "name": "Kabupaten Aceh Tamiang", "lat": 4.2819, "lon": 98.0583, "elev_m": 15.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.17", "name": "Kabupaten Bener Meriah", "lat": 4.7267, "lon": 96.8617, "elev_m": 1320.0, "zone": "DATARAN_TINGGI_TENGAH", "nearest_wmo": "96009"},
    {"region_code": "11.18", "name": "Kabupaten Pidie Jaya", "lat": 5.2411, "lon": 96.2469, "elev_m": 10.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.71", "name": "Kota Banda Aceh", "lat": 5.5483, "lon": 95.3238, "elev_m": 5.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96001"},
    {"region_code": "11.72", "name": "Kota Sabang", "lat": 5.8933, "lon": 95.3192, "elev_m": 85.0, "zone": "KEPULAUAN", "nearest_wmo": "96002"},
    {"region_code": "11.73", "name": "Kota Lhokseumawe", "lat": 5.1801, "lon": 97.1507, "elev_m": 6.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.74", "name": "Kota Langsa", "lat": 4.4683, "lon": 97.9683, "elev_m": 10.0, "zone": "PESISIR_TIMUR_UTARA", "nearest_wmo": "96009"},
    {"region_code": "11.75", "name": "Kota Subulussalam", "lat": 2.6419, "lon": 98.0053, "elev_m": 75.0, "zone": "PESISIR_BARAT_SELATAN", "nearest_wmo": "96011"},
]

ACEH_STATIONS_GIS: List[Dict[str, Any]] = [
    {"wmo_id": "96001", "station_name": "Stasiun Meteorologi Kelas I Sultan Iskandar Muda", "region_code": "11.06", "lat": 5.5225, "lon": 95.4170, "elev_m": 20.0, "zone": "PESISIR_TIMUR_UTARA"},
    {"wmo_id": "96002", "station_name": "Stasiun Meteorologi Maimun Saleh Sabang", "region_code": "11.72", "lat": 5.8742, "lon": 95.3397, "elev_m": 126.0, "zone": "KEPULAUAN"},
    {"wmo_id": "96003", "station_name": "Stasiun Klimatologi Aceh (Indrapuri)", "region_code": "11.06", "lat": 5.4045, "lon": 95.4472, "elev_m": 45.0, "zone": "PESISIR_TIMUR_UTARA"},
    {"wmo_id": "96009", "station_name": "Stasiun Meteorologi Malikussaleh Aceh Utara", "region_code": "11.08", "lat": 5.2286, "lon": 96.9475, "elev_m": 8.0, "zone": "PESISIR_TIMUR_UTARA"},
    {"wmo_id": "96011", "station_name": "Stasiun Meteorologi Cut Nyak Dhien Nagan Raya", "region_code": "11.15", "lat": 4.0450, "lon": 96.2483, "elev_m": 4.0, "zone": "PESISIR_BARAT_SELATAN"},
]

SPATIAL_LIMITATION_STATEMENT = (
    "KETERBATASAN ANALISIS SPASIAL: Jaringan stasiun pengamatan sinoptik utama BMKG yang terbuka "
    "di Provinsi Aceh terdiri atas 5 stasiun yang terkonsentrasi di wilayah pesisir dan lembah "
    "(Aceh Besar, Sabang, Aceh Utara, dan Nagan Raya). Mengingat topografi Pegunungan Bukit Barisan "
    "di bagian tengah Aceh (elevasi >1.000 mdpl) menciptakan efek orografis yang tajam, sistem ini "
    "TIDAK melakukan interpolasi permukaan kontinu (IDW/Kriging) dari 5 titik stasiun ke seluruh "
    "kabupaten pegunungan untuk menghindari galat estimasi yang menyesatkan. Analisis wilayah "
    "disajikan pada titik lokasi stasiun yang terverifikasi dan agregasi batas administrasi kabupaten/kota."
)


class AcehGISAnalyzer:
    """Mesin analisis geospasial dan pembentuk layer GeoJSON untuk Provinsi Aceh."""

    @staticmethod
    def generate_demo_disaster_dataset(
        output_path: Path = Path("data/demo/demo_bpba_disasters_aceh.csv"),
    ) -> Path:
        """
        Membuat dataset DEMO riwayat kejadian bencana hidrometeorologi Aceh (2021-2026)
        dengan distribusi spasial realistis (banjir tinggi di Aceh Utara, Aceh Timur, Aceh Tamiang,
        Aceh Barat, Nagan Raya; tanah longsor tinggi di Aceh Tengah, Bener Meriah, Gayo Lues).
        Diberi label eksplisit DEMO_SYNTHETIC.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(seed=20261119)

        high_flood_regions = ["11.08", "11.03", "11.16", "11.05", "11.15", "11.01", "11.10", "11.06"]
        high_landslide_regions = ["11.04", "11.17", "11.13", "11.02", "11.14", "11.06"]
        all_codes = [r["region_code"] for r in ACEH_REGENCIES_GIS]

        rows: List[Dict[str, Any]] = []
        dates = pd.date_range("2021-01-05", "2026-10-28", freq="7D")

        event_idx = 1
        for d in dates:
            month = d.month
            # Frekuensi bencana meningkat pada puncak musim hujan Aceh (Okt-Jan & Apr-Mei)
            is_wet_peak = month in (10, 11, 12, 1, 4, 5)
            n_events = int(rng.choice([0, 1, 2, 3], p=[0.25, 0.40, 0.25, 0.10] if is_wet_peak else [0.65, 0.25, 0.08, 0.02]))

            for _ in range(n_events):
                dtype_roll = rng.random()
                if dtype_roll < 0.58:
                    dtype = "BANJIR"
                    reg = str(rng.choice(high_flood_regions if rng.random() < 0.75 else all_codes))
                elif dtype_roll < 0.72:
                    dtype = "BANJIR_BANDANG"
                    reg = str(rng.choice(high_landslide_regions + high_flood_regions[:3]))
                elif dtype_roll < 0.90:
                    dtype = "TANAH_LONGSOR"
                    reg = str(rng.choice(high_landslide_regions if rng.random() < 0.80 else all_codes))
                else:
                    dtype = "ANGIN_KENCANG"
                    reg = str(rng.choice(all_codes))

                rows.append(
                    {
                        "event_code": f"DEMO-BPBA-{d.year}-{event_idx:04d}",
                        "region_code": reg,
                        "disaster_type": dtype,
                        "event_date": d.strftime("%Y-%m-%d"),
                        "casualties_dead": int(rng.choice([0, 0, 0, 1, 2], p=[0.90, 0.04, 0.03, 0.02, 0.01])),
                        "casualties_missing": 0,
                        "casualties_injured": int(rng.integers(0, 6)),
                        "affected_people": int(rng.integers(50, 3500)) if "BANJIR" in dtype else int(rng.integers(10, 300)),
                        "displaced_people": int(rng.integers(0, 800)) if "BANJIR" in dtype else int(rng.integers(0, 80)),
                        "houses_heavily_damaged": int(rng.integers(0, 15)),
                        "houses_moderately_damaged": int(rng.integers(0, 25)),
                        "houses_lightly_damaged": int(rng.integers(0, 45)),
                        "houses_submerged": int(rng.integers(20, 950)) if "BANJIR" in dtype else 0,
                        "public_facilities_damaged": int(rng.integers(0, 5)),
                        "data_mode": "DEMO_SYNTHETIC_DISASTER_RECORD",
                    }
                )
                event_idx += 1

        df_dis = pd.DataFrame(rows)
        df_dis.to_csv(output_path, index=False)
        return output_path

    @staticmethod
    def build_stations_geojson(obs_df: pd.DataFrame) -> Dict[str, Any]:
        """Membentuk GeoJSON FeatureCollection untuk 5 Stasiun BMKG Aceh beserta ringkasan iklim ekstrem."""
        work = obs_df.copy()
        work["is_extreme_50mm"] = (pd.to_numeric(work["rainfall_mm"], errors="coerce") >= 50.0).astype(int)
        work["is_heavy_20mm"] = (pd.to_numeric(work["rainfall_mm"], errors="coerce") >= 20.0).astype(int)

        stats_by_wmo = (
            work.groupby("wmo_id", as_index=False)
            .agg(
                obs_days=("rainfall_mm", "count"),
                mean_daily_rain_mm=("rainfall_mm", "mean"),
                max_daily_rain_mm=("rainfall_mm", "max"),
                r20mm_days=("is_heavy_20mm", "sum"),
                r50mm_extreme_days=("is_extreme_50mm", "sum"),
                mean_temp_c=("temp_avg_c", "mean"),
                mean_humidity_pct=("humidity_avg_pct", "mean"),
            )
            .round(2)
            .set_index("wmo_id")
            .to_dict(orient="index")
        )

        features: List[Dict[str, Any]] = []
        for st in ACEH_STATIONS_GIS:
            wmo = st["wmo_id"]
            st_stat = stats_by_wmo.get(wmo, {})
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(st["lon"]), float(st["lat"])],
                    },
                    "properties": {
                        "wmo_id": wmo,
                        "station_name": st["station_name"],
                        "region_code": st["region_code"],
                        "elevation_m": st["elev_m"],
                        "topography_zone": st["zone"],
                        "obs_days": int(st_stat.get("obs_days", 0)),
                        "mean_daily_rain_mm": float(st_stat.get("mean_daily_rain_mm", 0.0)),
                        "max_daily_rain_mm": float(st_stat.get("max_daily_rain_mm", 0.0)),
                        "r20mm_days": int(st_stat.get("r20mm_days", 0)),
                        "r50mm_extreme_days": int(st_stat.get("r50mm_extreme_days", 0)),
                        "mean_temp_c": float(st_stat.get("mean_temp_c", 0.0)),
                        "mean_humidity_pct": float(st_stat.get("mean_humidity_pct", 0.0)),
                        "data_nature": "OBSERVATION_STATION",
                        "source_attribution": "BMKG Provinsi Aceh",
                    },
                }
            )

        return {
            "type": "FeatureCollection",
            "metadata": {
                "layer_name": "Stasiun Pengamatan Cuaca BMKG Provinsi Aceh",
                "spatial_limitation_note": SPATIAL_LIMITATION_STATEMENT,
            },
            "features": features,
        }

    @staticmethod
    def _create_bounding_box_polygon(lon: float, lat: float, delta: float = 0.18) -> List[List[List[float]]]:
        """Membuat poligon kotak batas representatif kabupaten/kota jika shapefile detail BIG belum dimuat."""
        return [
            [
                [round(lon - delta, 5), round(lat - delta, 5)],
                [round(lon + delta, 5), round(lat - delta, 5)],
                [round(lon + delta, 5), round(lat + delta, 5)],
                [round(lon - delta, 5), round(lat + delta, 5)],
                [round(lon - delta, 5), round(lat - delta, 5)],
            ]
        ]

    @classmethod
    def build_disaster_density_geojson(cls, disaster_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Membentuk GeoJSON 23 Kabupaten/Kota Aceh dengan kepadatan kejadian bencana
        (banjir, banjir bandang, tanah longsor, angin kencang) dan dampak rumah terendam.
        """
        agg = (
            disaster_df.groupby("region_code", as_index=False)
            .agg(
                total_events=("event_code", "count"),
                flood_events=("disaster_type", lambda s: int((s == "BANJIR").sum())),
                flash_flood_events=("disaster_type", lambda s: int((s == "BANJIR_BANDANG").sum())),
                landslide_events=("disaster_type", lambda s: int((s == "TANAH_LONGSOR").sum())),
                wind_events=("disaster_type", lambda s: int((s.isin(["ANGIN_KENCANG", "CUACA_EKSTREM"])).sum())),
                total_affected_people=("affected_people", "sum"),
                total_houses_submerged=("houses_submerged", "sum"),
            )
            .set_index("region_code")
            .to_dict(orient="index")
        )

        features: List[Dict[str, Any]] = []
        for reg in ACEH_REGENCIES_GIS:
            code = reg["region_code"]
            d_stat = agg.get(code, {})
            total_ev = int(d_stat.get("total_events", 0))
            risk_class = "TINGGI" if total_ev >= 20 else ("SEDANG" if total_ev >= 10 else "RENDAH")

            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": cls._create_bounding_box_polygon(reg["lon"], reg["lat"]),
                    },
                    "properties": {
                        "region_code": code,
                        "region_name": reg["name"],
                        "centroid_lat": reg["lat"],
                        "centroid_lon": reg["lon"],
                        "elevation_m": reg["elev_m"],
                        "topography_zone": reg["zone"],
                        "nearest_bmkg_station_wmo": reg["nearest_wmo"],
                        "total_disaster_events": total_ev,
                        "flood_events": int(d_stat.get("flood_events", 0)),
                        "flash_flood_events": int(d_stat.get("flash_flood_events", 0)),
                        "landslide_events": int(d_stat.get("landslide_events", 0)),
                        "wind_events": int(d_stat.get("wind_events", 0)),
                        "total_affected_people": int(d_stat.get("total_affected_people", 0)),
                        "total_houses_submerged": int(d_stat.get("total_houses_submerged", 0)),
                        "hydromet_density_class": risk_class,
                    },
                }
            )

        return {
            "type": "FeatureCollection",
            "metadata": {
                "layer_name": "Peta Kepadatan Kejadian Bencana Hidrometeorologi Kabupaten/Kota Aceh",
                "spatial_limitation_note": SPATIAL_LIMITATION_STATEMENT,
            },
            "features": features,
        }

    @staticmethod
    def build_active_alerts_geojson(alerts: List[CAPAlertSchema]) -> Dict[str, Any]:
        """Membentuk GeoJSON poligon peringatan dini cuaca aktif dari dokumen CAP BMKG."""
        features: List[Dict[str, Any]] = []
        for alert in alerts:
            if alert.polygons_geojson:
                geometry: Dict[str, Any] = {
                    "type": "MultiPolygon",
                    "coordinates": [[ring] for ring in alert.polygons_geojson],
                }
            else:
                # Fallback titik pusat Provinsi Aceh jika dokumen CAP hanya mencantumkan teks wilayah tanpa tag <polygon>
                geometry = {"type": "Point", "coordinates": [96.749399, 4.695135]}

            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "cap_identifier": alert.cap_identifier,
                        "headline": alert.headline,
                        "event_type": alert.event_type,
                        "severity": alert.severity,
                        "urgency": alert.urgency,
                        "certainty": alert.certainty,
                        "effective_time": alert.effective_time.isoformat(),
                        "expires_time": alert.expires_time.isoformat(),
                        "affected_areas_text": alert.affected_areas_text,
                        "official_web_url": alert.official_web_url,
                        "source_attribution": alert.source_attribution,
                        "data_nature": "OFFICIAL_ALERT",
                    },
                }
            )

        return {
            "type": "FeatureCollection",
            "metadata": {
                "layer_name": "Poligon Peringatan Dini Cuaca Aktif BMKG (CAP v1.2)",
                "active_alerts_count": len(features),
            },
            "features": features,
        }

    @staticmethod
    def analyze_spatiotemporal_weather_disaster_link(
        obs_df: pd.DataFrame,
        disaster_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Menganalisis hubungan spasial-temporal antara zona topografi Aceh,
        frekuensi hujan lebat-ekstrem (>= 50 mm/hari), dan kejadian bencana banjir/longsor.
        """
        st_zone_map = {s["wmo_id"]: s["zone"] for s in ACEH_STATIONS_GIS}
        reg_zone_map = {r["region_code"]: r["zone"] for r in ACEH_REGENCIES_GIS}

        obs = obs_df.copy()
        obs["topography_zone"] = obs["wmo_id"].astype(str).map(st_zone_map)
        obs["is_extreme_50mm"] = (pd.to_numeric(obs["rainfall_mm"], errors="coerce") >= 50.0).astype(int)
        obs["month"] = pd.to_datetime(obs["observation_date"]).dt.month

        dis = disaster_df.copy()
        dis["topography_zone"] = dis["region_code"].astype(str).map(reg_zone_map)
        dis["month"] = pd.to_datetime(dis["event_date"]).dt.month

        rain_by_zone = (
            obs.groupby("topography_zone", as_index=False)
            .agg(
                mean_daily_rainfall_mm=("rainfall_mm", "mean"),
                max_daily_rainfall_mm=("rainfall_mm", "max"),
                extreme_50mm_days=("is_extreme_50mm", "sum"),
            )
            .round(2)
            .to_dict(orient="records")
        )

        disaster_by_zone = (
            dis.groupby("topography_zone", as_index=False)
            .agg(
                total_disasters=("event_code", "count"),
                flood_count=("disaster_type", lambda s: int(s.isin(["BANJIR", "BANJIR_BANDANG"]).sum())),
                landslide_count=("disaster_type", lambda s: int((s == "TANAH_LONGSOR").sum())),
                total_affected_people=("affected_people", "sum"),
            )
            .to_dict(orient="records")
        )

        # Korelasi temporal bulanan antara jumlah hari hujan ekstrem Aceh dan jumlah kejadian bencana
        monthly_ext = obs.groupby("month", as_index=False)["is_extreme_50mm"].sum()
        monthly_dis = dis.groupby("month", as_index=False)["event_code"].count().rename(columns={"event_code": "disaster_count"})
        merged_monthly = pd.merge(monthly_ext, monthly_dis, on="month", how="inner")

        monthly_corr = 0.0
        if len(merged_monthly) >= 3:
            monthly_corr = round(float(merged_monthly["is_extreme_50mm"].corr(merged_monthly["disaster_count"], method="spearman")), 4)

        return {
            "spatial_limitation_statement": SPATIAL_LIMITATION_STATEMENT,
            "rainfall_by_topography_zone": rain_by_zone,
            "disasters_by_topography_zone": disaster_by_zone,
            "monthly_extreme_rain_vs_disaster_spearman_rho": monthly_corr,
        }
