"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchFromBackend, formatWibTimestamp } from "@/lib/api";
import {
  ActiveAlertItem,
  ForecastSlot,
  RegencyItem,
  StandardAPIEnvelope,
  StationPredictionItem,
} from "@/types/api";
import ProvenanceHeader from "@/components/ProvenanceHeader";
import DataStateWrapper from "@/components/DataStateWrapper";

interface DashboardSummaryData {
  selected_region_code: string;
  location: {
    provinsi: string;
    kotkab: string;
    kecamatan: string;
    desa: string;
  };
  current_forecast_slot: ForecastSlot | null;
  upcoming_24h_slots: ForecastSlot[];
  active_alerts_count: number;
  active_alerts: ActiveAlertItem[];
  experimental_ml_highlights: StationPredictionItem[];
  ml_disclaimer: string;
}

export default function HomePage() {
  const [regionCode, setRegionCode] = useState<string>("11.71");
  const [regencies, setRegencies] = useState<RegencyItem[]>([]);
  const [envelope, setEnvelope] = useState<StandardAPIEnvelope<DashboardSummaryData> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback(async (selectedCode: string) => {
    setLoading(true);
    setError(null);
    try {
      const [regResp, sumResp] = await Promise.all([
        fetchFromBackend<{ regencies: RegencyItem[] }>("/regions"),
        fetchFromBackend<DashboardSummaryData>(`/dashboard/summary?region_code=${selectedCode}`),
      ]);
      setRegencies(regResp.data.regencies);
      setEnvelope(sumResp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat ringkasan cuaca Aceh.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSummary(regionCode);
  }, [regionCode, loadSummary]);

  const summary = envelope?.data;
  const activeAlerts = summary?.active_alerts || [];

  return (
    <div className="space-y-8">
      {/* Pita Status Peringatan Dini Resmi BMKG (Focal Point Utama Keselamatan) */}
      <section aria-labelledby="alert-banner-heading">
        {activeAlerts.length > 0 ? (
          <div className="border-2 border-[#B42318] bg-white dark:bg-[#102A43] rounded-md overflow-hidden">
            <div className="bg-[#B42318] text-white px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
              <h1 id="alert-banner-heading" className="text-sm sm:text-base font-extrabold tracking-wide">
                PERINGATAN DINI CUACA AKTIF BMKG: {activeAlerts.length} PERINGATAN DI PROVINSI ACEH
              </h1>
              <Link
                href="/peringatan-dini"
                className="min-h-[44px] inline-flex items-center px-3.5 py-1.5 text-xs font-bold bg-white text-[#B42318] rounded-sm"
              >
                Periksa Rincian Wilayah Terdampak
              </Link>
            </div>
            <div className="p-4 space-y-3">
              {activeAlerts.map((alert) => (
                <div key={alert.cap_identifier} className="border-b last:border-b-0 border-[#DCEEFF] pb-3 last:pb-0">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-bold">
                    <span className="px-2 py-0.5 bg-[#B54708] text-white rounded-sm">
                      SEVERITY: {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-[#102A43] dark:text-white">{alert.headline}</span>
                    <span className="text-[#173F5F] dark:text-[#DCEEFF] tabular-nums">
                      (Berlaku s.d. {formatWibTimestamp(alert.expires_time)})
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-[#102A43] dark:text-[#F5F8FC]">
                    <strong>Wilayah Terdampak:</strong> {alert.affected_areas_text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="border-2 border-[#18794E] bg-white dark:bg-[#102A43] rounded-md p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <span className="inline-block px-2.5 py-0.5 text-xs font-bold bg-[#18794E] text-white rounded-sm">
                STATUS PERINGATAN DINI RESMI BMKG: AMAN / TIDAK ADA PERINGATAN AKTIF
              </span>
              <h1 id="alert-banner-heading" className="mt-1.5 text-base font-bold text-[#102A43] dark:text-white">
                Tidak ada peringatan dini cuaca ekstrem aktif dari BMKG untuk Provinsi Aceh saat ini.
              </h1>
            </div>
            <Link
              href="/peringatan-dini"
              className="min-h-[44px] inline-flex items-center justify-center px-4 py-2 text-xs font-bold bg-[#173F5F] text-white rounded-md shrink-0"
            >
              Buka Halaman Peringatan Dini
            </Link>
          </div>
        )}
      </section>

      {/* Pemilih Wilayah Kabupaten/Kota Aceh */}
      <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-[#102A43] dark:text-white">
            Pantauan Prakiraan Cuaca Kabupaten/Kota di Provinsi Aceh
          </h2>
          <p className="text-xs text-[#173F5F] dark:text-[#DCEEFF]">
            Pilih salah satu dari 23 Kabupaten/Kota di Aceh untuk melihat kondisi prakiraan resmi BMKG.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label htmlFor="home-region-select" className="text-xs font-bold text-[#102A43] dark:text-white">
            Kabupaten/Kota:
          </label>
          <select
            id="home-region-select"
            value={regionCode}
            onChange={(e) => setRegionCode(e.target.value)}
            className="min-h-[44px] px-3 py-2 text-sm font-semibold border border-[#173F5F] rounded-md bg-[#F5F8FC] dark:bg-[#0A1929] text-[#102A43] dark:text-white"
          >
            {regencies.map((reg) => (
              <option key={reg.region_code} value={reg.region_code}>
                {reg.region_code} - {reg.region_name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => loadSummary(regionCode)}
            className="min-h-[44px] px-4 py-2 text-xs font-bold bg-[#173F5F] hover:bg-[#102A43] text-white rounded-md"
          >
            Segarkan Data
          </button>
        </div>
      </section>

      <DataStateWrapper
        loading={loading}
        error={error}
        isEmpty={!summary}
        onRetry={() => loadSummary(regionCode)}
      >
        {envelope && summary && (
          <div className="space-y-8">
            {/* Panel 1: Prakiraan Resmi BMKG Saat Ini & 24 Jam ke Depan */}
            <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden">
              <ProvenanceHeader
                category="OFFICIAL_BMKG_FORECAST"
                sourceAttribution="API Prakiraan Cuaca Publik BMKG (Resmi)"
                lastUpdatedWib={envelope.last_updated_wib}
                apiHealth={envelope.api_health}
                disclaimer="Data prakiraan model cuaca BMKG per 3 jam. Bukan merupakan angka observasi penakar hujan."
              />

              <div className="p-5 grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Kolom Kiri: Slot Cuaca Terdekat */}
                <div className="lg:col-span-5 bg-[#F5F8FC] dark:bg-[#0A1929] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5 flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-[#173F5F] dark:text-[#DCEEFF]">
                      Titik Representatif: {summary.location.desa}, {summary.location.kecamatan}
                    </span>
                    <h3 className="mt-1 text-xl font-extrabold text-[#102A43] dark:text-white">
                      {summary.location.kotkab}, Provinsi Aceh
                    </h3>

                    {summary.current_forecast_slot ? (
                      <div className="mt-4">
                        <div className="flex items-baseline gap-4 tabular-nums">
                          <span className="text-4xl font-extrabold text-[#102A43] dark:text-white">
                            {summary.current_forecast_slot.temperature_c.toFixed(1)}°C
                          </span>
                          <span className="text-base font-bold text-[#173F5F] dark:text-[#DCEEFF]">
                            {summary.current_forecast_slot.weather_desc_id}
                          </span>
                        </div>

                        <dl className="mt-4 grid grid-cols-2 gap-3 text-xs tabular-nums">
                          <div className="bg-white dark:bg-[#102A43] p-2.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                            <dt className="text-[#173F5F] dark:text-[#DCEEFF]">Kelembapan Udara</dt>
                            <dd className="mt-0.5 text-sm font-bold text-[#102A43] dark:text-white">
                              {summary.current_forecast_slot.humidity_pct}%
                            </dd>
                          </div>
                          <div className="bg-white dark:bg-[#102A43] p-2.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                            <dt className="text-[#173F5F] dark:text-[#DCEEFF]">Kecepatan & Arah Angin</dt>
                            <dd className="mt-0.5 text-sm font-bold text-[#102A43] dark:text-white">
                              {summary.current_forecast_slot.wind_speed_kmh} km/jam ({summary.current_forecast_slot.wind_dir_cardinal || "-"})
                            </dd>
                          </div>
                          <div className="bg-white dark:bg-[#102A43] p-2.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                            <dt className="text-[#173F5F] dark:text-[#DCEEFF]">Tutupan Awan</dt>
                            <dd className="mt-0.5 text-sm font-bold text-[#102A43] dark:text-white">
                              {summary.current_forecast_slot.cloud_cover_pct ?? "-"}%
                            </dd>
                          </div>
                          <div className="bg-white dark:bg-[#102A43] p-2.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                            <dt className="text-[#173F5F] dark:text-[#DCEEFF]">Jarak Pandang</dt>
                            <dd className="mt-0.5 text-sm font-bold text-[#102A43] dark:text-white">
                              {summary.current_forecast_slot.visibility_text || "> 10 km"}
                            </dd>
                          </div>
                        </dl>
                      </div>
                    ) : (
                      <p className="mt-4 text-sm">Slot prakiraan belum tersedia.</p>
                    )}
                  </div>

                  <div className="mt-5 pt-3 border-t border-[#DCEEFF] dark:border-[#173F5F] flex flex-wrap gap-2">
                    <Link
                      href={`/prakiraan?region_code=${regionCode}`}
                      className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold bg-[#173F5F] hover:bg-[#102A43] text-white rounded-md"
                    >
                      Lihat Prakiraan 3 Hari Lengkap
                    </Link>
                    <Link
                      href="/peta"
                      className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold border border-[#173F5F] text-[#102A43] dark:text-white rounded-md"
                    >
                      Buka Peta Interaktif Aceh
                    </Link>
                  </div>
                </div>

                {/* Kolom Kanan: Deret Waktu 24 Jam ke Depan (Per 3 Jam) */}
                <div className="lg:col-span-7">
                  <h4 className="text-sm font-bold text-[#102A43] dark:text-white mb-3">
                    Jadwal Prakiraan Cuaca 24 Jam ke Depan (Interval 3 Jam)
                  </h4>
                  <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                    <table className="w-full text-left border-collapse text-xs tabular-nums">
                      <thead>
                        <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                          <th className="py-2.5 px-3 font-bold">Waktu Lokal (WIB)</th>
                          <th className="py-2.5 px-3 font-bold">Kondisi Cuaca</th>
                          <th className="py-2.5 px-3 font-bold">Suhu (°C)</th>
                          <th className="py-2.5 px-3 font-bold">RH (%)</th>
                          <th className="py-2.5 px-3 font-bold">Angin (km/jam)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                        {summary.upcoming_24h_slots.map((slot) => (
                          <tr key={slot.forecast_time_utc} className="hover:bg-[#F5F8FC] dark:hover:bg-[#0A1929]">
                            <td className="py-2.5 px-3 font-semibold">{slot.forecast_time_local}</td>
                            <td className="py-2.5 px-3 font-bold text-[#173F5F] dark:text-[#DCEEFF]">
                              {slot.weather_desc_id}
                            </td>
                            <td className="py-2.5 px-3 font-bold">{slot.temperature_c.toFixed(1)}°C</td>
                            <td className="py-2.5 px-3">{slot.humidity_pct}%</td>
                            <td className="py-2.5 px-3">
                              {slot.wind_speed_kmh} ({slot.wind_dir_cardinal || "-"})
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </section>

            {/* Panel 2: Pemisahan Tegas - Ringkasan Prediksi Eksperimental Machine Learning vs Akses Cepat Edukasi */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <section className="lg:col-span-7 bg-white dark:bg-[#102A43] border-2 border-[#B54708] rounded-md overflow-hidden">
                <ProvenanceHeader
                  category="EXPERIMENTAL_ML_PREDICTION"
                  sourceAttribution="Model Machine Learning Aceh Siaga Cuaca"
                  lastUpdatedWib={summary.experimental_ml_highlights[0]?.predicted_at_wib || envelope.last_updated_wib}
                  disclaimer={summary.ml_disclaimer}
                />
                <div className="p-5">
                  <div className="bg-[#DCEEFF] dark:bg-[#173F5F] p-3 rounded-sm mb-4">
                    <p className="text-xs font-bold text-[#102A43] dark:text-white">
                      PERNYATAAN WAJIB: {summary.ml_disclaimer}
                    </p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs tabular-nums">
                      <thead>
                        <tr className="border-b border-[#DCEEFF] dark:border-[#173F5F]">
                          <th className="py-2 px-2 font-bold">Stasiun BMKG</th>
                          <th className="py-2 px-2 font-bold">Target (H+1)</th>
                          <th className="py-2 px-2 font-bold">Estimasi (mm)</th>
                          <th className="py-2 px-2 font-bold">Prob. Hujan Lebat</th>
                          <th className="py-2 px-2 font-bold">Kategori</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                        {summary.experimental_ml_highlights.map((item) => (
                          <tr key={item.wmo_id}>
                            <td className="py-2 px-2 font-semibold">{item.station_name}</td>
                            <td className="py-2 px-2">{item.target_prediction_date}</td>
                            <td className="py-2 px-2 font-bold">{item.predicted_rainfall_mm} mm</td>
                            <td className="py-2 px-2">{(item.predicted_extreme_probability * 100).toFixed(1)}%</td>
                            <td className="py-2 px-2">
                              <span
                                className={`px-2 py-0.5 font-bold rounded-sm text-white ${
                                  item.is_potential_heavy_rain ? "bg-[#B54708]" : "bg-[#18794E]"
                                }`}
                              >
                                {item.predicted_category}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="mt-4">
                    <Link
                      href="/machine-learning"
                      className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold bg-[#B54708] text-white rounded-md"
                    >
                      Periksa Evaluasi Model & Variabel Berpengaruh
                    </Link>
                  </div>
                </div>
              </section>

              <section className="lg:col-span-5 bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden flex flex-col justify-between">
                <ProvenanceHeader
                  category="DISASTER_AND_PREPAREDNESS"
                  sourceAttribution="BPBA Provinsi Aceh & Basarnas Banda Aceh"
                  lastUpdatedWib={envelope.last_updated_wib}
                />
                <div className="p-5 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-base font-bold text-[#102A43] dark:text-white">
                      Panduan Keselamatan & Kesiapsiagaan Bencana Hidrometeorologi
                    </h3>
                    <p className="mt-2 text-xs text-[#173F5F] dark:text-[#DCEEFF] leading-relaxed">
                      Langkah tindakan praktis menghadapi banjir, banjir bandang, tanah longsor di jalur lintas tengah/barat Aceh, persiapan Tas Siaga Bencana 72 Jam, serta daftar nomor darurat resmi.
                    </p>
                    <ul className="mt-3 space-y-1.5 text-xs font-semibold text-[#102A43] dark:text-white">
                      <li>- Pusdalops BPBA Provinsi Aceh: (0651) 34783</li>
                      <li>- Basarnas Kelas A Banda Aceh: 115 / (0651) 33876</li>
                      <li>- Panggilan Darurat Terpadu: 112</li>
                    </ul>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-2">
                    <Link
                      href="/edukasi"
                      className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold bg-[#18794E] text-white rounded-md"
                    >
                      Buka Panduan Kesiapsiagaan & Tas Darurat
                    </Link>
                    <Link
                      href="/analisis"
                      className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold bg-[#173F5F] text-white rounded-md"
                    >
                      Lihat Analisis Iklim Historis
                    </Link>
                  </div>
                </div>
              </section>
            </div>
          </div>
        )}
      </DataStateWrapper>
    </div>
  );
}
