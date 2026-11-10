# M4 File Mapping & Component Alignment

**Document Version:** 1.0.0  
**Target Milestone:** Milestone 4 (M4) — Steganographic Watermarking & Asset Integrity  
**Reference Source:** `D:\Projects\IPGuard\Progress Ali 2`  
**Target Repository:** `D:\Projects\IPGuard`  
**Status:** Planning & Verification Phase  

---

## 1. File Inventory & Disposition Matrix

Tabel berikut memetakan setiap file dari direktori `Progress Ali 2` ke repositori target `D:\Projects\IPGuard`, beserta tindakan yang harus diambil:

| No | Tipe | Sumber (`Progress Ali 2`) | Target (`D:\Projects\IPGuard`) | Tindakan | Deskripsi Komponen |
|:---:|:---:|:---|:---|:---:|:---|
| 1 | **Config** | `backend/backend/requirements.txt` | `backend/requirements.txt` | **UPDATE** | Menambahkan dependensi `Pillow>=11.0,<13.0` untuk decoding/encoding PNG. |
| 2 | **Config** | `backend/backend/.env.example` | `backend/.env.example` | **UPDATE** | Menambahkan variabel environment `STEGO_SIGNING_PRIVATE_KEY_B64`, `STEGO_ACTIVE_KEY_ID`, `STEGO_PUBLIC_KEYS_JSON`, dan parameter batas LSB. |
| 3 | **Core** | `backend/backend/app/core/config.py` | `backend/app/core/config.py` | **UPDATE** | Menambahkan field settings pydantic untuk konfigurasi steganografi dan ukuran maksimum gambar/payload. |
| 4 | **DB** | `backend/backend/app/db/migrations/versions/0007_asset_integrity_metadata.py` | `backend/app/db/migrations/versions/0007_asset_integrity_metadata.py` | **ADD NEW** | Migrasi Alembic untuk kolom integritas aset (`integrity_status`, dll). |
| 5 | **DB** | `backend/backend/app/db/migrations/versions/0008_audit_hash_chain.py` | `backend/app/db/migrations/versions/0008_audit_hash_chain.py` | **ADD NEW** | Migrasi Alembic untuk tabel audit hash chain (`audit_chain_heads`, `audit_events`). |
| 6 | **DB** | `backend/backend/app/db/migrations/versions/0009_png_lsb_derivatives.py` | `backend/app/db/migrations/versions/0009_png_lsb_derivatives.py` | **ADD NEW** | Migrasi Alembic untuk relasi aset turunan dan metadata watermark LSB. |
| 7 | **Model** | `backend/backend/app/models/audit.py` | `backend/app/models/audit.py` | **ADD NEW** | SQLAlchemy ORM models untuk `AuditChainHead` dan `AuditEvent`. |
| 8 | **Model** | `backend/backend/app/models/asset.py` | `backend/app/models/asset.py` | **UPDATE** | Menambahkan atribut `source_asset_id`, `derivative_type`, `watermark_id`, `stego_format_version`, dan relationship self-referencing. |
| 9 | **Schema**| `backend/backend/app/schemas/asset.py` | `backend/app/schemas/asset.py` | **UPDATE** | Pydantic schema: `StegoEmbedRequest`, `StegoEmbedResponse`, `WatermarkVerifyResponse`, `WatermarkExtractResponse`. |
| 10 | **Service**| `backend/backend/app/services/audit_chain.py` | `backend/app/services/audit_chain.py` | **ADD NEW** | Servis penulisan append-only ledger berbasis SHA-256 dan verifikasi rantai audit. |
| 11 | **Service**| `backend/backend/app/services/asset_integrity.py` | `backend/app/services/asset_integrity.py` | **ADD NEW** | Servis verifikasi integritas digest SHA-256 aset terhadap baseline database. |
| 12 | **Service**| `backend/backend/app/services/png_steganography.py` | `backend/app/services/png_steganography.py` | **ADD NEW** | **Core Algorithm LSB Engine:** Parsing IHDR, framing V1, pembatasan buffer, embedding, ekstraksi, Ed25519 signing. |
| 13 | **Service**| `backend/backend/app/services/steganography.py` | `backend/app/services/steganography.py` | **ADD NEW** | **Orkestrator Asset Vault:** Koordinasi download aset induk, embed LSB, pembuatan derivatif terenkripsi, pencatatan audit. |
| 14 | **Service**| `backend/backend/app/services/assets.py` | `backend/app/services/assets.py` | **UPDATE** | Validasi integritas saat download, atomic rollback ciphertext uncommitted, proteksi penghapusan induk ber-derivatif. |
| 15 | **API** | `backend/backend/app/api/routes/assets.py` | `backend/app/api/routes/assets.py` | **UPDATE** | Endpoint `/steganography/embed`, `/verify`, `/extract`, dan `/integrity`. |
| 16 | **Docs** | `backend/backend/docs/png-lsb-steganography.md` | `docs/png-lsb-steganography.md` | **ADD NEW** | Dokumentasi teknis format framing V1, kalkulasi kapasitas LSB, dan rotasi kunci. |
| 17 | **Docs** | `backend/backend/docs/audit-hash-chain-deployment.md` | `docs/audit-hash-chain-deployment.md` | **ADD NEW** | Dokumentasi deployment dan arsitektur audit hash chain. |
| 18 | **Test** | `backend/backend/tests/test_png_steganography.py` | `backend/tests/test_png_steganography.py` | **ADD NEW** | 16 unit test komprehensif algoritma framing LSB dan Ed25519. |
| 19 | **Test** | `backend/backend/tests/test_steganography_asset_integration.py` | `backend/tests/test_steganography_asset_integration.py` | **ADD NEW** | 5 test integrasi servis database SQLite + storage ciphertext. |
| 20 | **Test** | `backend/backend/tests/test_png_steganography_api.py` | `backend/tests/test_png_steganography_api.py` | **ADAPT** | Test API endpoint (perlu adaptasi env mock untuk platform Windows). |
| 21 | **Frontend**| `frontend/frontend/src/types/assets.ts` | `frontend/src/types/assets.ts` | **UPDATE** | Penambahan field TypeScript untuk response derivatif dan watermark. |
| 22 | **Frontend**| `frontend/frontend/src/services/assets.ts` | `frontend/src/services/assets.ts` | **UPDATE** | Penambahan fungsi API frontend `embedWatermark`, `verifyWatermark`, `extractWatermark`. |
| 23 | **Frontend**| `frontend/frontend/src/pages/assets/AssetVaultPage.tsx` | `frontend/src/pages/assets/AssetVaultPage.tsx` | **UPDATE** | Integrasi UI modal embed watermark, indikator kapasitas, tombol verifikasi & ekstraksi. |

