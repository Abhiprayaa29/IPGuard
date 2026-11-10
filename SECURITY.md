# Security Policy — IPGuard

Security is the core foundation of **IPGuard — Secure Digital Asset Protection Platform**. We take the security of our codebase, cryptographic implementations, and user data seriously.

---

## 1. Supported Versions

IPGuard is currently in pre-release version 1.0.0. Security patches and updates are actively maintained on the latest release and default branches.

| Version / Branch | Supported | Notes |
|---|:---:|---|
| `main` | :white_check_mark: Yes | Protected default development baseline |
| `release/m0-m4-final` | :white_check_mark: Yes | Milestone 0–4 frozen release candidate |
| Pre-release feature branches | :x: No | Ephemeral development branches |

---

## 2. Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

If you believe you have discovered a vulnerability in IPGuard:

1. **Private GitHub Advisory:** Use the "Report a vulnerability" button under the **Security** tab of the IPGuard GitHub repository.
2. **Direct Contact:** Alternatively, reach out directly to the project lead [@Abhiprayaa29](https://github.com/Abhiprayaa29).

### What to Include in Your Report
To help us investigate and reproduce the issue quickly, please include:
- A clear description of the vulnerability and its potential security impact.
- Affected component(s): Backend (FastAPI), Frontend (React), or Mobile (Android Authenticator).
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Relevant logs, request/response headers, or terminal outputs (ensure all personal secrets/passwords are redacted).

### Response Timeline
- **Acknowledgement:** We will acknowledge receipt of your vulnerability report within **48 hours**.
- **Assessment:** We will provide an initial assessment and timeline within **5 business days**.
- **Resolution:** A security patch will be prepared on a private branch and verified before being merged into `main`.

---

## 3. Cryptographic Scope & Invariants (Milestones 1–4)

### In-Scope Security Guarantees
- **ECDSA P-256 Key Pair Generation (M2):** Keys generated inside Android Keystore must be hardware-isolated (TEE / StrongBox) and non-exportable (`privateKey.encoded == null`).
- **Signature Verification (M2):** SHA256withECDSA signatures must be verified on the backend against the registered device public key.
- **Anti QR-Jacking / Shoulder Surfing (M2):** The browser session secret token (`token_hash`) must never be encoded in QR payloads or exposed to unauthenticated parties.
- **Pessimistic Row-Level Locking (M2):** PostgreSQL row locking (`SELECT FOR UPDATE`) prevents concurrent challenge re-use.
- **Origin Validation (M2):** Origin headers are validated against an allowed whitelist.
- **Authenticated Storage Confidentiality (M3):** Assets are encrypted using true XChaCha20-Poly1305 AEAD with 24-byte CSPRNG nonces and 16-byte Poly1305 MAC tags.
- **Cryptographic Per-Device Isolation (M3):** Master keys are derived via HKDF-SHA256 bound to individual `device_id` contexts; compromising one device key does not decrypt another device's vault.
- **In-Memory Decrypted Streaming (M3):** Ciphertexts are decrypted in memory upon authenticated request; plaintexts are never written to server disk.
- **Signed Steganographic Lineage (M4):** PNG LSB watermarks embed an `IPGW` v1 binary frame signed with Ed25519 (256-bit) and hashed via SHA-256.
- **Fail-Closed Payload Extraction (M4):** Steganographic payloads are strictly blocked from release (HTTP 409 Conflict) if digital signature or SHA-256 validation fails.
- **Immutable Audit Hash Chain (M4):** Steganography operations append rolling SHA-256 hashes linking sequential audit events, providing tamper-evident non-repudiation.

### Architectural Limitations & Out-of-Scope Boundaries
- **Spatial LSB Fragility:** LSB steganography is fragile by design. Resizing, lossy compression (JPEG, WebP), and filtering will alter pixel bits and fail verification. This is intentional to detect tampering and should not be confused with robust watermarking.
- **Signature Scope:** A valid Ed25519 signature establishes data authenticity under the signing key; it does not constitute an independent legal copyright title without external legal instruments.
- **Native Face Auth:** Android BiometricPrompt integration is a planned future enhancement; device authentication currently operates via ECDSA P-256 Keystore signatures.

---

## 4. Secret Hygiene Policy

1. **Zero Secret Commits:** Never commit `.env` files, private cryptographic seeds, API keys, or raw credentials into git.
2. **Key Generation:** Development keys must be generated using cryptographically secure random number generators (CSPRNG) and placed only in local `.env` files.
3. **Production Deployment:** In production environments, private keys (`STEGO_SIGNING_PRIVATE_KEY_B64`, `ASSET_VAULT_MASTER_KEY_B64`) must be injected via a Hardware Security Module (HSM) or cloud secrets manager (e.g., AWS Secrets Manager, Google Cloud Secret Manager, HashiCorp Vault).
