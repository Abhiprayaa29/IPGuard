# IPGuard — Final Acceptance Matrix
**Document ID:** `docs/FINAL_ACCEPTANCE_MATRIX.md`  
**Date:** November 10, 2026  
**Status Categories:**
- `IMPLEMENTED AND VERIFIED`: Feature is fully coded, integrated, and verified with automated test suites or browser acceptance.
- `IMPLEMENTED, PARTIALLY VERIFIED`: Feature is coded and partially tested, with physical/hardware acceptance pending or limited.
- `PLANNED`: Feature is designed or architecturally specified as a future enhancement but not yet coded.
- `NOT IMPLEMENTED`: Feature is not in current scope.
- `BLOCKED`: Feature is prevented from completing due to external dependency.

---

## Acceptance Matrix

| # | Feature / Capability | Milestone | Status | Verification Method | Test Evidence / Artifacts | Remaining Limitations |
| :-: | :--- | :-: | :---: | :--- | :--- | :--- |
| **1** | **Fail-Closed Configuration & Settings** | M1 | `IMPLEMENTED AND VERIFIED` | Unit & Integration Tests | `test_config.py`, `app.core.config` | None. Rejects missing keys in production. |
| **2** | **Safe Error Envelope (No Leakage)** | M1 | `IMPLEMENTED AND VERIFIED` | Unit & API Tests | `test_errors.py`, `app.core.errors` | None. Standard JSON error envelope enforced. |
| **3** | **PostgreSQL Database Schema & Migrations** | M1–M4 | `IMPLEMENTED AND VERIFIED` | Alembic Migration Engine | Migrations 0001–0009 applied cleanly | PostgreSQL 17 required. |
| **4** | **Health Check & Readiness Probes** | M1 | `IMPLEMENTED AND VERIFIED` | API HTTP Tests | `test_main.py` | None. |
| **5** | **Android Keystore ECDSA P-256 Keypair** | M2 | `IMPLEMENTED AND VERIFIED` | Unit & Device Tests | `M2.3A_KEYSTORE_REPORT.md`, Kotlin code | Requires Android API 28+ (Pie or later). |
| **6** | **One-Time Device Registration** | M2 | `IMPLEMENTED AND VERIFIED` | API Integration Tests | `test_auth_device_registration.py` | Device key uniqueness enforced in PostgreSQL. |
| **7** | **QR-Based Authentication Challenge** | M2 | `IMPLEMENTED AND VERIFIED` | Automated API & Web Tests | `test_auth_sessions.py`, `QrLoginPage.tsx` | Challenge nonce has 60s time-to-live (TTL). |
| **8** | **ECDSA P-256 Signature Verification** | M2 | `IMPLEMENTED AND VERIFIED` | Cryptographic Unit Tests | `test_auth_verification.py` | Verified against public key stored in DB. |
| **9** | **Physical Android Authenticator E2E** | M2 | `IMPLEMENTED, PARTIALLY VERIFIED` | Manual Device Testing | Verified with physical Android device; automated regression uses test fixtures | Hardware BiometricPrompt is not yet bound. |
| **10**| **Native Face Authentication** | M2 | `PLANNED` | Architectural Design | Documented in `docs/` as future proposal | Not implemented in current mobile app. |
| **11**| **XChaCha20-Poly1305 AEAD Asset Encryption**| M3 | `IMPLEMENTED AND VERIFIED` | Cryptographic Tests | `test_asset_storage.py`, 24-byte nonce check | Relies on backend master key seed. |
| **12**| **HKDF-SHA256 Per-Device Key Derivation**| M3 | `IMPLEMENTED AND VERIFIED` | Cryptographic Tests | `test_asset_crypto.py` | Keys deterministically derived per `device_id`. |
| **13**| **Atomic Ciphertext Storage & Cleanup** | M3 | `IMPLEMENTED AND VERIFIED` | Integration Tests | `test_asset_storage.py`, `backend/storage/` | Disk writes atomic; unlinks on asset delete. |
| **14**| **Decrypted In-Memory Streaming Download**| M3 | `IMPLEMENTED AND VERIFIED` | API & Browser Tests | `test_m4_e2e_user_workflow.py`, Playwright | Memory-only buffer; cipherteks unreadable on disk. |
| **15**| **Asset Delete Cascade Protection** | M3 | `IMPLEMENTED AND VERIFIED` | API Tests | `test_png_steganography_api.py` | HTTP 409 if active derivatives depend on asset. |
| **16**| **Secure Notes AES-256-GCM Vault** | M3 | `IMPLEMENTED AND VERIFIED` | Service & UI Tests | `test_notes.py`, `NotesPage.tsx` | Separate from binary asset vault. |
| **17**| **PNG LSB 1-bit RGB Watermark Embedding**| M4 | `IMPLEMENTED AND VERIFIED` | Unit & E2E Tests | `test_png_steganography.py`, Pillow | Restricted to 8-bit truecolor RGB/RGBA PNGs. |
| **18**| **Binary Framing `IPGW` Version 1** | M4 | `IMPLEMENTED AND VERIFIED` | Low-level Binary Tests | `test_png_steganography.py` | 170-byte fixed header structure. |
| **19**| **Ed25519 Hardware-Attributed Signing** | M4 | `IMPLEMENTED AND VERIFIED` | Crypto & API Tests | `test_m4_e2e_user_workflow.py` | 256-bit Edwards-curve digital signature. |
| **20**| **SHA-256 Watermark Payload Integrity** | M4 | `IMPLEMENTED AND VERIFIED` | Cryptographic Tests | `test_png_steganography.py` | Instant bit-rot and tamper detection. |
| **21**| **Derivative Asset Lineage Association** | M4 | `IMPLEMENTED AND VERIFIED` | DB & Integration Tests | `0009_png_lsb_derivatives.py`, PostgreSQL | Links `derivative_id` to `source_asset_id`. |
| **22**| **Append-Only Audit Hash Chain** | M4 | `IMPLEMENTED AND VERIFIED` | Concurrency Tests | `test_audit_chain_postgres.py` (24 workers) | Rolling SHA-256 hash linking on `AuditEvent`. |
| **23**| **Web Console Asset Vault M4 Workflow** | M4 | `IMPLEMENTED AND VERIFIED` | Playwright Browser Tests | 9 screenshots, `acceptance_results.json` | Requires browser with JS enabled. |
| **24**| **Tamper Detection & Verification Modal**| M4 | `IMPLEMENTED AND VERIFIED` | Browser & API Tests | `06_verify_success_modal.png` | Mutated piksel triggers immediate reject. |
| **25**| **Verified Watermark Payload Extraction**| M4 | `IMPLEMENTED AND VERIFIED` | Browser & API Tests | `07_extract_payload_modal.png` | Blocked with HTTP 409 if signature is invalid. |
| **26**| **Lossy Compression Watermark Robustness**| Post-M4 | `NOT IMPLEMENTED` | Documented Limitation | LSB is fragile by design | Resizing or JPEG conversion destroys watermark. |

---

## Summary Statistics
* **Total Tracked Capabilities:** 26
* **IMPLEMENTED AND VERIFIED:** 23 (88.5%)
* **IMPLEMENTED, PARTIALLY VERIFIED:** 1 (3.8%) — Physical Android hardware acceptance (automated tests complete)
* **PLANNED:** 1 (3.8%) — Native Face Auth (`BiometricPrompt`)
* **NOT IMPLEMENTED:** 1 (3.8%) — Lossy Compression Robust Steganography (DCT/DWT)
* **BLOCKED:** 0 (0%)
