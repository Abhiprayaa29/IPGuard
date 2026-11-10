# M4 Backend Implementation Report — Steganography & Integrity

**Document Version:** 1.0.0  
**Target Milestone:** Milestone 4 (M4) — Steganographic Watermarking & Asset Integrity  
**Branch:** `feature/m4-steganography-backend`  
**Base Commit Hash:** `82c07a0abb4fec08bc620275abb7a59325c9588d`  
**Execution Date:** 2026-11-10  
**Status:** Backend Implementation Executed & Verified  

---

## 1. Executive Summary

Milestone 4 (M4) Steganography and Asset Integrity telah berhasil diintegrasikan ke dalam backend repositori utama `D:\Projects\IPGuard` pada branch khusus `feature/m4-steganography-backend`.

Integrasi ini mempertahankan seluruh algoritma asli yang dibuat oleh Ali:
1. **PNG LSB Engine:** Preservasi penuh framing V1 (`IPGW` magic, 170-byte fixed header, SHA-256 payload digest, dan Ed25519 digital signature).
2. **Asset Vault Integration:** Derivatif steganografi disimpan sebagai aset digital terenkripsi **XChaCha20-Poly1305** yang terisolasi per-device (`derive_asset_key`).
3. **Database Integrity & Lineage:** Migrasi Alembic `0007`, `0008`, dan `0009` menambahkan pelacakan integritas aset, append-only audit hash chain, dan foreign key `RESTRICT` yang mencegah penghapusan aset induk jika derivatif masih ada.
4. **Audit Trail:** Setiap aktivitas embedding, verifikasi, dan ekstraksi dicatat secara permanen pada rantai audit kriptografis `audit_events`.

---

## 2. Rincian File yang Diubah & Ditambahkan

