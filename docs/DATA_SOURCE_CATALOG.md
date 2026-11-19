# KATALOG SUMBER DATA (DATA SOURCE CATALOG)
## ACEH SIAGA CUACA

Dokumen ini mencatat seluruh sumber data resmi yang digunakan dalam platform **ACEH SIAGA CUACA**, lengkap dengan spesifikasi teknis, metode akses, status verifikasi, dan keterbatasannya.

---

## 1. Tabel Ringkasan Ketersediaan & Verifikasi Sumber Data

| No | Nama Data | Sumber Resmi | URL / Endpoint | Format | Resolusi Waktu | Resolusi Spasial | Periode Tersedia | Metode Akses | Status Verifikasi | Keterbatasan Utama |
| :- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Prakiraan Cuaca Publik BMKG** | BMKG | `https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={KODE_ADM4}` | JSON | Interval 3 jam (Horizon 3 hari, update 2x/hari) | Tingkat Desa / Gampong (`ADM4`) | *Rolling* 3 hari ke depan (Real-time) | REST API Publik (GET) | **Terverifikasi (Aktif)** | Rate limit 60 req/menit/IP; tidak memuat angka curah hujan (`mm`); tidak menyimpan arsip historis. |
| 2 | **Peringatan Dini Cuaca (Nowcasting)** | BMKG | `https://www.bmkg.go.id/alerts/nowcast/id` | RSS 2.0 XML & CAP v1.2 XML | Real-time (Berbasis kejadian, masa berlaku 1–6 jam) | Poligon Koordinat (`lat,lon`) & Deskripsi Kecamatan/Kabupaten | Hanya peringatan yang sedang aktif saat diakses | HTTP GET Polling + XML Parsing mengikuti `<link>` RSS | **Terverifikasi (Aktif)** | Hanya menyajikan peringatan aktif; membutuhkan penyimpanan lokal (*archiving*) untuk analisis historis. |
| 3 | **Data Observasi Historis Harian Stasiun** | Pusat Database BMKG (Data Online) | `https://dataonline.bmkg.go.id/` | CSV / XLSX | Harian (Akumulasi 24 jam pukul 07.00 WIB) | Titik Koordinat Stasiun UPT BMKG | 1 Januari 2021 – Sekarang (Tersedia sejak >1980) | Unduh Manual via Portal Terautentikasi -> Pipeline Import CSV/XLSX | **Terverifikasi (Butuh Login Portal & Import File)** | Tidak ada REST API terbuka tanpa autentikasi/CAPTCHA; jumlah stasiun sinoptik di Aceh terbatas (~5–6 stasiun utama); terdapat kode `8888` dan `9999`. |
| 4 | **Riwayat Kejadian & Dampak Bencana Aceh** | BNPB (DIBI) & BPBA Aceh | `https://dibi.bnpb.go.id/` & `https://bpba.acehprov.go.id/` | CSV / XLSX / HTML Tabel | Harian / Per Kejadian Bencana | Tingkat Kabupaten/Kota (`ADM2`) atau Kecamatan (`ADM3`) | 1 Januari 2021 – Sekarang | Unduh Laporan CSV/XLSX -> Pipeline `disaster_import.py` | **Terverifikasi (Akses Publik via Unduh Tabel)** | Koordinat titik spesifik kejadian sering kali hanya tercatat pada level kabupaten/kecamatan; potensi *reporting delay*. |
| 5 | **Peta Indeks Risiko Bencana (InaRISK)** | BNPB | `https://inarisk.bnpb.go.id/` / `https://gis.bnpb.go.id/arcgis/rest/services/inarisk/` | WMS / ArcGIS REST / GeoJSON | Statis / Pemutakhiran Berkala | Grid Raster (30m–100m) & Agregasi Kabupaten | Versi Kajian Risiko Bencana Terbaru | WMS Layer Integration / GeoJSON Overlay | **Terverifikasi (Service Publik)** | Merupakan peta indeks kerentanan/risiko statis, bukan kondisi cuaca dinamis harian. |
| 6 | **Batas Wilayah Administrasi Aceh (ADM1–ADM4)** | BIG (TanahAir Indonesia) & Kemendagri | `https://tanahair.indonesia.go.id/` | GeoJSON / Shapefile (`.shp`) | Statis (Pemutakhiran Kepmendagri) | Provinsi (`11`), 23 Kab/Kota, 290 Kecamatan, ~6.500 Gampong | Kepmendagri Terbaru | File Statis GeoJSON -> Import ke PostGIS | **Terverifikasi (Tersedia)** | Ukuran geometri level desa (`ADM4`) cukup besar sehingga perlu penyederhanaan (*topology simplification*) untuk rendering web. |
| 7 | **Data Topografi & Elevasi (DEMNAS)** | BIG | `https://tanahair.indonesia.go.id/demnas/` | GeoTIFF | Statis | 0.27 arc-second (~8.3 meter) | Rilis Nasional DEMNAS | Unduh Tile GeoTIFF Aceh -> Ekstraksi Elevasi/Slope Stasiun | **Terverifikasi (Unduh Terbuka)** | Ukuran file raster mentah sangat besar; diproses secara *offline* untuk ekstraksi fitur elevasi/kemiringan wilayah. |
| 8 | **Data Kependudukan Kabupaten/Kota Aceh** | BPS Provinsi Aceh | `https://aceh.bps.go.id/` & `https://webapi.bps.go.id/` | JSON / XLSX / CSV | Tahunan | Tingkat Kabupaten/Kota (`ADM2`) & Kecamatan (`ADM3`) | 2021 – 2026 | Web API BPS (dengan API Key) atau Import CSV Tabel Dinamis | **Terverifikasi (Aktif)** | Resolusi waktu tahunan; digunakan sebagai variabel bobot populasi terdampak (*exposure*), bukan prediktor cuaca. |

