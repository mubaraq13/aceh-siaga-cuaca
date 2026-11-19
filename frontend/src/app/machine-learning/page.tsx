"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchFromBackend, formatWibTimestamp } from "@/lib/api";
import { StandardAPIEnvelope, StationPredictionItem } from "@/types/api";
import ProvenanceHeader from "@/components/ProvenanceHeader";
import DataStateWrapper from "@/components/DataStateWrapper";

export default function MachineLearningPage() {
  const [envelope, setEnvelope] = useState<StandardAPIEnvelope<any> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadMlData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchFromBackend<any>("/ml/predictions");
      setEnvelope(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat laporan evaluasi Machine Learning.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMlData();
  }, [loadMlData]);

  const ml = envelope?.data;

  return (
    <div className="space-y-8">
      {/* Banner Disclaimer Eksperimental Wajib */}
      <div className="border-2 border-[#B54708] bg-white dark:bg-[#102A43] rounded-md p-5">
        <span className="inline-block px-3 py-1 text-xs font-extrabold bg-[#B54708] text-white rounded-sm">
          PERINGATAN METODOLOGIS & BATAS TANGGUNG JAWAB PUBLIK
        </span>
        <h1 className="mt-2 text-xl font-extrabold text-[#102A43] dark:text-white">
          Analisis model eksperimental, bukan peringatan resmi BMKG.
        </h1>
        <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
          Seluruh estimasi curah hujan dan probabilitas hujan lebat pada halaman ini dihasilkan oleh algoritma Machine Learning berbasis fitur historis stasiun pengamatan untuk tujuan penelitian Data Science. Untuk keputusan keselamatan jiwa dan evakuasi, selalu ikuti Peringatan Dini Cuaca Resmi dari BMKG dan arahan BPBA/BPBD.
        </p>
      </div>

      <DataStateWrapper loading={loading} error={error} isEmpty={!ml} onRetry={loadMlData}>
        {envelope && ml && (
          <div className="space-y-8">
            {/* Panel 1: Hasil Prediksi Eksperimental H+1 pada 5 Stasiun BMKG Aceh */}
            <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden">
              <ProvenanceHeader
                category="EXPERIMENTAL_ML_PREDICTION"
                sourceAttribution={envelope.source_attribution}
                lastUpdatedWib={envelope.last_updated_wib}
                disclaimer={ml.mandatory_disclaimer}
              />

              <div className="p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="text-base font-bold text-[#102A43] dark:text-white">
                      Hasil Prediksi Eksperimental Curah Hujan (Horizon H+1 / 24 Jam ke Depan)
                    </h2>
                    <p className="text-xs text-[#173F5F] dark:text-[#DCEEFF] tabular-nums">
                      Versi Model: <strong>{ml.model_version}</strong> | Versi Dataset: <strong>{ml.dataset_version}</strong> | Waktu Training: <strong>{formatWibTimestamp(ml.trained_at_wib)}</strong>
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                  <table className="w-full text-left border-collapse text-xs tabular-nums">
                    <thead>
                      <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                        <th className="py-3 px-3 font-bold">WMO ID & Stasiun</th>
                        <th className="py-3 px-3 font-bold">Tanggal Target</th>
                        <th className="py-3 px-3 font-bold">Horizon</th>
                        <th className="py-3 px-3 font-bold">Estimasi Hujan (mm)</th>
                        <th className="py-3 px-3 font-bold">Prob. Hujan Lebat</th>
                        <th className="py-3 px-3 font-bold">Kategori Prediksi</th>
                        <th className="py-3 px-3 font-bold">Label Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                      {(ml.station_predictions || []).map((p: StationPredictionItem) => (
                        <tr key={p.wmo_id}>
                          <td className="py-3 px-3 font-bold">
                            {p.wmo_id} - {p.station_name}
                          </td>
                          <td className="py-3 px-3 font-semibold">{p.target_prediction_date}</td>
                          <td className="py-3 px-3">+{p.horizon_days} Hari (H+1)</td>
                          <td className="py-3 px-3 font-extrabold">{p.predicted_rainfall_mm} mm</td>
                          <td className="py-3 px-3 font-bold">
                            {(p.predicted_extreme_probability * 100).toFixed(1)}% (Ambang: {(p.decision_threshold * 100).toFixed(0)}%)
                          </td>
                          <td className="py-3 px-3">
                            <span
                              className={`px-2 py-0.5 font-bold rounded-sm text-white ${
                                p.is_potential_heavy_rain ? "bg-[#B54708]" : "bg-[#18794E]"
                              }`}
                            >
                              {p.predicted_category}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-[#B54708] dark:text-[#DCEEFF] font-semibold">
                            {p.disclaimer_label}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            {/* Panel 2: Evaluasi Performa Model vs Baseline (Klasifikasi & Regresi) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
                <h2 className="text-base font-bold text-[#102A43] dark:text-white">
                  1. Komparasi Metrik Klasifikasi Potensi Hujan Lebat (Data Tidak Seimbang)
                </h2>
                <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF] mb-3">
                  Evaluasi pada Holdout Test Set ({ml.split_summary?.test_period}) menggunakan Precision, Recall, F1-Score, dan PR-AUC.
                </p>
                <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                  <table className="w-full text-left border-collapse text-xs tabular-nums">
                    <thead>
                      <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                        <th className="py-2 px-2.5 font-bold">Algoritma Model</th>
                        <th className="py-2 px-2.5 font-bold">Precision</th>
                        <th className="py-2 px-2.5 font-bold">Recall</th>
                        <th className="py-2 px-2.5 font-bold">F1-Score</th>
                        <th className="py-2 px-2.5 font-bold">PR-AUC</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                      {Object.entries(ml.classification_comparison || {}).map(([name, m]: [string, any]) => (
                        <tr
                          key={name}
                          className={
                            name === ml.best_models?.best_classification_model
                              ? "bg-[#F5F8FC] dark:bg-[#0A1929] font-bold"
                              : ""
                          }
                        >
                          <td className="py-2 px-2.5">{name}</td>
                          <td className="py-2 px-2.5">{m.precision}</td>
                          <td className="py-2 px-2.5">{m.recall}</td>
                          <td className="py-2 px-2.5 font-bold text-[#173F5F] dark:text-[#DCEEFF]">{m.f1_score}</td>
                          <td className="py-2 px-2.5 font-bold">{m.pr_auc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
                <h2 className="text-base font-bold text-[#102A43] dark:text-white">
                  2. Komparasi Metrik Regresi Estimasi Curah Hujan Harian (mm/hari)
                </h2>
                <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF] mb-3">
                  Perbandingan MAE, RMSE, R², dan persentase peningkatan performa terhadap Baseline Persistence & Climatology.
                </p>
                <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                  <table className="w-full text-left border-collapse text-xs tabular-nums">
                    <thead>
                      <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                        <th className="py-2 px-2.5 font-bold">Algoritma Model</th>
                        <th className="py-2 px-2.5 font-bold">MAE (mm)</th>
                        <th className="py-2 px-2.5 font-bold">RMSE (mm)</th>
                        <th className="py-2 px-2.5 font-bold">R²</th>
                        <th className="py-2 px-2.5 font-bold">Skill vs Baseline</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                      {Object.entries(ml.regression_comparison || {}).map(([name, m]: [string, any]) => (
                        <tr
                          key={name}
                          className={
                            name === ml.best_models?.best_regression_model
                              ? "bg-[#F5F8FC] dark:bg-[#0A1929] font-bold"
                              : ""
                          }
                        >
                          <td className="py-2 px-2.5">{name}</td>
                          <td className="py-2 px-2.5">{m.MAE_mm}</td>
                          <td className="py-2 px-2.5 font-bold">{m.RMSE_mm}</td>
                          <td className="py-2 px-2.5">{m.R2_score}</td>
                          <td className="py-2 px-2.5">
                            {m.skill_vs_baseline_pct !== null ? `${m.skill_vs_baseline_pct}%` : "Baseline"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            {/* Panel 3: Grafik Feature Importance & Keterbatasan Model */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <section className="lg:col-span-7 bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
                <h2 className="text-base font-bold text-[#102A43] dark:text-white mb-1">
                  Variabel Prediktor Paling Berpengaruh (Top 10 Feature Importance)
                </h2>
                <p className="text-xs text-[#173F5F] dark:text-[#DCEEFF] mb-4">
                  Kontribusi fitur lag curah hujan, akumulasi rolling window, kelembapan, suhu, dan angin.
                </p>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={(ml.feature_importance_top15 || []).slice(0, 10)}
                      margin={{ left: 40, right: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis type="category" dataKey="feature" width={150} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="importance" name="Bobot Kepentingan" fill="#173F5F" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="lg:col-span-5 bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
                <h2 className="text-base font-bold text-[#102A43] dark:text-white mb-2">
                  Keterbatasan Ilmiah Model (Model Limitations)
                </h2>
                <ul className="space-y-2.5 text-xs text-[#173F5F] dark:text-[#DCEEFF] leading-relaxed">
                  {(ml.model_limitations || []).map((lim: string, idx: number) => (
                    <li key={idx} className="p-2.5 bg-[#F5F8FC] dark:bg-[#0A1929] rounded border border-[#DCEEFF] dark:border-[#173F5F]">
                      {idx + 1}. {lim}
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </div>
        )}
      </DataStateWrapper>
    </div>
  );
}
