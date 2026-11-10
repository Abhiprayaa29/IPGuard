# IPGuard — Master Technical Documentation Hub

Welcome to the central technical documentation repository for **IPGuard (Milestones M0–M4)**.

This documentation tree provides a comprehensive, navigable, and reproducible record of the IPGuard platform architecture, cryptographic design, milestone test reports, security audits, and operational runbooks. All resources are directly accessible on GitHub.

---

## 1. Project Overview

* **Primary Overview:** [`../README.md`](../README.md) — Main repository showcase, quickstart guide, and technology stack.
* **Codebase Structure:** [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) — Comprehensive directory tree and module organization.
* **Collaboration Guide:** [`COLLABORATION_GUIDE.md`](COLLABORATION_GUIDE.md) — Multi-agent engineering protocols, commit rules, and issue tracking.
* **Team Workflow:** [`TEAM_WORKFLOW.md`](TEAM_WORKFLOW.md) — Git workflow and integration standards.

---

## 2. Final Project Audit & Master Reports

* **Master Final Report:** [`FINAL_PROJECT_REPORT.md`](FINAL_PROJECT_REPORT.md) — Authoritative final report across 20 formal sections (Indonesian).
* **Final Acceptance Matrix:** [`FINAL_ACCEPTANCE_MATRIX.md`](FINAL_ACCEPTANCE_MATRIX.md) — 26-feature verification matrix covering Milestones M1 through M4.
* **Final Evidence Index:** [`FINAL_EVIDENCE_INDEX.md`](FINAL_EVIDENCE_INDEX.md) — Master navigation catalog of all test logs, scripts, and artifact outputs.
* **Final Handover Guide:** [`FINAL_HANDOVER.md`](FINAL_HANDOVER.md) — Operational runbook, runtime commands, and disaster recovery.
* **Freeze State Changelog:** [`FINAL_FREEZE_CHANGELOG.md`](FINAL_FREEZE_CHANGELOG.md) — File-by-file delta and repository freeze inventory.
* **Final Freeze Audit Report:** [`FINAL_FREEZE_REPORT.md`](FINAL_FREEZE_REPORT.md) — Pre-freeze verification and clean tree validation.
* **GitHub Release Report:** [`FINAL_GITHUB_RELEASE_REPORT.md`](FINAL_GITHUB_RELEASE_REPORT.md) — Summary of release branch, tag, and PR #9 configuration.

---

## 3. Milestone Technical Documentation

### Milestone 0 — Smartphone Authenticator Feasibility (VERIFIED)
* [`M0_TECHNICAL_FEASIBILITY.md`](M0_TECHNICAL_FEASIBILITY.md) — Baseline feasibility assessment of Android Keystore, CameraX, and local HTTPS.
* [`M0_COMPATIBILITY_REPORT.md`](M0_COMPATIBILITY_REPORT.md) — Hardware compatibility matrix across Android API levels.
* [`M0_ENVIRONMENT_REPORT.md`](M0_ENVIRONMENT_REPORT.md) — Host toolchain, Android SDK, and emulator setup.

### Milestone 1 — Foundation & Security Infrastructure (VERIFIED)
* [`M1_TEST_REPORT.md`](M1_TEST_REPORT.md) — Initial FastAPI baseline API tests, configuration guards, and error envelopes.
* [`DEVELOPMENT_SETUP.md`](DEVELOPMENT_SETUP.md) — Developer workstation configuration for backend and frontend.

### Milestone 2 — Hardware Device Authentication (VERIFIED)
* [`M2_MASTER_FINAL_AUDIT_REPORT.md`](M2_MASTER_FINAL_AUDIT_REPORT.md) — Master audit report for hardware authentication subsystem.
* [`M2_ARCHITECTURE.md`](M2_ARCHITECTURE.md) — Detailed mobile authenticator architecture and cryptographic handshake.
* [`M2.3A_KEYSTORE_REPORT.md`](M2.3A_KEYSTORE_REPORT.md) — Android Keystore non-exportable key generation and persistence.
* [`M2.3A_SECURITY_REVIEW.md`](M2.3A_SECURITY_REVIEW.md) — Independent security review of Keystore implementation.
* [`M2.3B_AUTHENTICATION_REPORT.md`](M2.3B_AUTHENTICATION_REPORT.md) — Challenge-response verification and signature validation.
* [`M2.4C_WEB_ARCHITECTURE.md`](M2.4C_WEB_ARCHITECTURE.md) — Web Console QR polling and session state machine.
* [`M2.4C_WEB_TEST_REPORT.md`](M2.4C_WEB_TEST_REPORT.md) — Frontend QR handshake integration test logs.
* [`M2.4D_ANDROID_INTEGRATION_REPORT.md`](M2.4D_ANDROID_INTEGRATION_REPORT.md) — Android CameraX scanner and approval UI.
* [`M2.4_API_CONTRACT.md`](M2.4_API_CONTRACT.md) — Out-of-band device authentication REST API specifications.
* [`M2_ANDROID_SETUP.md`](M2_ANDROID_SETUP.md) — Android Studio build, deployment, and ADB proxy instructions.
* [`ONE_TIME_DEVICE_ENROLLMENT.md`](ONE_TIME_DEVICE_ENROLLMENT.md) — Hardware device registration invariants and row-locking logic.

