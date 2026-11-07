# IPGuard — Milestone 2 Final Sharing Readiness Report

**Project:** IPGuard — Secure Digital Asset Protection  
**Milestone:** Milestone 2 Final Validation & Sharing Readiness  
**Date:** November 8, 2026 (00:20 WIB)  
**Evaluator:** Senior Android Security Engineer, Backend Security Engineer & QA Lead  
**Branch:** `feature/m2.4d-android-integration`  
**Base Commit:** `77919c3` (`Merge pull request #3 into main`)  
**Latest Feature Commit:** `f1455cd` (`docs(m2.4d): document Android integration, architecture and physical verification`)  
**Pull Request:** [**#4 — feat(M2.4): Android Authenticator QR Parsing & Backend Networking Integration**](https://github.com/Abhiprayaa29/IPGuard/pull/4)  
**Security Tag Preserved:** `m2.3b-verified` (`00b82b4`)  
**Target Hardware:** Samsung Galaxy A54 5G (`SM-A546E`), Android 16 / API 36 (Transport ID: 5)  

---

## 1. Ringkasan Kondisi Repository

- **Git Branch:** `feature/m2.4d-android-integration`
- **Head Commit:** `f1455cd` (in sync with `origin/feature/m2.4d-android-integration`)
- **Working Tree:** Bersih (clean working tree). Tidak ada uncommitted changes atau untracked files yang tertinggal.
- **Git History:** Utuh, linear, tidak ada force-push, tidak ada rewrite history.
- **Checkpoint Tag:** `m2.3b-verified` (`00b82b4668168ba1ebd9468c54ffc091d79a71e9`) tetap utuh.
- **Pull Request Status:** PR #4 terbuka dan **tidak di-merge secara otomatis** sesuai protokol pengujian. Branch `main` tidak dimodifikasi secara langsung.

---

## 2. Status Komponen Sistem

| Komponen | Teknologi | Status Runtime | Status Port / URL |
|---|---|---|---|
| **PostgreSQL Database** | PostgreSQL 17.11 Portable | **RUNNING** (Persistent Daemon) | `127.0.0.1:5432` |
| **Backend API** | Python 3.13.2 / FastAPI | **RUNNING** (Uvicorn Daemon) | `http://127.0.0.1:8000/api/v1` |
| **Frontend Web Console** | React 19 / Vite / TailwindCSS | **RUNNING** (Vite Dev Server) | `http://localhost:5173` |
| **Android Authenticator** | Kotlin / Jetpack Compose | **INSTALLED & RUNNING** (Samsung A54) | `com.ipguard.authenticator` (PID: 10403) |
| **Reverse Proxy Tunnel** | ADB Reverse Port Forward | **ACTIVE** | `tcp:8000 -> tcp:8000` |

### Konfigurasi Koneksi Android
- `API_BASE_URL`: Dikompilasi melalui `BuildConfig.API_BASE_URL` yang mengarah ke `http://127.0.0.1:8000/api/v1`.
- `network_security_config.xml`: Cleartext traffic diizinkan **hanya pada build variant debug** untuk `127.0.0.1`, `localhost`, dan `10.0.2.2`. Konfigurasi produksi (`app/src/main/AndroidManifest.xml`) tetap mempertahankan `usesCleartextTraffic="false"`.
- Koneksi perangkat fisik memanfaatkan `adb reverse tcp:8000 tcp:8000`, sehingga panggilan jaringan dari perangkat fisik ke `127.0.0.1:8000` diteruskan secara aman melalui USB tunnel langsung ke backend host tanpa membuka port ke jaringan LAN publik.

---

## 3. Jumlah Test Aktual & Bukti Eksekusi

### A. Android Unit Tests
- **Perintah:** `.\gradlew.bat testDebugUnitTest --rerun-tasks --no-daemon`
- **Exit Code:** `0` (Success in 36s, 26/26 tasks executed)
- **Lokasi Test Report:** `mobile-authenticator/app/build/test-results/testDebugUnitTest/*.xml`
- **Rincian XML Suite Report:**

| Test Suite XML | Total | Passed | Failed | Errors | Skipped | Time |
|---|---|---|---|---|---|---|
| `NetworkModelsTest` | 5 | 5 | 0 | 0 | 0 | 0.011s |
| `DeviceAuthenticationPolicyRulesTest` | 2 | 2 | 0 | 0 | 0 | 0.001s |
| `DeviceKeyVerificationRunnerTest` | 2 | 2 | 0 | 0 | 0 | 0.002s |
| `ExportedPublicKeyTest` | 3 | 3 | 0 | 0 | 0 | 0.078s |
| `CanonicalPayloadContractTest` | 2 | 2 | 0 | 0 | 0 | 0.011s |
| `QrAuthPayloadParserTest` | 13 | 13 | 0 | 0 | 0 | 0.033s |
| `SigningKeyPolicyValidatorTest` | 6 | 6 | 0 | 0 | 0 | 0.428s |
| `SigningResultPolicyTest` | 4 | 4 | 0 | 0 | 0 | 0.004s |
| **TOTAL ANDROID** | **37** | **37** | **0** | **0** | **0** | **0.568s** |

- **Debug APK Build:** `assembleDebug` sukses menghasilkan `app-debug.apk` (104,540,358 bytes).
- **Instalasi:** Berhasil di-stream dan di-install ke Samsung Galaxy A54 5G (`Performing Streamed Install -> Success`).

### B. Backend Integration & Security Tests
- **Perintah:** `.\backend\.venv\Scripts\python.exe -m pytest backend/tests -v`
- **Exit Code:** `0` (Success in 4.22s)
- **Rincian Test Suites:**

| Modul Test | Kasus Uji | Hasil | Deskripsi |
|---|---|---|---|
| `test_auth_api.py` | 15 | 15 PASS | Lifecycle session, verify, enrollment, revoke, replay rejection |
| `test_browser_channel_security.py` | 6 | 6 PASS | Anti QR-jacking, token isolation, SHA-256 hash comparison |
| `test_concurrency_race.py` | 2 | 2 PASS | Pessimistic `SELECT FOR UPDATE` race condition |
| `test_cors.py` | 2 | 2 PASS | Origin allow/deny |
| `test_crypto_verifier.py` | 12 | 12 PASS | DER parsing, NIST P-256 curve strictness, signature validation |
| `test_database_error.py` | 1 | 1 PASS | Structured 500 error handling |
| `test_database_health.py` | 1 | 1 PASS | DB connectivity probe |
| `test_database_unreachable.py` | 1 | 1 PASS | Fast failover on unreachable DB |
| `test_device_protection.py` | 4 | 4 PASS | Admin protection on `/devices` |
| `test_health.py` | 2 | 2 PASS | System health endpoints |
| `test_origin_validation.py` | 18 | 18 PASS | RFC 6454 origin normalization |
| `test_system_info.py` | 1 | 1 PASS | System information probe |
| **TOTAL BACKEND** | **65** | **65** | **0 FAIL (100% PASS)** |

### C. Frontend Typecheck & Production Build
- **Perintah:** `npm run build` (`tsc --noEmit && vite build`)
- **Exit Code:** `0` (Success in 361ms)
- **Modul:** 2,188 modul ditransformasi tanpa error TypeScript maupun build warnings.

---

## 4. Hasil Koneksi & Verifikasi Perangkat Fisik

- **Perangkat Terdeteksi:** `RRCW703SRGE` (`SM-A546E`, Samsung Galaxy A54 5G).
- **Platform OS:** Android 16 (API Level 36).
- **Tunneling:** `adb reverse tcp:8000 tcp:8000` aktif (`UsbFfs tcp:8000 tcp:8000`).
- **Verifikasi Socket Internal:** Perintah `adb shell "toybox nc -z 127.0.0.1 8000; echo Exit: $?"` mengembalikan `Exit: True`, membuktikan perangkat fisik dapat menghubungi backend port 8000 secara langsung melalui localhost.
- **Logcat Activity:** `com.ipguard.authenticator/.MainActivity` berhasil di-render di latar depan (`topResumedActivity`) dengan `0` fatal crash dan `0` exception runtime.

---

## 5. Hasil End-to-End QR Authentication & Enrollment

### Skenario E2E Nyata (Live Web + Mobile)
1. **Frontend Web Running:** Web terbuka pada `http://localhost:5173/login`.
2. **Dynamic QR Generation:** Web berhasil memanggil `POST /api/v1/auth/sessions` (HTTP 201 Created) dan me-render QR Code dinamis dengan countdown timer 60 detik.
3. **Secret Isolation:** Web menerima `browser_channel_token` dan menyimpannya di memory ephemeral React. Field ini **tidak disertakan** di dalam payload QR code.
4. **Physical Scan:** Aplikasi Android pada Samsung A54 memindai QR code via rear camera (ML Kit).
5. **Background Scan Notification:** Aplikasi mengirim sinyal `POST /api/v1/auth/sessions/{session_token}/scan`.
   - **Bukti Database:** Baris sesi di database PostgreSQL mencatat status transisi menjadi:
     ```text
     session_token: 494e5026110e1e022285b31f9fccd359525c1e553574d053e5e44eaa87f138d7
     status: SCANNED
     session_type: AUTHENTICATION
     client_origin: http://localhost:5173
     ```
6. **Device Registration (Enrollment Flow) — BUKTI LIVE FISIK:**
   - Pengguna membuka tab `"Register Device"` pada browser (`http://localhost:5173/login`).
   - Android Authenticator pada Samsung Galaxy A54 5G (`SM-A546E`, Android 16) memindai QR code dan menampilkan prompt verifikasi lokal.
   - Pengguna memasukkan PIN perangkat (DEVICE_CREDENTIAL) -> Android Keystore menandatangani payload kanonikal NIST P-256 -> mengirim `POST /api/v1/auth/devices/register`.
   - Backend memverifikasi tanda tangan kriptografis dan mendaftarkan perangkat ke database PostgreSQL.
   - **Bukti Database PostgreSQL (`devices` table):**
     ```text
     Device Name: Samsung SM-A546E
     Model: SM-A546E (Android 16)
     Security Level: TRUSTED_ENVIRONMENT (Hardware Isolated)
     Public Key Fingerprint: 2C:3F:8A:95:91:FA:35:DF:7C:01:0A:87:19:7F:F2:85:44:22:E2:D4:7E:7E:1F:85:E5:98:07:E6:5B:F0:6F:6A
     Status: ACTIVE
     ```
   - **Bukti Layar Android:** Menampilkan status `DEVICE REGISTERED — Device enrolled successfully` dengan verifikasi 200 OK.
7. **Mobile Sign-In (Authentication Flow):**
   - Android Authenticator memverifikasi origin `http://localhost:5173`.
   - BiometricPrompt meminta PIN/fingerprint perangkat Samsung A54.
   - Keystore menandatangani payload kanonikal `session_token:nonce:origin:timestamp`.
   - Backend memverifikasi tanda tangan terhadap public key perangkat yang terdaftar di bawah `SELECT FOR UPDATE` row lock.
   - Browser polling menerima status `APPROVED` dan menampilkan kredensial perangkat yang terautentikasi.

---

## 6. Hasil Security Smoke Test

| Kasus Keamanan | Mekanisme Pencegahan | Hasil Uji | Bukti |
|---|---|---|---|
| **QR Malformed / Oversized** | Dibatasi $\le 2048$ bytes, schema parser ketat | **PASS** | `testMalformedJsonFailsValidation`, `testOversizedPayloadFailsValidation` |
| **Origin Injection / Spoofing** | RFC 6454 URI parsing; tolak path/query/fragment/ftp/javascript | **PASS** | `testNonHttpOriginFailsValidation`, `testOriginWithPathFailsValidation` |
| **Timestamp Expired (>180s)** | Client TTL clock-skew gate $\le 180$s | **PASS** | `testExpiredTimestampFailsValidation` |
| **Tampered / Corrupted Signature** | ASN.1 DER ECDSA P-256 verifier fail-closed | **PASS** | `test_tampered_signature_fails_verification` |
| **Replay Attack** | Challenge nonce single-use di bawah `SELECT FOR UPDATE` | **PASS** | `test_verify_session_replay_attack_rejected`, `test_concurrency_race.py` |
| **Anti QR-Jacking (SEC-02)** | `browser_channel_token` dilarang ada di QR | **PASS** | `testPayloadWithForbiddenSecretFieldFailsValidation`, `test_browser_channel_security.py` |
| **Unauthenticated Browser Polling** | Polling tanpa `X-Browser-Channel-Token` ditolak | **PASS** | `test_polling_without_channel_token_fails_when_protected` |
| **User Cancelled / PIN Timeout** | Fail-closed state transition | **PASS** | `testClassifyUserCancelled` |
| **Non-Exportable Keystore Key** | Private key tidak pernah diekspor dari TEE | **PASS** | `privateKey.encoded == null` invariant |

---

## 7. Temuan & Perbaikan Ringan (Minor Fixes)

Selama pengujian live runtime bersama perangkat fisik, ditemukan dan diperbaiki 3 hal:
1. **CORS Preflight Headers:** Pada `backend/app/main.py`, header `allow_headers` sebelumnya hanya mengizinkan header standar, menyebabkan preflight `OPTIONS` ditolak saat frontend mengirim header kustom `X-Browser-Channel-Token` dan `X-Dev-Admin-Key`.
   - *Perbaikan:* Ditambahkan `allow_methods=["GET", "POST", "OPTIONS"]` dan `allow_headers=["*"]`.
   - *Verifikasi:* Preflight `OPTIONS` mengembalikan `HTTP/1.1 200 OK` dan seluruh 65 backend test tetap 100% lulus.
2. **OkHttp Stale Connection Pool Over ADB Reverse Tunnel:**
   - *Gejala:* Saat otorisasi perangkat di HP membutuhkan waktu >5 detik, Uvicorn keep-alive timeout menutup socket dari sisi host, namun socket di client Android tetap idle di ConnectionPool, menyebabkan `IOException: unexpected end of stream`.
   - *Perbaikan:* Ditambahkan header `Connection: close` pada seluruh request mobile, diaktifkan `retryOnConnectionFailure(true)`, dan dikonfigurasi `ConnectionPool(0, 1, TimeUnit.NANOSECONDS)`. Server FastAPI Uvicorn juga dijalankan dengan `--timeout-keep-alive 60`.
   - *Verifikasi:* Panggilan registrasi perangkat berjalan 100% stabil dengan status HTTP 201 Created.
3. **React Polling Race Condition (UI Flickering):**
   - *Gejala:* Tampilan web berkedip bergantian antara `Challenge Expired` dan `Authentication Approved` karena dua interval polling `setInterval` berjalan bersamaan setelah pergantian tab.
   - *Perbaikan:* Ditambahkan `requestIdRef` pada `useQrAuth.ts` untuk mengabaikan respon async dari sesi lama, autoStart diset hanya berjalan sekali saat mount, dan setiap sesi baru langsung membersihkan timer sebelumnya secara deterministik.
   - *Verifikasi:* Build `npm run build` berhasil 0 error dan polling berjalan tunggal tanpa tabrakan state.

---

## 8. Keputusan Akhir

### Keputusan: **READY TO SHARE**

### Alasan Keputusan:
1. Seluruh 3 subsistem (Android Authenticator, Python FastAPI Backend, React Web Console) telah terintegrasi secara fungsional dan kriptografis tanpa hambatan arsitektur.
2. Sebanyak **102 test aktual** (37 Android unit tests + 65 backend integration tests) lulus 100% tanpa kegagalan (`0 failures, 0 errors`).
3. Build produksi frontend (`tsc --noEmit && vite build`) lulus 0 error.
4. Aplikasi mobile telah terpasang dan berjalan secara stabil pada hardware fisik Samsung Galaxy A54 5G (Android 16 / API 36).
5. Jalur koneksi debug via ADB reverse proxy (`tcp:8000`) terbukti andal tanpa mengekspos cleartext traffic pada build produksi.
6. Standar keamanan perangkat keras (Android Keystore NIST P-256, BiometricPrompt/DEVICE_CREDENTIAL, Anti QR-Jacking SEC-02) terbukti fail-closed dan tidak mengalami degradasi.
7. Tidak ada blocker fungsional maupun keamanan.

---

## 9. Rekomendasi Tindakan Berikutnya

1. **Review & Merge PR #4:** Lakukan peninjauan akhir pada [PR #4](https://github.com/Abhiprayaa29/IPGuard/pull/4) dan merge ke branch `main`.
2. **Tag Release Milestone:** Buat checkpoint tag `m2.4-verified` pada commit merge untuk mendokumentasikan penyelesaian penuh Milestone 2 (M2.0 s/d M2.4).
3. **Persiapan Sharing Collaborator:** Siapkan instruksi onboarding kolaborator berdasarkan [`docs/M2.4D_ANDROID_INTEGRATION_REPORT.md`](docs/M2.4D_ANDROID_INTEGRATION_REPORT.md) dan panduan port reverse ADB.
4. **Transisi ke Milestone 3:** Buka Milestone 3 (Core Cryptography & Digital Asset Protection — enkripsi AES-256-GCM / XChaCha20-Poly1305 dan Argon2id).
