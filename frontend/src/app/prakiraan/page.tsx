"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchFromBackend } from "@/lib/api";
import { ForecastSlot, RegencyItem, StandardAPIEnvelope } from "@/types/api";
import ProvenanceHeader from "@/components/ProvenanceHeader";
import DataStateWrapper from "@/components/DataStateWrapper";

interface ForecastPayload {
  api_health: string;
  fetched_at_wib: string;
  adm4_code: string;
  location: {
    provinsi: string;
    kotkab: string;
    kecamatan: string;
    desa: string;
    latitude: number;
    longitude: number;
  };
  total_slots: number;
  forecast_horizon: string;
  slots: ForecastSlot[];
}

export default function PrakiraanCuacaPage() {
  const [regencies, setRegencies] = useState<RegencyItem[]>([]);
  const [selectedRegency, setSelectedRegency] = useState<string>("11.71");
  const [customAdm4, setCustomAdm4] = useState<string>("11.71.01.2001");
  const [envelope, setEnvelope] = useState<StandardAPIEnvelope<ForecastPayload> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadForecast = useCallback(async (adm4Query: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchFromBackend<ForecastPayload>(`/forecasts?adm4=${encodeURIComponent(adm4Query)}`);
      setEnvelope(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat data prakiraan cuaca BMKG.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFromBackend<{ regencies: RegencyItem[] }>("/regions")
      .then((res) => setRegencies(res.data.regencies))
      .catch(() => {});
    loadForecast("11.71.01.2001");
  }, [loadForecast]);

  const handleRegencyChange = (code: string) => {
    setSelectedRegency(code);
    const found = regencies.find((r) => r.region_code === code);
    const nextAdm4 = found ? found.representative_adm4 : `${code}.01.2001`;
    setCustomAdm4(nextAdm4);
    loadForecast(nextAdm4);
  };

  const handleAdm4Submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customAdm4.trim()) {
      loadForecast(customAdm4.trim());
    }
  };

  const forecast = envelope?.data;

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
        <h1 className="text-xl font-extrabold text-[#102A43] dark:text-white">
          Prakiraan Cuaca Resmi BMKG (3 Hari / Interval 3 Jam)
        </h1>
        <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
          Pilih Kabupaten/Kota di Provinsi Aceh atau masukkan kode desa/gampong (ADM4 format 11.xx.xx.xxxx) untuk memeriksa suhu, kelembapan, arah angin, dan kondisi cuaca per 3 jam.
        </p>

        <form onSubmit={handleAdm4Submit} className="mt-4 grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-5">
            <label htmlFor="regency-picker" className="block text-xs font-bold mb-1">
              1. Pilih Kabupaten / Kota (ADM2):
            </label>
            <select
              id="regency-picker"
              value={selectedRegency}
              onChange={(e) => handleRegencyChange(e.target.value)}
              className="w-full min-h-[44px] px-3 py-2 text-sm font-semibold border border-[#173F5F] rounded-md bg-[#F5F8FC] dark:bg-[#0A1929] text-[#102A43] dark:text-white"
            >
              {regencies.map((r) => (
                <option key={r.region_code} value={r.region_code}>
                  {r.region_code} - {r.region_name}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-4">
            <label htmlFor="adm4-input" className="block text-xs font-bold mb-1">
              2. Kode Gampong / Desa (ADM4 Aceh):
            </label>
            <input
              id="adm4-input"
              type="text"
              value={customAdm4}
              onChange={(e) => setCustomAdm4(e.target.value)}
              placeholder="Contoh: 11.71.01.2001"
              className="w-full min-h-[44px] px-3 py-2 text-sm font-mono border border-[#173F5F] rounded-md bg-[#F5F8FC] dark:bg-[#0A1929] text-[#102A43] dark:text-white"
            />
          </div>

          <div className="md:col-span-3">
            <button
              type="submit"
              className="w-full min-h-[44px] px-4 py-2 text-xs font-bold bg-[#173F5F] hover:bg-[#102A43] text-white rounded-md"
            >
              Tampilkan Prakiraan BMKG
            </button>
          </div>
        </form>
      </div>

      <DataStateWrapper
        loading={loading}
        error={error}
        isEmpty={!forecast || forecast.slots.length === 0}
        emptyMessage="Tidak ada slot prakiraan yang dikembalikan untuk kode wilayah tersebut."
        onRetry={() => loadForecast(customAdm4)}
      >
        {envelope && forecast && (
          <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden">
            <ProvenanceHeader
              category="OFFICIAL_BMKG_FORECAST"
              sourceAttribution={envelope.source_attribution}
              lastUpdatedWib={envelope.last_updated_wib}
              apiHealth={envelope.api_health}
              disclaimer={envelope.disclaimer}
            />

            <div className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-[#DCEEFF] dark:border-[#173F5F]">
                <div>
                  <h2 className="text-lg font-extrabold text-[#102A43] dark:text-white">
                    Gampong {forecast.location.desa}, Kec. {forecast.location.kecamatan}, {forecast.location.kotkab}
                  </h2>
                  <p className="text-xs text-[#173F5F] dark:text-[#DCEEFF] tabular-nums">
                    Kode ADM4: <strong>{forecast.adm4_code}</strong> | Koordinat: {forecast.location.latitude}, {forecast.location.longitude} | Total Slot: {forecast.total_slots}
                  </p>
                </div>
              </div>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs tabular-nums">
                  <thead>
                    <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                      <th className="py-3 px-3 font-bold">Waktu Lokal (WIB)</th>
                      <th className="py-3 px-3 font-bold">Prakiraan Cuaca</th>
                      <th className="py-3 px-3 font-bold">Suhu (°C)</th>
                      <th className="py-3 px-3 font-bold">Kelembapan (%)</th>
                      <th className="py-3 px-3 font-bold">Kecepatan Angin</th>
                      <th className="py-3 px-3 font-bold">Arah Angin</th>
                      <th className="py-3 px-3 font-bold">Tutupan Awan (%)</th>
                      <th className="py-3 px-3 font-bold">Jarak Pandang</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                    {forecast.slots.map((slot) => {
                      const isRainy = slot.weather_desc_id.toLowerCase().includes("hujan");
                      return (
                        <tr
                          key={slot.forecast_time_utc}
                          className="hover:bg-[#F5F8FC] dark:hover:bg-[#0A1929]"
                        >
                          <td className="py-2.5 px-3 font-semibold">{slot.forecast_time_local}</td>
                          <td className="py-2.5 px-3">
                            <span
                              className={`px-2 py-0.5 font-bold rounded-sm ${
                                isRainy
                                  ? "bg-[#B54708] text-white"
                                  : "bg-[#DCEEFF] text-[#102A43]"
                              }`}
                            >
                              {slot.weather_desc_id}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 font-bold">{slot.temperature_c.toFixed(1)}°C</td>
                          <td className="py-2.5 px-3">{slot.humidity_pct}%</td>
                          <td className="py-2.5 px-3">
                            {slot.wind_speed_kmh} km/jam ({slot.wind_speed_ms} m/s)
                          </td>
                          <td className="py-2.5 px-3">
                            {slot.wind_dir_cardinal || "-"} ({slot.wind_dir_deg ?? 0}°)
                          </td>
                          <td className="py-2.5 px-3">{slot.cloud_cover_pct ?? "-"}%</td>
                          <td className="py-2.5 px-3">{slot.visibility_text || "-"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}
      </DataStateWrapper>
    </div>
  );
}
