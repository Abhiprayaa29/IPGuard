# IPGuard Pre-Blockchain Architecture & Security Audit

**Audit Date:** 2026-11-11  
**Target Stage:** Pre-Blockchain Finalization (M1–M4 Foundation Hardening prior to M5 Blockchain Integration)  
**Branch Audited:** `feature/product-ui-redesign-device-lifecycle`

---

## 1. Executive Summary

IPGuard integrates a React 19 Web Console, FastAPI + SQLAlchemy backend backed by PostgreSQL 17, and a Kotlin + Jetpack Compose Android Authenticator bound to hardware/TEE keys (`AndroidKeyStore`) and native OS biometrics (`AndroidX BiometricPrompt`). Across M1–M4, the core cryptographic guarantees—hardware-backed ECDSA P-256 authentication, row-locked challenge consumption, XChaCha20-Poly1305 Asset Vault, AES-256-GCM Secure Notes, Ed25519-signed PNG LSB watermarks, Asset Integrity monitoring, and SHA-256 linked Audit Hash Chains—are functional and verified against PostgreSQL 17.

During Pre-Blockchain Finalization, this audit identified and hardened three cross-account / session replay boundary gaps on the backend, added fail-closed production enforcement for account recovery configuration, guarded against duplicate Android biometric signing launches observed in physical device logs, and verified full isolated database testing (`ipguard_test`) without disturbing preserved live user records in `ipguard`.

---

## 2. Backend Architecture Inventory

### 2.1 Authentication, Session & Device Lifecycle (`app/api/routes/auth.py`, `app/services/auth.py`)
- **Challenge Issuance (`POST /api/v1/auth/sessions`):** Issues 60-second `PENDING` `ENROLLMENT` or `AUTHENTICATION` challenges with 256-bit `session_token`, `challenge_nonce`, RFC 6454 trusted `client_origin`, and SEC-02 in-memory `browser_channel_token` (stored hashed via SHA-256 as `browser_channel_token_hash`).
- **Channel-Bound Polling (`GET /api/v1/auth/sessions/{session_token}`):** Enforces `X-Browser-Channel-Token` constant-time digest comparison and lazy expiration checking.
- **Atomic Consumption (`POST /devices/register`, `POST /sessions/{token}/verify`):** Uses PostgreSQL `SELECT ... FOR UPDATE` on both the target `AuthSession` row and canonical `Account` row (`_ensure_and_lock_account`) to guarantee single-winner challenge consumption and concurrency safety.
- **Canonical Payload & Signature Verification (`app/services/crypto.py`):** Validates `IPGUARD_AUTH_V1|<session_token>|<type>|<nonce>|<origin>|<timestamp>` (matching exact schema checks) and verifies ASN.1/DER ECDSA NIST P-256 (`secp256r1`) SHA-256 signatures.
- **Bearer Authorization Dependency (`app/api/deps.py`):** Supports full 64-hex tokens or unambiguous `ipguard_sess_<24-hex>` tokens, strictly requiring `status == "APPROVED"`, `expires_at > utc_now`, non-null bound `Device`, and `device.status == "ACTIVE"` (failing closed with HTTP `403` if `REVOKED` or `UNREGISTERED`).

### 2.2 Account Identity & Single-Device Enforcement (`app/models/auth.py`, `migrations/0010_account_device_lifecycle.py`)
- **Account Table:** Canonical `accounts` table (`DEFAULT_ACCOUNT_ID = "ipguard-primary"`).
- **Database Constraint:** Partial unique index `uq_devices_one_registered_per_account ON devices (account_id) WHERE status IN ('ACTIVE', 'REVOKED')`. `UNREGISTERED` rows retain audit history and free the `0/1` slot.
- **Lifecycle Endpoints:**
  - `GET /api/v1/auth/devices/summary`: Returns slot usage (`0/1` or `1/1`), `current_device`, and separated `UNREGISTERED` historical records.
  - `POST /api/v1/auth/devices/{device_id}/revoke`: Marks device `REVOKED`, preserves registration slot (`1/1`) and public key, invalidates active `APPROVED` sessions and cancels `PENDING`/`SCANNED` sessions for the account, and appends `DEVICE_REVOKED` to `audit_events`.
  - `POST /api/v1/auth/devices/{device_id}/restore`: Requires out-of-band `X-Account-Recovery-Key` (or `X-Dev-Admin-Key` in non-production), rejects revoked Bearer self-restore (`403`), rejects `UNREGISTERED` records (`409`), validates preserved SPKI public key, transitions `REVOKED -> ACTIVE`, and records `DEVICE_RESTORED`.
  - `POST /api/v1/auth/devices/{device_id}/unregister`: Transitions device to `UNREGISTERED`, frees the `0/1` account slot, invalidates active & pending sessions, preserves Notes, Assets, and audit chains, and appends `DEVICE_UNREGISTERED`.

