# IPGuard — Final Project Handover Document
**Document ID:** `docs/FINAL_HANDOVER.md`  
**Date:** November 10, 2026  
**Target Milestone:** Full Handover (Milestones 1–4)  
**Branch:** `feature/m4-steganography-backend`  
**Baseline Commit:** `82c07a0abb4fec08bc620275abb7a59325c9588d`  

---

## 1. Repository Layout

```
IPGuard/
├── backend/                  # FastAPI Core Backend Engine
│   ├── app/
│   │   ├── api/              # HTTP API routes and dependencies
│   │   ├── core/             # Configuration, error handlers, security
│   │   ├── db/               # Alembic migrations (0001–0009) and sessions
│   │   ├── models/           # SQLAlchemy ORM models (asset, audit, auth)
│   │   ├── schemas/          # Pydantic request/response validation schemas
│   │   ├── services/         # Cryptographic engines, stego, vault, audit
│   │   └── workers/          # Background integrity verification tasks
│   ├── storage/              # Encrypted ciphertext binaries (AEAD files)
│   ├── tests/                # Full Pytest test suite (209 test cases)
│   ├── requirements.txt      # Python dependencies (FastAPI, Cryptography, Pillow, etc.)
│   └── .env.example          # Environment template (NO SECRETS)
├── frontend/                 # React 19 Web Console
│   ├── src/
│   │   ├── components/       # UI components (auth QR, vault cards, modals)
│   │   ├── pages/            # Page controllers (AssetVault, QrLogin, Notes)
│   │   ├── services/         # Axios API clients
│   │   ├── types/            # TypeScript data contracts and interfaces
│   │   └── utils/            # Session token resolution and format helpers
│   ├── package.json          # Node dependencies (React 19, Vite 8, Tailwind 4)
│   └── .env.example          # Frontend environment template
├── android/                  # Android Authenticator Native Application
│   ├── app/src/main/java/    # Kotlin source (Keystore, CameraX, ZXing, Compose)
│   └── build.gradle.kts      # Android build configuration (API 28–36)
├── docs/                     # Technical specifications, reports, and evidence
│   ├── screenshots/          # Browser acceptance screenshots and results JSON
│   ├── FINAL_PROJECT_REPORT.md   # Comprehensive technical report (Indonesian)
│   ├── FINAL_ACCEPTANCE_MATRIX.md# Milestone feature status matrix
│   ├── FINAL_EVIDENCE_INDEX.md   # Navigable proof index
│   └── FINAL_HANDOVER.md         # This operational handover document
└── scripts/                  # Automation scripts (PostgreSQL, browser testing)
```

---

## 2. Runtime Requirements

| Component | Required Version | Supported Platforms | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | `3.13.x` (or `>= 3.11`) | Linux, macOS, Windows | Virtualenv recommended |
| **Node.js** | `>= 22.12.0` | Linux, macOS, Windows | npm 10+ included |
| **PostgreSQL**| `17.x` (17.11 tested) | Linux, macOS, Windows | Native installation, portable, or Docker |
| **Android SDK**| API `28` to `36` | Android physical device or AVD | Android 9.0 (Pie) minimum |
| **Peramban Web**| Chrome, Edge, Firefox, Brave | Desktop Web Browsers | Modern ECMAScript with WebCrypto |

---

## 3. Environment Configuration

### 3.1 Backend `.env`
Create `backend/.env` from `backend/.env.example`. **Never commit `.env` into version control.**

```ini
APP_NAME=IPGuard
APP_VERSION=1.0.0
APP_ENV=development
DATABASE_URL=postgresql+psycopg://ipguard:<PASSWORD>@127.0.0.1:5432/ipguard
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEV_ADMIN_KEY=ipguard-dev-admin-secret-key

# Milestone 4 — Ed25519 Steganography Signing Key Configuration
# Generate dev keys using: python -c "import secrets, base64; from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; from cryptography.hazmat.primitives import serialization; k = Ed25519PrivateKey.generate(); print(base64.b64encode(k.private_bytes_raw()).decode())"
STEGO_SIGNING_PRIVATE_KEY_B64=<Base64_Raw_32_Byte_Seed>
STEGO_ACTIVE_KEY_ID=<32_Hex_Chars_Key_ID>
STEGO_PUBLIC_KEYS_JSON={"<32_Hex_Chars_Key_ID>":"<Base64_Raw_32_Byte_Public_Key>"}
```

