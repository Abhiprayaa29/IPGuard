# IPGuard — Secure Digital Asset Protection

IPGuard is an enterprise-grade digital asset security platform designed to protect, store, manage, and verify the cryptographic integrity of creative and sensitive digital assets. It uses a device-bound architecture where an Android native mobile authenticator acts as the hardware-backed security key for approving sensitive operations initiated from the web console.

---

## 1. Project Overview

Digital creative assets (source code, proprietary media, architectural models, sensitive documents) face severe exposure risks: unauthorized exfiltration, metadata tampering, unauthorized redistribution, and credential theft. IPGuard addresses these threats through:
- **Zero-Trust Device Binding:** Operations on sensitive assets require cryptographic authorization from a physically bound, hardware-isolated Android device.
- **Defense in Depth:** Multi-tiered defense separating UX presence detection, device credential authorization, hardware keystore signing, and server-side verification.
- **Non-Exportable Device Identity:** Cryptographic private signing keys never leave the hardware boundary of the authenticator device.

---

## 2. Project Objectives

1. **Hardware-Backed Device Identity:** Bind exactly one active mobile device to an IPGuard user account using an ECDSA P-256 key pair generated and retained in Android Keystore (TEE-backed).
2. **Adaptive Authorization Policy:** Support resilient, multi-tiered authentication accommodating devices without mandatory biometric enrollment (e.g. optical sensor failure) through hardware Gatekeeper PIN/pattern authorization.
3. **Cryptographic Integrity & Attribution:** Sign every sensitive sign-in and authorization challenge with hardware-backed ECDSA SHA-256 signatures, validated by the backend before session access is granted.
4. **Zero-Knowledge Architecture:** Never transmit private keys, face biometric frames, or camera images across the network or persist them to disk.
5. **Team Collaboration:** Provide a clean, robust, monorepo foundation that team members can clone, configure, build, and extend seamlessly.

---

## 3. Key Features

- **Web Management Console (React + TypeScript):** Real-time system status monitoring, responsive layout, health probes, and preview interface.
- **RESTful API Backend (Python FastAPI + SQLAlchemy):** High-performance asynchronous API with PostgreSQL database connectivity, Alembic schema migrations, and structured error handling.
- **Native Android Authenticator (Kotlin + Jetpack Compose):**
  - **CameraX & Vision Engine:** Front-camera framing presence detection (Google ML Kit Face Detection) and rear-camera QR code reader (Google ML Kit Barcode Scanning).
  - **Hardware Keystore Manager:** Idempotent ECDSA P-256 key pair generation in Android Keystore, strict non-exportability (`privateKey.encoded == null`), and X.509 `SubjectPublicKeyInfo` export.
  - **Adaptive Authentication Engine (M2.3-B):** BiometricPrompt integration with `CryptoObject` supporting `BIOMETRIC_STRONG` (Class 3) and `DEVICE_CREDENTIAL` (PIN/pattern/password), fully verified on Android 16 (API 36).
  - **Cryptographic Live Diagnostics:** Real-time on-device signing test producing verified SHA256withECDSA signatures with authenticating method labeling.

---

## 4. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, React Router, TanStack Query, Axios, Lucide React |
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.x, Psycopg 3, Alembic, Pydantic v2, Pytest |
| **Database** | PostgreSQL 17 (Local Portable or Docker Compose) |
| **Mobile Authenticator** | Kotlin 2.0+, Jetpack Compose, Android Keystore, AndroidX Biometric, CameraX, Google ML Kit |
| **Tooling & DevOps** | Git, GitHub CLI (`gh`), Docker Compose, Gradle Wrapper 8.13, Android SDK Build-Tools 36 |

---

## 5. System Architecture

```text
+-----------------------+                    +------------------------------------+
|  IPGuard Web Console  |                    |        IPGuard REST API            |
|  (React + TypeScript) | ─── HTTP / REST ──►|       (Python FastAPI)             |
|  localhost:5173       |                    |       localhost:8000               |
+-----------------------+                    +------------------------------------+
                                                                │
                                                                ▼
                                                     +--------------------+
                                                     |    PostgreSQL      |
                                                     |    Database        |
                                                     +--------------------+
                                                                ▲
+----------------------------------------------------+          │
|       IPGuard Android Native Authenticator         |          │
|   - Jetpack Compose UI (9 Functional Screens)      |          │
|   - CameraX + ML Kit (Face Gate & QR Scanner)      |          │
|   - Android Keystore (ECDSA P-256, TEE-backed)     | ── M2.4 ─┘
|   - BiometricPrompt + CryptoObject                 |   (Challenge-Response)
|   - Adaptive Policy (PIN / Pattern / Biometric)    |
+----------------------------------------------------+
```

---

## 6. Repository Structure

