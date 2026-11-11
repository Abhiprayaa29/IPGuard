# IPGuard Complete Visual Evidence Catalog

**Repository:** `https://github.com/Abhiprayaa29/IPGuard`  
**Branch:** `feature/product-ui-redesign-device-lifecycle`  
**Collection Date:** 2026-11-11  
**Privacy Audit:** [`PRIVACY_REVIEW.md`](PRIVACY_REVIEW.md) — **43 PNGs + 20 source files inspected; zero live secrets exposed.**

---

## Status Classification Key

- **IMPLEMENTED**: Feature/behavior implemented in repository source code and present in current branch.
- **VERIFIED**: Observed in live running execution, automated test output, or physical device UI capture in this branch.
- **CAPTURED**: Real UI screenshot captured from live Playwright browser session or `adb screencap` on Samsung Galaxy A54 5G (`SM-A546E`).
- **CONCEPTUAL**: Simplified architectural or cryptographic model derived directly from source code (`sources/*.mmd` & `sources/*.svg`).
- **PLANNED**: Future roadmap item (specifically Milestone 5 Blockchain Audit Anchoring) — explicitly separated and **not implemented**.
- **BLOCKED / NOT AVAILABLE**: System-protected or hardware-interactive state not captured statlessly and never fabricated.

---

## 1. Web Console Screenshots (`web/` — 21 PNGs, Desktop `1440x900` & Mobile `390x844`)

All Web Console screenshots were captured from the redesigned React 19 + TypeScript UI running against isolated disposable PostgreSQL database `ipguard_test` (wiped immediately post-capture; live `ipguard` untouched).