### A. Modifikasi File yang Sudah Ada (*Modified Files*)
1. [`backend/requirements.txt`](file:///D:/Projects/IPGuard/backend/requirements.txt): Menambahkan `Pillow>=11.0,<13.0`.
2. [`backend/app/core/config.py`](file:///D:/Projects/IPGuard/backend/app/core/config.py): Menambahkan konfigurasi Ed25519 (`stego_signing_private_key_b64`, `stego_active_key_id`, `stego_public_keys_json`, dan limit gambar/payload).
3. [`backend/app/models/asset.py`](file:///D:/Projects/IPGuard/backend/app/models/asset.py): Menambahkan kolom `source_asset_id`, `derivative_type`, `watermark_id`, `stego_format_version`, dan relasi self-referencing.
4. [`backend/app/models/__init__.py`](file:///D:/Projects/IPGuard/backend/app/models/__init__.py): Mengekspor model `AuditChainHead` dan `AuditEvent`.
5. [`backend/app/schemas/asset.py`](file:///D:/Projects/IPGuard/backend/app/schemas/asset.py): Menambahkan schema `StegoEmbedRequest`, `StegoEmbedResponse`, `WatermarkVerifyResponse`, `WatermarkExtractResponse`.
6. [`backend/app/services/assets.py`](file:///D:/Projects/IPGuard/backend/app/services/assets.py): Menambahkan validasi integritas saat download, pembatalan file yatim saat transaksi gagal, dan proteksi foreign key saat penghapusan aset.
7. [`backend/app/services/asset_storage.py`](file:///D:/Projects/IPGuard/backend/app/services/asset_storage.py): Sinkronisasi operasi file storage.
8. [`backend/app/api/routes/assets.py`](file:///D:/Projects/IPGuard/backend/app/api/routes/assets.py): Mengimplementasikan endpoint `/steganography/embed`, `/verify`, `/extract`, dan `/integrity`.

### B. Penambahan File Baru (*New Files*)
1. **Migrations:**
   - [`backend/app/db/migrations/versions/0007_asset_integrity_metadata.py`](file:///D:/Projects/IPGuard/backend/app/db/migrations/versions/0007_asset_integrity_metadata.py)
   - [`backend/app/db/migrations/versions/0008_audit_hash_chain.py`](file:///D:/Projects/IPGuard/backend/app/db/migrations/versions/0008_audit_hash_chain.py)
   - [`backend/app/db/migrations/versions/0009_png_lsb_derivatives.py`](file:///D:/Projects/IPGuard/backend/app/db/migrations/versions/0009_png_lsb_derivatives.py)
2. **Models & Services:**
   - [`backend/app/models/audit.py`](file:///D:/Projects/IPGuard/backend/app/models/audit.py)
   - [`backend/app/services/png_steganography.py`](file:///D:/Projects/IPGuard/backend/app/services/png_steganography.py)
   - [`backend/app/services/steganography.py`](file:///D:/Projects/IPGuard/backend/app/services/steganography.py)
   - [`backend/app/services/audit_chain.py`](file:///D:/Projects/IPGuard/backend/app/services/audit_chain.py)
   - [`backend/app/services/asset_integrity.py`](file:///D:/Projects/IPGuard/backend/app/services/asset_integrity.py)
   - [`backend/app/workers/integrity.py`](file:///D:/Projects/IPGuard/backend/app/workers/integrity.py)
3. **Documentation:**
   - [`docs/png-lsb-steganography.md`](file:///D:/Projects/IPGuard/docs/png-lsb-steganography.md)
   - [`docs/audit-hash-chain-deployment.md`](file:///D:/Projects/IPGuard/docs/audit-hash-chain-deployment.md)
4. **Test Suites:**
   - [`backend/tests/test_png_steganography.py`](file:///D:/Projects/IPGuard/backend/tests/test_png_steganography.py)
   - [`backend/tests/test_steganography_asset_integration.py`](file:///D:/Projects/IPGuard/backend/tests/test_steganography_asset_integration.py)
   - [`backend/tests/test_png_steganography_api.py`](file:///D:/Projects/IPGuard/backend/tests/test_png_steganography_api.py)
   - [`backend/tests/test_audit_chain.py`](file:///D:/Projects/IPGuard/backend/tests/test_audit_chain.py)
   - [`backend/tests/test_asset_integrity.py`](file:///D:/Projects/IPGuard/backend/tests/test_asset_integrity.py)
   - [`backend/tests/test_asset_integrity_audit.py`](file:///D:/Projects/IPGuard/backend/tests/test_asset_integrity_audit.py)
   - [`backend/tests/test_asset_integrity_integration.py`](file:///D:/Projects/IPGuard/backend/tests/test_asset_integrity_integration.py)
   - [`backend/tests/test_asset_integrity_worker.py`](file:///D:/Projects/IPGuard/backend/tests/test_asset_integrity_worker.py)

---

## 3. Contoh Permintaan & Respons API (API Contract)

### 3.1 Embed Steganography Watermark
- **Endpoint:** `POST /api/v1/assets/{asset_id}/steganography/embed`
- **Headers:** `Authorization: Bearer <device_session_token>`
- **Request Body:**
  ```json
  {
    "payload_b64": "SGFrIENpcHRhIMKpIDIwMjYgSVBHdWFyZCBJbmRvbmVzaWE="
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "derivative": {
      "id": "e6f9822a-89a1-43ef-b311-2b0181b37812",
      "original_filename": "sample_photo.watermarked.png",
      "content_type": "image/png",
      "size_bytes": 1420580,
      "sha256_hash": "a1b2c3d4e5f6...",
      "encryption_version": "v1",
      "source_asset_id": "0d382186-3b4a-43ef-ba83-8a0923c2b018",
      "derivative_type": "PNG_LSB",
      "watermark_id": "99f81a2b-3c4d-5e6f-7a8b-9c0d1e2f3a4b",
      "stego_format_version": 1,
      "created_at": "2026-11-10T06:16:37.000Z",
      "updated_at": "2026-11-10T06:16:37.000Z",
      "encryption_status": "ENCRYPTED_XCHACHA20_POLY1305"
    },
    "watermark_id": "99f81a2b-3c4d-5e6f-7a8b-9c0d1e2f3a4b",
    "format_version": 1
  }
  ```

### 3.2 Verify Watermark
- **Endpoint:** `POST /api/v1/assets/{asset_id}/steganography/verify`
- **Response (`200 OK`):**
  ```json
  {
    "verified": true,
    "status": "VERIFIED",
    "watermark_id": "99f81a2b-3c4d-5e6f-7a8b-9c0d1e2f3a4b",
    "source_asset_id": "0d382186-3b4a-43ef-ba83-8a0923c2b018",
    "derivative_asset_id": "e6f9822a-89a1-43ef-b311-2b0181b37812",
    "format_version": 1
  }
  ```

### 3.3 Extract Watermark Payload
- **Endpoint:** `POST /api/v1/assets/{asset_id}/steganography/extract`
- **Response (`200 OK`):**
  ```json
  {
    "verified": true,
    "status": "VERIFIED",
    "watermark_id": "99f81a2b-3c4d-5e6f-7a8b-9c0d1e2f3a4b",
    "source_asset_id": "0d382186-3b4a-43ef-ba83-8a0923c2b018",
    "derivative_asset_id": "e6f9822a-89a1-43ef-b311-2b0181b37812",
    "format_version": 1,
    "payload_b64": "SGFrIENpcHRhIMKpIDIwMjYgSVBHdWFyZCBJbmRvbmVzaWE="
  }
  ```
- *Catatan Keamanan:* Jika signature Ed25519 tidak valid, endpoint mengembalikan `HTTP 409 Conflict` dan payload tidak pernah dirilis.

---

## 4. Evaluasi Keamanan & Batasan Arsitektur

1. **Ed25519 Private Key Secrecy:** Private seed hanya dimuat dari memory/environment (`STEGO_SIGNING_PRIVATE_KEY_B64`), tidak pernah dicatat di log audit atau respon API.
2. **Fragile Watermark Characteristic:** LSB steganography secara desain bersifat *tamper-evident*, bukan *robust*. Resizing, kompresi lossy JPEG, atau pengeditan piksel di luar IPGuard akan merusak tanda tangan digital Ed25519 dan menyebabkan verifikasi ditolak.
3. **Kerahasiaan Isi Payload:** Payload di dalam LSB frame dilindungi tanda tangan digital dan checksum integritas. Meskipun demikian, payload tersebut berada dalam bentuk plaintext di dalam byte gambar (namun file gambar itu sendiri terenkripsi XChaCha20-Poly1305 saat disimpan di vault).
