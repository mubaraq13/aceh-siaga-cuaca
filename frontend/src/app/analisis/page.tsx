"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BACKEND_ORIGIN, fetchFromBackend } from "@/lib/api";
import { StandardAPIEnvelope } from "@/types/api";
import ProvenanceHeader from "@/components/ProvenanceHeader";
import DataStateWrapper from "@/components/DataStateWrapper";

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

export default function AnalisisCuacaPage() {
  const [envelope, setEnvelope] = useState<StandardAPIEnvelope<any> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchFromBackend<any>("/analytics/historical");
      setEnvelope(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat data analisis cuaca historis.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const analytics = envelope?.data;
  const monthlyChartData = (analytics?.monthly_climatology || []).map((m: any) => ({
    ...m,
    month_label: MONTH_NAMES[(Number(m.month) || 1) - 1],
  }));

  return (
    <div className="space-y-8">
      <div className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
        <h1 className="text-xl font-extrabold text-[#102A43] dark:text-white">
          Analisis Statistik & Eksplorasi Data Historis Cuaca Aceh (EDA)
        </h1>
        <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
          Mencakup pemeriksaan kualitas data (penanganan kode khusus 8888 & 9999 BMKG), statistik deskriptif, siklus musiman Aceh, indeks iklim ekstrem WMO/ETCCDI, serta analisis korelasi Spearman dan Pearson.
        </p>
      </div>

      <DataStateWrapper loading={loading} error={error} isEmpty={!analytics} onRetry={loadAnalytics}>
        {envelope && analytics && (
          <div className="space-y-8">
            <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden">
              <ProvenanceHeader
                category="HISTORICAL_OBSERVATION"
                sourceAttribution={envelope.source_attribution}
                lastUpdatedWib={envelope.last_updated_wib}
                isDemoMode={envelope.is_demo_mode}
                disclaimer={envelope.disclaimer}
              />

              <div className="p-5 space-y-6">
                {/* Ringkasan Audit Kualitas Data */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 tabular-nums">
                  <div className="bg-[#F5F8FC] dark:bg-[#0A1929] p-3.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                    <span className="text-xs text-[#173F5F] dark:text-[#DCEEFF]">Total Baris Observasi</span>
                    <p className="text-xl font-extrabold mt-1">{analytics.data_quality?.total_records}</p>
                  </div>
                  <div className="bg-[#F5F8FC] dark:bg-[#0A1929] p-3.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                    <span className="text-xs text-[#173F5F] dark:text-[#DCEEFF]">Periode Analisis</span>
                    <p className="text-sm font-extrabold mt-1">
                      {analytics.data_quality?.period_start} s.d. {analytics.data_quality?.period_end}
                    </p>
                  </div>
                  <div className="bg-[#F5F8FC] dark:bg-[#0A1929] p-3.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                    <span className="text-xs text-[#173F5F] dark:text-[#DCEEFF]">Kode 8888 (Trace &rarr; 0.0 mm)</span>
                    <p className="text-xl font-extrabold mt-1">{analytics.data_quality?.trace_rainfall_8888_count} hari</p>
                  </div>
                  <div className="bg-[#F5F8FC] dark:bg-[#0A1929] p-3.5 rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                    <span className="text-xs text-[#173F5F] dark:text-[#DCEEFF]">Jumlah Stasiun BMKG</span>
                    <p className="text-xl font-extrabold mt-1">{analytics.data_quality?.stations_count} stasiun</p>
                  </div>
                </div>

                {/* Grafik Interaktif Recharts: Pola Bulanan Curah Hujan & Suhu/Kelembapan */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-4">
                    <h2 className="text-sm font-bold mb-1">
                      Grafik Klimatologi Curah Hujan Bulanan Provinsi Aceh (mm/bulan)
                    </h2>
                    <p className="text-xs text-[#173F5F] dark:text-[#DCEEFF] mb-4">
                      Puncak curah hujan terjadi pada periode Oktober-Desember (Monsun Barat) dan April-Mei (Transisi Ekuatorial).
                    </p>
                    <div className="h-72 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={monthlyChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month_label" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar
                            dataKey="avg_monthly_rainfall_mm"
                            name="Rata-Rata Bulanan (mm)"
                            fill="#173F5F"
                          />
                          <Bar
                            dataKey="median_monthly_rainfall_mm"
                            name="Median Bulanan (mm)"
                            fill="#18794E"
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-4">
                    <h2 className="text-sm font-bold mb-1">
                      Dinamika Suhu Rata-Rata (°C) & Frekuensi Hari Hujan Ekstrem (&ge;50 mm)
                    </h2>
                    <p className="text-xs text-[#173F5F] dark:text-[#DCEEFF] mb-4">
                      Perbandingan rata-rata suhu udara bulanan dengan total kejadian hujan lebat-ekstrem.
                    </p>
                    <div className="h-72 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={monthlyChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month_label" />
                          <YAxis yAxisId="left" />
                          <YAxis yAxisId="right" orientation="right" />
                          <Tooltip />
                          <Legend />
                          <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="total_extreme_days"
                            name="Kejadian Hujan >=50mm (Hari)"
                            stroke="#B42318"
                            strokeWidth={2.5}
                          />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="avg_temp_c"
                            name="Suhu Rata-Rata (°C)"
                            stroke="#173F5F"
                            strokeWidth={2}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Tabel Statistik Deskriptif Lengkap */}
                <div>
                  <h2 className="text-base font-bold mb-2">
                    Tabel Statistik Deskriptif Parameter Meteorologi Aceh
                  </h2>
                  <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                    <table className="w-full text-left border-collapse text-xs tabular-nums">
                      <thead>
                        <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                          <th className="py-2.5 px-3 font-bold">Variabel</th>
                          <th className="py-2.5 px-3 font-bold">N Valid</th>
                          <th className="py-2.5 px-3 font-bold">Mean</th>
                          <th className="py-2.5 px-3 font-bold">Std Dev</th>
                          <th className="py-2.5 px-3 font-bold">Min</th>
                          <th className="py-2.5 px-3 font-bold">Median (P50)</th>
                          <th className="py-2.5 px-3 font-bold">IQR</th>
                          <th className="py-2.5 px-3 font-bold">P90</th>
                          <th className="py-2.5 px-3 font-bold">P95</th>
                          <th className="py-2.5 px-3 font-bold">P99</th>
                          <th className="py-2.5 px-3 font-bold">Max</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                        {(analytics.descriptive_statistics || []).map((row: any) => (
                          <tr key={row.variable}>
                            <td className="py-2 px-3 font-mono font-bold">{row.variable}</td>
                            <td className="py-2 px-3">{row.count}</td>
                            <td className="py-2 px-3 font-semibold">{row.mean}</td>
                            <td className="py-2 px-3">{row.std}</td>
                            <td className="py-2 px-3">{row.min}</td>
                            <td className="py-2 px-3 font-bold">{row.median}</td>
                            <td className="py-2 px-3">{row.iqr}</td>
                            <td className="py-2 px-3">{row.q90}</td>
                            <td className="py-2 px-3">{row.q95}</td>
                            <td className="py-2 px-3 font-bold text-[#B54708]">{row.q99}</td>
                            <td className="py-2 px-3 font-bold text-[#B42318]">{row.max}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Analisis Korelasi Spearman & Pearson + Catatan Non-Kausalitas */}
                <div>
                  <h2 className="text-base font-bold mb-1">
                    Analisis Korelasi Variabel Meteorologi terhadap Curah Hujan Harian
                  </h2>
                  <p className="text-xs text-[#B54708] font-semibold mb-3">
                    Catatan Metodologis: {analytics.correlation_analysis?.methodology_note}
                  </p>
                  <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                    <table className="w-full text-left border-collapse text-xs tabular-nums">
                      <thead>
                        <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                          <th className="py-2.5 px-3 font-bold">Variabel Pendamping</th>
                          <th className="py-2.5 px-3 font-bold">Ukuran Sampel (N)</th>
                          <th className="py-2.5 px-3 font-bold">Spearman (&rho;)</th>
                          <th className="py-2.5 px-3 font-bold">Pearson (r)</th>
                          <th className="py-2.5 px-3 font-bold">p-value (Spearman)</th>
                          <th className="py-2.5 px-3 font-bold">Arah Asosiasi</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                        {(analytics.correlation_analysis?.rainfall_associations || []).map((c: any) => (
                          <tr key={c.variable}>
                            <td className="py-2 px-3 font-mono font-bold">{c.variable}</td>
                            <td className="py-2 px-3">{c.sample_size}</td>
                            <td className="py-2 px-3 font-bold">{c.spearman_rho}</td>
                            <td className="py-2 px-3">{c.pearson_r}</td>
                            <td className="py-2 px-3">{c.spearman_p_value}</td>
                            <td className="py-2 px-3 font-semibold">{c.direction}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Galeri 7 Visualisasi Publikasi Ilmiah Phase 2 */}
                <div>
                  <h2 className="text-base font-bold mb-3">
                    Visualisasi Grafik Penelitian Spasial-Temporal (Resolusi Publikasi)
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { file: "01_rainfall_trend.png", title: "1. Tren Curah Hujan Bulanan & Moving Average 6 Bulan" },
                      { file: "02_monthly_rainfall.png", title: "2. Siklus Klimatologi Curah Hujan Bulanan Aceh" },
                      { file: "03_rainfall_heatmap.png", title: "3. Heatmap Intensitas Curah Hujan Bulanan (Tahun x Bulan)" },
                      { file: "04_rainfall_distribution.png", title: "4. Distribusi Curah Hujan Harian & Ambang Ekstrem BMKG" },
                      { file: "05_temp_humidity_dynamics.png", title: "5. Profil Suhu Udara dan Kelembapan Relatif" },
                      { file: "06_regional_station_comparison.png", title: "6. Perbandingan Curah Hujan Tahunan Antar Stasiun Aceh" },
                      { file: "07_extreme_rain_calendar.png", title: "7. Kalender Frekuensi Hujan Lebat-Ekstrem (>= 50 mm/hari)" },
                    ].map((fig) => (
                      <figure
                        key={fig.file}
                        className="border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-3 bg-[#F5F8FC] dark:bg-[#0A1929]"
                      >
                        <figcaption className="text-xs font-bold mb-2 text-[#102A43] dark:text-white">
                          {fig.title}
                        </figcaption>
                        <img
                          src={`${BACKEND_ORIGIN}/static/figures/${fig.file}`}
                          alt={fig.title}
                          loading="lazy"
                          className="w-full h-auto rounded border border-[#DCEEFF]"
                        />
                      </figure>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}
      </DataStateWrapper>
    </div>
  );
}
