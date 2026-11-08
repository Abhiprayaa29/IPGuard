# IPGuard — Secure Digital Asset Protection

[![Milestone](https://img.shields.io/badge/Milestone-M2--Complete-brightgreen.svg)](docs/M2_FINAL_SHARING_READINESS.md)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-65%2F65%20PASS-success.svg)](backend/tests/)
[![Android Tests](https://img.shields.io/badge/Android%20Tests-37%2F37%20PASS-success.svg)](mobile-authenticator/app/src/test/)
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
5. [Technology Stack](#5-technology-stack)
6. [Repository Structure](#6-repository-structure)
7. [Milestone Roadmap](#7-milestone-roadmap)
8. [Prerequisites](#8-prerequisites)
9. [Installation Guide](#9-installation-guide)
10. [Environment Configuration](#10-environment-configuration)
11. [PostgreSQL Setup & Migrations](#11-postgresql-setup--migrations)
12. [Backend Setup & Execution](#12-backend-setup--execution)
13. [Frontend Setup & Execution](#13-frontend-setup--execution)
14. [Android Setup & Execution](#14-android-setup--execution)
15. [Physical Android Device Connection (ADB Reverse)](#15-physical-android-device-connection-adb-reverse)
16. [Running Automated Tests](#16-running-automated-tests)
17. [Building the Application](#17-building-the-application)
18. [API Documentation](#18-api-documentation)
19. [Security Architecture & Threat Model](#19-security-architecture--threat-model)
20. [Known Limitations & Architectural Boundaries](#20-known-limitations--architectural-boundaries)
21. [Collaboration Guide](#21-collaboration-guide)
22. [Contribution Guide](#22-contribution-guide)
23. [Security Reporting](#23-security-reporting)
24. [License and Project Usage Information](#24-license-and-project-usage-information)

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
- [x] **Fail-Closed Negative Security Enforcement:** Rejection of un-enrolled devices, expired challenges, and invalid origin headers.

### Planned Features (Future Milestones)
- [ ] **M3 — Digital Asset Vault:** Encrypted file storage and retrieval pipeline.
- [ ] **M3 — Symmetric Asset Encryption:** AES-256-GCM and XChaCha20-Poly1305 ciphers.
- [ ] **M3 — Key Derivation:** Argon2id passphrase-based key derivation.
- [ ] **M3 — Steganographic Watermarking:** PNG LSB steganography for copyright and watermark embedding.
- [ ] **M4 — Cryptographic Integrity Auditing:** SHA-256 Merkle-linked audit hash chain and tamper detection.
- [ ] **M4 — Hardware Attestation:** Remote Keymaster / Keymint certificate chain verification.
- [ ] **M5 — Multi-Tenant Access Control & Production Deployment:** Role-based permissions, cloud deployment, and penetration audits.

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

## 5. Technology Stack

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

## 6. Repository Structure

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

## 7. Milestone Roadmap

| Milestone | Focus Area | Status | Verification Summary |
|---|---|:---:|---|
| **M1** | Foundation & Architecture | **COMPLETE** | React frontend, FastAPI backend, PostgreSQL 17, Alembic migrations, Pytest suite. |
| **M2** | Authentication & Device Security | **COMPLETE** | **M2.0–M2.3:** Keystore ECDSA P-256, BiometricPrompt + CryptoObject, CameraX/ML Kit.<br>**M2.4-B:** Backend device registry, session locking (SEC-01), origin validation (SEC-03).<br>**M2.4-C:** Web QR auth UI, countdown timer, anti QR-jacking channel binding (SEC-02).<br>**M2.4-D:** Android QR parsing, hardware signing, OkHttp integration (Physically Verified on Samsung A54 5G). |
| **M3** | Core Cryptography & Asset Protection | **PLANNED** | Digital asset vault, streaming AES-256-GCM / XChaCha20-Poly1305 file encryption, Argon2id KDF, secure notes. |
| **M4** | Integrity & Advanced Protection | **PLANNED** | Cryptographic hashing, SHA-256 Merkle-linked audit hash chain, PNG LSB steganography, tamper-evident alerts. |
| **M5** | Integration, Testing & Release | **PLANNED** | End-to-end multi-tenant integration, penetration testing, packaging, and production deployment. |

---

## 8. Prerequisites

Ensure your development environment meets the following specifications:
- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python:** Python 3.13 (or 3.11+) with virtual environment support.
- **Node.js:** Node.js 22 LTS or newer with npm.
- **Java Development Kit (JDK):** OpenJDK 17.
- **Android SDK:** API 28–36, Platform-tools (`adb`).
- **Database:** PostgreSQL 17 (native or Docker Desktop).

---

## 9. Installation Guide

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

## 10. Environment Configuration

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

## 11. PostgreSQL Setup & Migrations

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

## 12. Backend Setup & Execution

Start the FastAPI application with Uvicorn:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 60
```
- **API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Health Endpoint:** `http://localhost:8000/api/v1/health`

---

## 13. Frontend Setup & Execution

Start the Vite development server:
```powershell
cd frontend
npm install
npm run dev
```
- **Web Console:** `http://localhost:5173`
- **QR Sign-In Page:** `http://localhost:5173/login`
- **System Status Dashboard:** `http://localhost:5173/system-status`

---

## 14. Android Setup & Execution

Build and install the Android Authenticator via Gradle:
```powershell
cd mobile-authenticator
.\gradlew.bat installDebug
adb shell am start -n com.ipguard.authenticator/.MainActivity
```

---

## 15. Physical Android Device Connection (ADB Reverse)

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

## 16. Running Automated Tests

IPGuard maintains strict test quality gates across all three subsystems:

### Backend Test Suite (Pytest)
```powershell
cd backend
python -m pytest -v
```
*Current result: 65 passed in 4.09s.*

### Frontend Typecheck & Production Build
```powershell
cd frontend
npm run typecheck
npm run build
```
*Current result: 2,188 modules transformed with 0 errors.*

### Android Unit Tests
```powershell
cd mobile-authenticator
.\gradlew.bat testDebugUnitTest --no-daemon
```
*Current result: 37 tests, 0 failures, 0 errors.*

---

## 17. Building the Application

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

## 18. API Documentation

Interactive OpenAPI / Swagger documentation is available at `http://localhost:8000/docs`.

### Key Milestone 2 Endpoints
- `POST /api/v1/auth/sessions/` — Create new QR authentication session.
- `GET /api/v1/auth/sessions/{session_token}` — Poll session state (SEC-02 protected).
- `POST /api/v1/auth/sessions/{session_token}/verify` — Verify mobile ECDSA challenge signature.
- `POST /api/v1/auth/devices/register` — Register newly enrolled hardware device public key.
- `GET /api/v1/auth/devices/` — List registered devices (protected by dev admin key).

Full API contracts are documented in [`docs/M2.4_API_CONTRACT.md`](docs/M2.4_API_CONTRACT.md).

---

## 19. Security Architecture & Threat Model

IPGuard implements defense-in-depth security:
1. **Hardware-Isolated Private Keys (Keystore):** Private keys are generated using `KeyGenParameterSpec` with curve `secp256r1` and stored in hardware TEE / StrongBox. Keys are explicitly non-exportable (`privateKey.encoded == null`).
2. **Standard Cryptographic Encoding:**
   - Public Keys: 91 bytes raw binary X.509 `SubjectPublicKeyInfo` DER (124 Base64 characters).
   - Signatures: Standard ASN.1 DER `SEQUENCE { r INTEGER, s INTEGER }`, typically 70–72 bytes binary (96 Base64 characters).
3. **Adaptive Biometric & Credential Signing:** Enforces `BIOMETRIC_STRONG` (Class 3) or `DEVICE_CREDENTIAL` (PIN/pattern/password). Weak Class 2 face recognition is strictly excluded from keystore crypto operations.
4. **Anti QR-Jacking Protection (SEC-02):** The browser session secret token (`token_hash`) is never encoded into the QR code or transmitted to the mobile phone. Only the initiating browser can retrieve the session access token.
5. **Pessimistic Row-Level Locking (SEC-01):** Challenge consumption in PostgreSQL uses `SELECT ... FOR UPDATE` to guarantee single-use nonce consumption.
6. **Origin Binding (SEC-03):** Authentication sessions are cryptographically bound to verified origins (e.g. `http://localhost:5173`).

---

## 20. Known Limitations & Architectural Boundaries

1. **Milestone Boundary (No User Multi-Tenancy Yet):** Milestone 2 establishes device-level identity and cryptographic challenge-response authentication. Multi-tenant user accounts (`users` table) are scheduled for Milestone 3.
2. **Single Active Device Policy:** The current device registry supports binding one active authenticator key per client context. Key rollover and multi-device revocation lists are scheduled for M3/M4.
3. **Physical Device Network Routing:** Connecting a physical mobile device requires either an active `adb reverse tcp:8000 tcp:8000` tunnel or configuring `IPGUARD_API_URL` to point to a reachable LAN IP address.

---

## 21. Collaboration Guide

Detailed instructions for repository collaborators, permission models, and candidate issue roadmaps for Milestone 3 and 4 are documented in [`docs/COLLABORATION_GUIDE.md`](docs/COLLABORATION_GUIDE.md).

---

## 22. Contribution Guide

We welcome contributions from invited team members! Please consult [`CONTRIBUTING.md`](CONTRIBUTING.md) for:
- Branching strategy (`feature/m3-...`, `feature/m4-...`, `fix/...`).
- Conventional Commit message formats.
- Pull Request submission standards.
- Zero-secrets verification rules.

---

## 23. Security Reporting

If you discover a potential security vulnerability within IPGuard, please consult [`SECURITY.md`](SECURITY.md) for our private disclosure process. **Do not create public GitHub issues for security vulnerabilities.**

---

## 24. License and Project Usage Information

- **Repository Visibility:** `PRIVATE`.
- **Status:** Proprietary / Pre-release research and development.
- **Copyright & Rights:** All rights reserved by the project owner ([@Abhiprayaa29](https://github.com/Abhiprayaa29)). Unauthorized copying, distribution, or public publishing of this repository is strictly prohibited.
