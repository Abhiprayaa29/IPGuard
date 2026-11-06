# IPGuard Project Structure

**Milestone:** M1 project foundation plus verified M2.2 camera and QR foundation  
**Date:** 2026-11-06  
**Repository:** `C:\Users\user\Documents\02_Projects\IPGuard`  
**Physical location:** `D:\Data\Documents\02_Projects\IPGuard` through the Windows Documents junction

> Sections describing the frontend, backend, and M1 decisions remain the baseline for those areas. The mobile authenticator M2.2 camera pipeline (CameraX, ML Kit Face Detection presence check, ML Kit Barcode QR scanner) is documented in [M2_ARCHITECTURE.md](M2_ARCHITECTURE.md) and [M2_TEST_REPORT.md](M2_TEST_REPORT.md).

---

## 1. Actual Source Tree

Runtime and generated directories (`node_modules`, `.venv`, `dist`, `logs`, `.pytest_cache`, `__pycache__`, and local editor metadata) are omitted from this tree. They are ignored by Git where appropriate.

```text
IPGuard/
├── frontend/
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── app/
│   │   │   ├── providers.tsx
│   │   │   └── router.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── AppShell.tsx
│   │   │   └── ui/
│   │   │       ├── ErrorBanner.tsx
│   │   │       ├── InfoRow.tsx
│   │   │       ├── RefreshButton.tsx
│   │   │       ├── StatusBadge.tsx
│   │   │       └── StatusCard.tsx
│   │   ├── hooks/
│   │   │   └── useSystemStatus.ts
│   │   ├── pages/
│   │   │   └── system-status/
│   │   │       ├── EnvironmentPanel.tsx
│   │   │       ├── ReadinessHero.tsx
│   │   │       ├── ServiceOverview.tsx
│   │   │       └── SystemStatusPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── systemStatus.ts
│   │   ├── styles/
│   │   │   └── index.css
│   │   ├── types/
│   │   │   └── system.ts
│   │   ├── utils/
│   │   │   ├── format.ts
│   │   │   └── status.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── .env                 (local, ignored)
│   ├── .env.example
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── health.py
│   │   │   │   └── system.py
│   │   │   ├── router.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── errors.py
│   │   │   └── __init__.py
│   │   ├── db/
│   │   │   ├── migrations/
│   │   │   │   ├── versions/
│   │   │   │   │   └── 0001_initial.py
│   │   │   │   ├── env.py
│   │   │   │   └── script.py.mako
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── common.py
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── health.py
│   │   │   └── __init__.py
│   │   ├── main.py
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_cors.py
│   │   ├── test_database_error.py
│   │   ├── test_database_health.py
│   │   ├── test_database_unreachable.py
│   │   ├── test_health.py
│   │   └── test_system_info.py
│   ├── .env                 (local, ignored)
│   ├── .env.example
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
│
├── mobile-authenticator/
│   ├── app/
│   │   ├── build.gradle.kts
│   │   └── src/main/
│   │       ├── AndroidManifest.xml
│   │       ├── java/com/ipguard/authenticator/
│   │       │   ├── MainActivity.kt
│   │       │   ├── IPGuardApp.kt
│   │       │   ├── navigation/
│   │       │   │   ├── AppDestination.kt
│   │       │   │   └── AppNavHost.kt
│   │       │   ├── security/
│   │       │   │   ├── DeviceAuthenticationPolicy.kt
│   │       │   │   ├── DeviceKeyExceptions.kt
│   │       │   │   ├── DeviceKeyManager.kt
│   │       │   │   ├── DeviceKeyVerificationRunner.kt
│   │       │   │   ├── DeviceSigningAuthenticator.kt
│   │       │   │   ├── ExportedPublicKey.kt
│   │       │   │   ├── KeySecurityLevel.kt
│   │       │   │   └── KeySecurityMetadata.kt
│   │       │   └── ui/
│   │       │       ├── camera/
│   │       │       │   ├── CameraPermission.kt
│   │       │       │   ├── CameraPreview.kt
│   │       │       │   ├── FacePresenceAnalyzer.kt
│   │       │       │   └── QrCodeAnalyzer.kt
│   │       │       ├── components/
│   │       │       │   ├── AppChrome.kt
│   │       │       │   ├── Controls.kt
│   │       │       │   └── InfoElements.kt
│   │       │       ├── screens/
│   │       │       │   ├── approval/ApprovalScreen.kt
│   │       │       │   ├── deviceinfo/DeviceInformationScreen.kt
│   │       │       │   ├── facegate/FaceGateScreen.kt
│   │       │       │   ├── registration/DeviceRegistrationScreen.kt
│   │       │       │   ├── request/AuthenticationRequestScreen.kt
│   │       │       │   ├── result/ResultScreen.kt
│   │       │       │   ├── scanner/QrScannerScreen.kt
│   │       │       │   ├── settings/SecuritySettingsScreen.kt
│   │       │       │   └── welcome/WelcomeScreen.kt
│   │       │       ├── state/
│   │       │       │   ├── AuthenticatorUiState.kt
│   │       │       │   ├── AuthenticatorViewModel.kt
│   │       │       │   └── PreviewResult.kt
│   │       │       └── theme/Theme.kt
│   │       └── res/values/strings.xml
│   │   ├── test/java/com/ipguard/authenticator/
│   │   │   └── security/
│   │   │       └── ExportedPublicKeyTest.kt
│   │   └── androidTest/java/com/ipguard/authenticator/
│   │       └── security/
│   │           ├── DeviceAuthenticationPolicyTest.kt
│   │           └── DeviceKeyPhysicalInstrumentationTest.kt
│   ├── gradle/wrapper/
│   ├── build.gradle.kts
│   ├── settings.gradle.kts
│   ├── gradle.properties
│   ├── gradlew
│   └── gradlew.bat
│
├── docs/
│   ├── M0_ENVIRONMENT_REPORT.md
│   ├── M0_COMPATIBILITY_REPORT.md
│   ├── M0_TECHNICAL_FEASIBILITY.md
│   ├── M1_TEST_REPORT.md
│   ├── M2_ANDROID_SETUP.md
│   ├── M2_ENVIRONMENT_REPORT.md
│   ├── M2_ARCHITECTURE.md
│   ├── M2_TEST_REPORT.md
│   ├── M2.3A_KEYSTORE_REPORT.md
│   ├── M2.3A_SECURITY_REVIEW.md
│   ├── M2.3B_AUTHENTICATION_REPORT.md
│   ├── PROJECT_STRUCTURE.md
│   ├── DEVELOPMENT_SETUP.md
│   └── assets/
│       ├── m2.0-build-probe.png
│       ├── m2.1/              eleven physical-device screenshots
│       ├── m2.2/              twelve physical-device camera/QR screenshots
│       ├── m2.3a_welcome.png
│       ├── m2.3a_device_info_live.png
│       ├── m2.3a_key_generated.png
│       ├── m2.3a_persistence_verified.png
│       └── m2.3a_key_deleted.png
│
├── scripts/
│   ├── android-env.ps1
│   └── dev-postgres.ps1
│
├── .env                     (local, ignored)
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

### Local/generated artifacts deliberately excluded from Git

```text
frontend/node_modules/
frontend/dist/
frontend/.vite/
backend/.venv/
backend/.pytest_cache/
backend/**/__pycache__/
mobile-authenticator/.gradle/
mobile-authenticator/app/build/
mobile-authenticator/build/
mobile-authenticator/local.properties
logs/
.env
backend/.env
frontend/.env
docs/.obsidian/
```

`docs/.obsidian/` is local Obsidian metadata that appeared in the documentation directory. It was not deleted or overwritten and is ignored by Git.

---

## 2. Architecture Overview

```text
React page (SystemStatusPage)
    │
    ├── useSystemStatus (TanStack Query)
    │
    ├── systemStatus service
    │       ├── /health
    │       ├── /health/database
    │       └── /system/info
    │
    └── single Axios client (api.ts)
                │
                ▼
        FastAPI /api/v1 router
                │
                ├── health route ──► health service
                ├── database route ──► SQLAlchemy Session ──► PostgreSQL
                └── system route
