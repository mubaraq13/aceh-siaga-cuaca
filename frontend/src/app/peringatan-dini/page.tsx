"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchFromBackend, formatWibTimestamp } from "@/lib/api";
import { ActiveAlertItem, StandardAPIEnvelope } from "@/types/api";
import ProvenanceHeader from "@/components/ProvenanceHeader";
import DataStateWrapper from "@/components/DataStateWrapper";

interface ActiveAlertsPayload {
  api_health: string;
  last_updated_wib: string;
  active_alerts_count: number;
  has_active_warning: boolean;
  alerts: ActiveAlertItem[];
}

export default function PeringatanDiniPage() {
  const [envelope, setEnvelope] = useState<StandardAPIEnvelope<ActiveAlertsPayload> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchFromBackend<ActiveAlertsPayload>("/alerts/active");
      setEnvelope(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memeriksa umpan RSS/CAP Peringatan Dini BMKG.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  const alertData = envelope?.data;

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-[#102A43] dark:text-white">
            Peringatan Dini Cuaca Ekstrem Resmi BMKG (Nowcasting CAP v1.2)
          </h1>
          <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
            Menampilkan peringatan resmi yang sedang aktif dari umpan Common Alerting Protocol (CAP) BMKG untuk wilayah Provinsi Aceh. Sistem ini tidak pernah mengarang peringatan dini.
          </p>
        </div>
        <button
          type="button"
          onClick={loadAlerts}
          className="min-h-[44px] px-4 py-2 text-xs font-bold bg-[#173F5F] hover:bg-[#102A43] text-white rounded-md shrink-0"
        >
          Periksa Pembaruan BMKG
        </button>
      </div>

      <DataStateWrapper loading={loading} error={error} isEmpty={!alertData} onRetry={loadAlerts}>
        {envelope && alertData && (
          <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden">
            <ProvenanceHeader
              category="OFFICIAL_BMKG_ALERT"
              sourceAttribution={envelope.source_attribution}
              lastUpdatedWib={envelope.last_updated_wib}
              apiHealth={envelope.api_health}
              disclaimer={envelope.disclaimer}
            />

            <div className="p-5">
              {alertData.alerts.length === 0 ? (
                <div className="border-2 border-[#18794E] bg-[#F5F8FC] dark:bg-[#0A1929] rounded-md p-6">
                  <span className="inline-block px-3 py-1 text-xs font-bold bg-[#18794E] text-white rounded-sm">
                    TIDAK ADA PERINGATAN DINI AKTIF
                  </span>
                  <h2 className="mt-2 text-lg font-extrabold text-[#102A43] dark:text-white">
                    Saat ini tidak terdapat peringatan dini cuaca ekstrem aktif dari BMKG untuk Provinsi Aceh.
                  </h2>
                  <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
                    Waktu pemeriksaan terakhir: {formatWibTimestamp(alertData.last_updated_wib)}. Anda juga dapat memeriksa portal resmi BMKG melalui tautan di bawah ini.
                  </p>
                  <div className="mt-4">
                    <a
                      href="https://www.bmkg.go.id/cuaca/peringatan-dini"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold bg-[#173F5F] text-white rounded-md"
                    >
                      Buka Portal Resmi Peringatan Dini BMKG
                    </a>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {alertData.alerts.map((alert) => (
                    <article
                      key={alert.cap_identifier}
                      className="border-2 border-[#B42318] rounded-md p-5 bg-[#F5F8FC] dark:bg-[#0A1929]"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#DCEEFF] dark:border-[#173F5F]">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="px-2.5 py-1 text-xs font-extrabold bg-[#B42318] text-white rounded-sm">
                            SEVERITY: {alert.severity.toUpperCase()}
                          </span>
                          <span className="px-2.5 py-1 text-xs font-bold bg-[#B54708] text-white rounded-sm">
                            URGENCY: {alert.urgency.toUpperCase()}
                          </span>
                          <span className="px-2.5 py-1 text-xs font-bold bg-[#173F5F] text-white rounded-sm">
                            CERTAINTY: {alert.certainty.toUpperCase()}
                          </span>
                        </div>
                        <span className="text-xs font-mono font-bold">ID CAP: {alert.cap_identifier}</span>
                      </div>

                      <h2 className="mt-3 text-lg font-extrabold text-[#102A43] dark:text-white">
                        {alert.headline}
                      </h2>

                      <dl className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs tabular-nums">
                        <div className="bg-white dark:bg-[#102A43] p-3 rounded border border-[#DCEEFF]">
                          <dt className="font-semibold text-[#173F5F] dark:text-[#DCEEFF]">Jenis Cuaca (Event)</dt>
                          <dd className="mt-1 font-bold text-sm">{alert.event_type}</dd>
                        </div>
                        <div className="bg-white dark:bg-[#102A43] p-3 rounded border border-[#DCEEFF]">
                          <dt className="font-semibold text-[#173F5F] dark:text-[#DCEEFF]">Waktu Mulai Berlaku</dt>
                          <dd className="mt-1 font-bold text-sm">{formatWibTimestamp(alert.effective_time)}</dd>
                        </div>
                        <div className="bg-white dark:bg-[#102A43] p-3 rounded border border-[#DCEEFF]">
                          <dt className="font-semibold text-[#173F5F] dark:text-[#DCEEFF]">Waktu Berakhir</dt>
                          <dd className="mt-1 font-bold text-sm text-[#B42318] dark:text-[#DCEEFF]">
                            {formatWibTimestamp(alert.expires_time)}
                          </dd>
                        </div>
                      </dl>

                      <div className="mt-4 space-y-2 text-sm">
                        <p>
                          <strong>Wilayah Terdampak:</strong> {alert.affected_areas_text}
                        </p>
                        <p className="leading-relaxed">
                          <strong>Rincian Peringatan BMKG:</strong> {alert.description}
                        </p>
                        {alert.instruction && (
                          <p className="p-3 bg-white dark:bg-[#102A43] border-l-4 border-[#B54708] text-xs font-semibold">
                            <strong>Arahan Keselamatan BMKG:</strong> {alert.instruction}
                          </p>
                        )}
                      </div>

                      <div className="mt-4 pt-3 border-t border-[#DCEEFF] dark:border-[#173F5F] flex flex-wrap gap-3">
                        <a
                          href={alert.official_web_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold bg-[#173F5F] text-white rounded-md"
                        >
                          Lihat Halaman Resmi BMKG
                        </a>
                        <a
                          href={alert.cap_xml_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="min-h-[44px] inline-flex items-center px-4 py-2 text-xs font-bold border border-[#173F5F] text-[#102A43] dark:text-white rounded-md"
                        >
                          Periksa Dokumen Sumber CAP XML
                        </a>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}
      </DataStateWrapper>
    </div>
  );
}
