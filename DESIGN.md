# DESIGN DIRECTION: ACEH SIAGA CUACA

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
