# LAPORAN AKHIR PROYEK IPGUARD
## Platform Perlindungan Aset Digital Berbasis Otentikasi Perangkat Keras dan Steganografi Kriptografis

---

**Identifikasi Dokumen:** `docs/FINAL_PROJECT_REPORT.md`  
**Proyek:** IPGuard (Intellectual Property Guard)  
**Versi Sistem:** 1.0.0  
**Cabang Git:** `feature/m4-steganography-backend`  
**Commit Baseline:** `82c07a0abb4fec08bc620275abb7a59325c9588d`  
**Status Evaluasi:** ACCEPTED & FULLY VERIFIED (READY WITH DOCUMENTED LIMITATIONS)  
**Tanggal Rilis Dokumen:** 10 November 2026  

---

## DAFTAR ISI

1. [Halaman Judul](#halaman-judul)
2. [Ringkasan Eksekutif](#ringkasan-eksekutif)
3. [Latar Belakang](#latar-belakang)
4. [Permasalahan](#permasalahan)
5. [Tujuan dan Manfaat](#tujuan-dan-manfaat)
6. [Ruang Lingkup Proyek](#ruang-lingkup-proyek)
7. [Gambaran Umum Sistem](#gambaran-umum-sistem)
8. [Arsitektur Teknologi](#arsitektur-teknologi)
9. [Implementasi Milestone 1 — Fondasi & Infrastruktur Keamanan](#implementasi-milestone-1)
10. [Implementasi Milestone 2 — Otentikasi Perangkat Keras & Verifikasi QR](#implementasi-milestone-2)
11. [Implementasi Milestone 3 — Digital Asset Vault & Enkripsi AEAD](#implementasi-milestone-3)
12. [Implementasi Milestone 4 — Steganografi Citra & Watermark Kriptografis](#implementasi-milestone-4)
13. [Arsitektur Keamanan & Model Ancaman](#arsitektur-keamanan)
14. [Alur Kerja Sistem (End-to-End User Journey)](#alur-kerja-sistem)
15. [Hasil Pengujian Sistem](#hasil-pengujian-sistem)
16. [Analisis Hasil & Validasi Kriptografi](#analisis-hasil)
17. [Keterbatasan Sistem](#keterbatasan-sistem)
18. [Kesimpulan](#kesimpulan)
19. [Rekomendasi Pengembangan Selanjutnya](#rekomendasi-pengembangan-selanjutnya)
20. [Referensi Teknis](#referensi-teknis)

---

## 1. HALAMAN JUDUL

* **Nama Proyek:** IPGuard — Secure Digital Asset Protection Platform
* **Klasifikasi Perangkat Lunak:** Cybersecurity, Cryptographic Vault & Digital Rights Attribution
* **Arsitektur Utama:** Backend REST API (FastAPI/Python), Frontend Web Console (React 19/Vite/TypeScript), Database Relasional (PostgreSQL 17.11), Mobile Authenticator (Android Kotlin Native / Jetpack Compose).
* **Lisensi / Kepemilikan:** Proprietary — IPGuard Development Team.

---

## 2. RINGKASAN EKSEKUTIF

IPGuard adalah platform perlindungan aset digital yang dirancang untuk mengatasi ancaman pembajakan, distribusi tanpa izin, pemalsuan identitas pencipta, dan kebocoran data sensitif. Platform ini mengintegrasikan tiga pilar keamanan utama:
1. **Otentikasi Tanpa Kata Sandi Terikat Perangkat Keras (*Hardware-Bound Passwordless Authentication*):** Mengeliminasi kerentanan kata sandi statis dan phising credential melalui pertukaran tantangan berbasis QR code yang ditandatangani secara kriptografis menggunakan kunci ECDSA NIST P-256 yang tersimpan di dalam Android Keystore perangkat mobile terdaftar.
2. **Kubah Aset Terenkripsi Kriptografi Terotentikasi (*Authenticated Asset Vault*):** Mengamankan berkas digital di media penyimpanan (*storage*) menggunakan cipher XChaCha20-Poly1305 AEAD dengan nonce 24-byte acak dan kunci turunan per-perangkat (HKDF-SHA256).
3. **Steganografi LSB Berbingkai Kriptografis (*Cryptographically Signed LSB Steganography*):** Menyisipkan identitas kepemilikan dan metadata ke dalam bit terkecil (*Least Significant Bit*) kanal warna RGB citra PNG secara tidak kasat mata (*invisible*), dilindungi oleh tanda tangan digital Ed25519 dan *hash digest* SHA-256, serta tercatat pada *append-only audit hash chain*.

Laporan ini menyajikan hasil audit komprehensif, evaluasi implementasi seluruh *milestone* (M1–M4), pengujian integrasi database riil PostgreSQL (209 pengujian backend lulus 100%), validasi *browser acceptance* riil menggunakan Playwright (9 berkas tangkapan layar verifikasi penuh), serta pengukuran distorsi citra (PSNR 68.37 dB). Seluruh bukti teknis telah diverifikasi dan didokumentasikan tanpa manipulasi klaim.

---

## 3. LATAR BELAKANG

Peningkatan adopsi media digital dalam industri kreatif, riset, dan korporasi menimbulkan tantangan kritis terhadap perlindungan hak cipta dan integritas data. Pendekatan konvensional yang mengandalkan tanda air kasat mata (*visible watermarks*) mudah dihilangkan menggunakan perangkat lunak penyunting citra modern atau model kecerdasan buatan (*generative AI inpainting*). Di sisi lain, *watermark* metadata standar (seperti EXIF, XMP) sangat rentan terhapus secara otomatis saat berkas diunggah ke berbagai platform media sosial atau transmisi web.

Selain itu, model otentikasi berbasis kata sandi tradisional dan OTP berbasis SMS rentan terhadap serangan rekayasa sosial, *credential stuffing*, dan *SIM swapping*. Diperlukan pendekatan holistik yang menggabungkan pembuktian kepemilikan fisik perangkat (*possession-based authentication*), isolasi kriptografis data tersimpan (*data-at-rest encryption*), dan penyisipan bukti kepemilikan langsung ke dalam struktur piksel citra digital.

---

## 4. PERMASALAHAN

Berdasarkan latar belakang tersebut, permasalahan teknis yang diselesaikan oleh IPGuard meliputi:
1. **Kerentanan Otentikasi Akses:** Bagaimana mencegah akses tidak sah ke kubah penyimpanan aset digital tanpa membebani pengguna dengan kata sandi yang rentan dibobol?
2. **Keamanan Penyimpanan Aset Digital:** Bagaimana memastikan berkas digital yang tersimpan pada server tidak dapat dibaca oleh pihak ketiga atau administrator server yang tidak memiliki otorisasi (*defense-in-depth*)?
3. **Penyisipan Bukti Kepemilikan yang Tidak Kasat Mata:** Bagaimana menanamkan metadata atribusi, hak cipta, dan identitas derivatif ke dalam citra tanpa merusak kualitas visual citra asli?
4. **Pembuktian Keaslian dan Deteksi Pemalsuan:** Bagaimana memverifikasi bahwa tanda air (*watermark*) berasal dari sumber tepercaya dan mendeteksi apakah citra telah mengalami manipulasi piksel sekecil apa pun?
5. **Keterlacakan Rekam Jejak (*Auditability*):** Bagaimana mencegah penyangkalan (*non-repudiation*) dan memastikan rekam jejak operasi keamanan aset tidak dapat dimanipulasi secara retrospektif?

---

## 5. TUJUAN DAN MANFAAT

### 5.1 Tujuan
* Mengembangkan arsitektur backend REST API yang aman, deterministik, dan dapat diaudit secara kriptografis.
* Mengimplementasikan otentikasi berbasis QR code yang diverifikasi melalui tanda tangan digital perangkat keras Android Keystore.
* Membangun media penyimpanan berkas digital terisolasi yang dienkripsi menggunakan XChaCha20-Poly1305 AEAD.
* Mengintegrasikan algoritma steganografi PNG LSB dengan bingkai biner `IPGW` versi 1 yang ditandatangani Ed25519 dan divalidasi SHA-256.
* Menyediakan antarmuka web responsif dan profesional untuk alur kerja unggah, konfigurasi, penyisipan, pengunduhan, verifikasi, dan ekstraksi metadata.

### 5.2 Manfaat
* **Bagi Kreator & Pemilik Aset:** Perlindungan karya digital orisinal, kepemilikan bukti derivatif yang tidak kasat mata, dan kemampuan membuktikan keaslian berkas di hadapan pihak ketiga.
* **Bagi Organisasi & Perusahaan:** Pengamanan dokumen rahasia dari kebocoran internal dengan isolasi kunci kriptografis berbasis perangkat keras dan rantai audit yang tidak dapat dimanipulasi (*tamper-evident*).

---

## 6. RUANG LINGKUP PROYEK

### 6.1 Cakupan Implementasi (In-Scope)
* **Milestone 1:** Struktur fondasi backend FastAPI, konfigurasi terpusat Pydantic Settings, penanganan galat aman (*safe exception handlers*), model basis data relasional PostgreSQL dengan migrasi skema Alembic (0001–0006).
* **Milestone 2:** Otentikasi berbasis QR code, protokol verifikasi tantangan kriptografis ECDSA P-256, registrasi perangkat satu kali (*one-time device enrollment*), manajemen siklus hidup sesi (*session status polling*).
* **Milestone 3:** Kubah aset terenkripsi (*Asset Vault*) berbasis XChaCha20-Poly1305 AEAD, derivasi kunci per-perangkat melalui HKDF-SHA256, Secure Notes AES-256-GCM, pengunduhan berkas terdekripsi langsung dalam memori (*byte-for-byte in-memory stream*).
* **Milestone 4:** Layanan steganografi citra PNG LSB 1-bit per kanal RGB, pembingkaian biner `IPGW` v1, tanda tangan digital Ed25519 (256-bit), verifikasi *digest* SHA-256, pembuatan aset derivatif terenkripsi, *audit hash chain* (Alembic 0007–0009), dan antarmuka terintegrasi pada Web Console.

### 6.2 Batasan Implementasi (Out-of-Scope)
* **Format Citra Non-PNG:** Steganografi LSB dibatasi secara ketat pada citra berformat PNG 8-bit truecolor (RGB dan RGBA). Citra terkompresi hilang (*lossy*) seperti JPEG atau WebP tidak didukung untuk penyisipan LSB.
* **Ketahanan Terhadap Kompresi Hilang:** Steganografi LSB bersifat *fragile* (rapuh). Manipulasi ukuran (*resizing*), konversi format ke lossy, atau penyuntingan piksel akan merusak muatan bit LSB dan sengaja dirancang memicu kegagalan verifikasi.
* **Otentikasi Wajah Biometrik Asli (*Native Face Auth*):** Integrasi `BiometricPrompt` wajah Android merupakan proposal pengembangan masa depan dan belum diimplementasikan pada aplikasi mobile.
* **Klaim Hukum Hak Cipta:** Tanda tangan Ed25519 membuktikan keaslian berkas di bawah kunci kriptografis yang tepercaya, namun bukan merupakan bukti hukum mutlak kepemilikan hak cipta menurut yurisdiksi pengadilan tanpa didukung dokumen legalitas formal.

---

## 7. GAMBARAN UMUM SISTEM

Sistem IPGuard terdiri dari tiga komponen utama yang saling berinteraksi:
1. **IPGuard Web Console (Frontend):** Antarmuka pengguna berbasis peramban (React 19, Vite, Tailwind CSS, Lucide Icons) yang menyediakan dasbor pemantauan, modul otentikasi QR, Secure Notes, dan manajemen Asset Vault & Steganografi.
2. **IPGuard Core API (Backend):** Layanan backend berbasis FastAPI (Python 3.13) yang mengelola logika bisnis, verifikasi kriptografis, orkestrasi penyimpanan cipherteks, dan pencatatan rantai audit ke database PostgreSQL.
3. **IPGuard Mobile Authenticator (Android Client):** Aplikasi mobile berbasis Kotlin native yang memanfaatkan modul keamanan Android Keystore untuk menghasilkan dan mengamankan pasangan kunci privat/publik ECDSA NIST P-256 serta memindai kode QR sesi.

---

## 8. ARSITEKTUR TEKNOLOGI

```
┌────────────────────────────────────────────────────────────────────────┐
│                        IPGUARD SYSTEM TOPOLOGY                         │
│                                                                        │
│  ┌───────────────────────┐                  ┌───────────────────────┐  │
│  │  React 19 Web Console │                  │  Android Authenticator│  │
│  │   (Vite / TypeScript) │                  │   (Kotlin / Keystore) │  │
│  └───────────┬───────────┘                  └───────────┬───────────┘  │
│              │ HTTP REST / Bearer Token                 │ ECDSA P-256  │
│              │ (TLS / Localhost 5173)                   │ Signature    │
│              ▼                                          ▼              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                   FastAPI Core Backend Engine                    │  │
│  │   - Dependency Injection Auth (Session / Hardware Device Context)│  │
│  │   - Asset Vault Orchestrator (XChaCha20-Poly1305 AEAD / HKDF)    │  │
│  │   - PNG Steganography Engine (LSB 1-bit / Ed25519 / SHA-256)      │  │
│  │   - Append-Only Audit Chain (SHA-256 Hash Linking)               │  │
│  └──────────────────┬─────────────────────────────┬─────────────────┘  │
│                     │                             │                    │
│                     ▼                             ▼                    │
│      ┌────────────────────────────┐  ┌───────────────────────────┐     │
│      │   PostgreSQL 17 Database   │  │   Encrypted Disk Storage  │     │
│      │  - devices / auth_sessions │  │  - /backend/storage/      │     │
│      │  - assets (lineage metadata│  │  - AEAD Encrypted Binaries│     │
│      │  - audit_events (hash chain│  │    (Raw bytes unreadable) │     │
│      └────────────────────────────┘  └───────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

### Rincian Tumpukan Teknologi (*Technology Stack*):
* **Bahasa Pemrograman Backend:** Python 3.13.2
* **Framework Web API:** FastAPI 0.115.x / Starlette / Uvicorn
* **Database Driver & ORM:** SQLAlchemy 2.0 / Psycopg 3 (native asynchronous/synchronous PostgreSQL driver)
* **Database Server:** PostgreSQL 17.11 (SCRAM-SHA-256 authentication)
* **Mesin Kriptografi:** PyCA/Cryptography (Ed25519, XChaCha20-Poly1305, HKDF, SHA-256, ECDSA NIST P-256)
* **Manipulasi Citra Digital:** Pillow (PIL Fork) versi 11.x
* **Frontend Web Framework:** React 19.3.1 / Vite 8.3.6 / TypeScript 7.0.2 / Tailwind CSS 4.3.4
* **Aplikasi Mobile:** Android SDK (API 28–36), Kotlin, Jetpack Compose, CameraX, ZXing Android Embedded.

---

## 9. IMPLEMENTASI MILESTONE 1 — FONDASI & INFRASTRUKTUR KEAMANAN

### 9.1 Ringkasan Tujuan
Membangun infrastruktur inti perangkat lunak yang andal, aman, dan dapat diperluas (*scalable*) dengan penegakan konfigurasi tertutup (*fail-closed configuration*) dan pelaporan kesalahan aman.

### 9.2 Komponen yang Diimplementasikan
* **Sistem Konfigurasi Terpusat (`app.core.config`):** Menggunakan `pydantic-settings` untuk memvalidasi seluruh variabel lingkungan (`.env`). Dalam mode produksi, sistem secara otomatis menolak inisialisasi jika kunci master tidak tersedia (*fail-closed*).
* **Penanganan Galat Aman (`app.core.errors`):** Menangkap semua eksepsi internal dan memetakannya ke format respons standar JSON `{"error": {"code": "...", "message": "..."}}`. Mencegah kebocoran *stack trace* atau informasi internal basis data ke publik.
* **Migrasi Database Terkelola:** Integrasi Alembic dari migrasi `0001_initial_schema.py` hingga pembentukan relasi perangkat dan sesi otentikasi.
* **Uji Baseline Backend:** Menyediakan infrastruktur pengujian berbasis Pytest dengan isolasi lingkungan dan *fixtures* pengujian otomatis.

---

## 10. IMPLEMENTASI MILESTONE 2 — OTENTIKASI PERANGKAT KERAS & VERIFIKASI QR

### 10.1 Ringkasan Tujuan
Menggantikan otentikasi kata sandi dengan verifikasi kepemilikan perangkat keras (*hardware-backed device authentication*) menggunakan tanda tangan kriptografis kurva eliptis.

### 10.2 Komponen yang Diimplementasikan
* **Aplikasi Android Authenticator:**
  * Modul `KeystoreHelper`: Menghasilkan pasangan kunci ECDSA NIST P-256 di dalam Android Keystore dengan bendera `PURPOSE_SIGN` dan proteksi perangkat keras (*StrongBox/TEE* jika tersedia).
  * Pemindai QR CameraX: Memindai payload JSON kode QR yang berisi URL origin, tipe sesi, token sesi, dan nilai acak tantangan (*challenge nonce*).
* **Alur Otentikasi Web QR:**
  1. Peramban meminta sesi baru: `POST /api/v1/auth/sessions`.
  2. Backend menghasilkan token sesi unik, *challenge nonce* 64 karakter heksadesimal, dan masa berlaku (*TTL*) 60 detik.
  3. Peramban menampilkan kode QR interaktif dan memulai *polling* status sesi (`GET /api/v1/auth/sessions/{token}`).
  4. Pengguna memindai kode QR menggunakan Android Authenticator.
  5. Aplikasi Android menandatangani *challenge nonce* menggunakan kunci privat ECDSA P-256 dan mengirimkan tanda tangan DER Base64 ke endpoint `POST /api/v1/auth/sessions/{token}/verify`.
  6. Backend memverifikasi tanda tangan terhadap kunci publik perangkat yang terdaftar di basis data. Jika valid, status sesi diperbarui menjadi `APPROVED`.
  7. Peramban mendeteksi status `APPROVED`, menyimpan token sesi di `sessionStorage`, dan membuka antarmuka terproteksi.
* **Klarifikasi Batasan Milestone 2:**
  * Pengujian otomatis unit/API memverifikasi verifikasi ECDSA P-256 secara matematis menggunakan kunci uji. Pengujian integrasi fisik melibatkan perangkat keras Android riil.
  * Fitur otentikasi biometrik wajah (*Native Face Auth*) belum diimplementasikan dan dicatat secara transparan sebagai proposal masa depan.

---

## 11. IMPLEMENTASI MILESTONE 3 — DIGITAL ASSET VAULT & ENKRIPSI AEAD

### 11.1 Ringkasan Tujuan
Menyediakan media penyimpanan aset digital yang aman dari akses fisik tidak sah dengan menerapkan enkripsi simetris modern terotentikasi (*Authenticated Encryption with Associated Data / AEAD*).

### 11.2 Komponen yang Diimplementasikan
* **Cipher XChaCha20-Poly1305:**
  * Menggunakan varian XChaCha20 dengan nonce diperpanjang (192-bit / 24-byte) yang aman dari risiko tabrakan nonce (*nonce collision*) pada pembuatan nonce acak (`os.urandom(24)`).
  * Dilengkapi tag otentikasi integritas Poly1305 128-bit (16-byte).
* **Derivasi Kunci Per-Perangkat (HKDF-SHA256):**
  * Kunci enkripsi aset tidak disimpan secara statis. Kunci diturunkan secara deterministik dari kunci master vault dan `device_id` pemilik menggunakan algoritma HKDF (*HMAC-based Extract-and-Expand Key Derivation Function*).
  * Memastikan isolasi data antar-perangkat (*cryptographic isolation*); kompromi pada satu perangkat tidak mengekspos aset perangkat lain.
* **Penyimpanan Berkas Atomik & Integritas SHA-256:**
  * Cipherteks disimpan di direktori fisik `backend/storage/` dengan nama berkas acak UUID.
  * *Digest* SHA-256 dari cipherteks dihitung saat penyimpanan dan dicatat pada tabel `assets` sebagai baseline integritas.
* **Pengunduhan Terdekripsi Aman (*In-Memory Decryption*):**
  * Endpoint `GET /api/v1/assets/{id}/download` membaca cipherteks dari disk, memverifikasi kepemilikan perangkat via Bearer token, mendekripsi data di dalam memori RAM, dan mengirimkannya langsung ke peramban tanpa pernah menuliskan berkas terdekripsi ke penyimpanan disk publik.

---

## 12. IMPLEMENTASI MILESTONE 4 — STEGANOGRAFI CITRA & WATERMARK KRIPTOGRAFIS

### 12.1 Ringkasan Tujuan
Menyediakan fungsionalitas penyisipan watermark kriptografis yang tidak kasat mata ke dalam citra PNG, menjamin integritas muatan, membuktikan asal-usul citra (*lineage attribution*), dan menyediakan mekanisme verifikasi serta ekstraksi metadata yang kebal pemalsuan.

### 12.2 Arsitektur Steganografi LSB & Pembingkaian Biner `IPGW`
Algoritma steganografi menyisipkan data biner ke dalam bit paling tidak signifikan (bit ke-0) dari kanal warna Merah (*Red*), Hijau (*Green*), dan Biru (*Blue*) pada setiap piksel, dengan mengabaikan kanal Alfa (*Alpha*) untuk mempertahankan transparansi citra PNG RGBA.

Struktur bingkai biner `IPGW` versi 1 didefinisikan sebagai berikut:

| Segmen Header | Panjang | Tipe Data | Deskripsi Fungsi |
| :--- | :--- | :--- | :--- |
| **Magic Header** | 4 byte | Karakter ASCII | Nilai tetap `IPGW` (`0x49 0x50 0x47 0x57`) sebagai penanda bingkai. |
| **Version & Flags** | 2 byte | `uint8` + `uint8` | Format versi (`0x01`) dan bendera opsi (`0x00`). |
| **Watermark UUID** | 16 byte | Biner UUID | Pengenal acak unik untuk tanda air spesifik. |
| **Source Asset UUID** | 16 byte | Biner UUID | ID aset master asli asal derivatif citra. |
| **Derivative Asset UUID**| 16 byte | Biner UUID | ID aset derivatif terdaftar di basis data. |
| **Payload Length** | 4 byte | Big-endian `uint32` | Panjang muatan metadata dalam satuan byte. |
| **Payload SHA-256** | 32 byte | Biner Hash | *Digest* SHA-256 dari muatan metadata untuk validasi integritas instan. |
| **Signing Key ID** | 16 byte | Biner Hash | Pengenal publik kunci Ed25519 pembuat tanda tangan (16 byte pertama SHA-256 kunci publik). |
| **Ed25519 Signature** | 64 byte | Tanda Tangan Biner | Tanda tangan kriptografis Ed25519 atas `STEGO_DOMAIN + PREFIX + PAYLOAD`. |
| **Payload Data** | Dinamis | UTF-8 JSON / String | Muatan metadata (hak cipta, lisensi, pernyataan kustom, deskripsi). |

Total ukuran header tetap (*fixed header*) sebelum muatan adalah **170 byte**.

### 12.3 Alur Kerja Aset Derivatif Terikat (*Asset Lineage*)
* Citra master asli dipertahankan tanpa modifikasi.
* Saat pengguna melakukan *embed*, backend mendekripsi citra master di memori, menyisipkan bingkai `IPGW`, menandatanganinya dengan kunci privat Ed25519, menghasilkan citra derivatif, mengenkripsi derivatif tersebut dengan XChaCha20-Poly1305, dan menyimpannya sebagai rekaman aset baru bertipe `PNG_LSB` dengan relasi `source_asset_id`.
* Perlindungan kaskade penghapusan (*delete protection*): Aset master asli dilarang dihapus (menghasilkan HTTP 409 Conflict) selama aset derivatifnya masih aktif di dalam sistem.

### 12.4 Rantai Audit Kriptografis (*Append-Only Audit Hash Chain*)
Setiap operasi terkait steganografi dicatat secara permanen pada tabel `audit_events`. Rantai audit menggunakan hashing kriptografis bergulir (*rolling hash*) di mana setiap rekaman baru mengikat *hash* dari rekaman sebelumnya:
$$\text{EventHash}_n = \text{SHA-256}(\text{EventHash}_{n-1} \parallel \text{ChainID} \parallel \text{Sequence} \parallel \text{EventType} \parallel \text{PayloadDigest})$$
Operasi penyisipan (`ASSET_STEGO_EMBEDDED`), verifikasi (`STEGO_WATERMARK_VERIFIED`), dan ekstraksi (`STEGO_PAYLOAD_EXTRACTED`) dicatat dalam transaksi independen yang kebal manipulasi.

---

## 13. ARSITEKTUR KEAMANAN & MODEL ANCAMAN

Sistem IPGuard menerapkan prinsip pertahanan berlapis (*defense-in-depth*):

```
┌────────────────────────────────────────────────────────────────────────┐
│                      SECURITY ARCHITECTURE LAYERS                      │
├────────────────────────────────────────────────────────────────────────┤
│ 1. TRANSPORT SECURITY       : TLS 1.3 / Enforced Origin Headers        │
│ 2. IDENTITY & ACCESS        : Hardware-Bound ECDSA P-256 Tokens        │
│ 3. STORAGE CONFIDENTIALITY  : True XChaCha20-Poly1305 AEAD per-device  │
│ 4. PIXEL PROVENANCE         : Ed25519 Signed LSB Framing (IPGW v1)     │
│ 5. METADATA INTEGRITY       : SHA-256 Payload Hash Matching            │
│ 6. NON-REPUDIATION AUDITING : Immutable Append-Only Audit Hash Chain   │
└────────────────────────────────────────────────────────────────────────┘
```

### Analisis Ketahanan Terhadap Vektor Serangan:
1. **Pencurian Kredensial (Credential Theft):** Otentikasi tidak menggunakan kata sandi statis. Kunci privat ECDSA tidak pernah keluar dari modul Android Keystore.
2. **Pemalsuan Tanda Air (Watermark Forgery):** Penyerang tidak dapat menyisipkan tanda air palsu yang mengatasnamakan otoritas sistem tanpa memiliki kunci privat Ed25519 server.
3. **Penyuntingan Piksel (Pixel Tampering):** Modifikasi pada satu bit piksel pada area bingkai akan merusak *checksum* SHA-256 atau tanda tangan digital Ed25519, yang langsung membatalkan verifikasi citra (*fail-closed*).
4. **Pembocoran Muatan Tanpa Izin (Unauthorized Payload Disclosure):** Endpoint ekstraksi menolak mengembalikan muatan metadata jika tanda tangan digital atau integritas berkas tidak lolos uji verifikasi (mengembalikan status HTTP 409 Conflict).
5. **Manipulasi Basis Data (Database Tampering):** Jika penyerang mengubah riwayat audit di basis data PostgreSQL, rantai *hash* `AuditEvent` akan terputus dan memicu kegagalan integritas saat fungsi `verify_audit_chain` dijalankan.

---

## 14. ALUR KERJA SISTEM (END-TO-END USER JOURNEY)

Alur kerja pengguna diuji dan dikonfirmasi melalui antarmuka Web Console Asset Vault:

1. **Otentikasi Sesi:** Pengguna membuka Web Console, memindai kode QR sesi melalui aplikasi Android Authenticator terdaftar, dan memperoleh token sesi terotentikasi perangkat keras.
2. **Unggah Citra Master:** Pengguna mengunggah berkas citra asli `master_artwork_256.png` (256x256 RGB). Berkas langsung dienkripsi dan disimpan di Asset Vault.
3. **Konfigurasi Watermark:** Pengguna menekan tombol *Watermark* pada baris citra asli, lalu mengisi formulir metadata hak cipta, lisensi komersial, pernyataan distribusi rahasia, dan deskripsi derivatif.
4. **Penyisipan Kriptografis (*Embedding*):** Pengguna menekan *Embed Watermark*. Backend menyisipkan bingkai `IPGW` versi 1, menandatangani muatan dengan Ed25519, membuat aset derivatif terenkripsi di basis data, dan memperbarui tampilan web.
5. **Pengunduhan Citra Ber-Watermark:** Pengguna menekan tombol unduh. Server mendekripsi citra secara *streaming* dan mengirimkan berkas asli `master_artwork_256.watermarked.png` ke folder unduhan peramban.
6. **Verifikasi Kriptografis:** Pengguna menekan tombol perisai verifikasi (*Verify Watermark*). Modal menampilkan status hijau `Watermark Verified & Authentic` lengkap dengan UUID dan status validitas tanda tangan.
7. **Ekstraksi Metadata Terverifikasi:** Pengguna menekan *Extract Verified Payload*. Modal menampilkan seluruh kartu metadata asli dan teks biner muatan yang diekstraksi dari piksel citra.
8. **Deteksi Manipulasi Citra (*Tamper Detection*):** Citra yang mengalami perubahan piksel (diuji dengan membalikkan 1 bit LSB) langsung ditolak saat diverifikasi dan muatannya diblokir dari ekstraksi.

---

## 15. HASIL PENGUJIAN SISTEM

### 15.1 Pengujian Regresi Backend (Pytest)
Pengujian dieksekusi menggunakan lingkungan Python 3.13 terhubung ke PostgreSQL 17.11 riil:
* **Total Kasus Uji:** 209 pengujian
* **Lulus (Passed):** 209 (100%)
* **Gagal (Failed):** 0
* **Dilewati (Skipped):** 0
* **Waktu Eksekusi:** 12.55 detik

Rincian cakupan modul uji utama:
* `test_m4_e2e_user_workflow.py`: Pengujian alur lengkap 6 langkah M4 (Lulus).
* `test_audit_chain_postgres.py`: Pengujian konkurensi penguncian baris PostgreSQL pada rantai audit dengan 24 thread simultan (Lulus).
* `test_png_steganography_api.py`: Integrasi endpoint `/embed`, `/verify`, `/extract`, dan isolasi multi-tenant (Lulus).
* `test_png_steganography.py`: Manipulasi biner LSB, preservasi transparansi RGBA, dan verifikasi Ed25519 (Lulus).
* `test_steganography_asset_integration.py`: Persistensi basis data derivatif dan *rollback safety* (Lulus).
* Pengujian fondasi M1, M2, dan M3: 100% lulus tanpa regresi.

### 15.2 Pengujian Statis & Build Frontend
* **Pemeriksaan Tipe TypeScript (`npm run typecheck`):** 0 error / validitas tipe 100%.
* **Build Produksi (`npm run build`):** Sukses dalam 6.13 detik (Vite/Rolldown).

### 15.3 Pengujian Penerimaan Peramban Riil (Playwright Browser Acceptance)
Pengujian otomatis menggunakan peramban Chromium riil (resolusi 1366x860) menghasilkan:
* **Status Penerimaan:** PASS (100%)
* **Kesalahan Konsol Peramban (*Page Errors*):** 0
* **Permintaan Jaringan Gagal (*Failed Requests*):** 0
* **Tangkapan Layar Verifikasi:** 9 berkas tersimpan pada direktori `docs/screenshots/m4_acceptance/`.

---

## 16. ANALISIS HASIL & VALIDASI KRIPTOGRAFI

Pengujian independen terhadap berkas biner citra hasil unduhan peramban (`master_artwork_256.watermarked.png`) menghasilkan bukti empiris berikut:

### 16.1 Analisis Biner Berkas Unduhan
* **Tanda Tangan Magic PNG:** Byte awal adalah `89 50 4E 47 0D 0A 1A 0A`. Membuktikan berkas yang diunduh adalah citra biner terdekripsi yang valid, bukan cipherteks mentah.
* **Keterbacaan Pustaka Grafis (Pillow):** Format `PNG`, Dimensi `256 x 256`, Mode Warna `RGB`. Dimensi dan geometri citra master dipertahankan secara sempurna.

### 16.2 Evaluasi Distorsi Visual (PSNR & MSE)
Evaluasi matematis perbandingan citra master asli terhadap citra ber-watermark menghasilkan:
* **Mean Squared Error (MSE):** `0.009471`
* **Peak Signal-to-Noise Ratio (PSNR):** **68.37 dB**

> *Catatan Ilmiah:* Nilai PSNR di atas 40 dB secara universal dianggap sebagai citra dengan distorsi yang tidak dapat dibedakan oleh mata manusia (*imperceptible*). Nilai 68.37 dB yang dicapai pada sampel uji 256x256 membuktikan bahwa modifikasi 1 bit pada kanal RGB mempertahankan fidelitas visual yang sangat tinggi. Nilai ini spesifik untuk sampel uji yang digunakan dan bervariasi bergantung pada ukuran citra dan panjang muatan.

### 16.3 Validasi Integritas Tanda Tangan Digital
* Parsing biner membuktikan keberadaan bingkai `IPGW` versi 1.
* Tanda tangan Ed25519 divalidasi berhasil menggunakan kunci publik server.
* *Checksum* SHA-256 muatan cocok secara matematis tanpa pergeseran bit.
* Muatan JSON yang diekstraksi dari piksel cocok 100% dengan metadata formulir yang diinput pengguna.

---

## 17. KETERBATASAN SISTEM

Untuk menjaga integritas teknis, keterbatasan sistem saat ini didokumentasikan secara transparan:
1. **Kerentanan Steganografi LSB (*Fragility*):** Steganografi LSB domain spasial bersifat rapuh terhadap operasi kompresi hilang (*JPEG lossy compression*), penyesuaian ukuran piksel (*resizing*), pemotongan (*cropping*), dan pemfilteran gambar. Operasi tersebut akan menghancurkan susunan bit LSB dan sengaja memicu kegagalan verifikasi.
2. **Cakupan Format Berkas:** Implementasi saat ini secara ketat terbatas pada citra PNG 8-bit truecolor. Citra biner terindeks (palet) atau format dokumen non-citra belum didukung oleh mesin steganografi.
3. **Kapasitas Penyisipan Terbatas Citra Kecil:** Kapasitas muatan ditentukan oleh rumus $\text{Kapasitas Byte} = \frac{\text{Lebar} \times \text{Tinggi} \times 3}{8}$. Citra dengan dimensi sangat kecil (misalnya di bawah 32x32 piksel) tidak memiliki kapasitas yang cukup untuk menampung header tetap 170 byte beserta muatan.
4. **Otentikasi Biometrik Native Android:** Verifikasi wajah asli pada Android (`BiometricPrompt`) saat ini masih merupakan proposal arsitektur dan belum diimplementasikan pada aplikasi mobile (otentikasi saat ini menggunakan tanda tangan ECDSA P-256 Android Keystore).
5. **Kunci Privat Ed25519 Lingkungan Pengembang:** Pada lingkungan pengujian lokal, benih kunci privat Ed25519 disuplai melalui berkas konfigurasi lokal. Untuk lingkungan produksi skala penuh, kunci wajib dikelola melalui modul keamanan perangkat keras (*Hardware Security Module / HSM*) atau layanan *KMS cloud*.

---

## 18. KESIMPULAN

Berdasarkan audit komprehensif terhadap arsitektur, repositori kode sumber, migrasi basis data, dan hasil pengujian riil:
1. **Milestone 1, 2, 3, dan 4 telah diimplementasikan secara solid, kohesif, dan terverifikasi secara fungsional.**
2. Sistem berhasil membuktikan konsep perlindungan aset digital berlapis: dari otentikasi fisik tanpa kata sandi, isolasi data terenkripsi XChaCha20-Poly1305, hingga penanaman bukti atribusi digital Ed25519 yang tidak kasat mata.
3. Seluruh 209 pengujian backend lulus (0 gagal, 0 dilewati), build frontend bersih dari galat tipe, dan pengujian penerimaan peramban riil membuktikan fungsionalitas end-to-end tanpa kendala teknis.
4. Proyek IPGuard dinyatakan **READY WITH DOCUMENTED LIMITATIONS** untuk diserahkan dan ditinjau pada tahap evaluasi akhir.

---

## 19. REKOMENDASI PENGEMBANGAN SELANJUTNYA

Untuk pengembangan pasca-Milestone 4, direkomendasikan langkah-langkah peningkatan berikut:
1. **Penerapan Steganografi Robust Domain Frekuensi (DCT/DWT):** Mengembangkan algoritma *watermarking* berbasis Transformasi Kosinus Diskrit (*Discrete Cosine Transform / DCT*) atau Transformasi Wavelet Diskrit (*DWT*) agar tanda air tahan terhadap kompresi JPEG dan perubahan ukuran citra.
2. **Implementasi Native BiometricPrompt Android:** Menyempurnakan aplikasi mobile Android Authenticator dengan otentikasi biometrik wajah/sidik jari native sebelum operasi penandatanganan ECDSA P-256 dieksekusi di Keystore.
3. **Integrasi Hardware Security Module (HSM / Cloud KMS):** Mengalihkan penyimpanan kunci privat penandatangan Ed25519 server ke layanan manajemen kunci terkelola (seperti Google Cloud KMS, AWS KMS, atau HashiCorp Vault) untuk memenuhi standar kepatuhan FIPS 140-3.
4. **Dukungan Format Tambahan:** Memperluas kapabilitas kubah aset untuk mengenkripsi dan menandai dokumen PDF dan citra medis (DICOM).

---

## 20. REFERENSI TEKNIS

1. **RFC 8439:** ChaCha20 and Poly1305 for IETF Protocols (IETF, 2018).
2. **RFC 8032:** Edwards-Curve Digital Signature Algorithm (EdDSA / Ed25519) (IETF, 2017).
3. **RFC 5869:** HMAC-based Extract-and-Expand Key Derivation Function (HKDF) (IETF, 2010).
4. **FIPS PUB 186-4:** Digital Signature Standard (DSS) — Elliptic Curve Digital Signature Algorithm (NIST, 2013).
5. **Portable Network Graphics (PNG) Specification (Second Edition):** ISO/IEC 15948:2004 / W3C Recommendation.
6. **Android Keystore System Documentation:** Hardware-backed Keystore and KeyGenParameterSpec Guidelines (Google Developers, 2024).
7. **FastAPI & Starlette Documentation:** Asynchronous Web API Design and Middleware Architecture.
8. **Playwright Documentation:** Cross-browser End-to-End Automation & Download Stream Verification.

---
*Laporan akhir ini disusun berdasarkan bukti eksekusi sistem riil pada cabang `feature/m4-steganography-backend`.*
