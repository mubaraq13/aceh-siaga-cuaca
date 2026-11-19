# KAMUS DATA (DATA DICTIONARY)
## ACEH SIAGA CUACA

Dokumen ini mendefinisikan skema atribut, tipe data, satuan pengukuran, aturan validasi, serta perlakuan terhadap nilai hilang (*missing values*) dan kode khusus untuk seluruh entitas data di dalam sistem **ACEH SIAGA CUACA**.

---

## 1. Skema Data Prakiraan Cuaca BMKG (`weather_forecasts`)
Sumber: `https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={KODE_ADM4}`

| Nama Field (API) | Nama Kolom (DB) | Tipe Data | Satuan | Deskripsi | Aturan Validasi & Normalisasi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `lokasi.adm1` | `adm1_code` | `VARCHAR(5)` | - | Kode Provinsi Kemendagri | Wajib bernilai `'11'` (Provinsi Aceh). |
| `lokasi.adm2` | `adm2_code` | `VARCHAR(10)` | - | Kode Kabupaten/Kota | Pola regex `^11\.\d{2}$`. |
| `lokasi.adm3` | `adm3_code` | `VARCHAR(15)` | - | Kode Kecamatan | Pola regex `^11\.\d{2}\.\d{2}$`. |
| `lokasi.adm4` | `adm4_code` | `VARCHAR(20)` | - | Kode Desa/Gampong | Pola regex `^11\.\d{2}\.\d{2}\.\d{4}$`. |
| `lokasi.lat` | `latitude` | `NUMERIC(9,6)` | Derajat ($\circ$) | Lintang lokasi gampong | Rentang Aceh: `1.900000` s.d. `6.200000`. |
| `lokasi.lon` | `longitude` | `NUMERIC(9,6)` | Derajat ($\circ$) | Bujur lokasi gampong | Rentang Aceh: `94.900000` s.d. `98.400000`. |
| `utc_datetime` | `forecast_time_utc` | `TIMESTAMPTZ` | UTC | Waktu target prakiraan dalam UTC | Wajib valid ISO-8601. |
| `local_datetime` | `forecast_time_local` | `TIMESTAMP` | WIB | Waktu target prakiraan lokal (`Asia/Jakarta`) | `utc_datetime + 7 hours`. |
| `analysis_date` | `analysis_time` | `TIMESTAMPTZ` | UTC / WIB | Waktu model prakiraan diproduksi oleh BMKG | Digunakan untuk melacak versi pemutakhiran prakiraan. |
| `t` | `temperature_c` | `NUMERIC(4,1)` | $^{\circ}\text{C}$ | Suhu udara permukaan prakiraan | Rentang wajar Aceh: `10.0` s.d. `42.0`. |
| `hu` | `humidity_pct` | `NUMERIC(5,2)` | `%` | Kelembapan udara relatif prakiraan | Rentang valid: `0.0` s.d. `100.0`. |
| `weather` | `weather_code` | `INTEGER` | Kode | Kode numerik kondisi cuaca BMKG | Contoh: `0` (Cerah), `3` (Berawan), `61` (Hujan Ringan), `63` (Hujan Sedang), `95` (Hujan Petir). |
| `weather_desc` | `weather_desc_id` | `VARCHAR(100)` | Teks | Deskripsi cuaca Bahasa Indonesia | **DILARANG** dikonversi menjadi angka curah hujan (`mm`). |
| `weather_desc_en` | `weather_desc_en` | `VARCHAR(100)` | Teks | Deskripsi cuaca Bahasa Inggris | Disimpan apa adanya untuk referensi. |
| `ws` | `wind_speed_kmh` | `NUMERIC(6,2)` | $\text{km/jam}$ | Kecepatan angin prakiraan | Rentang valid: $\ge 0.0$. Sediakan juga konversi `wind_speed_ms` ($\text{m/s} = \text{km/jam} / 3.6$). |
| `wd` | `wind_dir_cardinal` | `VARCHAR(10)` | Arah Mata Angin | Arah datangnya angin (`N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`, `VARIABLE`) | Validasi terhadap daftar arah mata angin standar. |
| `wd_deg` | `wind_dir_deg` | `NUMERIC(5,1)` | Derajat ($\circ$) | Sudut arah angin | Rentang: `0.0` s.d. `360.0`. |
| `tcc` | `cloud_cover_pct` | `NUMERIC(5,2)` | `%` | Persentase tutupan awan total (*Total Cloud Cover*) | Rentang: `0.0` s.d. `100.0`. |
| `vs_text` | `visibility_text` | `VARCHAR(30)` | $\text{km}$ / Teks | Jarak pandang dalam teks (misal: `> 10 km`, `< 4 km`) | Simpan nilai teks asli pada `visibility_text` dan angka meter pada `visibility_m` jika tersedia di `vs`. |

---

## 2. Skema Data Peringatan Dini Cuaca CAP BMKG (`weather_alerts`)
Sumber: `https://www.bmkg.go.id/alerts/nowcast/id` (RSS + CAP v1.2 XML)

