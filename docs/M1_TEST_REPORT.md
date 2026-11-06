# IPGuard M1 Test Report

**Milestone:** M1 — Project Foundation  
**Date:** 2026-11-06  
**Environment:** Windows 11 build 22621, PowerShell 5.1, Node.js 24.18.0, Python 3.13.2, PostgreSQL 17.11, Microsoft Edge headless  
**Repository:** `C:\Users\user\Documents\02_Projects\IPGuard`  
**Physical path:** `D:\Data\Documents\02_Projects\IPGuard`

---

## 1. Result Summary

| Area | Result | Evidence |
|---|---|---|
| Backend automated tests | **PASS** | 8 passed, 1 dependency warning |
| Dependency consistency | **PASS** | `pip check`: no broken requirements |
| Alembic state | **PASS** | `0001_initial (head)`, no pending upgrade operations |
| Live API health | **PASS** | HTTP 200 with expected metadata |
| Live PostgreSQL health | **PASS** | HTTP 200, real query, observed latency 0.78–41.66 ms |
| Real database outage | **PASS** | HTTP 503 in 3.02 seconds, generic error |
| Database recovery | **PASS** | HTTP 200 after restart, about 38 ms transport time |
| Frontend type safety | **PASS** | `tsc --noEmit` |
| Frontend production build | **PASS** | Vite build completed |
| Production dependency audit | **PASS** | 0 reported vulnerabilities |
| Browser UI states | **PASS** | Loading, healthy, refresh, error |
| Responsive layout | **PASS** | 390, 768, and 1440 px; no horizontal overflow |
| Secret-file exclusion | **PASS** | Active local password not found in untracked files |
| Docker Compose | **NOT TESTED** | Docker is not installed |
| Android runtime/hardware | **NOT TESTED** | M2 scope; SDK/toolchain absent |

M1 is functionally complete for the local Windows development foundation. The untested items are recorded as limitations, not as verified results.

---

## 2. Environment Under Test

```text
OS                 Windows 11 Home Single Language, 10.0.22621, 64-bit
PowerShell         5.1.22621.4249
Node.js            24.18.0
npm                11.16.0
Python             3.13.2
pytest             9.2.0
FastAPI            0.162.0
Uvicorn            0.54.0
SQLAlchemy         2.1.8
Pydantic           2.14.3
Alembic            1.20.1
Psycopg            3.3.8
PostgreSQL         17.11 (x86_64-windows)
React              19.3.1
Vite               8.3.6
TypeScript         7.0.2
Browser            Microsoft Edge, headless through temporary Playwright-core
```

Portable PostgreSQL runtime:

```text
C:\Users\user\AppData\Local\IPGuard\pgsql\17.11
C:\Users\user\AppData\Local\IPGuard\pgdata
```

The data directory and credentials are outside the repository and are not tracked.

---

## 3. Backend Automated Tests

Command:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -v
```

Result:

```text
collected 8 items

tests\test_cors.py ..                                                    [ 25%]
tests\test_database_error.py .                                           [ 37%]
tests\test_database_health.py .                                          [ 50%]
tests\test_database_unreachable.py .                                     [ 62%]
tests\test_health.py ..                                                  [ 87%]
tests\test_system_info.py .                                              [100%]

