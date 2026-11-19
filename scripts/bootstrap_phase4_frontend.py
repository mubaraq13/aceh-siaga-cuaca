#!/usr/bin/env python3
"""
Phase 4B Automated Builder (DESIGN.md & Next.js 7-Page Public Web Platform) - ACEH SIAGA CUACA
Menuliskan DESIGN.md dan seluruh kode sumber aplikasi frontend Next.js + TypeScript + Tailwind CSS + Leaflet + Recharts.
Jalankan dengan: python scripts\bootstrap_phase4_frontend.py
"""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FILES: dict[str, str] = {}

# ==============================================================================
# 1. DESIGN.md (Arah Desain Resmi Proyek)
# ==============================================================================
FILES["DESIGN.md"] = """# DESIGN DIRECTION: ACEH SIAGA CUACA

## 1. Identitas & Karakter Produk
- **Nama Produk / Logo Teks:** ACEH SIAGA CUACA
- **Tagline Resmi:** Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh.
- **Kategori Layanan:** Platform Publik Informasi Meteorologi, Sistem Informasi Geografis (GIS), Analisis Data Cuaca Historis, Eksperimen Machine Learning, dan Kesiapsiagaan Bencana Hidrometeorologi Provinsi Aceh.
- **Karakter Visual:** Modern, profesional, minimalis, informatif, dapat dipercaya (authoritative civic service), dan mengutamakan perangkat seluler (mobile-first).
- **Design Read:** `Reading this as: public hydrometeorological early-warning and disaster-preparedness web platform for Aceh citizens, BPBA/BPBD officers, and researchers, in an authoritative civic-meteorological functional style, dial ENERGY 1 / RHYTHM 2 / MOTION 1.`
- **Dials:** `ENERGY 1 / RHYTHM 2 / MOTION 1`

## 2. Palet Warna Resmi & Standar Kontras WCAG AA
Seluruh kombinasi warna wajib memenuhi rasio kontras minimum WCAG AA (4.5:1 untuk teks normal, 3:1 untuk teks besar):
- **Primary Deep Navy (`#102A43`):** Warna identitas utama header, teks judul utama, dan permukaan navigasi gelap (Kontras terhadap `#FFFFFF`: 13.8:1).
- **Secondary Maritime Blue (`#173F5F`):** Warna aksi utama (tombol primer, tab aktif, garis fokus keyboard, dan header panel data) (Kontras terhadap `#FFFFFF`: 10.4:1).
- **Soft Sky Tint (`#DCEEFF`):** Warna latar aksen informasi, pembatas struktural (border), dan badge atribusi sumber resmi (Kontras dengan teks `#102A43`: 11.2:1).
- **Canvas Background (`#F5F8FC`):** Latar belakang halaman utama pada mode terang untuk mengurangi silau layar.
- **Surface White (`#FFFFFF`):** Permukaan panel data, tabel prakiraan, dan kartu informasi.
- **Status Waspada / Siaga (`#B54708`):** Warna indikator peringatan tingkat Moderate/Waspada/Siaga dan label kehati-hatian eksperimental ML (Kontras terhadap `#FFFFFF`: 5.02:1 - Lulus WCAG AA).
- **Status Awas / Bahaya Ekstrem (`#B42318`):** Warna indikator peringatan dini tingkat Severe/Extreme dan hujan ekstrem (Kontras terhadap `#FFFFFF`: 5.86:1 - Lulus WCAG AA).
- **Status Aman / Normal (`#18794E`):** Warna indikator kondisi cuaca normal, koneksi API aktif, dan ketiadaan peringatan dini (Kontras terhadap `#FFFFFF`: 5.41:1 - Lulus WCAG AA).

## 3. Tipografi & Hierarki Pembacaan Data
- **Font Utama (Sans-Serif):** `'Plus Jakarta Sans', 'Segoe UI', Roboto, system-ui, -apple-system, sans-serif` untuk keterbacaan tinggi di berbagai ukuran layar tanpa ketergantungan pemuatan font eksternal saat jaringan lambat.
- **Font Numerik & Kode Wilayah (Monospace / Tabular):** `ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace` serta `font-variant-numeric: tabular-nums` pada seluruh angka suhu, persentase kelembapan, kecepatan angin, koordinat, kode wilayah ADM4, dan milimeter curah hujan.

## 4. Motif Identitas: Pita Provenance & Freshness Data
Setiap kontainer yang menyajikan informasi cuaca wajib memiliki pita kepala (header strip) yang mencantumkan:
1. **Badge Kategori & Sumber Data:** Membedakan dengan tegas antara `PRAKIRAAN RESMI BMKG`, `PERINGATAN DINI RESMI BMKG`, `OBSERVASI HISTORIS STASIUN`, `ANALISIS SPASIAL GIS`, dan `MODEL EKSPERIMENTAL ML`.
2. **Indikator Kesegaran Data (Data Freshness):** Menampilkan waktu pembaruan terakhir dalam zona waktu `Asia/Jakarta (WIB)` serta status kesehatan koneksi (`ONLINE` atau `MENGGUNAKAN CACHE TERAKHIR`).
"""