### 2.3 Secure Vaults, Integrity & Audit Hash Chain
- **Secure Notes (`app/services/notes.py`, `app/services/note_crypto.py`):** Encrypts plaintext with AES-256-GCM (+ Vigenère layer) using HKDF-SHA256 keys derived from `notes_master_key_bytes`, strictly isolated per authenticated `owner_id` (`device.device_id`).
- **Digital Asset Vault (`app/services/assets.py`, `app/services/asset_crypto.py`, `app/services/asset_storage.py`):** Stores encrypted files outside DB with XChaCha20-Poly1305 AEAD, HKDF-SHA256 per-device keys, and AAD `v1|<device_id>|<asset_id>`.
- **Asset Integrity (`app/services/asset_integrity.py`):** Streaming SHA-256 verification of stored ciphertext against `sha256_hash` using short row-locked transactions (`INTEGRITY_CHECK_STARTED`, `INTEGRITY_CHECK_PASSED` / mismatch events).
- **Steganography (`app/services/png_steganography.py`, `app/services/stego_lab.py`):** 1-bit RGB LSB packet (`IPGW`) signed with server Ed25519 (`STEGANOGRAPHY` keys) producing XChaCha20-encrypted `PNG_LSB` derivative assets; fail-closed read-only inspection withholding untrusted metadata unless status is `VALID`.
- **Audit Hash Chain (`app/services/audit_chain.py`):** Append-only SHA-256 domain-separated (`IPGUARD-AUDIT-V1\x00`) hash chains per `chain_id`, prohibiting storage of secrets/tokens via allowlisted key checks, with verification helper `verify_audit_chain`.

---

## 3. Frontend Web Console Inventory (`frontend/src/`)

- **Router & Layout (`app/router.tsx`, `components/layout/AppShell.tsx`):** Desktop sidebar + mobile drawer linking `/overview`, `/login`, `/devices`, `/notes`, `/assets`, `/steganography`, `/system-status`.
- **Token Lifecycle (`utils/session.ts`):** Bearer access token stored in browser `sessionStorage` (`ipguard_session_access_token`); SEC-02 polling secret stays strictly in JS hook memory (`hooks/useQrAuth.ts`).
- **System Probes (`services/systemStatus.ts`, `utils/status.ts`):** Live probe checks against `/health`, `/health/db`, `/system/info`, and `/system/overview` reporting `Operational`, `Degraded`, `Unavailable`, `Checking`, or `Unknown`.
- **Data Management Views:**
  - `DeviceManagementPage.tsx`: Displays `0/1` vs `1/1`, separated `Device History`, and confirmation dialogs for Revoke Access, Restore Access (recovery key field), and Unregister Device.
  - `NotesPage.tsx`, `AssetVaultPage.tsx`, `SteganographyLabPage.tsx`: Session-gated CRUD, image preview, PNG_LSB watermark embed/verify/extract, and read-only PNG inspection.

---

## 4. Android Authenticator Inventory (`mobile-authenticator/`)