8 passed, 1 warning in 3.13s
```

| Test file | Assertions | Result |
|---|---|---|
| `test_health.py` | Health metadata; unknown-route error envelope | PASS |
| `test_database_health.py` | Real PostgreSQL connection; status, engine, numeric latency | PASS |
| `test_database_error.py` | Safe 503 envelope; no private driver text, password, or URL | PASS |
| `test_database_unreachable.py` | Unreachable database fails within 5 seconds; safe 503 error | PASS |
| `test_system_info.py` | Non-sensitive metadata; no password or database URL | PASS |
| `test_cors.py` | Allowed origin header; unknown origin receives no CORS header | PASS |

The only warning is:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

This is a dependency-evolution warning. It did not fail a test.

`pip check` result:

```text
No broken requirements found.
```

---

## 4. Database and Migration Verification

Commands:

```powershell
.\.venv\Scripts\alembic.exe -c alembic.ini current
.\.venv\Scripts\alembic.exe -c alembic.ini check
```

Results:

```text
0001_initial (head)
No new upgrade operations detected.
```

Direct PostgreSQL inspection:

```text
database: ipguard
server:   PostgreSQL 17.11 on x86_64-windows
public tables: alembic_version
revision: 0001_initial
```

The empty baseline is intentional. M1 does not create asset, user, authentication, blockchain, or sharing tables.

---

## 5. Live API Verification

The backend was started with:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Service health

```http
GET /api/v1/health
```

```json
{
  "status": "ok",
  "service": "ipguard-api",
  "version": "1.0.0"
}
```

### Database health

```http
GET /api/v1/health/database
```

```json
{
  "status": "ok",
  "database": "postgresql",
  "latency_ms": 41.66
}
```

The value varied with pool warmth: 41.66 ms in the representative response above, 35.44 ms after recovery, and 0.78 ms on the final warm check. This endpoint performs a real `SELECT 1`; it does not return a hardcoded healthy response.

### System information

```http
GET /api/v1/system/info
```

```json
{
  "name": "IPGuard",
  "version": "1.0.0",
  "environment": "development",
  "api_version": "v1",
  "database_engine": "postgresql"
}
```

No credentials, database URL, host, user, or secret is returned.

---

## 6. Real Outage and Recovery Test

This test used the actual PostgreSQL server and the actual API; it did not mock the outage.

Steps:

1. Stop PostgreSQL with `scripts\dev-postgres.ps1 stop`.
2. Call `/api/v1/health/database` with an 8-second client limit.
3. Start PostgreSQL with `scripts\dev-postgres.ps1 start`.
4. Repeat the database health request until it succeeds.

Outage result:

```text
HTTP=503 TIME=3.019786
{"error":{"code":"database_unavailable","message":"PostgreSQL is unavailable."}}
```

Recovery result:

```text
HTTP=200 TIME=0.038429
{"status":"ok","database":"postgresql","latency_ms":35.44}
```

Conclusions:

- The API returns HTTP 503 rather than a misleading HTTP 200.
- The response body is generic and contains no driver or credential details.
- The 3-second PostgreSQL connect timeout prevents an indefinite wait.
- `pool_pre_ping=True` allows the pool to recover after PostgreSQL returns.
- PostgreSQL accepted connections again after restart.

The helper's final status:

```text
pg_ctl: server is running
127.0.0.1:5432 - accepting connections
```

---

## 7. Frontend Verification

### Typecheck

```powershell
Set-Location frontend
npm run typecheck
```

Result: PASS; no TypeScript diagnostics.

### Production build

```powershell
npm run build
```

Result:

```text
dist/index.html                   0.64 kB │ gzip:   0.37 kB
dist/assets/index-CCR-jIvp.css   41.19 kB │ gzip:   7.53 kB
dist/assets/index-BBcCfRIw.js   373.11 kB │ gzip: 120.22 kB

