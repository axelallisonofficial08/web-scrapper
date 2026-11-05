# NewsPulse & FactVerify AI Dashboard 📰🔍

Dashboard scraping berita & percakapan media sosial multi-platform dengan sistem verifikasi keaslian berita otomatis (Fact-Checking & Cross-Corroboration).

Dibuat untuk memudahkan Anda mencari topik atau klaim apa pun, mengumpulkan pemberitaan dari berbagai media besar, serta langsung **memverifikasi dan mengarahkan (redirect) ke situs sumber asli** untuk membuktikan apakah isu tersebut **faktual, rumor, atau hoaks**.

---

## 🚀 Fitur Utama

1. **Multi-Platform Scraper Real-Time:**
   - **Google News (Nasional & Global):** Mengambil liputan berita dari ratusan media nasional (Kompas, Detik, Tempo, CNN Indonesia, Antara, Tirto, Liputan6, dll).
   - **Bing News:** Mesin pencari berita alternatif untuk memastikan diversitas liputan.
   - **Reddit:** Memantau diskusi komunitas dan percakapan publik dari forum sosial media.
   - **X (Twitter) & Media Sosial:** Memantau cuitan dan postingan publik terkait isu yang Anda cari.
   - **TurnBackHoax (Mafindo / Cek Fakta):** Basis data cek fakta resmi untuk mendeteksi klaim disinformasi, manipulasi konten, atau scam.

2. **Mesin Verifikasi Keaslian ("Apakah Benar atau Tidak"):**
   - **Analisis Kroscek Media Arus Utama:** Menghitung berapa banyak media berita pers resmi dan terpercaya yang memberitakan isu tersebut secara independen.
   - **Deteksi Bantahan Hoaks:** Secara otomatis memberi tanda bahaya merah (*Alert*) jika terdapat catatan bantahan dari tim pemeriksa fakta TurnBackHoax / CekFakta.
   - **Indikator Clickbait & Sensasionalisme:** Menganalisis judul sensasional ("GEGER!", "HEBOH!", "MENGEJUTKAN!", ALL-CAPS) yang sering dipakai situs clickbait.
   - **Skor Validitas (0 - 100%):** Memberikan estimasi tingkat kredibilitas setiap artikel atau postingan.

3. **Redirect & Pemeriksaan Sumber Langsung:**
   - Setiap kartu berita dan postingan sosmed dilengkapi tombol **"Buka Sumber Asli"** dengan tautan langsung (unquoted & clean URL) ke situs aslinya.
   - Tombol **"Salin Tautan"** untuk membagikan bukti link dengan cepat.

4. **Navigasi & Filter Canggih (Didapat Dari Mana):**
   - **Filter Sumber Platform Dinamis:** Tombol pill interaktif otomatis dibuat sesuai platform yang ditemukan (`Semua`, `Google News`, `Bing News`, `X (Twitter)`, `Instagram`, `TikTok`, `Reddit`, `Cek Fakta`) lengkap dengan jumlah artikel per platform.
   - **Filter Redaksi / Sumber Spesifik:** Dropdown untuk menyaring artikel hanya dari penerbit tertentu (misal: hanya *Kompas.com*, *detikInet*, *IGN*, *Suara.com*, dll).
   - **Klik Langsung di Kartu:** Klik pada badge platform atau nama redaksi pada kartu apa pun untuk langsung memfilter.
   - **Banner Filter Aktif:** Indikator filter yang sedang diterapkan dengan tombol reset 1-klik.
   - Filter instan dengan kata kunci di dalam hasil.
   - Ekspor seluruh hasil temuan ke format **CSV** dan **JSON**.

---

## 📂 Struktur Proyek

```text
d:\Axel\Testing\
│
├── app.py                     # Backend FastAPI & Aggregator Scraper
├── run.bat                    # Script 1-klik untuk menjalankan server di Windows
├── requirements.txt           # Dependensi Python
├── README.md                  # Dokumentasi lengkap
│
├── scrapers/
│   ├── google_news.py         # Scraper Google News RSS (Indonesia & Global)
│   ├── bing_news.py           # Scraper Bing News RSS
│   ├── reddit.py              # Scraper Diskusi & Percakapan Reddit
│   ├── social_mentions.py     # Scraper Cuitan X/Twitter & Medsos
│   ├── fact_checker.py        # Scraper TurnBackHoax.id & CekFakta
│   └── analyzer.py            # Mesin analisis validitas, kredibilitas & hoaks
│
├── static/
│   ├── app.js                 # Logika interaktif frontend, filter, & copy link
│   └── style.css              # Styling tambahan, scrollbar & animasi hover
│
└── templates/
    └── index.html             # UI Dashboard modern responsif (Tailwind CSS & Lucide Icons)
```

---

## 🛠️ Cara Menjalankan Dashboard

### Cara 1: Menggunakan File Batch (Paling Praktis)
Cukup klik ganda (double-click) file:
```cmd
run.bat
```

### Cara 2: Lewat Terminal / PowerShell
Jalankan perintah berikut:
```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
```

Setelah server aktif:
1. Buka browser Anda dan kunjungi: **`http://127.0.0.1:7000`**
2. Ketik kata kunci / topik yang ingin diselidiki di kolom pencarian (misal: *Pilpres*, *Bansos Kemensos*, *Jokowi*, *KPK*, dll).
3. Klik tombol **"Scrap & Verifikasi"** atau tekan `Enter`.
4. Dashboard akan menampilkan banner kesimpulan verifikasi beserta daftar artikel dan cuitan dengan tautan langsung ke situs aslinya.