### Milestone 3 — Secure Digital Asset Vault (VERIFIED)
* [`M3_FINAL_SECURITY_REVIEW.md`](M3_FINAL_SECURITY_REVIEW.md) — Security audit of XChaCha20-Poly1305 AEAD cipher and subkey derivation.
* [`M3_ASSET_VAULT_BROWSER_E2E_REPORT.md`](M3_ASSET_VAULT_BROWSER_E2E_REPORT.md) — Web browser upload, download, and decryption testing.
* [`M3_ALIZA_ASSET_VAULT_INTEGRATION.md`](M3_ALIZA_ASSET_VAULT_INTEGRATION.md) — Core backend asset vault service integration report.
* [`M3_ANISA_INTEGRATION_REPORT.md`](M3_ANISA_INTEGRATION_REPORT.md) — Secure notes sub-encryption and multi-tenant authorization report.
* [`POST_MERGE_M2_M3_VERIFICATION.md`](POST_MERGE_M2_M3_VERIFICATION.md) — Post-merge verification across M2 and M3 boundaries.

### Milestone 4 — Steganography & Cryptographic Watermarking (VERIFIED)
* [`M4_FINAL_ACCEPTANCE_REPORT.md`](M4_FINAL_ACCEPTANCE_REPORT.md) — Architectural sign-off, mathematical invariants, and test summary.
* [`M4_BROWSER_ACCEPTANCE_REPORT.md`](M4_BROWSER_ACCEPTANCE_REPORT.md) — 14-step automated Playwright browser test execution report.
* [`M4_BACKEND_IMPLEMENTATION_REPORT.md`](M4_BACKEND_IMPLEMENTATION_REPORT.md) — Backend core service and REST route integration.
* [`M4_BACKEND_TEST_REPORT.md`](M4_BACKEND_TEST_REPORT.md) — 209-test backend suite verification against PostgreSQL.
* [`M4_FRONTEND_IMPLEMENTATION_REPORT.md`](M4_FRONTEND_IMPLEMENTATION_REPORT.md) — React 19 UI components and asset state management.
* [`M4_FRONTEND_TEST_REPORT.md`](M4_FRONTEND_TEST_REPORT.md) — Frontend TypeScript typecheck and production build validation.
* [`M4_PRE_FRONTEND_VALIDATION_REPORT.md`](M4_PRE_FRONTEND_VALIDATION_REPORT.md) — Intermediate backend verification before UI implementation.
* [`M4_INTEGRATION_PLAN.md`](M4_INTEGRATION_PLAN.md) — Original integration roadmap and dependency mapping.
* [`M4_FILE_MAPPING.md`](M4_FILE_MAPPING.md) — Cross-repository file transfer and adaptation mapping.
* [`M4_TEST_GAP_ANALYSIS.md`](M4_TEST_GAP_ANALYSIS.md) — Unit vs. integration test coverage analysis.
* [`png-lsb-steganography.md`](png-lsb-steganography.md) — Byte-level `IPGW` v1 binary framing format specification.
* [`audit-hash-chain-deployment.md`](audit-hash-chain-deployment.md) — Append-only audit hash chain deployment and concurrency specifications.

---

## 4. System Architecture

* **Master Architecture Specification:** [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md)
  * Multi-tier topology: Client (Web/Mobile), API Gateway (FastAPI), Storage & DB (PostgreSQL 17).
  * Subsystem breakdown: Auth, Asset Vault, Steganography, and Audit Hash Chain.
  * Component dependency map and directory layout.

---

## 5. Security Architecture

* **Cryptographic Architecture Specification:** [`SECURITY_ARCHITECTURE.md`](SECURITY_ARCHITECTURE.md)
  * Threat model and security perimeters.
  * Cryptographic primitive registry: ECDSA P-256, XChaCha20-Poly1305, AES-256-GCM, HKDF-SHA256, Ed25519, SHA-256.
  * Key management lifecycles (Android Keystore, Master Encryption Key, Stego Signing Keys).
  * Byte-level `IPGW` framing layout and fail-closed validation.
  * Audit hash chain mathematical invariants.

---

## 6. Data Flow & API Specifications

* **Data Flow Pipelines:** [`DATA_FLOW.md`](DATA_FLOW.md)
  * Sequence diagrams for Device Enrollment, Web QR Handshake, Asset Upload, Watermark Embedding, Watermark Verification, and Periodic Auditing.
* **Device Authentication API Contract:** [`M2.4_API_CONTRACT.md`](M2.4_API_CONTRACT.md)
* **Backend REST API Router:** [`../backend/app/api/router.py`](../backend/app/api/router.py)

---

## 7. Database & Migrations (PostgreSQL 17)

IPGuard uses Alembic to manage database migrations strictly in sequence:

| Migration File | Migration Name | Purpose |
| :--- | :--- | :--- |
| `0001_initial_schema.py` | Baseline Schema | Initial core tables and user models |
| `0002_add_auth_sessions.py` | Auth Sessions | Ephemeral challenge nonces and QR status |
| `0003_add_device_status.py` | Device Lifecycle | Device enrollment and active state |
| `0004_secure_notes.py` | Secure Notes | Encrypted user notes storage |
| `0005_asset_vault.py` | Asset Vault | Master asset metadata and cipher specifications |
| `0006_asset_encryption_metadata.py` | Encryption Meta | Protocol version tracking for assets |
| `0007_asset_integrity_metadata.py` | Integrity Meta | Periodic integrity check timestamps and status |
| `0008_audit_hash_chain.py` | Audit Hash Chain | Append-only `audit_events` and `audit_chain_heads` |
| `0009_png_lsb_derivatives.py` | PNG LSB Lineage | Lineage foreign keys (`source_asset_id`), `watermark_id`, and `derivative_type` |

* **Current Head:** `0009_png_lsb_derivatives`
* **Audit Deployment Guide:** [`audit-hash-chain-deployment.md`](audit-hash-chain-deployment.md)

---

## 8. Testing & Quality Assurance

* **Backend Test Suite:** 209 tests across all subsystems (100% PASS, 0 failures, 0 skipped).
* **Concurrency Test:** `backend/tests/test_audit_chain_postgres.py` validates row-level locking across 24 concurrent threads.
* **Frontend Quality:** TypeScript strict mode (0 errors), Vite production bundle (PASS).
* **Automated Acceptance Script:** [`../scripts/m4_browser_acceptance_test.py`](../scripts/m4_browser_acceptance_test.py)

---

## 9. Browser Screenshots & Acceptance Artifacts

All screenshots were generated during automated Playwright browser acceptance testing on Chromium (1366x860):

1. **Initial Vault State:** [`screenshots/m4_acceptance/01_asset_vault_initial.png`](screenshots/m4_acceptance/01_asset_vault_initial.png)
2. **Master Image Uploaded:** [`screenshots/m4_acceptance/02_asset_uploaded.png`](screenshots/m4_acceptance/02_asset_uploaded.png)
3. **Watermark Configuration:** [`screenshots/m4_acceptance/03_watermark_config_modal.png`](screenshots/m4_acceptance/03_watermark_config_modal.png)
4. **Embedding Success State:** [`screenshots/m4_acceptance/04_embed_success.png`](screenshots/m4_acceptance/04_embed_success.png)
5. **Derivative in Vault:** [`screenshots/m4_acceptance/05_vault_with_derivative.png`](screenshots/m4_acceptance/05_vault_with_derivative.png)
6. **Watermark Verification:** [`screenshots/m4_acceptance/06_verify_success_modal.png`](screenshots/m4_acceptance/06_verify_success_modal.png)
7. **Extracted Metadata:** [`screenshots/m4_acceptance/07_extract_payload_modal.png`](screenshots/m4_acceptance/07_extract_payload_modal.png)
8. **Derivative Inspection:** [`screenshots/m4_acceptance/08_derivative_inspect_modal.png`](screenshots/m4_acceptance/08_derivative_inspect_modal.png)
9. **Watermarked Filter Tab:** [`screenshots/m4_acceptance/09_watermarked_filter_tab.png`](screenshots/m4_acceptance/09_watermarked_filter_tab.png)

* **Machine-Readable Results:** [`screenshots/m4_acceptance/acceptance_results.json`](screenshots/m4_acceptance/acceptance_results.json)
* **Master Test Image:** [`screenshots/m4_acceptance/master_artwork_256.png`](screenshots/m4_acceptance/master_artwork_256.png)
* **Watermarked Derivative:** [`screenshots/m4_acceptance/master_artwork_256.watermarked.png`](screenshots/m4_acceptance/master_artwork_256.watermarked.png) (`PSNR = 68.37 dB`)
* **Tampered Pixel Test:** [`screenshots/m4_acceptance/tampered_artwork.png`](screenshots/m4_acceptance/tampered_artwork.png)

---

## 10. Deployment & Operational Handover

* **Master Handover Guide:** [`FINAL_HANDOVER.md`](FINAL_HANDOVER.md) — Comprehensive operator runbook.
* **Quick Reference Commands:**
  ```bash
  # Backend
  cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000
  
  # Frontend
  cd frontend && npm run dev
  ```
* **Production Status:** Evaluation & release candidate build (`release/m0-m4-final`); no live production deployment claimed.

---

## 11. Known Technical Limitations

1. **Spatial LSB Fragility:** LSB steganography is fragile by mathematical design. Any lossy compression (JPEG, WebP) or resizing intentionally destroys the payload and breaks signature validation.
2. **Truecolor PNG Scope:** Only 8-bit truecolor RGB/RGBA PNG images are currently supported.
3. **Legal Attribution:** Ed25519 digital signatures prove mathematical authenticity under a trusted key; they do not constitute statutory copyright registration.

---

## 12. Future Roadmap

1. **Milestone 5 (PLANNED):** Blockchain-based immutable audit anchoring using Merkle Tree roots on EVM networks.
2. **Android Client Enhancements (PLANNED):** Native `BiometricPrompt` hardware gating and Keymaster remote attestation.
