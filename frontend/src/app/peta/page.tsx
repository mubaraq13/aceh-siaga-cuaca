"use client";

import React, { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { fetchFromBackend } from "@/lib/api";
import { StandardAPIEnvelope } from "@/types/api";
import ProvenanceHeader from "@/components/ProvenanceHeader";
import DataStateWrapper from "@/components/DataStateWrapper";

const AcehLeafletMap = dynamic(() => import("@/components/AcehLeafletMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[500px] flex items-center justify-center bg-[#F5F8FC] dark:bg-[#0A1929] border border-[#DCEEFF] rounded-md text-sm font-semibold">
      Memuat kanvas peta interaktif Provinsi Aceh...
    </div>
  ),
});

interface GisLayersPayload {
  spatial_limitation_note: string;
  layers: {
    weather_stations: any;
    regency_disaster_density: any;
    active_weather_alerts: any;
  };
}

export default function PetaInteraktifPage() {
  const [envelope, setEnvelope] = useState<StandardAPIEnvelope<GisLayersPayload> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [showStations, setShowStations] = useState<boolean>(true);
  const [showDisasters, setShowDisasters] = useState<boolean>(true);
  const [showAlerts, setShowAlerts] = useState<boolean>(true);

  const loadGis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchFromBackend<GisLayersPayload>("/gis/layers");
      setEnvelope(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat layer geospasial Aceh.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGis();
  }, [loadGis]);

  const gisData = envelope?.data;

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
        <h1 className="text-xl font-extrabold text-[#102A43] dark:text-white">
          Peta Interaktif Spasial-Temporal Cuaca & Bencana Hidrometeorologi Aceh
        </h1>
        <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
          Klik pada titik stasiun BMKG, poligon kabupaten/kota, atau area peringatan dini untuk melihat rincian telemetri iklim ekstrem dan riwayat kejadian banjir/longsor.
        </p>
      </div>

      <DataStateWrapper loading={loading} error={error} isEmpty={!gisData} onRetry={loadGis}>
        {envelope && gisData && (
          <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden">
            <ProvenanceHeader
              category="SPATIOTEMPORAL_GIS"
              sourceAttribution={envelope.source_attribution}
              lastUpdatedWib={envelope.last_updated_wib}
              apiHealth={envelope.api_health}
              disclaimer={gisData.spatial_limitation_note}
            />

            <div className="p-5 space-y-5">
              {/* Kontrol Layer & Legenda Peta yang Jelas */}
              <div className="flex flex-wrap items-center justify-between gap-4 bg-[#F5F8FC] dark:bg-[#0A1929] p-3.5 rounded-md border border-[#DCEEFF] dark:border-[#173F5F]">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-xs font-bold">Lapisan Peta (Layers):</span>
                  <button
                    type="button"
                    onClick={() => setShowStations((s) => !s)}
                    aria-pressed={showStations}
                    className={`min-h-[44px] px-3 py-1.5 text-xs font-bold rounded-md border ${
                      showStations
                        ? "bg-[#173F5F] text-white border-[#173F5F]"
                        : "bg-white dark:bg-[#102A43] text-[#102A43] dark:text-white border-[#173F5F]"
                    }`}
                  >
                    {showStations ? "[Aktif]" : "[Nonaktif]"} 5 Stasiun BMKG Aceh
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowDisasters((s) => !s)}
                    aria-pressed={showDisasters}
                    className={`min-h-[44px] px-3 py-1.5 text-xs font-bold rounded-md border ${
                      showDisasters
                        ? "bg-[#173F5F] text-white border-[#173F5F]"
                        : "bg-white dark:bg-[#102A43] text-[#102A43] dark:text-white border-[#173F5F]"
                    }`}
                  >
                    {showDisasters ? "[Aktif]" : "[Nonaktif]"} Kepadatan Bencana 23 Kab/Kota
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAlerts((s) => !s)}
                    aria-pressed={showAlerts}
                    className={`min-h-[44px] px-3 py-1.5 text-xs font-bold rounded-md border ${
                      showAlerts
                        ? "bg-[#B42318] text-white border-[#B42318]"
                        : "bg-white dark:bg-[#102A43] text-[#102A43] dark:text-white border-[#B42318]"
                    }`}
                  >
                    {showAlerts ? "[Aktif]" : "[Nonaktif]"} Poligon Peringatan Dini CAP
                  </button>
                </div>

                {/* Legenda Visual */}
                <div className="flex flex-wrap items-center gap-4 text-xs font-semibold">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block w-3.5 h-3.5 rounded-full bg-[#173F5F] border border-white" />
                    Titik Stasiun BMKG
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block w-3.5 h-3.5 bg-[#B42318]" />
                    Bencana Tinggi (&ge;20 kejadian)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block w-3.5 h-3.5 bg-[#B54708]" />
                    Bencana Sedang (10-19 kejadian)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block w-3.5 h-3.5 bg-[#18794E]" />
                    Bencana Rendah (&lt;10 kejadian)
                  </span>
                </div>
              </div>

              <AcehLeafletMap
                stationsGeoJson={gisData.layers.weather_stations}
                disastersGeoJson={gisData.layers.regency_disaster_density}
                alertsGeoJson={gisData.layers.active_weather_alerts}
                showStations={showStations}
                showDisasters={showDisasters}
                showAlerts={showAlerts}
              />

              {/* Tabel Ringkasan Spasial 23 Kabupaten/Kota */}
              <div className="pt-4">
                <h2 className="text-base font-bold text-[#102A43] dark:text-white mb-2">
                  Matriks Spasial Kejadian Bencana Hidrometeorologi per Kabupaten/Kota di Aceh
                </h2>
                <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                  <table className="w-full text-left border-collapse text-xs tabular-nums">
                    <thead>
                      <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                        <th className="py-2.5 px-3 font-bold">Kode</th>
                        <th className="py-2.5 px-3 font-bold">Kabupaten / Kota</th>
                        <th className="py-2.5 px-3 font-bold">Zona Topografi</th>
                        <th className="py-2.5 px-3 font-bold">Banjir</th>
                        <th className="py-2.5 px-3 font-bold">Banjir Bandang</th>
                        <th className="py-2.5 px-3 font-bold">Tanah Longsor</th>
                        <th className="py-2.5 px-3 font-bold">Total Kejadian</th>
                        <th className="py-2.5 px-3 font-bold">Kepadatan</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                      {gisData.layers.regency_disaster_density.features.map((f: any) => {
                        const p = f.properties;
                        return (
                          <tr key={p.region_code}>
                            <td className="py-2 px-3 font-mono font-bold">{p.region_code}</td>
                            <td className="py-2 px-3 font-semibold">{p.region_name}</td>
                            <td className="py-2 px-3">{p.topography_zone}</td>
                            <td className="py-2 px-3">{p.flood_events}</td>
                            <td className="py-2 px-3">{p.flash_flood_events}</td>
                            <td className="py-2 px-3">{p.landslide_events}</td>
                            <td className="py-2 px-3 font-bold">{p.total_disaster_events}</td>
                            <td className="py-2 px-3">
                              <span
                                className={`px-2 py-0.5 font-bold rounded-sm text-white ${
                                  p.hydromet_density_class === "TINGGI"
                                    ? "bg-[#B42318]"
                                    : p.hydromet_density_class === "SEDANG"
                                    ? "bg-[#B54708]"
                                    : "bg-[#18794E]"
                                }`}
                              >
                                {p.hydromet_density_class}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        )}
      </DataStateWrapper>
    </div>
  );
}