# ==============================================================================
# 2. Konfigurasi Proyek Next.js (package.json, tsconfig, next.config, tailwind)
# ==============================================================================
FILES["frontend/package.json"] = """{
  "name": "aceh-siaga-cuaca-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "lint": "next lint"
  },
  "dependencies": {
    "leaflet": "^1.9.4",
    "next": "14.2.15",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.13.0"
  },
  "devDependencies": {
    "@types/leaflet": "^1.9.12",
    "@types/node": "^20.16.10",
    "@types/react": "^18.3.11",
    "@types/react-dom": "^18.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "typescript": "^5.6.3"
  }
}
"""

FILES["frontend/tsconfig.json"] = """{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""

FILES["frontend/next.config.mjs"] = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
"""

FILES["frontend/postcss.config.mjs"] = """/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;
"""

FILES["frontend/tailwind.config.ts"] = """import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#102A43",
          800: "#173F5F",
        },
        sky: {
          100: "#DCEEFF",
          50: "#F5F8FC",
        },
        status: {
          warning: "#B54708",
          danger: "#B42318",
          safe: "#18794E",
        },
      },
    },
  },
  plugins: [],
};

export default config;
"""

# ==============================================================================
# 3. Global CSS (frontend/src/app/globals.css)
# ==============================================================================
FILES["frontend/src/app/globals.css"] = """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-canvas: #F5F8FC;
  --bg-surface: #FFFFFF;
  --text-primary: #102A43;
  --text-secondary: #173F5F;
  --border-tint: #DCEEFF;
}

.dark {
  --bg-canvas: #0A1929;
  --bg-surface: #102A43;
  --text-primary: #F5F8FC;
  --text-secondary: #DCEEFF;
  --border-tint: #173F5F;
}

body {
  background-color: var(--bg-canvas);
  color: var(--text-primary);
  font-family: 'Plus Jakarta Sans', 'Segoe UI', Roboto, system-ui, -apple-system, sans-serif;
  line-height: 1.5;
  overflow-x: hidden;
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

/* Indikator Fokus Keyboard yang Jelas sesuai R-32 & WCAG AA */
*:focus-visible {
  outline: 3px solid #173F5F !important;
  outline-offset: 2px !important;
}

.dark *:focus-visible {
  outline: 3px solid #DCEEFF !important;
  outline-offset: 2px !important;
}
"""

