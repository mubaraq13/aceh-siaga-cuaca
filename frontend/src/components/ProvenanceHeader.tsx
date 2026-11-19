import React from "react";
import { DataCategory } from "@/types/api";
import { formatWibTimestamp } from "@/lib/api";

interface ProvenanceHeaderProps {
  category: DataCategory;
  sourceAttribution: string;
  lastUpdatedWib: string;
  apiHealth?: string;
  disclaimer?: string;
  isDemoMode?: boolean;
}

const CATEGORY_STYLES: Record<
  DataCategory,
  { badgeText: string; badgeClass: string }
> = {
  OFFICIAL_BMKG_FORECAST: {
    badgeText: "PRAKIRAAN RESMI BMKG",
    badgeClass: "bg-[#173F5F] text-white",
  },
  OFFICIAL_BMKG_ALERT: {
    badgeText: "PERINGATAN DINI RESMI BMKG (CAP)",
    badgeClass: "bg-[#B42318] text-white",
  },
  HISTORICAL_OBSERVATION: {
    badgeText: "OBSERVASI & ANALISIS HISTORIS",
    badgeClass: "bg-[#102A43] text-white",
  },
  SPATIOTEMPORAL_GIS: {
    badgeText: "DATA GEOSPASIAL & GIS ACEH",
    badgeClass: "bg-[#173F5F] text-white",
  },
  EXPERIMENTAL_ML_PREDICTION: {
    badgeText: "MODEL EKSPERIMENTAL MACHINE LEARNING",
    badgeClass: "bg-[#B54708] text-white",
  },
  DISASTER_AND_PREPAREDNESS: {
    badgeText: "EDUKASI & KONTAK DARURAT RESMI",
    badgeClass: "bg-[#18794E] text-white",
  },
  DASHBOARD_OVERVIEW: {
    badgeText: "RINGKASAN TERPADU ACEH",
    badgeClass: "bg-[#102A43] text-white",
  },
  GEOSPATIAL_REFERENCE: {
    badgeText: "REFERENSI WILAYAH KEMENDAGRI/BMKG",
    badgeClass: "bg-[#173F5F] text-white",
  },
  SYSTEM_HEALTH: {
    badgeText: "STATUS SISTEM",
    badgeClass: "bg-[#18794E] text-white",
  },
};

export default function ProvenanceHeader({
  category,
  sourceAttribution,
  lastUpdatedWib,
  apiHealth = "ONLINE",
  disclaimer,
  isDemoMode = false,
}: ProvenanceHeaderProps) {
  const meta = CATEGORY_STYLES[category] || CATEGORY_STYLES.DASHBOARD_OVERVIEW;
  const isDegraded = apiHealth !== "ONLINE";

  return (
    <div className="border-b border-[#DCEEFF] dark:border-[#173F5F] bg-[#F5F8FC] dark:bg-[#0A1929] px-4 py-3 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`px-2.5 py-1 font-semibold tracking-wide rounded-sm ${meta.badgeClass}`}>
            {meta.badgeText}
          </span>
          {isDemoMode && (
            <span className="px-2.5 py-1 font-semibold rounded-sm bg-[#B54708] text-white">
              MODE DEMO TERVALIDASI
            </span>
          )}
          <span className="font-medium text-[#102A43] dark:text-[#DCEEFF]">
            Sumber: {sourceAttribution}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3 tabular-nums">
          <span className="text-[#173F5F] dark:text-[#DCEEFF]">
            Pembaruan Data: <strong>{formatWibTimestamp(lastUpdatedWib)}</strong>
          </span>
          <span
            className={`px-2 py-0.5 font-semibold rounded-sm ${
              isDegraded
                ? "bg-[#B54708] text-white"
                : "bg-[#18794E] text-white"
            }`}
          >
            {isDegraded ? "STATUS: MENGGUNAKAN CACHE TERAKHIR" : "STATUS: TERHUBUNG"}
          </span>
        </div>
      </div>

      {isDegraded && (
        <p className="mt-2 font-medium text-[#B54708] dark:text-[#DCEEFF]">
          Perhatian: Koneksi langsung ke server eksternal sedang mengalami perlambatan. Menampilkan data valid terakhir yang berhasil disimpan pada waktu pembaruan di atas.
        </p>
      )}

      {disclaimer && (
        <p className="mt-1.5 text-[#173F5F] dark:text-[#DCEEFF]">
          Keterangan: {disclaimer}
        </p>
      )}
    </div>
  );
}
