# IPGuard Development Setup

**Project:** IPGuard — Secure Digital Asset Protection  
**Milestone:** M1 baseline plus current M2.1 authenticator interface  
**Platform:** Windows 11 / PowerShell 5.1  
**Last verified:** 2026-11-06

---

## 1. Prerequisites

| Requirement | Tested version | Notes |
|---|---|---|
| Windows | Windows 11 build 22621 | PowerShell 5.1.22621.4249 used |
| Node.js | 24.18.0 | Node 22.12 or newer required by the frontend toolchain |
| npm | 11.16.0 | Installed with Node.js |
| Python | 3.13.2 | `venv` support verified |
| pip | 26.2.2 in the system interpreter | The backend virtual environment contains its own pip |
| Git | 2.54.0.windows.1 | Do not commit without owner approval |
| PostgreSQL | 17.11 | Local portable runtime used for M1 verification |
| JDK | Temurin 17.0.20.1 | Required for the Android build; use `scripts\android-env.ps1` |
| Android SDK | API 36 / Build Tools 36.0.0 | Installed on D:; physical-device testing only |
| Gradle | 8.13 Wrapper | Checksum-pinned; do not use the global Gradle |
| Docker | Not installed | Compose file provided but not executed on this machine |

Android Studio, the Android SDK, Gradle, and the mobile authenticator are **not required for M1**, but the M2.0 CLI toolchain is now installed and the M2.1 interface is verified. See [M2_ANDROID_SETUP.md](M2_ANDROID_SETUP.md) and [M2_TEST_REPORT.md](M2_TEST_REPORT.md). Android Studio remains intentionally absent.

The repository path is:

```text
C:\Users\user\Documents\02_Projects\IPGuard
```

Windows maps `C:\Users\user\Documents` to `D:\Data\Documents` through a junction. The C: alias is valid; the physical files use D: capacity.

---

## 2. Environment Files

There are three environment files:

| File | Purpose | Commit? |
|---|---|---|
| `.env` | Docker Compose database variables | Never |
| `backend/.env` | FastAPI settings and database URL | Never |
| `frontend/.env` | Vite API base URL | Never |

The corresponding `.env.example` files contain placeholders only. Real local credentials were generated during M1 and stored only in ignored `.env` files.

### Backend settings

```dotenv
APP_NAME=IPGuard
APP_VERSION=1.0.0
APP_ENV=development
DATABASE_URL=postgresql+psycopg://ipguard:replace_with_a_strong_local_password@127.0.0.1:5432/ipguard
CORS_ORIGINS=http://localhost:5173
```

Notes:

- `DATABASE_URL` must use the `postgresql+psycopg://` driver prefix for Psycopg 3.
- URL-encode special characters in a password before putting it into the URL.
- Keep `CORS_ORIGINS` limited to the frontend origin(s) actually used.
- The API validates that `DATABASE_URL` exists and stops with a clear startup error if it is missing.
- The database engine uses a 3-second PostgreSQL connect timeout so health checks fail fast during an outage.

### Frontend settings

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Do not add a trailing slash; the client normalizes trailing slashes.

---

## 3. Database Setup

### Option A — Docker Compose (not verified on this machine)

Docker is unavailable in the current M0 environment, so these commands were **not executed**:

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard
Copy-Item .env.example .env
# Edit .env and replace POSTGRES_PASSWORD with a strong local-only password.
docker compose up -d database
docker compose ps
```

The Compose service is named `database`. The volume is `ipguard_postgres_data`. To stop the container without deleting data:

```powershell
docker compose stop database
```

Do not use `docker compose down -v` unless you intend to delete the local database volume.

### Option B — Existing local PostgreSQL

Create the role and databases from an administrator PostgreSQL session. The password below is a placeholder; use a local secret:

```sql
CREATE ROLE ipguard LOGIN PASSWORD 'replace_with_a_strong_local_password';
CREATE DATABASE ipguard OWNER ipguard;
CREATE DATABASE ipguard_test OWNER ipguard;
```

Then set `backend/.env` to use the matching `DATABASE_URL`.

### Option C — Portable PostgreSQL used for M1

This machine's runtime is outside the repository:

```text
C:\Users\user\AppData\Local\IPGuard\pgsql\17.11
C:\Users\user\AppData\Local\IPGuard\pgdata
C:\Users\user\AppData\Local\IPGuard\secrets\postgres.env
```

The server listens on `127.0.0.1:5432`. It is not a Windows service and is not on the global `PATH`. The helper script was verified with all three actions:

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard
.\scripts\dev-postgres.ps1 status
.\scripts\dev-postgres.ps1 start
.\scripts\dev-postgres.ps1 stop
```