# ==============================================================================
# 4. TypeScript Interfaces & API Client (src/types/api.ts & src/lib/api.ts)
# ==============================================================================
FILES["frontend/src/types/api.ts"] = """export type DataCategory =
  | "OFFICIAL_BMKG_FORECAST"
  | "OFFICIAL_BMKG_ALERT"
  | "HISTORICAL_OBSERVATION"
  | "SPATIOTEMPORAL_GIS"
  | "EXPERIMENTAL_ML_PREDICTION"
  | "DISASTER_AND_PREPAREDNESS"
  | "DASHBOARD_OVERVIEW"
  | "GEOSPATIAL_REFERENCE"
  | "SYSTEM_HEALTH";

export interface StandardAPIEnvelope<T> {
  status: string;
  data_category: DataCategory;
  source_attribution: string;
  disclaimer: string;
  last_updated_wib: string;
  api_health: string;
  is_demo_mode: boolean;
  data: T;
}

export interface RegencyItem {
  region_code: string;
  region_name: string;
  representative_adm4: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  topography_zone: string;
  nearest_bmkg_station_wmo: string;
}

export interface ForecastSlot {
  forecast_time_utc: string;
  forecast_time_local: string;
  analysis_time: string;
  temperature_c: number;
  humidity_pct: number;
  weather_code: number | null;
  weather_desc_id: string;
  weather_desc_en: string | null;
  wind_speed_kmh: number;
  wind_speed_ms: number;
  wind_dir_cardinal: string | null;
  wind_dir_deg: number | null;
  cloud_cover_pct: number | null;
  visibility_text: string | null;
}

export interface ActiveAlertItem {
  cap_identifier: string;
  sender: string;
  sent_time: string;
  status: string;
  msg_type: string;
  event_type: string;
  urgency: string;
  severity: string;
  certainty: string;
  effective_time: string;
  onset_time: string | null;
  expires_time: string;
  headline: string;
  description: string;
  instruction: string | null;
  official_web_url: string;
  cap_xml_url: string;
  affected_areas_text: string;
  polygons_geojson: number[][][];
  source_attribution: string;
}

export interface StationPredictionItem {
  wmo_id: string;
  station_name: string;
  region_code: string;
  last_observation_date: string;
  target_prediction_date: string;
  horizon_days: number;
  predicted_rainfall_mm: number;
  predicted_extreme_probability: number;
  decision_threshold: number;
  is_potential_heavy_rain: boolean;
  predicted_category: string;
  regression_model_used: string;
  classification_model_used: string;
  model_version: string;
  dataset_version: string;
  predicted_at_wib: string;
  top_contributing_features: Array<{ feature: string; importance: number }>;
  is_experimental: boolean;
  disclaimer_label: string;
}
"""

FILES["frontend/src/lib/api.ts"] = """import { StandardAPIEnvelope } from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export const BACKEND_ORIGIN = API_BASE_URL.replace(/\\/api\\/v1\\/?$/, "");

export async function fetchFromBackend<T>(endpoint: string): Promise<StandardAPIEnvelope<T>> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) detail = String(errJson.detail);
    } catch {
      // Gunakan kode HTTP standar bila gagal membaca JSON
    }
    throw new Error(`Gangguan komunikasi layanan data (${detail})`);
  }

  return (await response.json()) as StandardAPIEnvelope<T>;
}

export function formatWibTimestamp(isoString: string | undefined | null): string {
  if (!isoString) return "Belum tercatat";
  try {
    const dt = new Date(isoString);
    if (Number.isNaN(dt.getTime())) return isoString;
    return new Intl.DateTimeFormat("id-ID", {
      timeZone: "Asia/Jakarta",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(dt) + " WIB";
  } catch {
    return isoString;
  }
}
"""

# ==============================================================================
# 5. Komponen Inti: ProvenanceHeader, DataStateWrapper, Navbar, Footer
# ==============================================================================
FILES["frontend/src/components/ProvenanceHeader.tsx"] = """import React from "react";
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
"""

FILES["frontend/src/components/DataStateWrapper.tsx"] = """import React from "react";

interface DataStateWrapperProps {
  loading: boolean;
  error: string | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: React.ReactNode;
}

export default function DataStateWrapper({
  loading,
  error,
  isEmpty = false,
  emptyMessage = "Data belum tersedia untuk kriteria yang dipilih.",
  onRetry,
  children,
}: DataStateWrapperProps) {
  if (loading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="border border-[#DCEEFF] dark:border-[#173F5F] bg-white dark:bg-[#102A43] p-6 rounded-md"
      >
        <p className="text-sm font-semibold text-[#102A43] dark:text-white">
          Sedang memuat data meteorologi Aceh...
        </p>
        <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
          Mohon tunggu sebentar, sistem sedang memverifikasi pembaruan data terbaru.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        role="alert"
        className="border-2 border-[#B42318] bg-white dark:bg-[#102A43] p-6 rounded-md"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <span className="inline-block px-2.5 py-1 text-xs font-bold bg-[#B42318] text-white rounded-sm">
              GANGGUAN PENGAMBILAN DATA
            </span>
            <h3 className="mt-2 text-base font-bold text-[#102A43] dark:text-white">
              Tidak dapat memuat informasi terkini dari server backend
            </h3>
            <p className="mt-1 text-sm text-[#173F5F] dark:text-[#DCEEFF]">
              Rincian teknis: {error}. Pastikan server FastAPI aktif pada port 8000.
            </p>
          </div>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="min-h-[44px] px-4 py-2 text-sm font-semibold bg-[#173F5F] hover:bg-[#102A43] text-white rounded-md shrink-0"
            >
              Muat Ulang Data Cuaca
            </button>
          )}
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="border border-[#DCEEFF] dark:border-[#173F5F] bg-white dark:bg-[#102A43] p-6 rounded-md">
        <p className="text-sm font-semibold text-[#102A43] dark:text-white">
          {emptyMessage}
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
"""

