# IPGuard Cryptographic Key Lifecycle & Recovery Security Audit

**Audit Date:** 2026-11-11  
**Branch:** `feature/product-ui-redesign-device-lifecycle`  
**Scope:** Backend Cryptographic Services, Configuration Settings, Android Hardware Keystore, and Out-of-Band Recovery Authorization

*(No secrets, raw credentials, or fallback key literals are included in this document.)*

---

## 1. Key & Cryptographic Inventory Summary

| Domain | Algorithm & Size | Key Derivation / Wrapping | Nonce / Randomness | Storage Location | Rotation & Revocation | Production Fail-Closed Status |
|---|---|---|---|---|---|---|
| **Device Auth Keys** | ECDSA NIST P-256 (`secp256r1`) + SHA-256 | Hardware-generated per keypair | OS Hardware CSPRNG per ECDSA signature | Private key non-exportable in `AndroidKeyStore` (TEE/StrongBox); SPKI DER public key + colon-hex SHA-256 fingerprint in PostgreSQL `devices` | Server-side `REVOKED` (slot kept `1/1`), `UNREGISTERED` (slot freed `0/1`); local rotation blocked while enrolled under M2 policy | **PASS** |
| **Secure Notes** | AES-256-GCM (+ Vigenère layer) | HKDF-SHA256 (`salt=owner_id`, `info=ipguard-secure-notes-v1-hkdf-aes256gcm`, `32` bytes) | `os.urandom(12)` per field encryption (`v1$` envelope) | Environment / secret manager (`NOTES_MASTER_KEY_B64`); ciphertext only in PostgreSQL | Envelope version prefix `v1$`; master key rotation requires offline re-encryption migration | **PASS** (fails closed in `production`) |
| **Asset Vault** | XChaCha20-Poly1305 (IETF via PyNaCl) | HKDF-SHA256 (`salt=device_id`, `info=ipguard-asset-vault-v1-xchacha20poly1305`, `32` bytes) | `secrets.token_bytes(24)` CSPRNG 192-bit nonce per upload/derivative | Environment (`ASSET_VAULT_MASTER_KEY_B64`); AAD = `v1\|<device_id>\|<asset_id>`; encrypted binary on disk | Nonce stored per asset row; per-device derivation isolates owners; cross-device KEK/DEK wrapping not yet implemented | **PASS** (fails closed in `production`) |
| **PNG Steganography** | Ed25519 signing + SHA-256 payload digest + 1-bit RGB LSB framing | Domain prefix `IPGUARD-PNG-LSB-WATERMARK-V1\x00`; 128-bit `signing_key_id` = `SHA256(pub)[:16]` | Deterministic RFC 8032 Ed25519 signatures | `STEGO_SIGNING_PRIVATE_KEY_B64` + multi-key JSON map `STEGO_PUBLIC_KEYS_JSON` | Supports multiple active/historical verification public keys (`stego_public_keys_json`) for zero-downtime key rotation | **PASS** (no hardcoded private key fallback) |
| **Account Recovery Key** | HMAC-ready constant-time compare (`secrets.compare_digest`) / optional `SHA-256` digest | Optional `ACCOUNT_RECOVERY_KEY_SHA256` verification without storing plaintext | Out-of-band operator secret (`>=32` chars required in `production`) | Environment (`ACCOUNT_RECOVERY_KEY_SHA256` or `ACCOUNT_RECOVERY_KEY`); **stripped from frontend JS bundle** (`services/devices.ts`) | Server-wide static secret; manual operator rotation; **no per-user backup codes or per-key revocation list yet** | **HARDENED FOR SINGLE-OWNER; BLOCKED FOR MULTI-TENANT** |

---

## 2. Detailed Recovery Key (`X-Account-Recovery-Key`) Audit

Evaluated against IPGuard Pre-Blockchain Closure criteria:

| Criterion | Status | Evidence & Findings |
|---|---|---|
| **Entropy** | **PASS (Prod Enforced) / DEV WARN** | Production configuration validation (`effective_account_recovery_key`) rejects keys `< 32` characters and rejects the default development placeholder unless a valid 64-hex `ACCOUNT_RECOVERY_KEY_SHA256` digest is set. Local dev defaults are permitted only when `app_env != "production"`. |
| **Storage Protection & Hashing** | **PARTIAL (Hardened)** | Added `ACCOUNT_RECOVERY_KEY_SHA256` support so production servers need only store a SHA-256 hex digest rather than plaintext. Uses constant-time `secrets.compare_digest`. Plaintext fallback remains supported strictly for developer ergonomics in non-production. |
| **Rate Limiting** | **PASS (Hardened)** | Implemented per-`(client_ip, device_id)` sliding-window rate limiter on `POST /api/v1/auth/devices/{device_id}/restore`: maximum **5** failed authorization attempts per 60-second window before HTTP `429 recovery_rate_limited` (`test_21`). Note: In-memory bucket resets on single-process restart and requires Redis/shared store for horizontal scaling. |
| **Attempt Logging & Header Redaction** | **PASS (Hardened)** | Added `ipguard.security` structured audit logs (`recovery_attempt device_id=... client_ip=... outcome=... header_redacted=true`) recording authorized, rejected, bearer-self-restore, missing-auth, and rate-limited outcomes. Neither `X-Account-Recovery-Key` nor `X-Dev-Admin-Key` values are ever logged or echoed in error messages (`test_21`). |
| **Unauthorized & Self-Restore Prevention** | **PASS** | Revoked devices cannot restore themselves via Bearer token (`403 recovery_authorization_required`); unauthenticated calls fail closed (`401`); `UNREGISTERED` devices cannot be restored (`409 cannot_restore_unregistered_device`). |
| **Rotation & Individual Revocation** | **BLOCKED (Multi-Tenant)** | Currently uses a single server-level recovery secret/digest (`ACCOUNT_RECOVERY_KEY` / `ACCOUNT_RECOVERY_KEY_SHA256`). Suitable for **single-owner / operator-administered recovery**, **not** production self-service multi-account deployments where each account requires independently salted Argon2id/scrypt-hashed recovery codes and individual revocation records. |

---

## 3. Android Keystore Hardware Isolation Review (`DeviceKeyManager.kt`)

- Uses `KeyProperties.KEY_ALGORITHM_EC` (`secp256r1`) stored under alias `ipguard_device_signing_v1` in `AndroidKeyStore`.
- Enforces `setUserAuthenticationRequired(true)` with `0`-second validity window on API 30+, requiring per-operation `BiometricPrompt.CryptoObject` authorization (`AUTH_BIOMETRIC_STRONG or AUTH_DEVICE_CREDENTIAL`) prior to every ECDSA signature.
- Sets `setInvalidatedByBiometricEnrollment(true)` so newly enrolled OS biometrics invalidate old hardware signing keys cleanly.
- Verified that `BiometricFaceGateManager` runs native `AndroidX BiometricPrompt (BIOMETRIC_WEAK)` strictly as a separate gate without `CryptoObject`, leaving M2 Keystore hardware cryptography unchanged.

---

## 4. Recommended M5+ Enhancements (Deferred Out of Scope)

1. Introduce per-account hashed single-use recovery codes (or WebAuthn hardware backup keys) persisted in a dedicated `account_recovery_factors` table with individual revocation timestamps.
2. Introduce account-scoped envelope DEK wrapping (`Account Master KEK -> Account DEK -> Asset XChaCha20-Poly1305`) if asset portability across replacement phone hardware IDs is required.
3. Back the `/restore` rate limiter with Redis or PostgreSQL advisory counters when deploying multiple API workers.
