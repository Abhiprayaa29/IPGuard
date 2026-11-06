# M0 Compatibility Report

**Project:** IPGuard  
**Milestone:** M0 — Compatibility & Preparation  
**Date:** 2026-11-06  
**Scope:** Compatibility of the planned frontend, backend, database, infrastructure, and mobile-authenticator stack with the current Windows environment.

---

## 1. Compatibility Decision

| Area | Decision | Notes |
|---|---|---|
| Windows development | COMPATIBLE | PowerShell 5.1 and Windows 11 build 22621 |
| React + TypeScript + Vite | COMPATIBLE, NOT YET INSTALLED | Node.js 24.18.0 and npm registry availability verified |
| Python + FastAPI | COMPATIBLE, NOT YET INSTALLED | Python 3.13.2 and PyPI availability verified |
| PostgreSQL | COMPATIBLE VIA PORTABLE RUNTIME | PostgreSQL 17.11 binaries verified; Docker absent |
| Docker Compose infrastructure | DOCUMENTED, NOT RUNNABLE HERE | Docker/Compose are not installed |
| Android build toolchain | INCOMPLETE | ADB and a device exist; Android Studio/SDK/Gradle do not |
| Android authenticator design | FEASIBLE, RUNTIME UNVERIFIED | Design is technically coherent; physical PoC belongs to M2 |
| M1 start | ALLOWED | No critical frontend/backend/database blocker |

No compatibility claim is made for Android build or hardware cryptographic behavior until it is tested in M2.

---

## 2. Windows and PowerShell Compatibility

The project must run from Windows PowerShell without relying on Unix-only tooling.

| Concern | Assessment | Mitigation |
|---|---|---|
| Long paths | Workspace path is moderately long: `C:\Users\user\Documents\02_Projects\IPGuard`; the Documents directory is a junction to `D:\Data\Documents` | Keep dependency directories shallow; enable long paths only if a real failure appears |
| Shell syntax | PowerShell 5.1 cannot use `&&` | Use `;`, `if ($?)`, or documented separate commands |
| Execution policy | Not yet tested for project scripts | Document `powershell -ExecutionPolicy Bypass -File ...` if needed |
| Path separators | Python, Node, Vite, and Alembic support Windows paths | Use `pathlib` in backend code where paths are constructed |
| Portable PostgreSQL | Verified by executing `postgres --version`, `psql --version`, and `initdb --version` | Use full binary paths; do not assume `psql` is on PATH |
| Docker | Unavailable | Portable local PostgreSQL is the current verification path |
| File watching | Vite/Uvicorn on Windows are supported | Verify during M1; avoid network drives |
| C: disk space | 6.79 GB free at M0 time | Place future Android SDK/emulator and Gradle caches on D:; the project itself is physically on D: via the Documents junction |

---

## 3. Frontend Compatibility

### Runtime prerequisites

| Requirement | Environment | Result |
|---|---|---|
| Node.js >= 20.19 (Vite 7 class) | Node.js 24.18.0 | PASS |
| npm | 11.16.0 | PASS |
| Git | 2.54.0 | PASS |
| npm registry access | HTTP 200 from registry | PASS |

The exact application dependency versions will be resolved and recorded during M1 installation and in `docs/M1_TEST_REPORT.md`. The planned stack is compatible with current Node.js:

- React 19.x
- TypeScript 5.x
- Vite 7.x
- Tailwind CSS v4 with `@tailwindcss/vite`
- React Router 7.x
- TanStack Query 5.x
- Axios 1.x
- Lucide React

No frontend blocker was found. Tailwind v4's Vite plugin avoids a separate PostCSS configuration and is the intended integration.

### Network assumptions

- Frontend dev server: `http://localhost:5173`
- API base: `http://localhost:8000/api/v1`
- CORS must allow only the configured frontend origin.
- The frontend must use `VITE_API_BASE_URL` rather than hardcoding the API origin in multiple modules.

---

## 4. Backend Compatibility