Override paths if the runtime is moved:

```powershell
$env:IPGUARD_PG_ROOT = 'D:\dev-tools\pgsql\17.11'
$env:IPGUARD_PGDATA = 'D:\dev-data\ipguard\pgdata'
$env:IPGUARD_PGLOG_DIR = 'D:\dev-data\ipguard\logs'
.\scripts\dev-postgres.ps1 start
```

Do not commit the data directory or secret file. They are outside the repository and are not tracked.

---

## 4. Backend Setup

### First-time installation

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
Copy-Item .env.example .env
# Edit backend\.env and set a real local DATABASE_URL.
```

The verified installation produced these direct versions:

```text
fastapi 0.162.0
uvicorn 0.54.0
SQLAlchemy 2.1.8
pydantic 2.14.3
pydantic-settings 2.16.2
alembic 1.20.1
psycopg 3.3.8
pytest 9.2.0
httpx 0.28.1
```

### Apply migrations

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\backend
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
.\.venv\Scripts\alembic.exe -c alembic.ini current
```

Expected current revision:

```text
0001_initial (head)
```

`0001_initial` is a deliberate baseline with no domain tables. The database currently contains only `alembic_version`.

### Start the API

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/api/v1/health`
- Database health: `http://localhost:8000/api/v1/health/database`
- System info: `http://localhost:8000/api/v1/system/info`
- Swagger UI: `http://localhost:8000/docs`

Stop the API with `Ctrl+C` in its terminal.

### Backend tests

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\backend
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m pip check
```

The database-health test is an integration test and requires PostgreSQL to be running. If PostgreSQL is down, the health test will fail by design; the separate mocked failure test still verifies safe 503 handling.

---

## 5. Frontend Setup

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\frontend
npm install --no-fund
Copy-Item .env.example .env
npm run dev
```

Open:

```text
http://localhost:5173/system-status
```

The Vite dev server is configured for port `5173` with `strictPort: true`. If the port is occupied, identify the owning process rather than killing it blindly:

```powershell
Get-NetTCPConnection -LocalPort 5173 -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

### Typecheck and production build

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\frontend
npm run typecheck
npm run build
```

The production build is written to `frontend\dist`. To preview it:

```powershell
npm run preview
```

The `preview` script is configured but was not the primary M1 integration path; M1 used the verified Vite development server and a headless browser.

### npm audit

A production-scope audit at M1 time reported zero vulnerabilities:

```text
vulnerabilities: 0
```

This is a snapshot, not a permanent security guarantee. Re-run the audit when dependencies change.

---

## 6. Full Local Verification Checklist

Run these commands from the repository root unless noted.

```powershell
# 1. Database
.\scripts\dev-postgres.ps1 status

# 2. Backend tests
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\alembic.exe -c alembic.ini current
Set-Location ..

# 3. Frontend checks
Set-Location frontend
npm run typecheck
npm run build
Set-Location ..

# 4. Android build and lint
. .\scripts\android-env.ps1
Set-Location mobile-authenticator
.\gradlew.bat :app:assembleDebug :app:lintDebug
adb install -r app\build\outputs\apk\debug\app-debug.apk
adb shell am start -W -n com.ipguard.authenticator/.MainActivity
Set-Location ..

# 5. Start the API in one terminal
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 6. Start the frontend in another terminal
Set-Location frontend
npm run dev
```

Then open `http://localhost:5173/system-status` and use **Refresh connection**.

Expected healthy state:

- Frontend card: Online
- Backend API card: Online
- PostgreSQL card: Online
- Hero: “All core systems operational”
- API base URL: `http://localhost:8000/api/v1`