### 3.2 Frontend `.env`
Create `frontend/.env`:
```ini
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 4. Database Setup & Migration Execution

1. **Verify PostgreSQL Service:**
   Ensure PostgreSQL 17 is active and listening on port 5432.
2. **Apply All Database Migrations:**
   ```powershell
   Set-Location D:\Projects\IPGuard\backend
   .\.venv\Scripts\alembic upgrade head
   ```
3. **Verify Current Migration Head:**
   ```powershell
   .\.venv\Scripts\alembic current
   ```
   *Expected output:* `0009_png_lsb_derivatives (head)`

---

## 5. Service Startup Instructions

### 5.1 Start Backend Server
```powershell
Set-Location D:\Projects\IPGuard\backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```
API documentation is available at: `http://127.0.0.1:8000/docs`

### 5.2 Start Frontend Web Console
```powershell
Set-Location D:\Projects\IPGuard\frontend
npm run dev
```
Web console is accessible at: `http://127.0.0.1:5173`

### 5.3 Android Authenticator Setup
1. Open the `android/` directory in Android Studio (Ladybug or newer).
2. Sync Gradle dependencies.
3. Build and install debug APK onto physical Android device:
   ```bash
   ./gradlew installDebug
   ```
4. Ensure the Android device and development host are on the same local network or use ADB reverse proxy:
   ```bash
   adb reverse tcp:8000 tcp:8000
   ```

---

## 6. Testing Commands & Verification

### 6.1 Backend Full Test Suite
```powershell
$env:IPGUARD_TEST_POSTGRES_URL = "postgresql+psycopg://ipguard:<PASSWORD>@127.0.0.1:5432/disposable_ipguard_test"
Set-Location D:\Projects\IPGuard\backend
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Result:* `209 passed, 0 skipped` in ~12 seconds.

### 6.2 Frontend Static Check & Production Build
```powershell
Set-Location D:\Projects\IPGuard\frontend
npm run typecheck    # Must return 0 errors
npm run build        # Must compile clean production bundle in dist/
```

### 6.3 Automated Real Browser Acceptance Test (Playwright)
Ensure both backend (port 8000) and frontend (port 5173) are running, then execute:
```powershell
Set-Location D:\Projects\IPGuard\backend
.\.venv\Scripts\python.exe ..\scripts\m4_browser_acceptance_test.py
```
*Expected Result:* 14 acceptance steps pass, 9 screenshots saved to `docs/screenshots/m4_acceptance/`.

---

## 7. Security Precautions & Operational Invariants

1. **Private Key Secrecy:** `STEGO_SIGNING_PRIVATE_KEY_B64` is a raw cryptographic seed. Never log it, never serialize it to JSON responses, and never commit `.env` into git.
2. **Encrypted Storage Invariant:** Files in `backend/storage/` must remain in ciphertext form. Decryption must occur exclusively in memory upon authenticated request.
3. **Audit Hash Chain Invariant:** Never modify or delete rows from `audit_events`. Doing so breaks the rolling SHA-256 hash linking and fails cryptographic verification.
4. **Delete Cascade Invariant:** Master original assets cannot be deleted while active derivatives depend on them (`asset_has_derivatives`).
5. **Fail-Closed Watermark Extraction:** Any asset that fails Ed25519 signature verification or SHA-256 checksum matching must be rejected with HTTP 409 Conflict.

---

## 8. Current Git State & Submission Notice

* **Branch:** `feature/m4-steganography-backend`
* **Status:** Clean uncommitted development state preserved. No unstaged work discarded.
* **Review Readiness:** Ready for formal peer review and PR handoff.