```

The visible M1 page proves the complete readiness chain. It is not a business dashboard.

### Android M2.2 composition

```text
MainActivity (single ComponentActivity)
    │
    └── IPGuardTheme
            │
            └── IPGuardApp
                    ├── AuthenticatorViewModel (preview StateFlow)
                    ├── Navigation Compose controller
                    └── AppNavHost
                            ├── nine screen composables
                            │       ├── FaceGateScreen ──► CameraPreview + FacePresenceAnalyzer
                            │       └── QrScannerScreen ──► CameraPreview + QrCodeAnalyzer
                            ├── camera pipeline (CameraPermission, CameraPreview)
                            ├── shared AppChrome/Controls/InfoElements
                            └── result/{outcome} terminal route
```

The Android application implements on-device CameraX and ML Kit face presence checking and QR code scanning. It has no remote repository, database, HTTP client, biometric, Keystore, or signing layer yet. See [M2_ARCHITECTURE.md](M2_ARCHITECTURE.md).

---

## 3. Frontend Decisions

### Feature-oriented composition

The page-specific implementation lives under `pages/system-status/`, with smaller components split by responsibility:

- `ReadinessHero` — branding, overall state, last check, refresh action.
- `ServiceOverview` — frontend, API, and PostgreSQL probes.
- `EnvironmentPanel` — non-sensitive metadata and API base URL.
- `SystemStatusPage` — query orchestration and error aggregation.

Reusable presentation primitives live under `components/ui/`; the common application frame lives under `components/layout/`.

### Single API client

`src/services/api.ts` is the only Axios instance. It reads `VITE_API_BASE_URL`, applies an 8-second timeout, and converts Axios failures into safe user-facing messages. Feature services must import this client rather than creating new instances.

### Data and state

TanStack Query owns server-state loading, retries, refresh, and cache state. No global state library was added because M1 has no requirement for one. The query is not polled automatically; refresh is explicit.

### Types and utils

- `types/system.ts` describes API payloads and probe results.
- `utils/format.ts` formats latency and timestamps.
- `utils/status.ts` derives the overall status and its label.

### Styling

- Tailwind CSS v4 through `@tailwindcss/vite`; no separate PostCSS setup.
- Design tokens and keyframes are defined in `src/styles/index.css`.
- Dark navy base, teal primary accent, gold secondary accent.
- Responsive grid, reduced-motion support, visible focus treatment.
- No external font request; the application uses a system font stack.

### Routing

React Router provides:

- `/` → redirect to `/system-status`.
- `/system-status` → readiness page.
- Unknown routes → redirect to `/system-status`.

---

## 4. Backend Decisions

### Modular API layout

- `api/router.py` composes versioned routes.
- `api/routes/health.py` owns health and database-health contracts.
- `api/routes/system.py` owns safe application metadata.
- `schemas/common.py` defines response and error models.
- `services/health.py` contains the database probe logic.
- `db/session.py` owns the engine, session factory, and FastAPI dependency injection.
- `core/config.py` owns environment settings.
- `core/errors.py` provides a consistent error envelope and generic 500 handling.

### API versioning

The complete application router is mounted at `/api/v1`. Future endpoints must remain under this prefix unless a new API version is explicitly introduced.

### Database approach

M1 uses synchronous SQLAlchemy sessions with Psycopg 3. This is deliberate:

- The current health probe is a simple query; async SQLAlchemy adds complexity without a present benefit.
- FastAPI can run synchronous dependencies safely in its thread pool.
- The repository can migrate individual use cases to async later if measurements justify it.

The engine uses `pool_pre_ping=True` so a terminated PostgreSQL server does not permanently poison pooled connections. It also uses a 3-second PostgreSQL connect timeout so the health endpoint fails promptly instead of waiting indefinitely during an outage. Session cleanup is guaranteed through a dependency with `try/finally`.

### Error contract

Errors are returned in a consistent shape:

```json
{
  "error": {
    "code": "database_unavailable",
    "message": "PostgreSQL is unavailable."
  }
}
```

Database errors use HTTP 503 and do not return driver text, connection strings, usernames, hostnames, or passwords. Validation errors exclude submitted input values from their response.

### CORS

CORS allows only the origin(s) listed in `CORS_ORIGINS` and only the methods/headers needed by this milestone. The configured development origin is `http://localhost:5173`.