---

## 2. Daftar Stasiun Pengamatan BMKG di Provinsi Aceh

Berikut adalah daftar stasiun meteorologi dan klimatologi resmi BMKG di wilayah Provinsi Aceh yang menjadi rujukan data observasi historis (`weather_stations`):

| Kode WMO / ID | Nama Stasiun | Kabupaten / Kota | Koordinat Perkiraan (Lat, Lon) | Elevasi (mdpl) | Tipe Stasiun |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `96001` | Stasiun Meteorologi Kelas I Sultan Iskandar Muda | Kab. Aceh Besar (Blang Bintang) | `5.5225, 95.4170` | ~20 m | Meteorologi Sinoptik / Penerbangan |
| `96002` | Stasiun Meteorologi Maimun Saleh | Kota Sabang (Cot Ba'U) | `5.8742, 95.3397` | ~126 m | Meteorologi Sinoptik / Maritim |
| `96003` | Stasiun Klimatologi Aceh | Kab. Aceh Besar (Indrapuri) | `5.4045, 95.4472` | ~45 m | Klimatologi Rujukan Provinsi |
| `96009` | Stasiun Meteorologi Malikussaleh | Kab. Aceh Utara (Muara Batu) | `5.2286, 96.9475` | ~8 m | Meteorologi Sinoptik |
| `96011` | Stasiun Meteorologi Cut Nyak Dhien | Kab. Nagan Raya (Kuala Pesisir) | `4.0450, 96.2483` | ~4 m | Meteorologi Sinoptik |

*Catatan: Selain 5 stasiun utama di atas, BMKG dan Dinas Pengairan/Pertanian memiliki jaringan Pos Hujan Kerjasama (OBS) dan Automatic Rain Gauge (ARG) di kabupaten/kota yang datanya dapat diimpor ke dalam tabel `weather_observations` melalui modul import CSV/XLSX apabila diperoleh dari permohonan data ke Stasiun Klimatologi Aceh.*

---

## 3. Daftar 23 Kabupaten/Kota di Provinsi Aceh (Kode Administrasi `ADM2`)

Seluruh kode wilayah pada aplikasi mengacu pada kode standar Kemendagri yang digunakan oleh API BMKG:

1. `11.01` — Kabupaten Aceh Selatan
2. `11.02` — Kabupaten Aceh Tenggara
3. `11.03` — Kabupaten Aceh Timur
4. `11.04` — Kabupaten Aceh Tengah
5. `11.05` — Kabupaten Aceh Barat
6. `11.06` — Kabupaten Aceh Besar
7. `11.07` — Kabupaten Pidie
8. `11.08` — Kabupaten Aceh Utara
9. `11.09` — Kabupaten Simeulue
10. `11.10` — Kabupaten Aceh Singkil
11. `11.11` — Kabupaten Bireuen
12. `11.12` — Kabupaten Aceh Barat Daya
13. `11.13` — Kabupaten Gayo Lues
14. `11.14` — Kabupaten Aceh Jaya
15. `11.15` — Kabupaten Nagan Raya
16. `11.16` — Kabupaten Aceh Tamiang
17. `11.17` — Kabupaten Bener Meriah
18. `11.18` — Kabupaten Pidie Jaya
19. `11.71` — Kota Banda Aceh
20. `11.72` — Kota Sabang
21. `11.73` — Kota Lhokseumawe
22. `11.74` — Kota Langsa
23. `11.75` — Kota Subulussalam

---

## 4. Prosedur Resmi Permohonan Data Historis Lengkap (Jika Melampaui Kuota Portal Data Online)

Apabila peneliti membutuhkan data curah hujan per jam (*hourly rainfall*) atau data pos hujan kerjasama seluruh kabupaten yang tidak tercantum di unduhan mandiri `dataonline.bmkg.go.id`:
1. Buat akun peneliti/mahasiswa di `https://dataonline.bmkg.go.id/` untuk mengunduh data harian stasiun sinoptik secara langsung.
2. Untuk data pos hujan tingkat kecamatan dan data per jam, ajukan surat permohonan data untuk keperluan penelitian akademik/kebencanaan (tarif Rp 0,- / Nol Rupiah sesuai PP No. 47 Tahun 2018 & Peraturan BMKG tentang Tarif PNBP Nol Rupiah untuk Penelitian/Pendidikan) yang ditujukan kepada **Kepala Stasiun Klimatologi Aceh (Aceh Besar)** dengan melampirkan proposal penelitian dan daftar parameter yang diminta.
3. Simpan berkas CSV/XLSX yang diterima ke dalam direktori `data/raw/bmkg/` dan jalankan pipeline `python -m src.data_collection.bmkg_historical_import`.