| Requirement | Environment | Result |
|---|---|---|
| Python | 3.13.2 | PASS |
| pip | 26.2.2 | PASS |
| venv | Available | PASS |
| PyPI access | HTTP 200 | PASS |
| Windows Uvicorn host | Supported | Expected PASS; verify during M1 |
| Psycopg 3 | Windows wheels available for current Python | Expected PASS; verify installation |
| SQLAlchemy 2.x | Supports Python 3.13 | Expected PASS; verify installation |
| FastAPI / Pydantic 2.x | Support Python 3.13 | Expected PASS; verify installation |
| Alembic | Pure Python / supported | Expected PASS; verify migration |
| Pytest / HTTPX | Supported | Expected PASS; verify tests |

The backend will use synchronous SQLAlchemy sessions in M1. This avoids unnecessary async complexity in the initial foundation while still providing a production-viable architecture. FastAPI remains capable of serving async routes later when a concrete need arises.

No backend blocker was found.

---

## 5. Database Compatibility

### Environment state

- No Windows PostgreSQL service was installed.
- No `psql` on PATH.
- No Docker or Docker Compose.
- Port 5432 was free.
- PostgreSQL 17.11 x64 portable binaries were downloaded from EDB, extracted locally, and their executables were verified.
- No global installation, PATH modification, service registration, or registry change was made.

### Portable runtime

```text
C:\Users\user\AppData\Local\IPGuard\pgsql\17.11
```

Verified:

```text
postgres (PostgreSQL) 17.11
psql (PostgreSQL) 17.11
initdb (PostgreSQL) 17.11
```

### Compatibility assessment

| Requirement | Assessment |
|---|---|
| PostgreSQL on Windows x64 | COMPATIBLE; binaries execute |
| Psycopg 3 driver to PostgreSQL 17 | COMPATIBLE by design; will be proven in M1 |
| SQLAlchemy 2.x + psycopg | COMPATIBLE; will be proven in M1 |
| Alembic migrations | COMPATIBLE; will be proven in M1 |
| Docker Compose delivery | CANNOT RUN HERE; file will still be provided |
| Database service availability | Will be a locally managed process for M1 verification |
| Credential handling | `.env` files will be gitignored; examples contain no real password |

### Port choice

`5432` is free and will be used by the portable instance unless it becomes occupied. If a later conflict occurs, the port will be changed explicitly in `.env` and documented; no process will be terminated automatically.

---

## 6. Android and Mobile Authenticator Compatibility

### What is available

- ADB 1.0.41 / 37.0.0
- Authorized Samsung SM-A546E device
- Android 16 / API 36
- arm64-v8a
- Platform feature declarations for face, fingerprint, hardware keystore, app attestation key, secure lock screen, and cameras

### What is missing

- Android Studio
- Android SDK
- `sdkmanager` / `avdmanager`
- Build tools (`aapt2`, `apksigner`)
- Emulator
- Gradle / Gradle wrapper
- Local Kotlin compiler
- A test APK and any runtime verification of Keystore or biometrics

### JDK assessment

Oracle JDK 22.0.2 is installed. It is not the recommended default for an Android project. For M2:

1. Prefer the JetBrains Runtime bundled with Android Studio.
2. Otherwise use a supported JDK 17 or 21 and point Gradle at it explicitly.
3. Do not assume JDK 22 works with the selected Android Gradle Plugin until tested.

### Device-feature interpretation

The connected device declares face and fingerprint hardware. That does **not** prove:

- that face unlock is Class 3 (BIOMETRIC_STRONG);
- that face recognition identity matching is available to a custom app;
- that StrongBox is present;
- that a non-exportable P-256 key can be created and used for signing;
- that biometric-gated key use succeeds;
- that ML Kit face detection or barcode scanning works with the installed Google Play services;
- that camera/QR flow works in the final app.

These are M2 runtime tests. The mobile authenticator must not be described as hardware-verified before then.

### Android build compatibility conclusion

The conceptual stack is compatible with modern Android:

- Kotlin native application
- Android Keystore / ECDSA P-256
- Android BiometricPrompt
- CameraX
- ML Kit Face Detection
- ML Kit Barcode Scanning
- HTTPS
- QR-based pairing

The **build environment is not ready**, but this does not block M1. Android Studio and the SDK must be installed and verified before M2 implementation.

---

## 7. Smartphone Authenticator Design Compatibility

The design separates three concerns:

1. **Face presence gate (UX):** ML Kit Face Detection can detect a face and its position. It is not face recognition.
2. **Device possession/authentication (security):** a non-exportable Android Keystore private key signs a backend challenge; the backend verifies with the registered public key.
3. **Biometric authorization (local key use):** BiometricPrompt can require a strong biometric before the key operation.

This separation is technically sound. It avoids the common but incorrect assumption that "a face was detected" equals "the registered user was recognized and authenticated."

### Compatibility caveats

| Caveat | Consequence |
|---|---|
| ML Kit Face Detection is not recognition | It cannot prove user identity by itself |
| Face unlock quality varies by device | Do not assume strong face biometrics |
| StrongBox is optional | Must probe availability and fall back to TEE/software-backed keys |
| Key attestation must be validated | A public key registration without attestation can be spoofed |
| Biometric enrollment changes can invalidate keys | Define recovery/re-enrollment UX in M2 |
| QR pairing is a bootstrap step, not authentication | Pairing must be user-confirmed and short-lived |
| HTTPS alone is insufficient | Add challenge TTL, one-time nonces, replay protection, origin/device binding |
| Mobile device may be offline | Challenge must be time-bounded and failure-safe |

Overall: **CONCEPTUALLY COMPATIBLE; HARDWARE RUNTIME UNVERIFIED**.

---

## 8. Port, Service, and Resource Compatibility

| Resource | Current state | Required action |
|---|---|---|
| Port 5173 | Free | Use for Vite |
| Port 8000 | Free | Use for FastAPI |
| Port 5432 | Free | Use for PostgreSQL |
| Existing Node processes | None blocking identified ports | Recheck before starting M1 |
| Existing PostgreSQL services | None | Local portable process will be used |
| Docker daemon | Unavailable | Document alternative; do not require Docker |
| C: free space | 6.79 GB | Tight for M2 Android tooling |
| D: free space | 60.89 GB | Preferred location for Android SDK/emulator/Gradle caches |

---

## 9. Dependency and Tool Gaps

### Blockers for M1

None, provided the portable PostgreSQL runtime is used and the machine remains online for npm/PyPI package installation.

### Non-blocking gaps for M1

- Docker and Docker Compose
- System PostgreSQL client
- Android Studio/SDK/Gradle
- Android-compatible JDK baseline
- StrongBox/biometric verification

### M2 prerequisites

1. Install Android Studio plus SDK Platform Tools and an SDK platform.
2. Create and commit a Gradle wrapper.
3. Configure a supported JDK.
4. Build and install a minimal proof-of-concept APK.
5. Query and record Keystore/StrongBox/biometric capability on the physical device.
6. Decide whether the Face Gate is only face-presence detection or requires a separate liveness/recognition design. If recognition is required, define the on-device model, privacy model, thresholds, and anti-spoofing approach explicitly.

---

## 10. M0 Acceptance Verification

| Criterion | Result |
|---|---|
| Workspace checked | PASS |
| Windows environment checked | PASS |
| Node.js and npm checked | PASS |
| Python and pip checked | PASS |
| Git checked | PASS |
| PostgreSQL or Docker alternative checked | PASS via portable PostgreSQL; Docker absent |
| Android development tools checked | PASS with gaps |
| Smartphone authentication architecture analyzed | PASS |
| Android Keystore feasibility analyzed | PASS (design), runtime pending |
| Face Gate and face recognition distinguished | PASS |
| All constraints documented | PASS |

**Compatibility conclusion:** M1 may proceed. The environment supports the M1 stack, with PostgreSQL supplied by a user-local portable runtime. Android development readiness is **PARTIAL** and must be completed before M2.