FILES["frontend/src/components/Navbar.tsx"] = """"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Beranda" },
  { href: "/prakiraan", label: "Prakiraan Cuaca" },
  { href: "/peta", label: "Peta Interaktif" },
  { href: "/analisis", label: "Analisis Cuaca" },
  { href: "/machine-learning", label: "Machine Learning" },
  { href: "/peringatan-dini", label: "Peringatan Dini" },
  { href: "/edukasi", label: "Edukasi Kesiapsiagaan" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("aceh_siaga_theme");
    if (savedTheme === "dark") {
      setDarkMode(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    const nextDark = !darkMode;
    setDarkMode(nextDark);
    if (nextDark) {
      document.documentElement.classList.add("dark");
      window.localStorage.setItem("aceh_siaga_theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      window.localStorage.setItem("aceh_siaga_theme", "light");
    }
  };

  return (
    <header className="bg-[#102A43] text-white border-b border-[#173F5F] sticky top-0 z-50">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-white focus:text-[#102A43] focus:px-4 focus:py-2 focus:font-bold"
      >
        Lewati ke konten utama
      </a>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between min-h-[68px] py-2 gap-4">
          <div>
            <Link
              href="/"
              className="text-lg sm:text-xl font-extrabold tracking-tight text-white block"
            >
              ACEH SIAGA CUACA
            </Link>
            <p className="text-xs text-[#DCEEFF] hidden sm:block">
              Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={darkMode ? "Aktifkan Mode Terang" : "Aktifkan Mode Gelap"}
              className="min-h-[44px] px-3 py-2 text-xs font-semibold bg-[#173F5F] hover:bg-[#DCEEFF] hover:text-[#102A43] text-white rounded-md transition-colors"
            >
              {darkMode ? "Mode Terang" : "Mode Gelap"}
            </button>

            <button
              type="button"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-nav-menu"
              className="lg:hidden min-h-[44px] px-3 py-2 text-xs font-bold bg-[#173F5F] text-white rounded-md"
            >
              {mobileMenuOpen ? "Tutup Menu" : "Menu Navigasi"}
            </button>
          </div>
        </div>

        {/* Navigasi Desktop */}
        <nav
          aria-label="Navigasi Utama"
          className="hidden lg:flex items-center gap-1 pb-2 overflow-x-auto"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`min-h-[44px] px-3.5 py-2.5 text-sm font-semibold rounded-md flex items-center transition-colors ${
                  isActive
                    ? "bg-[#DCEEFF] text-[#102A43]"
                    : "text-[#F5F8FC] hover:bg-[#173F5F]"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Navigasi Mobile */}
        {mobileMenuOpen && (
          <nav
            id="mobile-nav-menu"
            aria-label="Navigasi Seluler"
            className="lg:hidden py-3 border-t border-[#173F5F] flex flex-col gap-1"
          >
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={isActive ? "page" : undefined}
                  className={`min-h-[44px] px-4 py-2.5 text-sm font-semibold rounded-md flex items-center ${
                    isActive
                      ? "bg-[#DCEEFF] text-[#102A43]"
                      : "text-white hover:bg-[#173F5F]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        )}
      </div>
    </header>
  );
}
"""

