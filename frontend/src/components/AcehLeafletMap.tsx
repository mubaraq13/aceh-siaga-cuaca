"use client";

import React, { useEffect, useRef } from "react";
import L from "leaflet";

interface AcehLeafletMapProps {
  stationsGeoJson: any;
  disastersGeoJson: any;
  alertsGeoJson: any;
  showStations: boolean;
  showDisasters: boolean;
  showAlerts: boolean;
}

export default function AcehLeafletMap({
  stationsGeoJson,
  disastersGeoJson,
  alertsGeoJson,
  showStations,
  showDisasters,
  showAlerts,
}: AcehLeafletMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [4.695135, 96.749399],
      zoom: 7,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map);

    layerGroupRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    const group = layerGroupRef.current;
    if (!group) return;
    group.clearLayers();

    // 1. Layer Kepadatan Bencana Kabupaten/Kota Aceh
    if (showDisasters && disastersGeoJson?.features) {
      L.geoJSON(disastersGeoJson, {
        style: (feature) => {
          const risk = feature?.properties?.hydromet_density_class;
          const fillColor =
            risk === "TINGGI" ? "#B42318" : risk === "SEDANG" ? "#B54708" : "#18794E";
          return {
            color: "#102A43",
            weight: 1.5,
            fillColor,
            fillOpacity: 0.35,
          };
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties || {};
          layer.bindPopup(
            `<div style="font-size:12px;line-height:1.4;color:#102A43;">
              <strong>${p.region_code} - ${p.region_name}</strong><br/>
              Zona: ${p.topography_zone}<br/>
              Total Kejadian Bencana: <strong>${p.total_disaster_events}</strong><br/>
              Banjir: ${p.flood_events} | Banjir Bandang: ${p.flash_flood_events}<br/>
              Tanah Longsor: ${p.landslide_events} | Angin Ekstrem: ${p.wind_events}<br/>
              Kelas Kepadatan Bencana: <strong>${p.hydromet_density_class}</strong>
            </div>`
          );
        },
      }).addTo(group);
    }

    // 2. Layer Poligon Peringatan Dini Cuaca CAP BMKG
    if (showAlerts && alertsGeoJson?.features) {
      L.geoJSON(alertsGeoJson, {
        style: () => ({
          color: "#B42318",
          weight: 2.5,
          dashArray: "6, 4",
          fillColor: "#B42318",
          fillOpacity: 0.25,
        }),
        pointToLayer: (_feat, latlng) =>
          L.circleMarker(latlng, {
            radius: 10,
            color: "#B42318",
            fillColor: "#B42318",
            fillOpacity: 0.8,
          }),
        onEachFeature: (feature, layer) => {
          const p = feature.properties || {};
          layer.bindPopup(
            `<div style="font-size:12px;line-height:1.4;color:#102A43;">
              <strong style="color:#B42318;">PERINGATAN DINI RESMI BMKG</strong><br/>
              <strong>${p.headline || p.event_type}</strong><br/>
              Severity: ${p.severity} | Urgency: ${p.urgency}<br/>
              Wilayah: ${p.affected_areas_text}<br/>
              Berlaku s.d.: ${p.expires_time}
            </div>`
          );
        },
      }).addTo(group);
    }

    // 3. Layer 5 Titik Stasiun Pengamatan BMKG di Aceh
    if (showStations && stationsGeoJson?.features) {
      L.geoJSON(stationsGeoJson, {
        pointToLayer: (_feature, latlng) =>
          L.circleMarker(latlng, {
            radius: 8,
            color: "#FFFFFF",
            weight: 2,
            fillColor: "#173F5F",
            fillOpacity: 0.95,
          }),
        onEachFeature: (feature, layer) => {
          const p = feature.properties || {};
          layer.bindPopup(
            `<div style="font-size:12px;line-height:1.4;color:#102A43;">
              <strong>WMO ${p.wmo_id} - ${p.station_name}</strong><br/>
              Elevasi: ${p.elevation_m} mdpl | Zona: ${p.topography_zone}<br/>
              Hujan Harian Maksimum: <strong>${p.max_daily_rain_mm} mm</strong><br/>
              Hari Hujan >= 20 mm (R20mm): <strong>${p.r20mm_days} hari</strong><br/>
              Hari Hujan Ekstrem >= 50 mm (R50mm): <strong>${p.r50mm_extreme_days} hari</strong>
            </div>`
          );
        },
      }).addTo(group);
    }
  }, [stationsGeoJson, disastersGeoJson, alertsGeoJson, showStations, showDisasters, showAlerts]);

  return (
    <div
      ref={mapContainerRef}
      className="w-full h-[500px] rounded-md border border-[#DCEEFF] dark:border-[#173F5F] z-0"
      aria-label="Peta Interaktif Spasial-Temporal Cuaca dan Bencana Provinsi Aceh"
    />
  );
}
