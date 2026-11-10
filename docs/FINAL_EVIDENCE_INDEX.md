# IPGuard — Final Evidence Index
**Document ID:** `docs/FINAL_EVIDENCE_INDEX.md`  
**Date:** November 10, 2026  
**Purpose:** Navigable master index of all implementation artifacts, test outputs, browser screenshots, cryptographic evidence, and database migrations.

---

## 1. Browser Acceptance Testing Evidence (M4)

All visual and operational acceptance testing was conducted using Playwright Chromium (1366x860) against the live IPGuard stack.

| Asset Filename | Description & Significance | Link |
| :--- | :--- | :--- |
| **acceptance_results.json** | Complete machine-readable acceptance test output, execution metrics, PSNR/MSE results, and browser health logs. | [`acceptance_results.json`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/acceptance_results.json) |
| **01_asset_vault_initial.png** | Unlocked Asset Vault showing active hardware-authenticated session pill (`Hardware-Bound Active`). | [`01_asset_vault_initial.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/01_asset_vault_initial.png) |
| **02_asset_uploaded.png** | Master PNG image (`master_artwork_256.png`) listed in the vault with `Original Asset` badge. | [`02_asset_uploaded.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/02_asset_uploaded.png) |
| **03_watermark_config_modal.png**| Steganography configuration modal showing auto-bound Ed25519 hardware parameters and custom metadata inputs. | [`03_watermark_config_modal.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/03_watermark_config_modal.png) |
| **04_embed_success.png** | Successful LSB embedding state displaying Derivative Filename, Derivative Asset UUID, and Watermark UUID. | [`04_embed_success.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/04_embed_success.png) |
| **05_vault_with_derivative.png**| Vault table displaying derivative asset with `PNG_LSB Derivative` badge and parent lineage link. | [`05_vault_with_derivative.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/05_vault_with_derivative.png) |
| **06_verify_success_modal.png** | Watermark verification modal showing `Watermark Verified & Authentic` (Ed25519 & SHA-256 match). | [`06_verify_success_modal.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/06_verify_success_modal.png) |
| **07_extract_payload_modal.png**| Watermark extraction modal rendering structured metadata cards and decoded JSON payload. | [`07_extract_payload_modal.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/07_extract_payload_modal.png) |
| **08_derivative_inspect_modal.png**| Technical metadata inspection modal displaying decrypted thumbnail preview, cipher suite, and lineage. | [`08_derivative_inspect_modal.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/08_derivative_inspect_modal.png) |
| **09_watermarked_filter_tab.png**| Tab filter interaction showing isolated view of watermarked derivatives. | [`09_watermarked_filter_tab.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/09_watermarked_filter_tab.png) |
| **master_artwork_256.watermarked.png**| Actual watermarked binary file downloaded through the browser during acceptance test (`PSNR = 68.37 dB`). | [`master_artwork_256.watermarked.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/master_artwork_256.watermarked.png) |
| **tampered_artwork.png** | Test artifact with pixel (0, 0) bit-flip proving active tamper rejection. | [`tampered_artwork.png`](file:///D:/Projects/IPGuard/docs/screenshots/m4_acceptance/tampered_artwork.png) |

---

## 2. Test Suites and Execution Scripts

| Script / Test File | Purpose & Scope | Execution Command |
| :--- | :--- | :--- |
| [`scripts/m4_browser_acceptance_test.py`](file:///D:/Projects/IPGuard/scripts/m4_browser_acceptance_test.py) | Playwright automated browser test script (14 test steps). | `python scripts/m4_browser_acceptance_test.py` |
| [`backend/tests/test_m4_e2e_user_workflow.py`](file:///D:/Projects/IPGuard/backend/tests/test_m4_e2e_user_workflow.py) | E2E API workflow test: upload $\to$ embed $\to$ download $\to$ verify $\to$ extract $\to$ tamper reject. | `pytest tests/test_m4_e2e_user_workflow.py -v` |
| [`backend/tests/test_audit_chain_postgres.py`](file:///D:/Projects/IPGuard/backend/tests/test_audit_chain_postgres.py) | PostgreSQL row-lock concurrency test across 24 concurrent threads. | `pytest tests/test_audit_chain_postgres.py -v` |
| [`backend/tests/test_png_steganography_api.py`](file:///D:/Projects/IPGuard/backend/tests/test_png_steganography_api.py) | Isolated HTTP integration tests for signed PNG LSB Asset Vault endpoints. | `pytest tests/test_png_steganography_api.py -v` |
| [`backend/tests/test_png_steganography.py`](file:///D:/Projects/IPGuard/backend/tests/test_png_steganography.py) | Low-level bit manipulation, framing, RGBA alpha preservation, and Ed25519 signing. | `pytest tests/test_png_steganography.py -v` |
| [`backend/tests/test_steganography_asset_integration.py`](file:///D:/Projects/IPGuard/backend/tests/test_steganography_asset_integration.py) | Database derivative persistence, deletion cascade blocking, and rollback safety. | `pytest tests/test_steganography_asset_integration.py -v` |

---

## 3. Milestone Documentation Index

### Milestone 4 — Steganography & Watermarking
* [`docs/M4_BROWSER_ACCEPTANCE_REPORT.md`](file:///D:/Projects/IPGuard/docs/M4_BROWSER_ACCEPTANCE_REPORT.md) — Comprehensive browser test report with visual evidence.
* [`docs/M4_FINAL_ACCEPTANCE_REPORT.md`](file:///D:/Projects/IPGuard/docs/M4_FINAL_ACCEPTANCE_REPORT.md) — Final architectural sign-off and cryptographic invariants.
* [`docs/M4_FRONTEND_IMPLEMENTATION_REPORT.md`](file:///D:/Projects/IPGuard/docs/M4_FRONTEND_IMPLEMENTATION_REPORT.md) — Frontend component architecture and state management.
* [`docs/M4_FRONTEND_TEST_REPORT.md`](file:///D:/Projects/IPGuard/docs/M4_FRONTEND_TEST_REPORT.md) — Frontend build and typecheck logs.
* [`docs/M4_BACKEND_IMPLEMENTATION_REPORT.md`](file:///D:/Projects/IPGuard/docs/M4_BACKEND_IMPLEMENTATION_REPORT.md) — Backend core service integration details.
* [`docs/M4_PRE_FRONTEND_VALIDATION_REPORT.md`](file:///D:/Projects/IPGuard/docs/M4_PRE_FRONTEND_VALIDATION_REPORT.md) — Pre-frontend validation and PostgreSQL migration checks.
* [`docs/M4_INTEGRATION_PLAN.md`](file:///D:/Projects/IPGuard/docs/M4_INTEGRATION_PLAN.md) — Initial integration roadmap and dependency mapping.
* [`docs/png-lsb-steganography.md`](file:///D:/Projects/IPGuard/docs/png-lsb-steganography.md) — `IPGW` binary framing specification and byte-level layout.
* [`docs/audit-hash-chain-deployment.md`](file:///D:/Projects/IPGuard/docs/audit-hash-chain-deployment.md) — Append-only audit chain architecture.

### Milestone 3 — Asset Vault & Secure Notes
* [`docs/M3_FINAL_SECURITY_REVIEW.md`](file:///D:/Projects/IPGuard/docs/M3_FINAL_SECURITY_REVIEW.md) — XChaCha20-Poly1305 AEAD security audit.
* [`docs/M3_ASSET_VAULT_BROWSER_E2E_REPORT.md`](file:///D:/Projects/IPGuard/docs/M3_ASSET_VAULT_BROWSER_E2E_REPORT.md) — Vault upload/download browser testing.
* [`docs/M3_ALIZA_ASSET_VAULT_INTEGRATION.md`](file:///D:/Projects/IPGuard/docs/M3_ALIZA_ASSET_VAULT_INTEGRATION.md) — Asset Vault backend integration details.

### Milestone 2 — Device Authentication & QR
* [`docs/M2_MASTER_FINAL_AUDIT_REPORT.md`](file:///D:/Projects/IPGuard/docs/M2_MASTER_FINAL_AUDIT_REPORT.md) — Complete M2 audit report.
* [`docs/M2.4C_WEB_ARCHITECTURE.md`](file:///D:/Projects/IPGuard/docs/M2.4C_WEB_ARCHITECTURE.md) — Web QR authentication architecture.
* [`docs/M2.3A_KEYSTORE_REPORT.md`](file:///D:/Projects/IPGuard/docs/M2.3A_KEYSTORE_REPORT.md) — Android Keystore ECDSA P-256 implementation.
* [`docs/M2_ANDROID_SETUP.md`](file:///D:/Projects/IPGuard/docs/M2_ANDROID_SETUP.md) — Android application build and setup guide.

### Milestone 1 — Foundation
* [`docs/M1_TEST_REPORT.md`](file:///D:/Projects/IPGuard/docs/M1_TEST_REPORT.md) — Core API baseline test report.
* [`docs/DEVELOPMENT_SETUP.md`](file:///D:/Projects/IPGuard/docs/DEVELOPMENT_SETUP.md) — Initial developer setup guide.

---

## 4. Database Migration Sequence (Alembic)

Database migrations must be applied sequentially from 0001 to 0009:

1. `0001_initial_schema.py` — Baseline tables for initial application foundation.
2. `0002_add_auth_sessions.py` — QR authentication session tracking.
3. `0003_add_device_status.py` — Device lifecycle status tracking.
4. `0004_secure_notes.py` — Secure notes encrypted storage schema.
5. `0005_asset_vault.py` — Digital asset vault metadata schema.
6. `0006_asset_encryption_metadata.py` — Encryption protocol version tracking.
7. [`0007_asset_integrity_metadata.py`](file:///D:/Projects/IPGuard/backend/app/db/migrations/versions/0007_asset_integrity_metadata.py) — Periodic integrity check tracking columns.
8. [`0008_audit_hash_chain.py`](file:///D:/Projects/IPGuard/backend/app/db/migrations/versions/0008_audit_hash_chain.py) — Append-only cryptographic audit hash chain table (`audit_events`).
9. [`0009_png_lsb_derivatives.py`](file:///D:/Projects/IPGuard/backend/app/db/migrations/versions/0009_png_lsb_derivatives.py) — Derivative asset lineage (`source_asset_id`, `derivative_type`, `watermark_id`, `stego_format_version`).

Current Alembic Head: `0009_png_lsb_derivatives`.

---

## 5. Core Source Code Mapping

| Subsystem | Key Source Files |
| :--- | :--- |
| **Steganography Engine** | [`backend/app/services/png_steganography.py`](file:///D:/Projects/IPGuard/backend/app/services/png_steganography.py), [`backend/app/services/steganography.py`](file:///D:/Projects/IPGuard/backend/app/services/steganography.py) |
| **Audit Hash Chain** | [`backend/app/services/audit_chain.py`](file:///D:/Projects/IPGuard/backend/app/services/audit_chain.py), [`backend/app/models/audit.py`](file:///D:/Projects/IPGuard/backend/app/models/audit.py) |
| **Asset Vault Service** | [`backend/app/services/assets.py`](file:///D:/Projects/IPGuard/backend/app/services/assets.py), [`backend/app/services/asset_storage.py`](file:///D:/Projects/IPGuard/backend/app/services/asset_storage.py), [`backend/app/models/asset.py`](file:///D:/Projects/IPGuard/backend/app/models/asset.py) |
| **API Endpoints** | [`backend/app/api/routes/assets.py`](file:///D:/Projects/IPGuard/backend/app/api/routes/assets.py), [`backend/app/api/routes/auth.py`](file:///D:/Projects/IPGuard/backend/app/api/routes/auth.py) |
| **Web Console UI** | [`frontend/src/pages/assets/AssetVaultPage.tsx`](file:///D:/Projects/IPGuard/frontend/src/pages/assets/AssetVaultPage.tsx), [`frontend/src/services/assets.ts`](file:///D:/Projects/IPGuard/frontend/src/services/assets.ts), [`frontend/src/types/assets.ts`](file:///D:/Projects/IPGuard/frontend/src/types/assets.ts) |
| **Android Authenticator** | `android/app/src/main/java/com/ipguard/authenticator/` (Kotlin, Keystore, CameraX) |