- **Biometric Gate (`security/BiometricFaceGateManager.kt`, `AuthenticatorViewModel.kt`):** Runs native `AndroidX BiometricPrompt` with `BIOMETRIC_WEAK` (without `CryptoObject`) prior to hardware Keystore signing.
- **Hardware Keystore & M2 Signing (`security/DeviceKeyManager.kt`, `DeviceSigningAuthenticationManager.kt`):** Manages non-exportable ECDSA P-256 keypair inside Android Keystore / TEE, authorizing signing via `BiometricPrompt.CryptoObject` (fallback/strong biometric policy governed by `DeviceAuthenticationPolicy.kt`).
- **QR & Network Flow (`security/qr/QrAuthPayloadParser.kt`, `network/`):** Parses QR challenges, verifies canonical format, sends `/scan`, then `/devices/register` (`ENROLLMENT`) or `/verify` (`AUTHENTICATION`), and syncs status via `GET /auth/devices/{device_id}/status`.

---

## 5. Known Architectural Limitations & M5 Readiness

### 5.1 Intentional Single-Owner Scope vs Multi-Account Support
- Web Console flows currently operate against the canonical account `DEFAULT_ACCOUNT_ID = "ipguard-primary"` because IPGuard M1–M4 does not yet introduce username/password or OIDC user accounts.
- Database schema and API isolation (`accounts`, `devices.account_id`, `auth_sessions.account_id`) support multi-account separation (`Account A` vs `Account B`), enforced only when provisioned or authorized server-side (`X-Dev-Admin-Key` in non-production).

### 5.2 Device Key-Bound Resources Across Unregister + Re-Enroll of a Different Device
- Under M3/M4, `Note.owner_id` and `Asset.device_id` (plus XChaCha20-Poly1305 AAD `v1|<device_id>|<asset_id>`) bind encrypted records to the enrolling `device_id`.
- Unregistering preserves all Notes, Assets, and Audit events intact in PostgreSQL. If the same device (`device_id`) re-enrolls under its original `account_id`, records remain bound to it; however, enrolling a *different* hardware `device_id` under the same `account_id` cannot decrypt prior device-AAD assets without an account-scoped KEK/DEK wrapping layer (recommended enhancement for M5/post-M4).

---

## 6. Hardening Changes Applied in Pre-Blockchain Finalization

1. **Blocked Unauthenticated `account_id` Spoofing (`backend/app/api/routes/auth.py`):** `POST /api/v1/auth/sessions` and `GET /api/v1/auth/devices/summary` now reject non-default `account_id` values with HTTP `403` unless authorized by authenticated Bearer token or valid `X-Account-Recovery-Key` / non-production `X-Dev-Admin-Key`.
2. **Enforced Cross-Account Session & Device Isolation (`backend/app/services/auth.py`):**
   - `verify_session_signature` verifies `device.account_id == session.account_id` (`403 cross_owner_forbidden`) and rejects non-`PENDING`/`SCANNED` states (`REVOKED`, `REJECTED`, `APPROVED`).
   - `register_device` forbids re-enrolling an `UNREGISTERED` historical `device_id` onto a different `account_id` (`409 cross_account_device_conflict`) and blocks re-use of consumed/revoked sessions.
3. **Production Recovery Key Fail-Closed Validation (`backend/app/core/config.py`, `backend/app/main.py`):** Startup fails closed in `app_env == "production"` if `ACCOUNT_RECOVERY_KEY` is missing or left at the default development value.
4. **Android Duplicate Signing Prompt Guard (`ApprovalScreen.kt`, `AuthenticatorViewModel.kt`):** Added `AuthFlowStep.AWAITING_DEVICE_AUTHENTICATION` to UI `isProcessing` and added an in-flight re-entry guard in `approveAndExecuteAuth` to eliminate duplicate `BiometricFragment` launch errors seen in physical device logcat.

---

## 7. Readiness Hooks for M5 Blockchain Integration

- **`audit_events` (`chain_id`, `sequence`, `prev_hash`, `event_hash`):** Ready for periodic Merkle root / checkpoint anchoring onto blockchain ledgers without storing plaintext secrets off-chain or on-chain.
- **`assets` (`id`, `sha256_hash`, `watermark_id`, `source_asset_id`):** Provides deterministic content and derivative digests suitable for immutable ownership/timestamp anchoring.
- **`accounts` & `devices` (`account_id`, `device_id`, `public_key_fingerprint`, `status`):** Establishes clean identity boundaries for associating hardware keys and lifecycle revocations with M5 on-chain registries.