FILES["frontend/src/components/Footer.tsx"] = """import React from "react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-[#102A43] text-[#F5F8FC] border-t border-[#173F5F] mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h2 className="text-base font-bold text-white">ACEH SIAGA CUACA</h2>
            <p className="mt-2 text-xs text-[#DCEEFF] leading-relaxed">
              Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh.
              Mengintegrasikan data prakiraan dan peringatan dini resmi BMKG,
              analisis spasial-temporal GIS, serta riset evaluasi Machine Learning.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-bold text-white">Atribusi & Pemisahan Sumber Data</h3>
            <ul className="mt-2 space-y-1.5 text-xs text-[#DCEEFF]">
              <li>1. Prakiraan Cuaca 3 Hari: API Publik Resmi BMKG (ADM4 Aceh).</li>
              <li>2. Peringatan Dini Cuaca: RSS & Common Alerting Protocol (CAP v1.2) BMKG.</li>
              <li>3. Prediksi Machine Learning: Eksperimen riset akademik, bukan peringatan resmi BMKG.</li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-bold text-white">Akses Cepat Keselamatan</h3>
            <div className="mt-2 flex flex-col gap-2 text-xs">
              <Link href="/peringatan-dini" className="text-[#DCEEFF] underline hover:text-white py-1">
                Periksa Peringatan Dini Cuaca Aktif BMKG
              </Link>
              <Link href="/edukasi" className="text-[#DCEEFF] underline hover:text-white py-1">
                Daftar Kontak Darurat BPBA, Basarnas & Tas Siaga Bencana
              </Link>
              <Link href="/peta" className="text-[#DCEEFF] underline hover:text-white py-1">
                Peta Sebaran Stasiun Cuaca & Riwayat Bencana Aceh
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-[#173F5F] flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs text-[#DCEEFF] gap-2">
          <span>Zona Waktu Operasional: Asia/Jakarta (WIB / UTC+7)</span>
          <span>Wilayah Fokus: Provinsi Aceh (23 Kabupaten/Kota)</span>
        </div>
      </div>
    </footer>
  );
}
"""

# ==============================================================================
# 6. Root Layout (frontend/src/app/layout.tsx)
# ==============================================================================
FILES["frontend/src/app/layout.tsx"] = """import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "ACEH SIAGA CUACA - Informasi Cuaca & Kesiapsiagaan Bencana Provinsi Aceh",
  description:
    "Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh berbasis Data BMKG, GIS, dan Machine Learning.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body className="min-h-screen flex flex-col">
        <Navbar />
        <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
"""

# ==============================================================================
# 7. HALAMAN 1: HOME (frontend/src/app/page.tsx)
# ==============================================================================
FILES["frontend/src/app/page.tsx"] = """"use client";

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
"""

# ==============================================================================
# 8. HALAMAN 2: PRAKIRAAN CUACA (frontend/src/app/prakiraan/page.tsx)
# ==============================================================================
FILES["frontend/src/app/prakiraan/page.tsx"] = """"use client";

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
"""

# ==============================================================================
# 9. HALAMAN 3: PETA INTERAKTIF GIS (Komponen Leaflet & Halaman Peta)
# ==============================================================================
FILES["frontend/src/components/AcehLeafletMap.tsx"] = """"use client";

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
"""

FILES["frontend/src/app/peta/page.tsx"] = """"use client";

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
"""

# ==============================================================================
# 10. HALAMAN 4: ANALISIS CUACA HISTORIS (frontend/src/app/analisis/page.tsx)
# ==============================================================================
FILES["frontend/src/app/analisis/page.tsx"] = """"use client";

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
"""

# ==============================================================================
# 11. HALAMAN 5: MACHINE LEARNING (frontend/src/app/machine-learning/page.tsx)
# ==============================================================================
FILES["frontend/src/app/machine-learning/page.tsx"] = """"use client";

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
"""

# ==============================================================================
# 12. HALAMAN 6: PERINGATAN DINI RESMI BMKG (frontend/src/app/peringatan-dini/page.tsx)
# ==============================================================================
FILES["frontend/src/app/peringatan-dini/page.tsx"] = """"use client";

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
"""

# ==============================================================================
# 13. HALAMAN 7: EDUKASI KESIAPSIAGAAN (frontend/src/app/edukasi/page.tsx)
# ==============================================================================
FILES["frontend/src/app/edukasi/page.tsx"] = """"use client";

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
"""


def main() -> None:
    print(f"[PHASE 4B FRONTEND BUILDER] Menuliskan DESIGN.md dan aplikasi Next.js ke: {BASE_DIR}")
    for rel_path, content in FILES.items():
        target = BASE_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"  [OK] {rel_path} ({len(content)} bytes)")
    print("\n[PHASE 4B FRONTEND BUILDER] Selesai! Ikuti langkah instalasi & verifikasi di bawah.")


if __name__ == "__main__":
    main()