```text
IPGuard/
├── frontend/                  React + TypeScript web console
│   ├── public/                Static public assets (favicon.svg)
│   ├── src/                   Application source (pages, components, services, hooks)
│   ├── package.json           Node.js dependencies and build scripts
│   └── vite.config.ts         Vite bundler configuration
├── backend/                   Python FastAPI REST API
│   ├── app/                   API routes, core config, database models, schemas, services
│   ├── tests/                 Pytest test suite (health, db, system, cors)
│   ├── alembic.ini            Database migration configuration
│   └── requirements.txt       Python dependencies
├── mobile-authenticator/      Native Android Kotlin application
│   ├── app/                   Source code (Compose UI, CameraX, Keystore, Biometric)
│   ├── gradle/wrapper/        Pinned Gradle Wrapper distribution
│   ├── build.gradle.kts       Multiplatform build definitions
│   └── gradlew.bat            Gradle build executable
├── docs/                      Technical reports, architecture, and team guides
│   ├── M2.3B_AUTHENTICATION_REPORT.md  Adaptive authentication physical verification
│   ├── M2.3A_KEYSTORE_REPORT.md        Keystore key generation & TEE report
│   ├── M2_ARCHITECTURE.md              Mobile and system architecture specification
│   ├── TEAM_WORKFLOW.md                Team Git & PR collaboration guidelines
│   └── assets/                         Physical device test evidence and screenshots
├── scripts/                   Development automation helpers (PowerShell)
├── docker-compose.yml         PostgreSQL local development container
├── .gitignore                 Comprehensive ignore rules for secrets, builds, and artifacts
├── .env.example               Docker Compose environment template
└── README.md                  Project master documentation
```

---

## 7. Current Milestone Status

Official 5-Milestone Roadmap:

| Milestone | Name | Status | Details |
|---|---|:---:|---|
| **M1** | Foundation & Architecture | **COMPLETE** | React frontend, FastAPI backend, PostgreSQL, Alembic, health probes, Pytest suite. |
| **M2** | Authentication & Device Security | **IN PROGRESS** | **M2.0–M2.3-B Complete:** CameraX, ML Kit, Android Keystore P-256, BiometricPrompt + CryptoObject with Device Credential. **M2.4-B Complete:** Backend Core Engine, PostgreSQL Schema, ECDSA P-256 verifier, pessimistic row-level locking & origin whitelisting. **M2.4-C Next:** Frontend QR display, polling & anti-QR-jacking. |
| **M3** | Core Cryptography & Asset Protection | **NOT STARTED** | Digital asset encryption (AES-256-GCM / XChaCha20-Poly1305), Argon2id key derivation, access policies. |
| **M4** | Integrity & Advanced Protection | **NOT STARTED** | Cryptographic hashing, robust steganographic watermarking, tamper-evidence auditing. |
| **M5** | Integration, Testing & Release | **NOT STARTED** | End-to-end integration, security penetration audits, packaging, and production deployment. |

---

## 8. Development Setup

### Prerequisites
- **Operating System:** Windows 10/11 (PowerShell 5.1+ or PowerShell 7+)
- **Node.js:** Node.js 22 LTS or newer and npm
- **Python:** Python 3.13 (or 3.11+) with virtual environment support
- **Git:** Git 2.40+
- **Android SDK:** Android Studio Ladybug/Meerkat or Android SDK Command-line Tools (API 34–36, Platform-tools `adb`)
- **Database:** PostgreSQL 17 or Docker Desktop with Compose

---

## 9. Environment Configuration

Copy the example environment templates before running any service. Never commit real `.env` files.

### Root `.env` (Docker Compose)
```powershell
Copy-Item .env.example .env
```

### Backend `.env` (`backend/.env`)
```powershell
Copy-Item backend\.env.example backend\.env
```
Ensure `DATABASE_URL` is set:
```dotenv
APP_NAME=IPGuard
APP_VERSION=1.0.0
APP_ENV=development
DATABASE_URL=postgresql+psycopg://ipguard:strong_password@127.0.0.1:5432/ipguard
CORS_ORIGINS=http://localhost:5173
```

### Frontend `.env` (`frontend/.env`)
```powershell
Copy-Item frontend\.env.example frontend\.env
```
```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 10. How to Run Backend

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```powershell
   alembic -c alembic.ini upgrade head
   ```
5. Start the FastAPI development server:
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Interactive Swagger docs available at: `http://localhost:8000/docs`

---

## 11. How to Run Frontend

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Start Vite development server:
   ```powershell
   npm run dev
   ```
   Open: `http://localhost:5173`

---

## 12. How to Run Android Authenticator

1. Connect an Android physical device via USB or start an emulator:
   ```powershell
   adb devices -l
   ```
2. Navigate to `mobile-authenticator`:
   ```powershell
   cd mobile-authenticator
   ```
3. Build and install debug APK:
   ```powershell
   .\gradlew.bat installDebug
   ```
4. Launch the application:
   ```powershell
   adb shell am start -n com.ipguard.authenticator/.MainActivity
   ```

---

## 13. Testing Instructions

### Backend Unit & Integration Tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

### Frontend Typecheck & Build
```powershell
cd frontend
npm run typecheck
npm run build
```

### Android Unit Tests & Lint
```powershell
cd mobile-authenticator
.\gradlew.bat testDebugUnitTest
.\gradlew.bat lintDebug
```

### Android Connected Hardware Tests (Physical Device)
```powershell
cd mobile-authenticator
.\gradlew.bat :app:connectedDebugAndroidTest "-Pandroid.testInstrumentationRunnerArguments.class=com.ipguard.authenticator.security.DeviceAuthenticationPolicyTest"
```

---

## 14. Team Development Workflow

All contributors must adhere to standard team engineering practices:
- **Private Repository:** IPGuard is an internal private repository. Never fork or publish code to public repositories.
- **Branch Naming:** Create feature branches from `main` (e.g. `feature/backend-device-enrollment`, `feature/qr-challenge-signing`).
- **No Direct Push to `main`:** Submit a Pull Request (PR) and require code review before merging.
- **Zero Secrets Policy:** Never commit `.env`, `local.properties`, keystores, or private keys. Pre-commit scans are enforced.
- **Detailed Workflow Guide:** Refer to [`docs/TEAM_WORKFLOW.md`](docs/TEAM_WORKFLOW.md) for step-by-step collaboration commands.