| Elemen XML CAP | Nama Kolom (DB) | Tipe Data | Deskripsi | Aturan Validasi |
| :--- | :--- | :--- | :--- | :--- |
| `<identifier>` | `cap_identifier` | `VARCHAR(100)` | ID unik dokumen CAP dari BMKG | `UNIQUE NOT NULL` (kunci deduplikasi). |
| `<sender>` | `sender` | `VARCHAR(150)` | Identitas pengirim resmi BMKG | Wajib terverifikasi domain/identitas BMKG. |
| `<sent>` | `sent_time` | `TIMESTAMPTZ` | Waktu peringatan diterbitkan | Konversi ke `TIMESTAMPTZ` (`Asia/Jakarta`). |
| `<status>` | `status` | `VARCHAR(30)` | Status peringatan (`Actual`, `Exercise`, `System`, `Test`) | Hanya tampilkan `status = 'Actual'` ke publik. |
| `<msgType>` | `msg_type` | `VARCHAR(30)` | Jenis pesan (`Alert`, `Update`, `Cancel`) | Jika `Cancel`, tandai peringatan sebelumnya tidak aktif. |
| `<info><event>` | `event_type` | `VARCHAR(100)` | Jenis kejadian cuaca (misal: `Hujan Lebat disertai Kilat/Petir dan Angin Kencang`) | Tidak boleh kosong. |
| `<info><urgency>` | `urgency` | `VARCHAR(30)` | Tingkat urgensi (`Immediate`, `Expected`, `Future`, `Past`, `Unknown`) | Enum standar OASIS CAP 1.2. |
| `<info><severity>` | `severity` | `VARCHAR(30)` | Tingkat keparahan (`Extreme`, `Severe`, `Moderate`, `Minor`, `Unknown`) | Menentukan skema warna badge peringatan di UI. |
| `<info><certainty>` | `certainty` | `VARCHAR(30)` | Tingkat kepastian (`Observed`, `Likely`, `Possible`, `Unlikely`, `Unknown`) | Enum standar OASIS CAP 1.2. |
| `<info><effective>` | `effective_time` | `TIMESTAMPTZ` | Waktu mulai berlaku | Wajib diparsing dengan timezone offset aslinya. |
| `<info><onset>` | `onset_time` | `TIMESTAMPTZ` | Waktu perkiraan kejadian cuaca dimulai | Opsional jika sama dengan `effective_time`. |
| `<info><expires>` | `expires_time` | `TIMESTAMPTZ` | Waktu kedaluwarsa peringatan | Menentukan status `is_active = (NOW() < expires_time)`. |
| `<info><headline>` | `headline` | `TEXT` | Judul ringkas peringatan dini | Ditampilkan pada banner utama. |
| `<info><description>` | `description` | `TEXT` | Uraian lengkap wilayah dan potensi cuaca | Ditampilkan utuh tanpa pemotongan makna. |
| `<info><instruction>` | `instruction` | `TEXT` | Arahan keselamatan resmi dari BMKG | Ditampilkan pada detail peringatan. |
| `<info><web>` | `official_web_url` | `TEXT` | Tautan halaman web resmi BMKG terkait peringatan | Ditampilkan sebagai link rujukan resmi. |
| `<area><areaDesc>` | `affected_areas_text` | `TEXT` | Daftar teks kabupaten/kecamatan terdampak | Diparsing untuk relasi ke tabel `regions`. |
| `<area><polygon>` | `geom` | `GEOMETRY(MultiPolygon, 4326)` | Poligon koordinat wilayah terdampak | Format CAP adalah `lat,lon` sedangkan PostGIS WKT adalah `lon lat` — **WAJIB** dibalik urutan koordinatnya saat parsing! |

---

## 3. Skema Data Observasi Historis BMKG (`weather_observations`)
Sumber: Berkas CSV/XLSX Data Online BMKG (`dataonline.bmkg.go.id`)