| Filename | Category | Description | Platform | Status | Source |
| --- | --- | --- | --- | --- | --- |
| [`overview-desktop.png`](web/overview-desktop.png) | Web Overview | Security Overview with Device Binding, System Health, Notes, Vault & recent Audit Events | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/OverviewPage.tsx` |
| [`overview-mobile.png`](web/overview-mobile.png) | Web Overview | Responsive mobile viewport layout of Security Overview | React 19 (`390x844`) | **CAPTURED / VERIFIED** | `frontend/src/pages/OverviewPage.tsx` |
| [`qr-authentication.png`](web/qr-authentication.png) | Authentication | Dynamic 60s QR Challenge & SEC-02 transport guarantees | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/LoginPage.tsx` |
| [`device-management-slot-empty.png`](web/device-management-slot-empty.png) | Device Lifecycle | `0/1` UNREGISTERED account device slot waiting for enrollment | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/DeviceManagementPage.tsx` |
| [`device-management-active.png`](web/device-management-active.png) | Device Lifecycle | `1/1` REGISTERED & `ACTIVE` bound device posture card | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/DeviceManagementPage.tsx` |
| [`device-management-revoked.png`](web/device-management-revoked.png) | Device Lifecycle | `REVOKED` state preserving `1/1` slot lock and session invalidation | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/DeviceManagementPage.tsx` |
| [`device-management-restore-dialog.png`](web/device-management-restore-dialog.png) | Device Lifecycle | Out-of-band `X-Account-Recovery-Key` modal dialog | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/DeviceManagementPage.tsx` |
| [`device-management-unregister-dialog.png`](web/device-management-unregister-dialog.png) | Device Lifecycle | Unregister confirmation modal releasing `0/1` slot | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/DeviceManagementPage.tsx` |
| [`secure-notes-empty.png`](web/secure-notes-empty.png) | Secure Notes | Authenticated empty state prior to creating first encrypted note | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/NotesPage.tsx` |
| [`secure-notes-create-modal.png`](web/secure-notes-create-modal.png) | Secure Notes | New note modal encrypted before DB storage via AES-256-GCM + HKDF | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/NotesPage.tsx` |
| [`secure-notes.png`](web/secure-notes.png) | Secure Notes | Decrypted Secure Notes grid view after creation | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/NotesPage.tsx` |
| [`asset-vault.png`](web/asset-vault.png) | Asset Vault | Original + `PNG_LSB` derivative asset table with integrity & cipher details | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/AssetVaultPage.tsx` |
| [`asset-vault-upload-modal.png`](web/asset-vault-upload-modal.png) | Asset Vault | XChaCha20-Poly1305 encrypted asset upload modal | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/AssetVaultPage.tsx` |
| [`asset-vault-preview-modal.png`](web/asset-vault-preview-modal.png) | Asset Vault | In-memory decrypted PNG preview, SHA-256 digest & lineage inspection modal | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/AssetVaultPage.tsx` |
| [`asset-vault-rename-modal.png`](web/asset-vault-rename-modal.png) | Asset Vault | Encrypted metadata asset rename modal | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/AssetVaultPage.tsx` |
| [`steganography-lab.png`](web/steganography-lab.png) | Steganography Lab | Encode Watermark view with PNG RGB channel capacity & fragility notice | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/StegoLabPage.tsx` |
| [`steganography-inspect-valid.png`](web/steganography-inspect-valid.png) | Steganography Lab | Read-only watermark inspection: `VALID_WATERMARK` (Ed25519 + SHA-256 verified) | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/StegoLabPage.tsx` |
| [`steganography-inspect-invalid-sig.png`](web/steganography-inspect-invalid-sig.png) | Steganography Lab | Signature bit-flip detection: `INVALID_SIGNATURE` fail-closed payload withhold | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/StegoLabPage.tsx` |
| [`steganography-inspect-corrupted.png`](web/steganography-inspect-corrupted.png) | Steganography Lab | Corrupted payload detection: `CORRUPTED_PAYLOAD` SHA-256 mismatch | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/StegoLabPage.tsx` |
| [`steganography-inspect-no-watermark.png`](web/steganography-inspect-no-watermark.png) | Steganography Lab | Clean unwatermarked PNG detection: `NO_WATERMARK` | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/StegoLabPage.tsx` |
| [`system-status.png`](web/system-status.png) | System Status | Live `/health`, `/health/db`, Auth & Vault readiness telemetry | React 19 (`1440x900`) | **CAPTURED / VERIFIED** | `frontend/src/pages/SystemStatusPage.tsx` |

---

## 2. Physical Android Authenticator Screenshots (`android/` — 8 PNGs, `1080x2340`)

Captured directly on physical **Samsung Galaxy A54 5G (`SM-A546E`)**, **Android 16 (API 36)** via `adb screencap -p` (`serial: RRCW703SRGE`).

| Filename | Category | Description | Platform | Status | Source |
| --- | --- | --- | --- | --- | --- |
| [`authenticator-home.png`](android/authenticator-home.png) | Mobile Home | Welcome screen showing `SM-A546E` posture, Keystore TEE, Face Gate availability & actions | Kotlin / Compose | **CAPTURED / VERIFIED** | `mobile-authenticator` (`WelcomeScreen`) |
| [`device-registration.png`](android/device-registration.png) | Enrollment | One-time enrollment `Bind this phone` overview, guarantees & 4-step pipeline | Kotlin / Compose | **CAPTURED / VERIFIED** | `mobile-authenticator` (`DeviceRegistrationScreen`) |
| [`qr-scanner.png`](android/qr-scanner.png) | QR Scanner | Live CameraX rear camera viewfinder with on-device ML Kit scanner frame | Kotlin / CameraX | **CAPTURED / VERIFIED** | `mobile-authenticator` (`QrScannerScreen`) |
| [`authentication-request.png`](android/authentication-request.png) | Sign-In Review | `Verify sign-in request` showing 5-step authentication pipeline & request context | Kotlin / Compose | **CAPTURED / VERIFIED** | `mobile-authenticator` (`ApprovalScreen`) |
| [`approval-screen.png`](android/approval-screen.png) | Approval Action | Lower section with Native Face Gate notice, warning & `Continue to Face & Approval` | Kotlin / Compose | **CAPTURED / VERIFIED** | `mobile-authenticator` (`ApprovalScreen`) |
| [`device-information.png`](android/device-information.png) | Device Info | Hardware identity, masked device ID (`ipguard-de...4757`), auth policy & Keystore status | Kotlin / Compose | **CAPTURED / VERIFIED** | `mobile-authenticator` (`DeviceInfoScreen`) |
| [`security-settings.png`](android/security-settings.png) | Security Policy | `Security & about IPGuard` covering `BiometricPrompt (BIOMETRIC_WEAK)` & ECDSA P-256 rules | Kotlin / Compose | **CAPTURED / VERIFIED** | `mobile-authenticator` (`SecurityAboutScreen`) |
| [`secure-vault-info.png`](android/secure-vault-info.png) | Vault Overview | Mobile `Secure Asset Vault` posture card (`XChaCha20-Poly1305` + `HKDF-SHA256`) | Kotlin / Compose | **CAPTURED / VERIFIED** | `mobile-authenticator` (`SecureVaultInfoScreen`) |

### Uncaptured Runtime / OS-Protected Android States (Explicitly Not Fabricated)

| State | Status | Technical Reason |
| --- | --- | --- |
| Native OS `BiometricPrompt` sheet | **BLOCKED / NOT AVAILABLE** | OS-protected system overlay (`FLAG_SECURE` / hardware biometric dialog requires live interactive physical trigger; never mocked). |
| Biometric Failure / Revoked Rejection live dialog | **NOT AVAILABLE** | Requires stateful live session rejection loop; behavior verified in code and automated tests (`BiometricFaceGateManagerTest`). |

---

## 3. Architecture Diagrams (`architecture/` — 5 PNGs + `.svg`/`.mmd` Sources)

Every diagram was constructed directly from repository models, API routes, and Android managers. Vector/text sources live in [`architecture/sources/`](architecture/sources/).

| Filename | Sources | Description | Status | Verified From |
| --- | --- | --- | --- | --- |
| [`system-architecture.png`](architecture/system-architecture.png) | [`.svg`](architecture/sources/system-architecture.svg) · [`.mmd`](architecture/sources/system-architecture.mmd) | Client layer, Android TEE boundary, FastAPI services, PG 17, Disk Vault & planned M5 hook | **IMPLEMENTED (M1–M4) / PLANNED (M5 box)** | `backend/app/`, `frontend/src/`, `mobile-authenticator/` |
| [`authentication-flow.png`](architecture/authentication-flow.png) | [`.svg`](architecture/sources/authentication-flow.svg) · [`.mmd`](architecture/sources/authentication-flow.mmd) | 10-step QR Challenge-Response flow highlighting SEC-02 channel token separation | **IMPLEMENTED / VERIFIED** | `backend/app/api/routes/`, `QrAuthPayloadParser.kt` |
| [`device-lifecycle.png`](architecture/device-lifecycle.png) | [`.svg`](architecture/sources/device-lifecycle.svg) · [`.mmd`](architecture/sources/device-lifecycle.mmd) | `UNREGISTERED` / `ACTIVE` / `REVOKED` state transitions, `1/1` slot lock & `X-Account-Recovery-Key` | **IMPLEMENTED / VERIFIED** | `backend/app/models/auth.py`, `test_device_lifecycle.py` |
| [`database-erd.png`](architecture/database-erd.png) | [`.svg`](architecture/sources/database-erd.svg) · [`.mmd`](architecture/sources/database-erd.mmd) | Exact PostgreSQL schema across Migrations `0001–0011` (`accounts`, `devices`, `auth_sessions`, `notes`, `assets`, `audit_*`) | **IMPLEMENTED / VERIFIED** | `backend/app/models/`, `migrations/versions/0010_*.py` |
| [`deployment-architecture.png`](architecture/deployment-architecture.png) | [`.svg`](architecture/sources/deployment-architecture.svg) · [`.mmd`](architecture/sources/deployment-architecture.mmd) | Local engineering workstation topology + `SM-A546E` over `adb reverse` + planned cloud boundary | **VERIFIED (Local) / PLANNED (Cloud/M5)** | `docker`, `vite`, `uvicorn`, `postgresql 17.11` |

---

## 4. Cryptography Diagrams (`cryptography/` — 5 PNGs + `.svg`/`.mmd` Sources)

Source files live in [`cryptography/sources/`](cryptography/sources/).

| Filename | Sources | Description | Status | Verified From |
| --- | --- | --- | --- | --- |
| [`device-authentication.png`](cryptography/device-authentication.png) | [`.svg`](cryptography/sources/device-authentication.svg) · [`.mmd`](cryptography/sources/device-authentication.mmd) | Two-gate Native Face `BIOMETRIC_WEAK` pre-check + Keystore `CryptoObject` ECDSA `secp256r1` | **IMPLEMENTED / VERIFIED** | `DeviceKeyManager.kt`, `BiometricFaceGateManager.kt` |
| [`secure-notes-encryption.png`](cryptography/secure-notes-encryption.png) | [`.svg`](cryptography/sources/secure-notes-encryption.svg) · [`.mmd`](cryptography/sources/secure-notes-encryption.mmd) | `HKDF-SHA256` per-device subkey + `AES-256-GCM` `v1$...` wire encoding | **IMPLEMENTED / VERIFIED** | `backend/app/services/note_crypto.py` |
| [`asset-vault-encryption.png`](cryptography/asset-vault-encryption.png) | [`.svg`](cryptography/sources/asset-vault-encryption.svg) · [`.mmd`](cryptography/sources/asset-vault-encryption.mmd) | `XChaCha20-Poly1305` (192-bit nonce) ciphertext isolation + `SHA-256` integrity monitor | **IMPLEMENTED / VERIFIED** | `backend/app/services/asset_crypto.py`, `asset_integrity.py` |
| [`steganography-workflow.png`](cryptography/steganography-workflow.png) | [`.svg`](cryptography/sources/steganography-workflow.svg) · [`.mmd`](cryptography/sources/steganography-workflow.mmd) | `IPGW` v1 binary frame, `Ed25519` signature, 1-bit RGB LSB embedding & fragility boundary | **IMPLEMENTED / VERIFIED** | `backend/app/services/png_steganography.py` |
| [`audit-hash-chain.png`](cryptography/audit-hash-chain.png) | [`.svg`](cryptography/sources/audit-hash-chain.svg) · [`.mmd`](cryptography/sources/audit-hash-chain.mmd) | Sequential `SHA-256` chain (`IPGUARD-AUDIT-V1`) vs. **PLANNED** M5 Merkle blockchain anchor | **M4 VERIFIED / M5 PLANNED** | `backend/app/services/audit_chain.py` |

---

## 5. Testing & Verification Evidence (`testing/` — 4 PNGs)

Rendered directly from verbatim command executions recorded on **2026-11-11 UTC**. No test counts or metrics were extrapolated or fabricated.

| Filename | Category | Description | Command & Scope | Status |
| --- | --- | --- | --- | --- |
| [`backend-tests.png`](testing/backend-tests.png) | Backend Pytest | `pytest -v --tb=short` — **225 passed, 0 failed, 0 skipped** (`16.92s`) | Isolated `ipguard_test` + `audit_ipguard_test` | **VERIFIED** |
| [`frontend-build.png`](testing/frontend-build.png) | Web Typecheck & Build | `npm run typecheck && npm run build` — `tsc --noEmit` (0 errors), Vite `2206` modules (`431 ms`) | `D:\Projects\IPGuard\frontend` | **VERIFIED** |
| [`android-tests.png`](testing/android-tests.png) | Android Unit Tests | `.\gradlew.bat testDebugUnitTest assembleDebug --no-daemon` — **11 JUnit suites, 68 passed, 0 failed, 0 skipped** | `D:\Projects\IPGuard\mobile-authenticator` | **VERIFIED** |
| [`audit-chain-verification.png`](testing/audit-chain-verification.png) | Audit Hash Chain | Live verification across **117 non-empty chains** (`124` total heads incl. `7` 0-event heads): **818/818 events valid, 0 chain breaks** (`ipguard-dev-1fbd21364ac24757`: `80/80` valid) | Read-only transaction w/ rollback against `ipguard` | **VERIFIED** |
| *Physical Device E2E* | Mobile + Web E2E | Interactive end-to-end physical phone run post-`cb0aa6b` not captured in this automated session | Prior physical evidence tracked historically in `docs/assets/` | **NOT AVAILABLE (post-`cb0aa6b` run)** |

---

## 6. Historical Evidence Preserved Untouched

- `docs/assets/` (`m2.1/`, `m2.2/`, `m3/`, legacy PNGs) — Preserved intact as Milestone 2–3 historical proof.
- `docs/screenshots/m4_acceptance/` & `docs/screenshots/m4_stego_lab/` — Preserved intact as Milestone 4 acceptance proof.
