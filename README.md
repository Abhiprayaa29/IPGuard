# IPGuard — Secure Digital Asset Protection Platform

[![Milestone Status](https://img.shields.io/badge/Status-M0--M4%20Verified%20%26%20Frozen-brightgreen.svg)](#key-features)
[![Backend Tests](https://img.shields.io/badge/Backend%20Pytest-209%2F209%20PASS%20(100%25)-success.svg)](#testing)
[![Frontend Build](https://img.shields.io/badge/Frontend%20Build-Vite%20%2F%20React%2019%20PASS-success.svg)](#testing)
[![Browser Acceptance](https://img.shields.io/badge/Browser%20Acceptance-Playwright%20PASS-success.svg)](#screenshots--visual-showcase)
[![Python](https://img.shields.io/badge/Python-3.13.2-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.3-61dafb.svg)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.11-336791.svg)](https://www.postgresql.org/)
[![Android SDK](https://img.shields.io/badge/Android%20API-28--36-orange.svg)](mobile-authenticator/)
[![Cryptography](https://img.shields.io/badge/Ciphers-XChaCha20--Poly1305%20%7C%20Ed25519%20%7C%20ECDSA%20P--256-blueviolet.svg)](#security-architecture)

> **IPGuard** is an end-to-end digital asset protection platform that unifies **hardware-bound mobile authentication**, **authenticated zero-knowledge file encryption**, and **tamper-evident cryptographic steganography**.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features & Milestone Implementation](#key-features--milestone-implementation)
3. [System Architecture](#system-architecture)
4. [Technology Stack](#technology-stack)
5. [System Workflow](#system-workflow)
6. [Screenshots & Visual Showcase](#screenshots--visual-showcase)
7. [Getting Started & Installation](#getting-started--installation)
8. [Testing & Quality Verification](#testing--quality-verification)
9. [Security Architecture & Cryptographic Design](#security-architecture--cryptographic-design)
10. [Known Limitations](#known-limitations)
11. [Future Roadmap](#future-roadmap)
12. [Project Documentation Links](#project-documentation-links)
13. [License & Usage](#license--usage)

---

## Project Overview

### The Problem
High-value digital media, intellectual property (IP), source code archives, CAD blueprints, and sensitive documents face critical vulnerabilities when shared or stored in centralized systems:
1. **Credential Theft & Phishing:** Traditional passwords and SMS/email 2FA tokens can be intercepted or relayed via reverse proxies.
2. **Data-at-Rest Exposure:** Plaintext or weakly encrypted cloud storage exposes original master files to unauthorized server administrators or disk exfiltration.
3. **Attribution Loss & Watermark Removal:** Traditional visible watermarks are trivial to crop or remove via generative inpainting tools, while EXIF metadata is routinely stripped during web transmission.
4. **Undetected File Tampering:** Organizations lack verifiable mechanisms to prove whether a distributed asset has been altered, forged, or compromised.

### The IPGuard Solution
IPGuard establishes a defense-in-depth security model across three synchronized layers:
* **Hardware-Bound Identity (M2):** Eliminates static passwords. User actions and console access require cryptographic challenge signatures generated inside the **Android Keystore (TEE / StrongBox)** using **ECDSA NIST P-256** keys via dynamic QR codes.
* **Authenticated Storage Isolation (M3):** Digital assets are encrypted prior to disk write using **XChaCha20-Poly1305 AEAD** with 24-byte CSPRNG nonces and per-device **HKDF-SHA256** key derivation.
* **Invisible Cryptographic Watermarking (M4):** Digital proofs of authorship and license metadata are embedded directly into the 1-bit Least Significant Bits (LSB) of RGB pixel channels in PNG images. Every embedded watermark carries an `IPGW` binary frame signed with **Ed25519 (256-bit)** and checksummed with **SHA-256**, while all lifecycle operations are appended to an immutable **Audit Hash Chain**.

---

## Key Features & Milestone Implementation

### Milestone 0 — Smartphone Authenticator Feasibility (VERIFIED)
- Evaluated and documented the technical feasibility of mobile hardware security.
- Specified non-exportable Android Keystore key generation, CameraX barcode vision pipelines, and HTTPS challenge-response workflows.

### Milestone 1 — Foundation & Security Infrastructure (VERIFIED)
- **Asynchronous FastAPI Core:** Production-ready Python 3.13 backend gateway.
- **Fail-Closed Configuration:** Centralized Pydantic settings enforcing strict production key requirements.
- **Safe Error Envelopes:** Standardized JSON error responses masking internal database stack traces.
- **PostgreSQL 17 Integration:** Managed schema evolution via Alembic migrations (0001–0006 baseline).

### Milestone 2 — Hardware Device Authentication (VERIFIED)
- **Android Authenticator Companion:** Native Kotlin app running on Android API 28–36 (Jetpack Compose).
- **Hardware-Isolated ECDSA P-256:** Cryptographic private keys generated inside Android Keystore (`privateKey.encoded == null`).
- **Dynamic Web QR Authentication:** Ephemeral session challenges (60s TTL) with Anti-QR Jacking browser secrets (SEC-02).
- **One-Time Device Enrollment:** Enforces strict hardware binding via PostgreSQL row-level locks (`SELECT FOR UPDATE`), rejecting duplicate registrations.
- *(Note: Native Face Authentication via Android `BiometricPrompt` is a planned future enhancement).*

### Milestone 3 — Authenticated Digital Asset Vault (VERIFIED)
- **True XChaCha20-Poly1305 AEAD:** Symmetric encryption using 192-bit (24-byte) CSPRNG nonces and 128-bit Poly1305 MAC tags.
- **HKDF-SHA256 Key Derivation:** Deterministic per-device cryptographic isolation (`v1|device_id|asset_id`).
- **In-Memory Streaming Decryption:** Endpoint `GET /api/v1/assets/{id}/download` decrypts ciphertexts on-the-fly in memory, preventing plaintext writes to server disks.
- **Secure Notes Vault:** AES-256-GCM encrypted personal notes with hardware device ownership checks.

### Milestone 4 — Steganography & Digital Watermarking (VERIFIED)
- **PNG LSB Embedding Engine:** 1-bit per RGB channel spatial embedding preserving RGBA transparency.
- **Binary Framing (`IPGW` v1):** 170-byte fixed header containing magic bytes, Watermark UUID, Source Asset UUID, Derivative UUID, payload length, and SHA-256 digest.
- **Ed25519 Digital Signing:** Domain-separated 256-bit Edwards-curve digital signatures proving attribution.
- **Derivative Asset Lineage:** Database schema associating derivatives to original masters (`source_asset_id`), enforcing delete cascade protection.
- **Append-Only Audit Hash Chain:** Rolling SHA-256 hashes linking sequential audit events (`AuditEvent`) in PostgreSQL.
- **Fail-Closed Extraction:** Watermark payloads are strictly withheld (HTTP 409 Conflict) if pixel tampering or signature invalidity is detected.
- **Web Console Workflow:** Interactive UI in React 19 for upload, watermark configuration, embedding, downloading, verification, and payload extraction.

---

## System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer ["Client & Interface Layer"]
        WC["React 19 Web Console<br/>(Vite / Tailwind / TypeScript)"]
        MA["Android Authenticator<br/>(Kotlin / CameraX / Compose)"]
    end

    subgraph SecurityBoundary ["Hardware Security Module"]
        KS["Android Keystore<br/>(TEE / StrongBox)"]
        ECDSA["ECDSA NIST P-256<br/>(Non-Exportable Key)"]
        KS --- ECDSA
    end

    subgraph Gateway ["FastAPI Gateway & Core Engine"]
        API["FastAPI REST Router<br/>(app.api.routes)"]
        AUTH["Auth & Session Controller<br/>(Bearer Token / Origin Check)"]
        VAULT["Asset Vault Orchestrator<br/>(app.services.assets)"]
        STEGO["Steganography Engine<br/>(app.services.png_steganography)"]
        AUDIT["Audit Chain Service<br/>(app.services.audit_chain)"]
    end

    subgraph StorageLayer ["Encrypted Storage & Database"]
        PG[("PostgreSQL 17.11 DB<br/>- devices & auth_sessions<br/>- assets lineage<br/>- audit_events hash chain")]
        DISK[("Physical Disk Storage<br/>(backend/storage/)<br/>XChaCha20-Poly1305 Ciphertexts")]
    end

    WC -- "1. Request Session Challenge" --> API
    API -- "2. Dynamic QR (60s TTL)" --> WC
    MA -- "3. Scan QR Code" --> WC
    MA -- "4. Sign Nonce via Keystore" --> KS
    MA -- "5. Submit ECDSA Signature" --> API
    API -- "6. Approve Session" --> PG
    WC -- "7. Authenticated Bearer Requests" --> API

    API --> AUTH
    AUTH --> VAULT
    VAULT -- "Encr/Decr (HKDF-SHA256)" --> DISK
    VAULT --> STEGO
    STEGO -- "Ed25519 Sign & SHA-256 LSB" --> DISK
    STEGO --> AUDIT
    AUDIT -- "Rolling SHA-256 Prev-Hash" --> PG
```

---

## Technology Stack

| Domain | Technologies |
| :--- | :--- |
| **Frontend Web Console** | React 19.3, Vite 8.3, TypeScript 7.0, Tailwind CSS 4.3, Lucide React, Axios |
| **Backend Core API** | Python 3.13.2, FastAPI 0.115, Starlette, Uvicorn, Pydantic v2 |
| **Database & Migrations**| PostgreSQL 17.11, SQLAlchemy 2.0, Psycopg 3, Alembic (Migrations 0001–0009) |
| **Cryptographic Suite** | PyCA/Cryptography (Ed25519, XChaCha20-Poly1305, HKDF, SHA-256, ECDSA NIST P-256) |
| **Image Processing** | Pillow (PIL Fork) 11.x (8-bit truecolor RGB/RGBA raster manipulation) |
| **Mobile Hardware Client**| Android SDK (API 28–36), Kotlin, Jetpack Compose, Android Keystore, CameraX, ZXing |
| **Testing & Automation** | Pytest 9.2, Playwright Chromium, AnyIO |

---

## System Workflow

```
[ Master PNG Upload ]
         │
         ▼
[ In-Memory Preview & Metadata ] ── (XChaCha20-Poly1305 Encrypted to Vault)
         │
         ▼
[ Configure Watermark ] ─────────── (Auto-bind Hardware ID, Ed25519 Key ID, SHA-256 Digest)
         │                          (Custom: Copyright, License, Statement, Description)
         ▼
[ LSB Embedding Engine ] ────────── (1-bit LSB in row-major RGB channels)
         │                          (IPGW v1 Binary Framing + Ed25519 Digital Signature)
         ▼
[ Encrypted Derivative Created ] ── (Lineage: source_asset_id linked; audit chain appended)
         │
    ┌────┴───────────────────────────┬──────────────────────────────┐
    ▼                                ▼                              ▼
[ Download Watermarked PNG ]   [ Verify Watermark ]          [ Extract Metadata ]
  (Decrypted byte-for-byte;      (Live validation of           (Structured JSON & text;
   valid truecolor PNG file)      Ed25519 & SHA-256 digest)     strictly fail-closed on tamper)
```

---

## Screenshots & Visual Showcase

All screenshots were captured directly during automated Playwright browser acceptance testing on Chromium (1366x860) against live services:

| Asset Vault Overview | Uploaded Master Image |
| :---: | :---: |
| ![Asset Vault](docs/screenshots/m4_acceptance/01_asset_vault_initial.png) | ![Master Uploaded](docs/screenshots/m4_acceptance/02_asset_uploaded.png) |
| *Hardware-authenticated console with active device status.* | *Original master PNG uploaded and encrypted with AEAD.* |

| Watermark Configuration | Embedding Success State |
| :---: | :---: |
| ![Watermark Configuration](docs/screenshots/m4_acceptance/03_watermark_config_modal.png) | ![Embedding Success](docs/screenshots/m4_acceptance/04_embed_success.png) |
| *Auto-bound cryptographic parameters and custom metadata form.* | *Derivative asset created with verified Ed25519 signature.* |

| Derivative Vault Listing | Cryptographic Verification |
| :---: | :---: |
| ![Vault with Derivative](docs/screenshots/m4_acceptance/05_vault_with_derivative.png) | ![Verify Watermark](docs/screenshots/m4_acceptance/06_verify_success_modal.png) |
| *Derivative record linked to parent (`from 5dfe779a...`).* | *Live validation of Ed25519 signature and SHA-256 integrity.* |

| Extracted Metadata Modal | Technical Inspect Panel |
| :---: | :---: |
| ![Payload Extraction](docs/screenshots/m4_acceptance/07_extract_payload_modal.png) | ![Asset Inspection](docs/screenshots/m4_acceptance/08_derivative_inspect_modal.png) |
| *Structured metadata cards and raw JSON decoded from pixels.* | *Decrypted thumbnail preview and technical cipher specifications.* |

---

## Getting Started & Installation

### Prerequisites
* **Python:** 3.13.x (or `>= 3.11`)
* **Node.js:** `>= 22.12.0` (with npm 10+)
* **PostgreSQL:** `17.x` (17.11 recommended)
* **Android Studio:** Ladybug or newer (for mobile authenticator)

### 1. Database Setup
Ensure PostgreSQL is active and create the database user:
```sql
CREATE USER ipguard WITH PASSWORD 'your_secure_password';
CREATE DATABASE ipguard OWNER ipguard;
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and supply your DATABASE_URL and local dev keys

# Run database migrations (0001 through 0009)
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```bash
cd ../frontend
npm install
cp .env.example .env
npm run dev
```
Web Console will be accessible at: `http://127.0.0.1:5173`

### 4. Android Authenticator Setup
1. Open the `mobile-authenticator/` directory in Android Studio.
2. Build and deploy the debug APK onto your physical Android device.
3. Use ADB reverse proxy if testing over USB:
   ```bash
   adb reverse tcp:8000 tcp:8000
   ```

---

## Testing & Quality Verification

IPGuard enforces strict verification across all layers:

### 1. Backend Pytest Test Suite
```bash
cd backend
pytest -v
```
* **Status:** **209 passed, 0 failed, 0 skipped** across all M1, M2, M3, and M4 modules.
* **Concurrency:** Includes `test_audit_chain_postgres.py` row-lock serialization across 24 concurrent threads.

### 2. Frontend Static Check & Production Build
```bash
cd frontend
npm run typecheck    # TypeScript strict mode: 0 errors
npm run build        # Production bundle compiled cleanly via Vite
```

### 3. Automated Real Browser Acceptance Testing (Playwright)
```bash
cd backend
python ../scripts/m4_browser_acceptance_test.py
```
* **Status:** 14-step automated user journey passed with **0 browser errors** and **0 failed network requests**.
* **Distortion Verification:** $\text{MSE} = 0.009471$, $\text{PSNR} = 68.37\text{ dB}$ *(imperceptible watermark quality on 256x256 test sample)*.

---

## Security Architecture & Cryptographic Design

| Cryptographic Primitive | Role in IPGuard | Implementation Details |
| :--- | :--- | :--- |
| **XChaCha20-Poly1305** | Authenticated Storage Encryption | 192-bit CSPRNG nonces, 128-bit Poly1305 MAC tags. Protects all file ciphertexts at rest. |
| **AES-256-GCM** | Secure Notes Encryption | 96-bit random IVs, 128-bit authentication tags. Encrypts personal notes records. |
| **HKDF-SHA256** | Key Derivation Pipeline | Derives deterministic per-device subkeys from master keys, ensuring tenant isolation. |
| **SHA-256** | Integrity Hashing & Checksums | Computes ciphertext baselines, payload integrity hashes, and rolling audit chain event hashes. |
| **Ed25519 (256-bit)** | Steganographic Attribution | Asymmetric digital signature proving watermark authenticity under the trusted key. |
| **ECDSA NIST P-256** | Hardware Device Authentication | Non-exportable keys in Android Keystore used to sign out-of-band login challenges. |
| **Spatial LSB Framing** | Invisible Watermarking | Embeds 170-byte fixed `IPGW` v1 binary frames into 1-bit LSBs of RGB pixel channels. |
| **Audit Hash Chain** | Non-Repudiation Audit Ledger | Sequential SHA-256 event linking ($\text{EventHash}_n = \text{SHA-256}(\text{EventHash}_{n-1} \parallel \dots)$). |

---

## Known Limitations

1. **Spatial LSB Fragility:** Spatial LSB steganography is fragile by design. Resizing, cropping, filtering, or lossy re-compression (JPEG/WebP) will alter pixel bits and intentionally invalidate the Ed25519 signature and SHA-256 checksum. It is not robust watermarking.
2. **Format Scope:** LSB steganography is strictly restricted to 8-bit truecolor RGB/RGBA PNG images.
3. **Hardware Device Validation:** Automated regression testing utilizes cryptographic test fixtures; physical Android device acceptance requires manual QR scanning on physical hardware.
4. **Legal Scope:** An Ed25519 digital signature establishes mathematical authenticity under the signing key; it does not constitute an independent legal copyright certificate without registered legal title.
5. **Native Face Authentication:** Biometric verification via Android `BiometricPrompt` is documented as a planned future proposal (`PLANNED`).

---

## Future Roadmap

### Milestone 5 — Blockchain-Based Immutable Audit Logging (PLANNED)
* **Merkle Tree Aggregation:** Periodic batching of `audit_events` into cryptographic Merkle Trees.
* **Smart Contract Anchoring:** Publishing Merkle roots to public or consortium EVM blockchains (Ethereum, Polygon, or Arbitrum) for decentralized immutability.
* **Public Verifier Portal:** Web tool allowing third parties to verify asset hashes against blockchain checkpoints without requiring server access.

### Future Android Client Enhancements (PLANNED)
* **Native BiometricPrompt Binding:** Class 3 biometrics gating Keystore key usage directly before signing.
* **Remote Attestation:** Keymaster / Keymint certificate chain verification to validate hardware TEE integrity against Google servers.

---

## Project Documentation Links

For in-depth architectural, test, and operational details, refer to:
* [`docs/FINAL_PROJECT_REPORT.md`](docs/FINAL_PROJECT_REPORT.md) — Comprehensive master report (Formal Indonesian).
* [`docs/FINAL_ACCEPTANCE_MATRIX.md`](docs/FINAL_ACCEPTANCE_MATRIX.md) — Feature status matrix across M1–M4.
* [`docs/FINAL_EVIDENCE_INDEX.md`](docs/FINAL_EVIDENCE_INDEX.md) — Navigable evidence and test artifact index.
* [`docs/FINAL_HANDOVER.md`](docs/FINAL_HANDOVER.md) — Operational handover and deployment guide.
* [`docs/M4_BROWSER_ACCEPTANCE_REPORT.md`](docs/M4_BROWSER_ACCEPTANCE_REPORT.md) — Real browser test logs and metrics.
* [`docs/png-lsb-steganography.md`](docs/png-lsb-steganography.md) — Byte-level `IPGW` framing specification.

---

## License & Usage

Copyright © 2026 IPGuard Project. All rights reserved.  
Proprietary academic and technical evaluation codebase.