| Kode Kolom BMKG | Nama Kolom (DB) | Tipe Data | Satuan | Deskripsi | Penanganan Kode Khusus & Anomali |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `WMO_ID` / `Stasiun` | `station_id` | `INTEGER` (FK) | - | Referensi ke tabel `weather_stations` | Wajib cocok dengan stasiun terdaftar. |
| `Tanggal` | `observation_date` | `DATE` | Tanggal (WIB) | Tanggal pengamatan harian | Format input `DD-MM-YYYY` atau `YYYY-MM-DD` dinormalisasi ke `YYYY-MM-DD`. |
| `Tn` | `temp_min_c` | `NUMERIC(4,1)` | $^{\circ}\text{C}$ | Suhu udara minimum harian | Nilai `9999`, `8888`, `-` -> `NULL`. Rentang valid: `10.0` s.d. `35.0`. |
| `Tx` | `temp_max_c` | `NUMERIC(4,1)` | $^{\circ}\text{C}$ | Suhu udara maksimum harian | Nilai `9999`, `8888`, `-` -> `NULL`. Wajib memenuhi `temp_max_c >= temp_min_c`. |
| `Tavg` | `temp_avg_c` | `NUMERIC(4,1)` | $^{\circ}\text{C}$ | Suhu udara rata-rata harian | Nilai `9999`, `8888`, `-` -> `NULL`. |
| `RH_avg` | `humidity_avg_pct` | `NUMERIC(5,2)` | `%` | Kelembapan udara rata-rata harian | Nilai `9999`, `8888`, `-` -> `NULL`. Rentang valid: `10.0` s.d. `100.0`. |
| `RR` | `rainfall_mm` | `NUMERIC(6,2)` | $\text{mm/hari}$ | Curah hujan harian | **ATURAN KRITIS:**<br>1. Jika `RR == 8888` -> set `rainfall_mm = 0.0` dan `is_trace_rainfall = TRUE` (hujan tidak terukur / $<0.05\text{ mm}$).<br>2. Jika `RR == 9999` atau kosong/`-` -> set `rainfall_mm = NULL` dan `is_missing_rainfall = TRUE`.<br>3. Jika `RR < 0` atau `RR > 600` -> tandai anomali pada `quality_flag`. |
| `ss` | `sunshine_hours` | `NUMERIC(4,1)` | $\text{jam}$ | Durasi penyinaran matahari harian | Nilai `9999`, `8888`, `-` -> `NULL`. Rentang valid: `0.0` s.d. `12.5` jam. |
| `ff_x` | `wind_speed_max_ms` | `NUMERIC(5,2)` | $\text{m/s}$ | Kecepatan angin maksimum harian | Nilai `9999`, `8888`, `-` -> `NULL`. Rentang valid: `0.0` s.d. `60.0` m/s. |
| `ddd_x` | `wind_dir_max_deg` | `NUMERIC(5,1)` | Derajat ($\circ$) | Arah angin saat kecepatan maksimum | Nilai `9999`, `8888`, `-` -> `NULL`. Rentang valid: `0.0` s.d. `360.0`. |
| `ff_avg` | `wind_speed_avg_ms` | `NUMERIC(5,2)` | $\text{m/s}$ | Kecepatan angin rata-rata harian | Nilai `9999`, `8888`, `-` -> `NULL`. |
| `ddd_car` | `wind_dir_predominant` | `VARCHAR(10)` | Arah | Arah angin terbanyak (`C` = Calm, `N`, `NE`, dst.) | Trim spasi berlebih; jika `-` atau `9999` -> `NULL`. |

---

## 4. Klasifikasi Intensitas Curah Hujan Resmi BMKG (Target & Labeling)
Digunakan secara konsisten pada EDA, visualisasi dashboard, dan pembentukan kelas target Machine Learning:

| Kategori Intensitas Hujan | Ambang Batas Curah Hujan Harian ($\text{mm/hari}$) | Ambang Batas Curah Hujan Per Jam ($\text{mm/jam}$) | Kode Kelas ML (`rainfall_category`) | Warna Status UI |
| :--- | :--- | :--- | :--- | :--- |
| **Berawan / Tidak Hujan** | $0.0\text{ mm}$ (termasuk *Trace* `8888`) | $0.0\text{ mm}$ | `0` (`NO_RAIN`) | Abu-abu / Biru Muda (`#E2E8F0`) |
| **Hujan Ringan** | $0.5 - 20.0\text{ mm/hari}$ | $0.1 - 5.0\text{ mm/jam}$ | `1` (`LIGHT`) | Hijau / Biru Cerah (`#38BDF8`) |
| **Hujan Sedang** | $20.1 - 50.0\text{ mm/hari}$ | $5.1 - 10.0\text{ mm/jam}$ | `2` (`MODERATE`) | Kuning Waspada (`#FACC15`) |
| **Hujan Lebat** | $50.1 - 100.0\text{ mm/hari}$ | $10.1 - 20.0\text{ mm/jam}$ | `3` (`HEAVY`) | Oranye Siaga (`#FB923C`) |
| **Hujan Sangat Lebat** | $100.1 - 150.0\text{ mm/hari}$ | $> 20.0\text{ mm/jam}$ | `4` (`VERY_HEAVY`) | Merah Awas (`#EF4444`) |
| **Hujan Ekstrem** | $> 150.0\text{ mm/hari}$ | - | `5` (`EXTREME`) | Ungu/Merah Tua Ekstrem (`#991B1B`) |

*Catatan: Untuk klasifikasi biner potensi cuaca ekstrem (`is_extreme_rain`), ambang batas positif didefinisikan pada $RR \ge 50.0\text{ mm/hari}$ (Hujan Lebat s.d. Ekstrem) mengingat pada topografi Aceh curah hujan $\ge 50\text{ mm/hari}$ sudah signifikan memicu limpasan permukaan (*runoff*) dan kenaikan debit sungai.*