### Configuration

Pydantic Settings resolves the backend `.env` path relative to the backend package, so the API works regardless of whether it is launched from the repository root or the backend directory. Real environment files are ignored by Git. `DATABASE_URL` is required and has no hardcoded credential fallback.

### Migrations

The initial revision `0001_initial` is an intentional baseline with no domain tables. It still exercises Alembic's version-table creation and revision tracking. Domain tables will be added only with the milestone that owns them.

The database currently contains only:

```text
alembic_version
```

This avoids premature asset/user/authentication schemas.

---

## 5. Android Authenticator Decisions

### Single activity and explicit navigation

`MainActivity` hosts one Compose application. `AppDestination` is the route registry, while `AppNavHost` owns callbacks and route transitions. Routes currently use strings rather than type-safe objects because the graph is small, all arguments are primitive preview values, and the navigation library is already verified.

### Preview state boundary

`AuthenticatorViewModel` exposes a read-only `StateFlow<AuthenticatorUiState>`. M2.1 has no mutation path. Device facts come from Android `Build` and `BuildConfig`; the sign-in request and one-phone counts are constants. No DataStore, database, network, or cryptographic object exists yet.

### Terminal result handling

Setup, approval, and rejection converge on `result/{outcome}`. `ResultScreen` intercepts Android system back and returns to Welcome, matching the visible back action. This prevents a completed or rejected approval from returning to the decision screen.