---

## 2. Analisis Potensi Konflik Terhadap M1, M2, dan M3

### 2.1 Kompatibilitas dengan M1 (System Status & Device Protection)
- **Status:** **TIDAK ADA KONFLIK.**
- Modul steganografi dan integritas aset beroperasi di layer domain aset digital dan audit ledger; tidak menyentuh logika endpoint `system_info` maupun proteksi status unregistered M1.

### 2.2 Kompatibilitas dengan M2 (Hardware-Bound Authentication)
- **Status:** **TERINTEGRASI PENUH.**
- Seluruh endpoint steganografi (`/embed`, `/verify`, `/extract`) memanfaatkan dependency yang sama: `get_current_authenticated_device`.
- Operasi hanya dapat dieksekusi oleh perangkat yang memiliki token sesi valid dari hardware authenticator Android ECDSA P-256.
- Aset derivatif secara otomatis mewarisi `device_id` dari perangkat yang meminta embedding.

### 2.3 Kompatibilitas dengan M3 (Asset Vault & Cryptography)
- **Status:** **SANGAT HARMONIS.**
- **Format Penyimpanan:** Aset derivatif hasil watermark disimpan menggunakan enkripsi **XChaCha20-Poly1305** yang identik dengan aset asli, menggunakan kunci turunan per-device (`derive_asset_key`).
- **AAD Binding:** Menggunakan formula binding context aman: `v1|device_id|derivative_asset_id`.
- **Enkapsulasi:** Format LSB hanya dimodifikasi pada byte gambar PNG *sebelum* dienkripsi oleh AEAD dan *setelah* didekripsi saat download/ekstraksi. AEAD ciphertext tetap valid dan tidak terkontaminasi.
- **Foreign Key Safety:** Penambahan kolom `source_asset_id` pada tabel `assets` bersifat nullable (`nullable=True`), sehingga seluruh aset M3 yang sudah ada di database tetap valid tanpa perlu modifikasi data historis.