### API checks from PowerShell

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/database
Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/info
```

---

## 7. Verified vs Unverified Commands

### Verified on this machine

- Node.js, npm, Python, pip, Git, and ADB version checks
- PostgreSQL portable binary checks (`postgres`, `psql`, `initdb`)
- PostgreSQL cluster initialization, role/database creation, startup, and shutdown
- `scripts\dev-postgres.ps1 start|stop|status`
- Alembic `upgrade head`, `current`, and `check`
- FastAPI startup through the backend virtual environment
- All three API endpoints via live HTTP calls
- Actual PostgreSQL outage test (HTTP 503 in about 3 seconds) and recovery (HTTP 200)
- `pip install -r requirements.txt`, `pip check`, and `pytest`
- `npm install`, `npm run typecheck`, `npm run build`, and `npm run dev`
- Browser-level UI verification using the installed Microsoft Edge in headless mode
- Loading, healthy, refresh-busy, and API-error UI states
- Database session injection, CORS allow/deny behavior, and safe error shapes
- Android SDK/JDK/Gradle environment through `scripts\android-env.ps1`
- `:app:assembleDebug`, `:app:lintDebug`, APK install, and cold launch on the physical Samsung SM-A546E
- All nine M2.1 screens, setup/approval/rejection preview flows, terminal result back behavior, and absence of fatal app exceptions

### Not verified on this machine

- `docker compose up` (Docker is not installed)
- Docker volume persistence
- Android camera, QR, Face Gate, BiometricPrompt, Keystore, StrongBox, attestation, signing, or live backend integration
- Android Studio and emulator behavior (intentionally not installed)
- HTTPS deployment or certificate pinning
- Production hosting, reverse proxy, backups, and monitoring
- `npm run preview` as the primary integration server

These are recorded limitations, not claimed successes.

---

## 8. Troubleshooting

### Database health returns HTTP 503

1. Verify PostgreSQL is running:

   ```powershell
   .\scripts\dev-postgres.ps1 status
   ```

2. Verify the port:

   ```powershell
   Get-NetTCPConnection -LocalPort 5432 -State Listen
   ```

3. Verify `DATABASE_URL` in `backend\.env` uses `postgresql+psycopg://`.
4. Check that the role can log in and that the database exists.
5. Restart the API after fixing configuration.

The API intentionally does not return the raw driver error. The connect timeout is 3 seconds, so an unavailable PostgreSQL server normally produces the 503 response in roughly that time. Inspect local logs if needed, but never add passwords or complete connection URLs to application logs.

### CORS error in the browser

- The browser origin must exactly match an entry in `CORS_ORIGINS`.
- `http://localhost:5173` and `http://127.0.0.1:5173` are different origins.
- Update the backend `.env` and restart the API after changing origins.
- Do not use a wildcard for credentialed production traffic.

### Port already in use

Check the owner before taking action:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

Change the port explicitly in the relevant command and update the frontend API URL or backend CORS setting. Do not terminate an unrelated user process.

### Alembic cannot import `app`

Run Alembic from `backend\`, where `alembic.ini` has `prepend_sys_path = .`, or invoke it with an explicit working directory. The verified command is:

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\backend
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
```

### Pytest warning about Starlette TestClient and HTTPX

The M1 test run emits one warning:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

All backend tests pass at the time of this note. The warning is recorded as a known dependency-evolution item; HTTPX remains the requested test dependency for M1.

### C: drive space

The project is physically on D: through the Documents junction, but the portable PostgreSQL runtime is under C:. Android SDK, JDK, Gradle, and project caches are already installed on D:. Monitor:

```powershell
Get-PSDrive C, D | Select-Object Name, @{n='FreeGB';e={[math]::Round($_.Free/1GB,2)}}
```

---

## 9. Security Rules for Contributors

- Never commit `.env`, database credentials, private keys, or real tokens.
- Never log a full `DATABASE_URL`; it can contain a password.
- Keep CORS restricted to the actual frontend origin.
- Do not put secrets into QR payloads later.
- Do not represent ML Kit Face Detection as face recognition.
- Do not add product features outside the active milestone without owner approval.
- Do not run destructive database commands against a non-development database.
- Do not create a Git commit or push without explicit approval.