### Shared presentation layer

The theme and three component files own the visual language. Screen files contain composition and copy references, not API calls. All user-facing copy is in `res/values/strings.xml` so later localization and wording review are centralized.

### Deliberately deferred layers

CameraX/ML Kit, Keystore, biometric prompt, DataStore, HTTP/JSON client, challenge handling, and signing are absent. They must be added only with the milestone that owns them and only with physical-device evidence.

---

## 6. Directory Boundaries

| Area | Purpose | Current boundary |
|---|---|---|
| `frontend/src/app` | App-wide providers and routes | No feature business logic |
| `frontend/src/pages` | Route pages and page-specific composition | System Status only |
| `frontend/src/components` | Shared UI and layout | No API calls |
| `frontend/src/services` | HTTP access | One Axios client |
| `frontend/src/hooks` | Server-state orchestration | Readiness query only |
| `backend/app/api` | HTTP contracts | Health and system info only |
| `backend/app/core` | Config and error handling | No domain logic |
| `backend/app/db` | Engine, sessions, migrations | No domain tables |
| `backend/app/models` | Future SQLAlchemy domain models | Intentionally empty placeholder |
| `backend/app/schemas` | API contracts | Health/system metadata |
| `backend/app/services` | Application services | Database health probe |
| `backend/tests` | Automated tests | Health/system/CORS/database behavior |
| `mobile-authenticator/app/src/main/.../navigation` | Route registry and graph | Preview screens only |
| `mobile-authenticator/app/src/main/.../ui/components` | Shared presentation primitives | No API, camera, or crypto calls |
| `mobile-authenticator/app/src/main/.../ui/screens` | Nine screen compositions | Preview UI and static copy |
| `mobile-authenticator/app/src/main/.../ui/state` | Preview state and ViewModel | In-memory constants; no persistence |
| `mobile-authenticator/app/src/main/.../ui/theme` | Compose theme | Styling only |

---

## 7. Infrastructure Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | PostgreSQL 17.11 development container and named volume |
| `.env.example` | Root Compose template with placeholder password |
| `backend/.env.example` | API settings template |
| `frontend/.env.example` | API base URL template |
| `scripts/android-env.ps1` | Session-local Android SDK/JDK/Gradle environment and PATH |
| `scripts/dev-postgres.ps1` | Start/stop/status helper for the local portable PostgreSQL fallback |
| `.gitignore` | Excludes secrets, environments, dependencies, builds, logs, and local metadata |

The Compose file is provided for reproducibility but could not be executed on this machine because Docker is not installed. Local verification used the portable PostgreSQL 17.11 runtime described in the setup guide.

---

## 8. Deliberate Non-Goals

The current structure intentionally does **not** include:

- Android authentication, camera, QR decoding, Keystore, biometric, network, or signing implementation
- Web login/registration routes or live challenge handling
- Domain asset models
- Encryption/steganography modules
- Blockchain tables or services
- Sharing/audit schemas
- WebAuthn or live QR authentication code

These remain outside the completed M0/M1/M2.0/M2.1 scope and must be introduced by their approved milestones. The M2.1 Android screens are preview-only.