built in 425ms
```

### Dependency audit

```text
Production dependency vulnerabilities: 0
```

This is a point-in-time npm audit result, not a guarantee for future dependency versions.

### Browser integration test

The browser test used the installed Microsoft Edge in headless mode. Playwright-core was installed only in a temporary directory outside the repository; it was not added to frontend dependencies.

Observed states:

| State | Result |
|---|---|
| Initial loading | PASS — hero shows secure-connection loading copy and “Checking systems” |
| Healthy | PASS — all layers online; API base URL visible |
| Refresh busy | PASS — button shows “Refreshing connection” and is disabled |
| Backend unavailable | PASS — error alert and “Core services unreachable” |
| Error message | `Connection attention required / Backend API — The service could not be reached.` |
| Backend process stopped by test | PASS, deliberately for the error-state check |

Saved evidence in the ignored `logs` directory:

```text
logs/system-status.loading.png
logs/system-status.healthy.png
logs/system-status.error.png
logs/system-status.mobile.png
logs/ui-verification.json
```

The backend was restarted after the error-state test. Final live health checks returned HTTP 200.

### Responsive verification

Measured `document.documentElement.scrollWidth` and `document.body.scrollWidth` against `window.innerWidth`:

| Viewport | Horizontal overflow |
|---|---|
| 390 × 844 | None |
| 768 × 900 | None |
| 1440 × 1000 | None |

The mobile screenshot confirmed that the header, readiness hero, service cards, environment panel, and footer remain usable at 390 px. This was a layout check, not a formal WCAG audit.

---

## 8. Security and Configuration Checks

| Check | Result |
|---|---|
| `.env` ignored by Git | PASS |
| `backend/.env` ignored by Git | PASS |
| `frontend/.env` ignored by Git | PASS |
| `.venv`, `node_modules`, `dist`, `logs` ignored | PASS |
| `docs/.obsidian` ignored without deleting local metadata | PASS |
| Active database password absent from untracked source/docs | PASS |
| Allowed CORS origin only | PASS |
| Unknown origin receives no CORS header | PASS |
| Database failure response sanitized | PASS |
| System info contains no database URL or password | PASS |
| No secrets in frontend bundle flow | PASS — frontend only receives `VITE_API_BASE_URL` |

The Git repository was initialized with branch `main`. No commit was created. The local real environment files remain untracked and ignored.

---

## 9. M1 Definition-of-Done Traceability

| Requirement | Status | Evidence |
|---|---|---|
| Monorepo with frontend, backend, docs, scripts | PASS | Actual source tree in `PROJECT_STRUCTURE.md` |
| Frontend runs and builds | PASS | Typecheck, Vite build, dev server |
| Backend runs | PASS | Live Uvicorn process and HTTP checks |
| PostgreSQL configured | PASS | PostgreSQL 17.11 accepting connections |
| Environment templates | PASS | Three `.env.example` files, placeholders only |
| No secrets tracked | PASS | Ignore checks and secret scan; no commit created |
| System Status page | PASS | Browser screenshots and UI state checks |
| Real frontend → API → DB chain | PASS | Live database probe with measured latency |
| Health endpoint | PASS | HTTP 200 and expected JSON |
| Database health endpoint | PASS | Real query; 200 healthy, 503 unavailable |
| Consistent error handling | PASS | 404, 503, and validation handlers |
| CORS restricted to frontend | PASS | Automated allow/deny tests |
| API versioning | PASS | `/api/v1` |
| Alembic initialized | PASS | Baseline head and check |
| Automated tests | PASS | 8 tests |
| Loading/error/refresh states | PASS | Headless Edge integration test |
| Responsive layout | PASS | Three viewport widths |
| M0 documentation retained | PASS | Three M0 reports |
| No M2 feature creep | PASS | No login, asset, cryptography, blockchain, or Android implementation |

---

## 10. Known Limitations

1. **Docker Compose was not executed.** Docker is not installed on this machine. The provided Compose file is therefore unverified at runtime.
2. **Android is not implemented or tested.** Android Studio, SDK, Gradle, and an APK runtime are absent. Keystore, StrongBox, BiometricPrompt, CameraX, and ML Kit remain M2 work.
3. **The Starlette/HTTPX deprecation warning remains.** It is non-fatal; all tests pass.
4. **Database outage detection is bounded, not instantaneous.** The configured connect timeout is 3 seconds, producing a measured 503 at about 3.02 seconds.
5. **No formal accessibility audit was performed.** Semantic structure, keyboard focus, labels, reduced-motion CSS, and responsive behavior were considered, but no axe/WCAG certification is claimed.
6. **No production deployment was performed.** HTTPS, reverse proxy, backups, monitoring, process supervision, and production secrets management are outside M1.
7. **The local portable PostgreSQL runtime is outside the repository.** It is user-local, single-node, and not a Windows service.
8. **Docker and Android commands are documented but marked unverified** in the setup guide.

---

## 11. M2 Readiness

### Foundation: GO

The M1 backend, frontend, database path, error behavior, configuration, and tests are ready to support the next milestone.

### Android authenticator: CONDITIONAL / NOT READY

Before authenticator implementation can be verified:

1. Install Android Studio and the required SDK/platform/build tools, preferably on D: because C: free space is limited.
2. Verify a Gradle project builds and installs on the connected `SM-A546E` (Android 16/API 36, arm64-v8a).
3. Run a hardware-backed Keystore probe on the device.
4. Verify biometric capability, enrollment state, and the intended authentication class.
5. Verify CameraX and ML Kit Face Detection behavior with the target device camera.
6. Define the challenge-response and QR protocol before implementing security-sensitive flows.

### Architecture guardrails for M2

- Do not treat ML Kit Face Detection as face recognition.
- Do not log or transmit raw biometric data.
- Do not place secrets in QR codes.
- Keep database credentials server-side.
- Add domain tables only through reviewed Alembic revisions.
- Add tests for each new security boundary before representing it as complete.

---

## 12. Final State

At the end of verification:

- PostgreSQL is running on `127.0.0.1:5432`.
- FastAPI is running on `127.0.0.1:8000`.
- Vite is running on port 5173.
- The API health and database health endpoints return HTTP 200.
- Git is initialized on `main`; no commit has been created.
- M1 documentation is complete.
