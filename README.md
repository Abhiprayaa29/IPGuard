# IPGuard — Secure Digital Asset Protection

[![Milestone](https://img.shields.io/badge/Milestone-M3--Complete-brightgreen.svg)](docs/M3_ALIZA_ASSET_VAULT_INTEGRATION.md)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-114%2F114%20PASS-success.svg)](backend/tests/)
[![Android Tests](https://img.shields.io/badge/Android%20Tests-59%2F59%20PASS-success.svg)](mobile-authenticator/app/src/test/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-22%20LTS-green.svg)](https://nodejs.org/)
[![Android API](https://img.shields.io/badge/Android%20API-28--36-orange.svg)](docs/ANDROID_COMPATIBILITY.md)
[![Repository Visibility](https://img.shields.io/badge/Visibility-Private-red.svg)](#24-license-and-project-usage-information)

IPGuard is a secure digital asset protection platform designed to store, manage, and cryptographically protect sensitive digital files and intellectual property. IPGuard enforces a **Zero-Trust hardware-backed device binding architecture**, where a companion native Android Authenticator app functions as a hardware security key. Sensitive web console operations and logins require out-of-band cryptographic challenge signatures created inside the Android Keystore (TEE / StrongBox).

---

## Table of Contents

1. [Project Title and Introduction](#1-project-title-and-introduction)
2. [Project Purpose and Problem Statement](#2-project-purpose-and-problem-statement)
3. [Key Features & Implementation Status](#3-key-features--implementation-status)
4. [Architecture Overview](#4-architecture-overview)
5. [Device Enrollment & Authentication Lifecycle](#5-device-enrollment--authentication-lifecycle)
6. [Technology Stack](#6-technology-stack)
7. [Repository Structure](#7-repository-structure)
8. [Milestone Roadmap](#8-milestone-roadmap)
9. [Prerequisites](#9-prerequisites)
10. [Installation Guide](#10-installation-guide)
11. [Environment Configuration](#11-environment-configuration)
12. [PostgreSQL Setup & Migrations](#12-postgresql-setup--migrations)
13. [Backend Setup & Execution](#13-backend-setup--execution)
14. [Frontend Setup & Execution](#14-frontend-setup--execution)
15. [Android Setup & Execution](#15-android-setup--execution)
16. [Physical Android Device Connection (ADB Reverse)](#16-physical-android-device-connection-adb-reverse)
17. [Running Automated Tests](#17-running-automated-tests)
18. [Building the Application](#18-building-the-application)
19. [API Documentation](#19-api-documentation)
20. [Security Architecture & Threat Model](#20-security-architecture--threat-model)
21. [Known Limitations & Architectural Boundaries](#21-known-limitations--architectural-boundaries)
22. [Collaboration Guide](#22-collaboration-guide)
23. [Contribution Guide](#23-contribution-guide)
24. [Security Reporting](#24-security-reporting)
25. [License and Project Usage Information](#25-license-and-project-usage-information)

---

## 1. Project Title and Introduction

**IPGuard — Secure Digital Asset Protection**

IPGuard bridges modern web application convenience with the rigorous physical security guarantees of mobile hardware security modules. It operates across three interconnected subsystems:
- **Web Management Console:** React 19 + TypeScript single-page application.
- **Cryptographic Backend API:** Asynchronous Python 3.13 FastAPI gateway with PostgreSQL 17.
- **Mobile Hardware Authenticator:** Native Android application (Kotlin + Jetpack Compose) running on Android API 28–36.

---

## 2. Project Purpose and Problem Statement

### Problem Statement
Digital assets (proprietary source code, CAD blueprints, sensitive research, high-value media, and corporate records) face severe vulnerabilities when protected solely by traditional passwords or SMS/TOTP two-factor authentication:
1. **Credential Stuffing & Phishing:** Software tokens can be intercepted or relayed via reverse proxies.
2. **Key Exfiltration:** Cryptographic private keys stored in browser localStorage or software files are vulnerable to malware extraction.
3. **QR-Jacking & Man-in-the-Middle:** Generic QR login flows often fail to bind the scanning session to the initiating browser origin.

### IPGuard Solution
IPGuard establishes a **Zero-Trust Device-Bound Identity**:
- Cryptographic private signing keys are generated inside the Android hardware security module (TEE / StrongBox) and marked **strictly non-exportable**.
- Login challenges are delivered via dynamic QR codes with 60-second TTL and strict origin binding (RFC 6454).
- Anti QR-jacking architecture (SEC-02) ensures browser access tokens are never transmitted inside the QR code.
- Out-of-band verification requires user biometric consent (`BIOMETRIC_STRONG` or secure PIN/pattern).

---

## 3. Key Features & Implementation Status

To ensure complete engineering transparency, features are categorized by their actual implementation state:

### Currently Implemented & Verified
- [x] **Hardware Keystore Key Generation (M2.3-A):** NIST P-256 (`secp256r1`) key pair generation in Android Keystore with non-exportable private keys (`privateKey.encoded == null`).
- [x] **Adaptive Biometric & Credential Signing (M2.3-B):** `BiometricPrompt` with `CryptoObject` supporting Class 3 biometrics and hardware Gatekeeper PIN/pattern fallback.
- [x] **Vision Pipeline & QR Decoding (M2.0–M2.2):** CameraX and Google ML Kit on-device barcode parsing with zero external network transmission.
- [x] **Backend Device Registry & Verification Engine (M2.4-B):** PostgreSQL storage, pessimistic row-level locking (`SELECT ... FOR UPDATE` SEC-01), and ASN.1 DER ECDSA signature verification.
- [x] **Dynamic Web QR Authentication (M2.4-C):** Dynamic QR generation, 60s countdown timer, auto-refresh, and Anti QR-jacking browser secret binding (SEC-02).
- [x] **Mobile Networking & Challenge Approval (M2.4-D):** OkHttp 4.12.0 client with connection lifecycle management, approval UI, and physical end-to-end verification.
- [x] **One-Time Device Enrollment & Sign-In Only Lifecycle (M2 Hardening):** Hardware authenticators are enrolled once (`ACTIVE`), subsequent logins strictly perform hardware challenge-response (`Sign In`), duplicate enrollments are rejected with HTTP 409 `DEVICE_ALREADY_REGISTERED` via pessimistic row-level locking, and administrative unregistration decouples the device without deleting records.
- [x] **Secure Notes Digital Vault (M3 Core):** Zero-Knowledge encrypted personal notes using HKDF-SHA256 key derivation, AES-256-GCM authenticated encryption (random 96-bit IV, 128-bit authentication tag), educational Vigenère transformation layer, and strict owner isolation bound to the verified M2 hardware `device_id`.
- [x] **Digital Asset Vault & File Protection (M3 Core):** True XChaCha20-Poly1305 AEAD encrypted file storage (`PyNaCl` / libsodium C-bindings), 24-byte CSPRNG nonces, 16-byte Poly1305 authentication tags, per-device HKDF-SHA256 key isolation, canonical AAD context binding (`v1|device_id|asset_id`), atomic temporary-to-permanent file writes (`.tmp` to permanent), and magic-byte signature validation blocking dangerous executable formats.
- [x] **Full-Stack Asset Vault Console (M3 Core):** React 19 single-page console with drag-and-drop file upload, upload progress tracking, category filtering (Images, Docs, Archives), in-memory decrypted image preview, original binary download stream with automatic URL revocation, in-place rename dialog, permanent delete confirmation, and persistent `sessionStorage` hardware session binding.
- [x] **Browser End-to-End Verification (M3 Core):** Comprehensive browser testing of Asset Vault workflows (upload, in-memory preview, in-place rename, oversized file >50MB rejection, PDF upload, dynamic filtering by Image/Doc category, and cryptographic metadata inspection) using authenticated sessions authorized via M2 hardware authenticator.
- [x] **Fail-Closed Negative Security Enforcement:** Rejection of un-enrolled devices, expired challenges, unauthorized cross-device asset access, corrupted ciphertexts, and invalid origin headers.

### Planned Features (Future Milestones)

#### Milestone 4 — Integrity & Advanced Protection (PLANNED)
- [ ] **Asset Integrity Monitoring:** Periodic SHA-256 asset integrity verification, detection of unauthorized file modifications, integrity status reporting, and automated tamper detection.
- [ ] **Audit Hash Chain:** Append-only cryptographic audit event ledger with SHA-256 linked event hashes (`prev_hash` linkage), audit chain verification, and tamper-evident audit history (tamper-evident, not tamper-proof).
- [ ] **Steganographic Watermarking:** PNG LSB (Least Significant Bit) steganography for watermark embedding, watermark extraction, extracted watermark validation, and detection of damaged or modified embedded watermarks.
- [ ] **Hardware Attestation:** Remote Keymaster / Keymint certificate chain verification for Android Keystore authenticators.

#### Milestone 5 — Advanced Integration, Blockchain Exploration & Release (PLANNED)
- [ ] **Multi-Tenant Access Control & RBAC:** Multi-tenant user accounts (`users` table), role-based permissions, and enterprise organization mapping.
- [ ] **Cross-Device Identity & Key Lifecycle:** Multi-device bindings per user context, cryptographic key rollover, and distributed revocation lists.
- [ ] **Blockchain Exploration (Optional / Future Extension):** Public or consortium distributed ledger anchoring for cryptographic audit chain roots and timestamp proofs; strict architectural boundary ensuring zero plaintext assets or private keys are ever stored on-chain (strictly separated from the local audit hash chain).
- [ ] **Production Hardening & Verification:** End-to-end multi-tenant integration testing, third-party security penetration testing, backup and disaster recovery validation, container packaging, and cloud production deployment.

---

## 4. Architecture Overview

```text
+-------------------------------------------------------------------------+
|                           IPGuard Architecture                          |
+-------------------------------------------------------------------------+

  1. WEB MANAGEMENT CONSOLE (Browser)
     [React 19 + TypeScript + Vite + Tailwind CSS]
     - Renders dynamic QR codes with 60-second TTL & SHA-256 channel tokens
     - Polls authentication session state securely (SEC-02 browser binding)
     - Port: http://localhost:5173
                   |
                   | REST API & Polling (SEC-02)
                   v
  2. REST API BACKEND & STORAGE
     [Python 3.13 + FastAPI + PostgreSQL 17 + SQLAlchemy + Alembic]
     - Pessimistic Row-Level Locking (SELECT FOR UPDATE - SEC-01)
     - Origin Whitelist Enforcement (SEC-03)
     - Cryptographic Verifier: NIST P-256 ECDSA (SHA256withECDSA)
     - Session Engine: Registration, Challenge generation, Verification
     - Port: http://localhost:8000 (Swagger: /docs)
                   ^
                   | Out-of-Band Physical Scanning & REST Verification
                   | (via ADB reverse tcp:8000 tcp:8000 on physical USB)
                   |
  3. ANDROID NATIVE AUTHENTICATOR
     [Kotlin + Jetpack Compose + Android Keystore (minSdk 28, targetSdk 36)]
     - Google ML Kit Barcode Scanner + CameraX Vision Pipeline
     - Non-Exportable Private Key inside Hardware TEE / StrongBox (ECDSA P-256)
     - Adaptive BiometricPrompt with CryptoObject (Class 3 Strong Biometric or PIN/Pattern)
     - Resilient OkHttp Client with explicit connection lifecycle control
```

---

## 5. Device Enrollment & Authentication Lifecycle

IPGuard enforces the hardware authenticator security principle:
> **A device is registered once. After successful registration, it can only sign in.**

The companion Android smartphone acts as a **dedicated physical hardware security token**. Private keys are permanently bound to the device's hardware security module (TEE / StrongBox) and never cross the process or network boundary.

```mermaid
flowchart TD
    subgraph Enrollment ["1. First-Time Enrollment"]
        E1[Install Android Authenticator] --> E2[Web: 'Register Device' Tab]
        E2 --> E3[Scan ENROLLMENT QR Code]
        E3 --> E4[Generate Keystore ECDSA P-256 Key]
        E4 --> E5[Biometric / PIN User Authorization]
        E5 --> E6[Sign Canonical Payload & Submit Public Key]
        E6 --> E7[Backend PostgreSQL: Status ACTIVE]
    end

    subgraph Authentication ["2. Subsequent Hardware Sign-In"]
        A1[Enrolled Phone Status: ACTIVE] --> A2[Web: 'Mobile Sign-In' Tab]
        A2 --> A3[Scan AUTHENTICATION QR Code]
        A3 --> A4[Authorize with Existing Hardware Key]
        A4 --> A5[Verify Signature & Grant Session]
        A5 --> A6[Unlock Web Console & M3 Vault]
    end

    subgraph Management ["3. Device Lifecycle Management"]
        M1[Web: Device Management] --> M2{Administrative Action}
        M2 -- Revoke Access --> M3[Status: REVOKED<br>Registration Slot Retained]
        M2 -- Unregister Device --> M4[Status: UNREGISTERED<br>Releases Slot, Preserves Notes]
        M4 --> E1
    end
```

### First-Time Enrollment Flow
1. **Device Preparation:** Install the IPGuard Authenticator on an Android device running API 28+ (tested through API 36).
2. **Challenge Creation:** On the Web Console, select the **Register Device** tab to create an `ENROLLMENT` session challenge with a strict 60-second TTL.
3. **Presence Gate & QR Scan:** In the mobile app, tap **Set up this device**, pass the front-camera presence check, and scan the QR code.
4. **Hardware Key Initialization:** If the Android Keystore does not already hold the signing key (`ipguard_device_signing_v1`), the app invokes `ensureSigningKey()` to generate a non-exportable NIST P-256 (`secp256r1`) key pair inside the TEE/StrongBox.
5. **Biometric Consent:** The user authorizes registration via `BiometricPrompt` using Class 3 strong biometrics (fingerprint) or the device's secure lock screen credential (PIN, pattern, password).
6. **Backend Verification:** The Android client submits the canonical signature and raw X.509 SubjectPublicKeyInfo DER public key to `POST /api/v1/auth/devices/register`.
7. **Active State:** The backend cryptographically validates the signature, ensures no duplicate registration exists, records the device with status **`ACTIVE`**, and atomically approves the web session.

### Subsequent Sign In Flow
1. **Sign-In Only Lock:** Once enrolled, the Android app switches to trusted authenticator mode, locking out registration flows and offering **Sign In (Scan QR)**.
2. **Challenge Acquisition:** The user initiates web login via the **Mobile Sign-In** tab, which displays an `AUTHENTICATION` session QR code.
3. **Out-of-Band Signature:** The user scans the QR code. The app retrieves the canonical challenge bytes and requests hardware authorization via `BiometricPrompt`.
4. **Existing Key Policy:** The challenge is signed strictly using the pre-existing, enrolled hardware signing key. The app **never generates a replacement key automatically** during sign-in.
5. **Session Authorization:** Backend verifies the signature against the registered public key via PostgreSQL pessimistic row-level locking (`SELECT ... FOR UPDATE`), approving the web session and issuing the session token.

### Device Management (Revoke Access vs Unregister Device)
Administrative controls on the Web Console (`/devices`) decouple authentication access from registration slot ownership:
- **Revoke Access (`POST /api/v1/auth/devices/{device_id}/revoke`):**
  Immediately terminates all active sessions and sets device status to `REVOKED`. The registration slot **remains locked** to prevent unauthorized re-registration from that device identity.
- **Unregister Device (`POST /api/v1/auth/devices/{device_id}/unregister`):**
  Sets `unregistered_at = now()`, marks registration status as `UNREGISTERED`, invalidates active sessions, and **frees the registration slot**. This allows a replacement device or the same device to undergo clean enrollment.
- **Data & Secure Notes Preservation:**
  Neither action deletes the database `Device` record or the associated Milestone 3 **Secure Notes**. Notes created by the device remain safely isolated under their `owner_id` (`device_id`). If the same device re-enrolls, its existing identity is reactivated, preserving note ownership seamlessly.

### Security Notes
- **Hardware Isolation:** Private signing keys reside exclusively within the Android hardware security module (TEE / StrongBox) and can never be extracted (`privateKey.encoded == null`).
- **Public Key Verification:** Only public keys (X.509 DER) are sent to the backend for signature verification.
- **Backend as Source of Truth:** Device registration and access states are authoritatively verified and enforced by the PostgreSQL backend using pessimistic locking. Local client states in SharedPreferences serve purely for UI responsiveness and synchronization.
- **Non-Security Identifiers:** Device IDs (e.g., client UUIDs or Android IDs) are non-security identifiers; the cryptographic ECDSA signature verified against the enrolled public key is the sole authoritative proof of hardware identity.

---

## 6. Technology Stack

| Layer | Component | Version / Specification | Role |
|---|---|---|---|
| **Frontend** | React | 19.3.1 | Core UI framework |
| | TypeScript | 7.0.2 | Strict static typing |
| | Vite | 8.3.6 | Frontend bundler & dev server |
| | Tailwind CSS | 4.3.4 | Utility-first CSS engine |
| **Backend** | Python | 3.13 | Primary server runtime |
| | FastAPI | 0.115+ | High-performance async API |
| | SQLAlchemy | 2.x | ORM & database query engine |
| | Alembic | 1.14+ | Schema migration framework |
| | Cryptography | 44.x | ECDSA P-256 verification |
| **Database** | PostgreSQL | 17 | Relational persistence & row locking |
| **Mobile** | Kotlin | 2.2.21 | Native Android development |
| | Jetpack Compose | BOM 2025.12.01 | Declarative mobile UI |
| | Android Keystore | API 28–36 | Hardware-backed key generation |
| | CameraX | 1.6.2 | Vision pipeline management |
| | Google ML Kit | 16.1.7 / 17.3.0 | On-device face & barcode ML |
| | OkHttp | 4.12.0 | Asynchronous HTTP client |
| **DevOps** | GitHub Actions | Ubuntu Latest | Continuous integration quality gate |

---

## 7. Repository Structure

```text
IPGuard/
├── .github/                        # CI workflows, PR & Issue templates
│   ├── workflows/ci.yml            # Automated CI quality gate
│   ├── ISSUE_TEMPLATE/             # Bug report & feature request templates
│   └── PULL_REQUEST_TEMPLATE.md    # Pull Request submission checklist
├── backend/                        # FastAPI REST API & Crypto Verifier
│   ├── alembic.ini                 # Alembic migration configuration
│   ├── requirements.txt            # Python dependencies
│   ├── app/                        # Application source code
│   │   ├── api/routes/             # Endpoint controllers (auth, health, system)
│   │   ├── core/                   # Settings, origin validator, errors
│   │   ├── db/migrations/          # Alembic version files
│   │   ├── models/                 # SQLAlchemy ORM models (devices, sessions)
│   │   └── services/               # Cryptography verifier, auth session service
│   └── tests/                      # Pytest test suite (65 test cases)
├── frontend/                       # React 19 + TypeScript Web Console
│   ├── src/
│   │   ├── components/auth/        # QR cards, countdown timers, displays
│   │   ├── hooks/                  # Custom hooks (useQrAuth)
│   │   └── pages/auth/             # QR login & system status views
│   ├── package.json                # Dependencies and build scripts
│   └── vite.config.ts              # Vite bundler configuration
├── mobile-authenticator/           # Android Native Kotlin Authenticator
│   ├── app/
│   │   ├── build.gradle.kts        # Android build config (minSdk 28, targetSdk 36)
│   │   └── src/main/java/com/ipguard/authenticator/
│   │       ├── network/            # OkHttp client, DTOs, API service
│   │       ├── security/           # Keystore manager, signing policy
│   │       └── ui/                 # Jetpack Compose screens and navigation
│   └── build.gradle.kts            # Root Gradle configuration
├── docs/                           # Architecture, security & audit reports
│   ├── ANDROID_COMPATIBILITY.md    # Cross-device compatibility specification
│   ├── COLLABORATION_GUIDE.md      # Collaborator onboarding & roadmap guide
│   ├── M2_ARCHITECTURE.md          # Milestone 2 system architecture
│   ├── M2.4_API_CONTRACT.md        # REST API endpoint contract
│   └── M2_MASTER_FINAL_AUDIT_REPORT.md # Master audit verification report
├── .env.example                    # Docker Compose environment template
├── CONTRIBUTING.md                 # Contribution & branching standards
├── docker-compose.yml              # Local PostgreSQL 17 container
├── README.md                       # Master documentation
└── SECURITY.md                     # Vulnerability disclosure policy
```

---

## 8. Milestone Roadmap

| Milestone | Focus Area | Status | Verification Summary / Objectives |
|---|---|:---:|---|
| **M1** | Foundation & Architecture | **COMPLETE** | React frontend, FastAPI backend, PostgreSQL 17, Alembic migrations, Pytest suite. |
| **M2** | Authentication & Device Security | **COMPLETE** | **M2.0–M2.3:** Keystore ECDSA P-256, BiometricPrompt + CryptoObject, CameraX/ML Kit.<br>**M2.4-B:** Backend device registry, session locking (SEC-01), origin validation (SEC-03).<br>**M2.4-C:** Web QR auth UI, countdown timer, anti QR-jacking channel binding (SEC-02).<br>**M2.4-D:** Android QR parsing, hardware signing, OkHttp integration.<br>**M2 Hardening:** One-Time Device Enrollment and Sign-In Only lifecycle (Physically Verified on Samsung A54 5G). |
| **M3** | Core Cryptography & Asset Protection | **COMPLETE** | **Digital Asset Vault:** True XChaCha20-Poly1305 AEAD encrypted file storage (`PyNaCl` / libsodium), 24-byte CSPRNG nonces, 16-byte Poly1305 auth tags, per-device HKDF-SHA256 key isolation, AAD context binding (`v1|device_id|asset_id`), atomic temporary-to-permanent file writes, and magic-byte signature validation.<br>**Secure Notes Vault:** AES-256-GCM + HKDF-SHA256 + Vigenère layer + M2 device-bound owner isolation.<br>**Full-Stack Console & E2E:** 100% verified via automated regression tests (114 backend tests) and browser E2E workflows authorized via physical Android hardware token (Samsung SM-A546E). |
| **M4** | Integrity & Advanced Protection | **PLANNED** | **Asset Integrity Monitoring:** Periodic SHA-256 asset digest auditing and unauthorized modification detection.<br>**Audit Hash Chain:** Immutable-style append-only SHA-256 linked event hashes creating a tamper-evident audit history.<br>**Steganographic Watermarking:** PNG LSB watermark embedding, extraction, validation, and damage detection. |
| **M5** | Advanced Integration, Blockchain Exploration & Release | **PLANNED** | **Access & Identity:** Multi-tenant access control (RBAC) and cross-device key lifecycle.<br>**Blockchain Exploration:** Optional public/consortium distributed ledger anchoring for audit chain roots and timestamp proofs (zero plaintext assets or keys on-chain).<br>**Release Readiness:** Penetration testing, backup/recovery validation, packaging, and production deployment. |

---

## 9. Prerequisites

Ensure your development environment meets the following specifications:
- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python:** Python 3.13 (or 3.11+) with virtual environment support.
- **Node.js:** Node.js 22 LTS or newer with npm.
- **Java Development Kit (JDK):** OpenJDK 17.
- **Android SDK:** API 28–36, Platform-tools (`adb`).
- **Database:** PostgreSQL 17 (native or Docker Desktop).

---

## 10. Installation Guide

```bash
# 1. Clone repository
git clone https://github.com/Abhiprayaa29/IPGuard.git
cd IPGuard

# 2. Initialize environment templates
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

---

## 11. Environment Configuration

IPGuard strictly separates development configuration from secrets. **Never commit real `.env` files.**

### Root `.env` (Docker Compose)
```dotenv
POSTGRES_DB=ipguard
POSTGRES_USER=ipguard
POSTGRES_PASSWORD=replace_with_a_strong_local_password
POSTGRES_PORT=5432
```

### Backend `.env` (`backend/.env`)
```dotenv
APP_NAME=IPGuard
APP_VERSION=1.0.0
APP_ENV=development
DATABASE_URL=postgresql+psycopg://ipguard:replace_with_a_strong_local_password@127.0.0.1:5432/ipguard
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEV_ADMIN_KEY=ipguard-dev-admin-secret-key
```

### Frontend `.env` (`frontend/.env`)
```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 12. PostgreSQL Setup & Migrations

1. Start database via Docker Compose or native PostgreSQL 17 service:
   ```bash
   docker-compose up -d
   ```
2. Apply database migrations using Alembic:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   alembic -c alembic.ini upgrade head
   ```

---

## 13. Backend Setup & Execution

Start the FastAPI application with Uvicorn:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 60
```
- **API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Health Endpoint:** `http://localhost:8000/api/v1/health`

---

## 14. Frontend Setup & Execution

Start the Vite development server:
```powershell
cd frontend
npm install
npm run dev
```
- **Web Console:** `http://localhost:5173`
- **QR Sign-In Page:** `http://localhost:5173/login`
- **Device Management:** `http://localhost:5173/devices`
- **Secure Notes Vault:** `http://localhost:5173/notes`
- **Digital Asset Vault:** `http://localhost:5173/assets`
- **System Status Dashboard:** `http://localhost:5173/system-status`

---

## 15. Android Setup & Execution

Build and install the Android Authenticator via Gradle:
```powershell
cd mobile-authenticator
.\gradlew.bat installDebug
adb shell am start -n com.ipguard.authenticator/.MainActivity
```

---

## 16. Physical Android Device Connection (ADB Reverse)

When testing with a physical Android device connected via USB, the mobile client must route traffic to the host computer's backend on port 8000.

Run the following command while your phone is connected with USB Debugging enabled:
```powershell
adb reverse tcp:8000 tcp:8000
```
Verify active tunnels:
```powershell
adb reverse --list
# Expected output: (reverse) tcp:8000 tcp:8000
```

> [!NOTE]
> Do NOT use `10.0.2.2` when testing on physical hardware. `10.0.2.2` is exclusively an alias for host loopback on the Android Emulator.

---

## 17. Running Automated Tests

IPGuard maintains strict test quality gates across all three subsystems:

### Backend Test Suite (Pytest)
```powershell
cd backend
python -m pytest -v
```
*Current result: 114 passed across 10 test suites (M1 + M2 + M3 Secure Notes + M3 Digital Asset Vault + Lifecycle suite).*

### Frontend Typecheck & Production Build
```powershell
cd frontend
npm run typecheck
npm run build
```
*Current result: 2,195 modules transformed with 0 errors.*

### Android Unit Tests
```powershell
cd mobile-authenticator
.\gradlew.bat testDebugUnitTest --no-daemon
```
*Current result: 59 unit tests passed across 10 test suites in 0.45s, 0 failures, 0 errors.*

---

## 18. Building the Application

### Frontend Production Bundle
```powershell
cd frontend && npm run build
```
Outputs static assets into `frontend/dist/`.

### Android Debug APK
```powershell
cd mobile-authenticator && .\gradlew.bat assembleDebug --no-daemon
```
Outputs APK into `mobile-authenticator/app/build/outputs/apk/debug/app-debug.apk`.

---

## 19. API Documentation

Interactive OpenAPI / Swagger documentation is available at `http://localhost:8000/docs`.

### Key Authentication & Device Endpoints
- `POST /api/v1/auth/sessions` — Create new QR authentication or enrollment session.
- `GET /api/v1/auth/sessions/{session_token}` — Poll session state (SEC-02 protected).
- `POST /api/v1/auth/sessions/{session_token}/scan` — Notify backend that QR code was scanned.
- `POST /api/v1/auth/sessions/{session_token}/verify` — Verify mobile ECDSA challenge signature.
- `POST /api/v1/auth/devices/register` — Register newly enrolled hardware device public key.
- `GET /api/v1/auth/devices/{device_id}/status` — Synchronize device enrollment and access status.
- `POST /api/v1/auth/devices/{device_id}/revoke` — Revoke device access (retains registration lock).
- `POST /api/v1/auth/devices/{device_id}/unregister` — Unregister device binding and free enrollment slot.
- `GET /api/v1/auth/devices` — List registered devices (protected by dev admin key or bearer token).

### Milestone 3 Secure Notes Endpoints
- `GET /api/v1/notes` — List owner's encrypted notes (requires bearer token).
- `POST /api/v1/notes` — Create encrypted note with AES-256-GCM ciphertext and Vigenère educational layer.
- `GET /api/v1/notes/{id}` — Retrieve specific note ciphertext.
- `PUT /api/v1/notes/{id}` — Update note ciphertext.
- `DELETE /api/v1/notes/{id}` — Delete note.

### Milestone 3 Digital Asset Vault Endpoints
- `POST /api/v1/assets` — Upload digital asset with magic-byte validation, XChaCha20-Poly1305 encryption, and atomic storage.
- `GET /api/v1/assets` — List digital assets owned by authenticated device (descending by timestamp).
- `GET /api/v1/assets/{id}` — Retrieve digital asset metadata and SHA-256 ciphertext digest.
- `GET /api/v1/assets/{id}/download` — Verify integrity, decrypt in memory, and download binary attachment.
- `PATCH /api/v1/assets/{id}` — Rename digital asset without altering encrypted binary file.
- `DELETE /api/v1/assets/{id}` — Delete asset record and permanently unlink ciphertext binary from disk.

Full API contracts are documented in [`docs/M2.4_API_CONTRACT.md`](docs/M2.4_API_CONTRACT.md), [`docs/ONE_TIME_DEVICE_ENROLLMENT.md`](docs/ONE_TIME_DEVICE_ENROLLMENT.md), and [`docs/M3_ALIZA_ASSET_VAULT_INTEGRATION.md`](docs/M3_ALIZA_ASSET_VAULT_INTEGRATION.md).

---

## 20. Security Architecture & Threat Model

IPGuard implements defense-in-depth security:
1. **Hardware-Isolated Private Keys (Keystore):** Private keys are generated using `KeyGenParameterSpec` with curve `secp256r1` and stored in hardware TEE / StrongBox. Keys are explicitly non-exportable (`privateKey.encoded == null`).
2. **Standard Cryptographic Encoding:**
   - Public Keys: 91 bytes raw binary X.509 `SubjectPublicKeyInfo` DER (124 Base64 characters).
   - Signatures: Standard ASN.1 DER `SEQUENCE { r INTEGER, s INTEGER }`, typically 70–72 bytes binary (96 Base64 characters).
3. **Adaptive Biometric & Credential Signing:** Enforces `BIOMETRIC_STRONG` (Class 3) or `DEVICE_CREDENTIAL` (PIN/pattern/password). Weak Class 2 face recognition is strictly excluded from keystore crypto operations.
4. **Anti QR-Jacking Protection (SEC-02):** The browser session secret token (`token_hash`) is never encoded into the QR code or transmitted to the mobile phone. Only the initiating browser can retrieve the session access token.
5. **Pessimistic Row-Level Locking (SEC-01):** Challenge consumption in PostgreSQL uses `SELECT ... FOR UPDATE` to guarantee single-use nonce consumption.
6. **Origin Binding (SEC-03):** Authentication sessions are cryptographically bound to verified origins (e.g. `http://localhost:5173`).
7. **One-Time Enrollment Enforcement:** Backend rejects duplicate enrollments with HTTP 409 `DEVICE_ALREADY_REGISTERED`, preventing silent key replacement or race conditions.
8. **M3 Secure Notes Zero-Knowledge Storage:** Secure Notes are encrypted client-side using HKDF-SHA256 derived keys and AES-256-GCM. The database stores ciphertext only; notes are strictly isolated by `owner_id` mapped to the verified `device_id`.
9. **M3 Digital Asset Vault AEAD Isolation:** Digital assets are encrypted using libsodium XChaCha20-Poly1305 with per-device HKDF-SHA256 keys and AAD context binding (`v1|device_id|asset_id`). Atomic filesystem writes (`.tmp` to permanent) prevent partial writes, and unauthorized cross-device decryption attempts fail-closed with HTTP 404/403.
10. **Tamper-Evident Integrity Assurance (Planned M4 & M5):** Continuous SHA-256 asset monitoring and append-only audit hash chains ensure tamper-evident event histories, with optional public/consortium blockchain anchoring planned for M5 without ever placing plaintext assets or private keys on-chain.

---

## 21. Known Limitations & Architectural Boundaries

1. **Milestone Boundary (Device-Level Identity):** Milestones 1–3 establish device-level hardware identity and cryptographic challenge-response authentication. Multi-tenant username/password user accounts (`users` table) are scheduled for Milestone 4/5.
2. **Single Active Device Policy:** The current device registry supports binding one active authenticator key per client context. Key rollover and multi-device revocation lists are scheduled for M4.
3. **Physical Device Network Routing:** Connecting a physical mobile device requires either an active `adb reverse tcp:8000 tcp:8000` tunnel or configuring `IPGUARD_API_URL` to point to a reachable LAN IP address.
4. **Asset Upload In-Memory Buffering:** Digital asset upload currently enforces an in-memory buffer up to 50 MB (preventing memory exhaustion / DoS attacks); true multi-part streaming file uploads are planned for future optimization.
5. **Original Format Decryption:** Digital assets are decrypted in ephemeral browser memory and downloaded in their original binary format; proprietary `.ipguard` encrypted container export is not implemented.
6. **Asynchronous File Cleanup:** Unlinking deleted assets is executed synchronously during asset deletion; an asynchronous background worker for orphan-file sweeps remains a future maintenance enhancement.

---

## 22. Collaboration Guide

Detailed instructions for repository collaborators, permission models, and candidate issue roadmaps for Milestone 4 and 5 are documented in [`docs/COLLABORATION_GUIDE.md`](docs/COLLABORATION_GUIDE.md).

---

## 23. Contribution Guide

We welcome contributions from invited team members! Please consult [`CONTRIBUTING.md`](CONTRIBUTING.md) for:
- Branching strategy (`feature/m4-...`, `feature/m5-...`, `fix/...`).
- Conventional Commit message formats.
- Pull Request submission standards.
- Zero-secrets verification rules.

---

## 24. Security Reporting

If you discover a potential security vulnerability within IPGuard, please consult [`SECURITY.md`](SECURITY.md) for our private disclosure process. **Do not create public GitHub issues for security vulnerabilities.**

---

## 25. License and Project Usage Information

- **Repository Visibility:** `PRIVATE`.
- **Status:** Proprietary / Pre-release research and development.
- **Copyright & Rights:** All rights reserved by the project owner ([@Abhiprayaa29](https://github.com/Abhiprayaa29)). Unauthorized copying, distribution, or public publishing of this repository is strictly prohibited.
