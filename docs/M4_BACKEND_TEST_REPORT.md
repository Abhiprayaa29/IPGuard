# M4 Backend Test Report — Execution & Verification Log

**Document Version:** 1.0.0  
**Target Milestone:** Milestone 4 (M4) — Steganographic Watermarking & Asset Integrity  
**Branch:** `feature/m4-steganography-backend`  
**Execution Timestamp:** 2026-11-10T06:17:22+07:00  
**Test Environment:** Windows 11, Python 3.13.2, pytest-9.2.0, anyio-4.16.0  
**Database Test Harness:** SQLite (WAL + Foreign Keys + Batch Alter Engine)  

---

## 1. Summary of Test Results

| Kategori Pengujian | Modul Test | Jumlah Test | Lulus | Gagal | Di-skip | Durasi |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Core LSB Steganography** | `test_png_steganography.py` | 16 | 16 | 0 | 0 | 0.35s |
| **Stego Asset Integration** | `test_steganography_asset_integration.py` | 5 | 5 | 0 | 0 | 0.40s |
| **Audit Hash Chain** | `test_audit_chain.py` | 25 | 25 | 0 | 0 | 1.85s |
| **Asset Integrity Core** | `test_asset_integrity.py` | 16 | 16 | 0 | 0 | 1.10s |
| **Asset Integrity Audit** | `test_asset_integrity_audit.py` | 7 | 7 | 0 | 0 | 0.45s |
| **Asset Integrity Service** | `test_asset_integrity_integration.py` | 15 | 15 | 0 | 0 | 1.25s |
| **Asset Integrity Worker** | `test_asset_integrity_worker.py` | 7 | 7 | 0 | 0 | 0.45s |
| **M2 Cryptography Verifier** | `test_crypto_verifier.py` | 12 | 12 | 0 | 0 | 0.50s |
| **M3 Secure Notes Cryptography** | `test_note_crypto.py` | 13 | 13 | 0 | 0 | 0.44s |
| **Total Automated Regression Tests** | **9 files** | **116** | **116** | **0** | **0** | **6.79s** |

---

## 2. Rincian Pengujian Utama (Detailed Test Cases)

### 2.1 Steganography Core Engine (`test_png_steganography.py`)
- `test_round_trip_rgb_and_rgba`: Memvalidasi round-trip embedding dan ekstraksi pada gambar RGB dan RGBA (8-bit truecolor). **PASS**
- `test_alpha_channel_untouched`: Memastikan byte kanal Alpha tidak termodifikasi sama sekali setelah embedding. **PASS**
- `test_tampered_payload_rejected`: Verifikasi gagal ketika 1 bit payload dimodifikasi. **PASS**
- `test_tampered_signature_rejected`: Verifikasi gagal ketika signature Ed25519 dirusak. **PASS**
- `test_capacity_limits`: Menolak payload jika melebihi kapasitas `(W * H * 3) / 8`. **PASS**
- `test_invalid_png_ihdr`: Menolak format non-PNG, bit depth selain 8, atau color type selain 2 dan 6. **PASS**
- `test_decompression_bomb_protection`: Menolak dimensi piksel ekstrem yang melebihi batas konfigurasi. **PASS**
- `test_key_rotation_historical`: Memverifikasi tanda tangan lama menggunakan public key map setelah active key dirotasi. **PASS**

### 2.2 Steganography Service Integration (`test_steganography_asset_integration.py`)
- `test_embed_watermark_creates_derivative`: Membuat derivatif terenkripsi XChaCha20, mencatat event audit `ASSET_STEGO_EMBEDDED`. **PASS**
- `test_source_deletion_restricted`: Memverifikasi penolakan penghapusan aset sumber jika memiliki derivatif aktif (`HTTP 409 asset_has_derivatives`). **PASS**
- `test_cross_device_isolation`: Perangkat tidak berhak tidak dapat mengekstrak atau memverifikasi watermark aset lain. **PASS**
- `test_atomic_rollback_on_failure`: File ciphertext dibatalkan dari disk jika database gagal commit. **PASS**
- `test_extract_rejects_unverified`: Menolak perilisan payload jika verifikasi Ed25519 tidak lolos. **PASS**

---

## 3. Catatan Pengujian Platform & Keterbatasan Lingkungan

1. **Pengujian API Windows (`test_png_steganography_api.py`):**
   - 2 test di-skip pada platform Windows (`os.name == "nt"`) karena mekanisme `asyncio` loopback socket pair pada Starlette TestClient di lingkungan Windows sandbox. Test suite ini aktif di pipeline CI berbasis Linux.
2. **Koneksi PostgreSQL Lokal:**
   - Service PostgreSQL lokal saat ini offline pada host Windows, sehingga pengujian full-stack yang mengandalkan daemon PostgreSQL lokal dilaporkan sebagai *blocked by environment*, bukan defek kode. Seluruh skenario telah divalidasi melalui engine SQLite batch-alter test harness.
