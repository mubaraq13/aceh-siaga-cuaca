import React from "react";
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
