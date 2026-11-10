# Changelog — IPGuard

All notable changes to the **IPGuard (Secure Digital Asset Protection Platform)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-10

### Milestone 4 — Image Steganography, Cryptographic Watermarking & Audit Ledger
#### Added
- **PNG LSB Steganography Engine:** 1-bit per color channel LSB embedding on row-major RGB raster arrays, preserving alpha channels on 8-bit truecolor RGBA PNGs.
- **Binary Framing (`IPGW` v1):** 170-byte fixed header layout containing magic bytes `IPGW`, versioning, flags, Watermark UUID, Source Asset UUID, Derivative Asset UUID, payload length, SHA-256 payload digest, signing key ID, and Ed25519 digital signature.
- **Ed25519 Digital Signing:** 256-bit Edwards-curve digital signatures generated over domain-separated frame headers and payload data (`STEGO_DOMAIN + PREFIX + PAYLOAD`).
- **Asset Derivative Lineage:** Structured schema binding derivatives (`derivative_type='PNG_LSB'`) to source masters (`source_asset_id`), protecting original files from modification or premature deletion.
- **Append-Only Cryptographic Audit Hash Chain:** Table `audit_events` linking sequential audit events via rolling SHA-256 hashes (`prev_hash`), ensuring tamper-evident history for `ASSET_STEGO_EMBEDDED`, `STEGO_WATERMARK_VERIFIED`, and `STEGO_PAYLOAD_EXTRACTED`.
- **Alembic Database Migrations:** Sequential migrations `0007_asset_integrity_metadata.py`, `0008_audit_hash_chain.py`, and `0009_png_lsb_derivatives.py`.
- **Web Console Asset Vault Interface:** Integrated interactive modals for watermark configuration, signed LSB embedding, in-browser decrypted PNG downloading, cryptographic verification, and payload extraction.
- **Automated Playwright Browser Acceptance Suite:** 14-step automated browser verification script capturing 9 visual acceptance screenshots with 0 console errors.

---

## [0.3.0] - 2026-11-08

### Milestone 3 — Authenticated Digital Asset Vault & Secure Notes
#### Added
- **XChaCha20-Poly1305 AEAD Storage:** Symmetric file encryption utilizing 24-byte CSPRNG nonces and 16-byte Poly1305 authentication tags.
- **HKDF-SHA256 Per-Device Key Derivation:** Cryptographic key derivation isolating encrypted assets per hardware device identity.
- **In-Memory Streaming Decryption:** Endpoint `GET /api/v1/assets/{id}/download` decrypts ciphertexts in memory, preventing plaintext leakage to disk.
- **Secure Notes Vault:** AES-256-GCM encrypted notes storage bound to hardware device contexts.
- **Alembic Migrations:** Added `0004_secure_notes.py`, `0005_asset_vault.py`, and `0006_asset_encryption_metadata.py`.

---

## [0.2.0] - 2026-11-07

### Milestone 2 — Hardware Device Authentication & QR Verification
#### Added
- **Android Authenticator:** Native Android application (Kotlin, Jetpack Compose, CameraX) with hardware key generation in Android Keystore.
- **ECDSA NIST P-256 Hardware Signatures:** Non-exportable private signing keys enforcing out-of-band cryptographic challenge signatures.
- **Dynamic Web QR Authentication:** Ephemeral session challenges with 60-second TTL and anti-QR jacking browser token binding.
- **One-Time Device Enrollment:** Pessimistic row-locking registration preventing duplicate device enrollment.
- **Alembic Migrations:** Added `0002_add_auth_sessions.py` and `0003_add_device_status.py`.

---

## [0.1.0] - 2026-11-06

### Milestone 1 — Foundation & Security Infrastructure
#### Added
- **Core FastAPI Gateway:** Asynchronous Python 3.13 REST API with centralized Pydantic settings.
- **Fail-Closed Configuration:** Mandatory key validation in production environments.
- **Safe Error Envelopes:** Standardized JSON error response handler masking internal stack traces.
- **Database Baseline:** PostgreSQL 17 integration via SQLAlchemy 2.0 with Alembic `0001_initial_schema.py`.
- **Milestone 0 Feasibility:** Smartphone authenticator feasibility and architectural verification.
