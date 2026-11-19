"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchFromBackend } from "@/lib/api";
import { StandardAPIEnvelope } from "@/types/api";
import ProvenanceHeader from "@/components/ProvenanceHeader";
import DataStateWrapper from "@/components/DataStateWrapper";

export default function EdukasiKesiapsiagaanPage() {
  const [envelope, setEnvelope] = useState<StandardAPIEnvelope<any> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHazardIndex, setSelectedHazardIndex] = useState<number>(0);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  const loadEducation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchFromBackend<any>("/education/preparedness");
      setEnvelope(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat panduan kesiapsiagaan bencana.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEducation();
    try {
      const saved = window.localStorage.getItem("aceh_siaga_emergency_bag");
      if (saved) setCheckedItems(JSON.parse(saved));
    } catch {
      // Abaikan jika localStorage tidak aktif
    }
  }, [loadEducation]);

  const toggleChecklist = (itemName: string) => {
    setCheckedItems((prev) => {
      const next = { ...prev, [itemName]: !prev[itemName] };
      try {
        window.localStorage.setItem("aceh_siaga_emergency_bag", JSON.stringify(next));
      } catch {
        // Abaikan jika localStorage penuh
      }
      return next;
    });
  };

  const edu = envelope?.data;
  const guides = edu?.guides || [];
  const activeGuide = guides[selectedHazardIndex] || guides[0];

  return (
    <div className="space-y-8">
      <div className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
        <h1 className="text-xl font-extrabold text-[#102A43] dark:text-white">
          Edukasi Kesiapsiagaan Bencana Hidrometeorologi & Kontak Darurat Provinsi Aceh
        </h1>
        <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
          Panduan praktis menghadapi banjir, tanah longsor, dan angin kencang, daftar periksa Tas Siaga Bencana 72 Jam, serta nomor layanan darurat resmi yang telah diverifikasi di Provinsi Aceh.
        </p>
      </div>

      <DataStateWrapper loading={loading} error={error} isEmpty={!edu} onRetry={loadEducation}>
        {envelope && edu && (
          <div className="space-y-8">
            {/* Panel 1: Panduan Pra, Saat, dan Pasca Bencana */}
            <section className="bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md overflow-hidden">
              <ProvenanceHeader
                category="DISASTER_AND_PREPAREDNESS"
                sourceAttribution={envelope.source_attribution}
                lastUpdatedWib={envelope.last_updated_wib}
                disclaimer={envelope.disclaimer}
              />

              <div className="p-5 space-y-5">
                <div className="flex flex-wrap gap-2" role="tablist" aria-label="Pilih Jenis Bencana Hidrometeorologi">
                  {guides.map((g: any, idx: number) => (
                    <button
                      key={g.hazard_type}
                      type="button"
                      role="tab"
                      aria-selected={selectedHazardIndex === idx}
                      onClick={() => setSelectedHazardIndex(idx)}
                      className={`min-h-[44px] px-4 py-2 text-xs font-bold rounded-md border ${
                        selectedHazardIndex === idx
                          ? "bg-[#173F5F] text-white border-[#173F5F]"
                          : "bg-[#F5F8FC] dark:bg-[#0A1929] text-[#102A43] dark:text-white border-[#173F5F]"
                      }`}
                    >
                      {g.title}
                    </button>
                  ))}
                </div>

                {activeGuide && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <div className="border border-[#DCEEFF] dark:border-[#173F5F] bg-[#F5F8FC] dark:bg-[#0A1929] rounded-md p-4">
                      <span className="inline-block px-2.5 py-0.5 text-xs font-bold bg-[#173F5F] text-white rounded-sm">
                        1. SEBELUM KEJADIAN (PRA-BENCANA)
                      </span>
                      <ul className="mt-3 space-y-2 text-xs leading-relaxed">
                        {activeGuide.before_event.map((step: string, i: number) => (
                          <li key={i}>- {step}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="border-2 border-[#B54708] bg-[#F5F8FC] dark:bg-[#0A1929] rounded-md p-4">
                      <span className="inline-block px-2.5 py-0.5 text-xs font-bold bg-[#B54708] text-white rounded-sm">
                        2. SAAT KEJADIAN DARURAT
                      </span>
                      <ul className="mt-3 space-y-2 text-xs leading-relaxed font-medium">
                        {activeGuide.during_event.map((step: string, i: number) => (
                          <li key={i}>- {step}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="border border-[#18794E] bg-[#F5F8FC] dark:bg-[#0A1929] rounded-md p-4">
                      <span className="inline-block px-2.5 py-0.5 text-xs font-bold bg-[#18794E] text-white rounded-sm">
                        3. SETELAH KEJADIAN (PASCA-BENCANA)
                      </span>
                      <ul className="mt-3 space-y-2 text-xs leading-relaxed">
                        {activeGuide.after_event.map((step: string, i: number) => (
                          <li key={i}>- {step}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </section>

            {/* Panel 2: Daftar Cek Interaktif Tas Siaga Bencana & Nomor Darurat Terverifikasi */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <section className="lg:col-span-5 bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
                <h2 className="text-base font-bold text-[#102A43] dark:text-white">
                  Daftar Periksa Tas Siaga Bencana (Persediaan 72 Jam)
                </h2>
                <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF] mb-4">
                  Centang perlengkapan yang sudah Anda siapkan di rumah (tersimpan otomatis di perangkat Anda).
                </p>

                <div className="space-y-2.5">
                  {(edu.emergency_bag_checklist || []).map((c: any) => {
                    const isChecked = Boolean(checkedItems[c.item]);
                    return (
                      <label
                        key={c.item}
                        className="flex items-start gap-3 p-3 rounded-md border border-[#DCEEFF] dark:border-[#173F5F] bg-[#F5F8FC] dark:bg-[#0A1929] cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleChecklist(c.item)}
                          className="mt-1 w-5 h-5 accent-[#173F5F]"
                        />
                        <span className="text-xs">
                          <strong className="block text-[#102A43] dark:text-white">{c.item}</strong>
                          <span className="text-[#173F5F] dark:text-[#DCEEFF]">{c.detail}</span>
                        </span>
                      </label>
                    );
                  })}
                </div>
              </section>

              <section className="lg:col-span-7 bg-white dark:bg-[#102A43] border border-[#DCEEFF] dark:border-[#173F5F] rounded-md p-5">
                <h2 className="text-base font-bold text-[#102A43] dark:text-white">
                  Nomor Layanan Darurat Resmi Terverifikasi di Provinsi Aceh
                </h2>
                <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF] mb-4">
                  Hubungi instansi resmi berikut untuk pelaporan kejadian banjir, tanah longsor, evakuasi SAR, dan informasi meteorologi.
                </p>

                <div className="overflow-x-auto border border-[#DCEEFF] dark:border-[#173F5F] rounded-md">
                  <table className="w-full text-left border-collapse text-xs tabular-nums">
                    <thead>
                      <tr className="bg-[#DCEEFF] dark:bg-[#173F5F] text-[#102A43] dark:text-white">
                        <th className="py-2.5 px-3 font-bold">Instansi Resmi</th>
                        <th className="py-2.5 px-3 font-bold">Nomor Telepon / Call Center</th>
                        <th className="py-2.5 px-3 font-bold">Alamat & Status Verifikasi</th>
                        <th className="py-2.5 px-3 font-bold">Situs Resmi</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#DCEEFF] dark:divide-[#173F5F]">
                      {(edu.verified_emergency_contacts || []).map((contact: any) => (
                        <tr key={contact.agency}>
                          <td className="py-3 px-3 font-bold">{contact.agency}</td>
                          <td className="py-3 px-3 font-extrabold text-sm text-[#B42318] dark:text-[#DCEEFF]">
                            {contact.phone}
                          </td>
                          <td className="py-3 px-3">
                            <div>{contact.address}</div>
                            <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-bold bg-[#18794E] text-white rounded-sm">
                              {contact.verification_status}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <a
                              href={contact.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="underline font-bold text-[#173F5F] dark:text-[#DCEEFF]"
                            >
                              Buka Situs
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          </div>
        )}
      </DataStateWrapper>
    </div>
  );
}
