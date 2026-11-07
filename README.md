# IPGuard — Secure Digital Asset Protection

[![Milestone](https://img.shields.io/badge/Milestone-M2--Complete-brightgreen.svg)](docs/M2_FINAL_SHARING_READINESS.md)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-65%2F65%20PASS-success.svg)](backend/tests/)
[![Android Tests](https://img.shields.io/badge/Android%20Tests-37%2F37%20PASS-success.svg)](mobile-authenticator/app/src/test/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-22%20LTS-green.svg)](https://nodejs.org/)
[![Android API](https://img.shields.io/badge/Android%20API-28--36-orange.svg)](docs/ANDROID_COMPATIBILITY.md)

IPGuard is an enterprise-grade digital asset security platform designed to store, manage, and cryptographically protect high-value digital assets (source code, architectural models, proprietary media, sensitive contracts). IPGuard enforces a **Zero-Trust hardware-backed device binding architecture**, where a companion native Android Authenticator app functions as a hardware security key. Sensitive web console operations and logins require out-of-band cryptographic challenge signatures created inside the Android Keystore (TEE / StrongBox).

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Milestone Roadmap Status](#2-milestone-roadmap-status)
3. [Prerequisites](#3-prerequisites)
4. [Quickstart Guide](#4-quickstart-guide)
5. [Environment Configuration](#5-environment-configuration)
6. [Database Setup & Migrations](#6-database-setup--migrations)
7. [Running the Backend](#7-running-the-backend)
8. [Running the Frontend](#8-running-the-frontend)
9. [ADB Reverse & Physical Android Setup](#9-adb-reverse--physical-android-setup)
10. [Building & Installing Android Authenticator](#10-building--installing-android-authenticator)
11. [Running Tests](#11-running-tests)
12. [Security Architecture & Guarantees](#12-security-architecture--guarantees)
13. [Cross-Device Compatibility](#13-cross-device-compatibility)
14. [Known Limitations & Roadmap Boundaries](#14-known-limitations--roadmap-boundaries)
15. [Troubleshooting Guide](#15-troubleshooting-guide)
16. [Contributing Guidelines](#16-contributing-guidelines)
17. [Security Policy & Disclosures](#17-security-policy--disclosures)
18. [Maintainer & License](#18-maintainer--license)

---

## 1. System Architecture

IPGuard is structured as a modular three-subsystem monorepo:

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
     - High-Performance OkHttp Client with explicit connection lifecycle control
```

---

## 2. Milestone Roadmap Status

| Milestone | Subsystem / Focus | Status | Verification Summary |
|---|---|:---:|---|
| **M1** | Foundation & Architecture | **COMPLETE** | React frontend, FastAPI backend, PostgreSQL 17, Alembic migrations, Pytest suite. |
| **M2** | Authentication & Device Security | **COMPLETE** | **M2.0–M2.3:** Keystore ECDSA P-256, BiometricPrompt + CryptoObject, CameraX/ML Kit.<br>**M2.4-B:** Backend device registry, session locking (SEC-01), origin validation (SEC-03).<br>**M2.4-C:** Web QR auth UI, countdown timer, anti QR-jacking channel binding (SEC-02).<br>**M2.4-D:** Android QR parsing, hardware signing, OkHttp integration (Physically Verified on Samsung A54 5G). |
| **M3** | Core Cryptography & Asset Protection | **PLANNED** | Digital asset encryption (AES-256-GCM / XChaCha20-Poly1305), Argon2id key derivation, access policies. |
| **M4** | Integrity & Advanced Protection | **PLANNED** | Cryptographic hashing, robust steganographic watermarking, tamper-evident audit logs. |
| **M5** | Integration, Testing & Release | **PLANNED** | End-to-end integration, security penetration audits, packaging, and production deployment. |

---

## 3. Prerequisites

Before installing, ensure your host development environment has:

- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python:** Version 3.13 (or 3.11+) with `venv` and `pip`.
- **Node.js:** Node.js 22 LTS or newer with `npm`.
- **Java Development Kit (JDK):** JDK 17 (required for Gradle and Android build tools).
- **Android SDK:** API Level 34–36, Platform-tools (`adb`).
- **Database:** PostgreSQL 17 (native installation or Docker Desktop).
- **Physical Device (Optional for mobile testing):** Android device running Android 9+ (API 28–36) with USB debugging enabled.

---

## 4. Quickstart Guide

Clone the repository and set up all components in minutes:

```powershell
# 1. Clone the repository
git clone https://github.com/Abhiprayaa29/IPGuard.git
cd IPGuard

# 2. Configure environment files
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env

# 3. Setup and start PostgreSQL database (native or via docker-compose)
docker-compose up -d

# 4. Initialize backend environment
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic -c alembic.ini upgrade head

# 5. Start Backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 60

# 6. In a new terminal, start Frontend dev server
cd ..\frontend
npm install
npm run dev

# 7. (Optional) Setup Android USB reverse tunnel & install
adb reverse tcp:8000 tcp:8000
cd ..\mobile-authenticator
.\gradlew.bat installDebug
adb shell am start -n com.ipguard.authenticator/.MainActivity
```

Open your browser to `http://localhost:5173` to access the IPGuard Web Console.

---

## 5. Environment Configuration

IPGuard maintains strict separation of configuration templates. **Never commit `.env` files containing real secrets.**

### Root `.env` (Docker Compose)
Used to start the local development database:
```dotenv
POSTGRES_DB=ipguard
POSTGRES_USER=ipguard
POSTGRES_PASSWORD=replace_with_a_strong_local_password
POSTGRES_PORT=5432
```

### Backend `.env` (`backend/.env`)
Controls database connectivity, origin filtering, and session parameters:
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
Directs API queries to the local backend gateway:
```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Android Config (`mobile-authenticator`)
The Android application defaults to connecting to `http://127.0.0.1:8000/api/v1` via ADB reverse. To customize the endpoint without modifying code, set the environment variable prior to building:
```powershell
$env:IPGUARD_API_URL="http://192.168.1.100:8000/api/v1"
.\gradlew.bat assembleDebug
```

---

## 6. Database Setup & Migrations

IPGuard uses PostgreSQL with Alembic schema management.

1. Ensure PostgreSQL 17 is running on `127.0.0.1:5432`.
2. Apply database migrations to bring the schema to the latest version:
   ```powershell
   cd backend
   alembic -c alembic.ini upgrade head
   ```
3. To verify current database revision:
   ```powershell
   alembic -c alembic.ini current
   ```

---

## 7. Running the Backend

Start the FastAPI application with Uvicorn:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 60
```

- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Alternative Documentation (ReDoc):** `http://localhost:8000/redoc`
- **System Health Endpoint:** `http://localhost:8000/api/v1/health`

---

## 8. Running the Frontend

Start the Vite development server:

```powershell
cd frontend
npm run dev
```

- **Local Access:** `http://localhost:5173`
- **QR Login Page:** `http://localhost:5173/login`
- **System Status Dashboard:** `http://localhost:5173/system-status`

---

## 9. ADB Reverse & Physical Android Setup

When testing with a physical Android device over USB, the device cannot resolve `http://localhost:8000` to your host computer automatically.

### Configuring ADB Reverse
Run the following command while your phone is connected via USB with USB Debugging enabled:

```powershell
adb reverse tcp:8000 tcp:8000
```

This maps any HTTP request made on the phone to `http://127.0.0.1:8000` directly into your host machine's port 8000.

To verify active reverse tunnels:
```powershell
adb reverse --list
# Expected output: (reverse) tcp:8000 tcp:8000
```

> [!NOTE]
> Do NOT use `10.0.2.2` when testing on physical hardware. `10.0.2.2` is exclusively an alias for the host loopback on the standard Android Emulator.

---

## 10. Building & Installing Android Authenticator

1. Check connected device:
   ```powershell
   adb devices -l
   ```
2. Build and install debug APK:
   ```powershell
   cd mobile-authenticator
   .\gradlew.bat installDebug
   ```
3. Launch the Authenticator:
   ```powershell
   adb shell am start -n com.ipguard.authenticator/.MainActivity
   ```

---

## 11. Running Tests

IPGuard maintains strict test quality gates across all three subsystems.

### Backend Test Suite (Pytest)
Executes 65 unit, integration, origin validation, and cryptographic tests:
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

### Frontend Verification
Performs TypeScript strict type-checking and production bundling:
```powershell
cd frontend
npm run typecheck
npm run build
```

### Android Unit Tests
Runs 37 unit tests covering KeyStore manager, payload parsers, challenge signing, and state machines:
```powershell
cd mobile-authenticator
.\gradlew.bat testDebugUnitTest --no-daemon
```

### Full Pre-Push Verification Check
Run all three in sequence:
```powershell
cd backend; .\.venv\Scripts\python.exe -m pytest -v; cd ..\frontend; npm run build; cd ..\mobile-authenticator; .\gradlew.bat testDebugUnitTest --no-daemon
```

---

## 12. Security Architecture & Guarantees

IPGuard is engineered according to defense-in-depth principles:

1. **Hardware-Isolated Private Keys (Keystore):**
   Private signing keys are generated using `KeyGenParameterSpec` with `PURPOSE_SIGN`, curve `secp256r1` (NIST P-256), and stored in hardware TEE / StrongBox. Keys are explicitly non-exportable (`privateKey.encoded == null`).
2. **Standard Cryptographic Encoding:**
   - Public Keys: 91 bytes raw binary X.509 `SubjectPublicKeyInfo` DER (124 Base64 characters).
   - Signatures: Standard ASN.1 DER `SEQUENCE { r INTEGER, s INTEGER }`, typically 70–72 bytes binary (96 Base64 characters).
3. **Adaptive BiometricPrompt & Device Credential:**
   Enforces `BIOMETRIC_STRONG` (Class 3) or `DEVICE_CREDENTIAL` (PIN/pattern/password). Weak Class 2 face recognition is strictly excluded from keystore crypto authentication. A secure lockscreen is mandatory.
4. **Anti QR-Jacking / Shoulder Surfing Protection (SEC-02):**
   The browser session access token (`token_hash`) is never encoded into the QR code or transmitted to the mobile phone. Only the initiating browser that knows the original polling secret can redeem the approved session.
5. **Pessimistic Row-Level Locking (SEC-01):**
   Challenge consumption in PostgreSQL uses `SELECT ... FOR UPDATE` to guarantee exactly single-use nonce consumption and prevent concurrent replay attacks.
6. **Origin Binding (SEC-03):**
   Browser sessions are cryptographically bound to verified origins (e.g. `http://localhost:5173`), preventing cross-site session creation.

---

## 13. Cross-Device Compatibility

The Android Authenticator is designed to be **device-agnostic**:
- Supports Android API 28 (Android 9 Pie) through API 36 (Android 16).
- Zero manufacturer-specific hardcoding: dynamically evaluates `Build.MANUFACTURER`, `Build.MODEL`, and `KeyInfo.isInsideSecureHardware()`.
- Generates anonymous, app-scoped UUIDs (`ipguard-dev-<16 hex chars>`) stored in private preferences; does not access IMEI, MAC addresses, or hardware serial numbers.
- For in-depth compatibility matrix, modality ladders, and testing results across Samsung, Google Pixel, Xiaomi, and emulators, see [`docs/ANDROID_COMPATIBILITY.md`](docs/ANDROID_COMPATIBILITY.md).

---

## 14. Known Limitations & Roadmap Boundaries

To maintain engineering integrity, the following boundaries are explicitly documented:

1. **Milestone Boundary (No User Multi-Tenancy Yet):**
   Milestone 2 strictly implements device-level identity and cryptographic challenge-response authentication. There is currently no `users` table or multi-user access control list; this will be introduced in Milestone 3 alongside encrypted asset access.
2. **Single Active Device Policy:**
   The current device registry supports binding one active authenticator key per client context. Key rollover and multi-device revocation lists are scheduled for M3/M4.
3. **Physical Device Network Routing:**
   Connecting a physical mobile device requires either an active `adb reverse tcp:8000 tcp:8000` tunnel or configuring `IPGUARD_API_URL` to point to a reachable LAN IP address with appropriate firewall rules.

---

## 15. Troubleshooting Guide

| Issue | Root Cause | Solution |
|---|---|---|
| `java.net.ConnectException: Failed to connect to /127.0.0.1:8000` | ADB reverse tunnel is inactive or USB disconnected. | Run `adb reverse tcp:8000 tcp:8000` and confirm with `adb reverse --list`. |
| `java.io.IOException: unexpected end of stream` | Uvicorn keep-alive timeout closed socket while entering PIN. | Authenticator now uses `Connection: close` and retries automatically. Run uvicorn with `--timeout-keep-alive 60`. |
| `CORS request failed / Origin not allowed` | Browser origin is not in backend whitelist. | Add origin to `CORS_ORIGINS` and `TRUSTED_ORIGINS` in `backend/.env`. |
| `DeviceLockScreenRequiredException` on phone | Phone does not have a secure lock screen (PIN/Pattern/Password/Fingerprint). | Open Android Settings -> Security -> Screen Lock and set a PIN or pattern. |
| Camera preview black or QR scanner not reading | Camera permission denied. | Allow camera permission in Android app info settings. |

---

## 16. Contributing Guidelines

We welcome contributions from collaborators! Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) for:
- Branching strategy (`feature/*`, `fix/*`).
- Conventional Commit message formats.
- Pull Request submission standards.
- Zero-secrets verification rules.

---

## 17. Security Policy & Disclosures

If you discover a potential security vulnerability within IPGuard, please consult [`SECURITY.md`](SECURITY.md) for our private disclosure process. **Do not create public GitHub issues for security vulnerabilities.**

---

## 18. Maintainer & License

- **Project Lead & Maintainer:** [@Abhiprayaa29](https://github.com/Abhiprayaa29)
- **Repository:** [https://github.com/Abhiprayaa29/IPGuard](https://github.com/Abhiprayaa29/IPGuard)
- **Status:** Proprietary / Pre-release research and development. All rights reserved by the repository owner.
