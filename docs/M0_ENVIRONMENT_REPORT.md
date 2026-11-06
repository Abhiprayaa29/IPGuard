# M0 Environment Report

**Project:** IPGuard — Secure Digital Asset Protection  
**Milestone:** M0 — Compatibility & Preparation  
**Date:** 2026-11-06  
**Status:** COMPLETED WITH RECORDED LIMITATIONS  
**Scope:** Workspace and development-environment verification only. No product features or Android source code were created.

---

## 1. Executive Summary

The Windows workspace is available at `C:\Users\user\Documents\02_Projects\IPGuard` and was empty before M0. There was no Git repository, no previous configuration, and no user work to preserve.

Frontend, backend, and database work for M1 is not blocked:

- Node.js 24.18.0 and npm 11.16.0 are available.
- Python 3.13.2, pip 26.2.2, and `venv` are available.
- Git 2.54.0 is available.
- Docker and a PostgreSQL system installation are not available.
- PostgreSQL 17.11 was provisioned as a **user-local portable runtime** for local verification. It is not a Windows service and was not added to the global `PATH`.
- Android build tooling (Android Studio, Android SDK, `sdkmanager`, Gradle) is not installed.
- A physical Android device is connected through ADB: Samsung SM-A546E, Android 16 (API 36), arm64-v8a.

M1 can proceed. Android build and physical cryptographic testing remain deferred to M2.

---

## 2. Operating System Information

| Item | Value |
|---|---|
| OS | Microsoft Windows 11 Home Single Language |
| Version / build | 10.0.22621 (Build 22621) |
| Architecture | 64-bit |
| PowerShell | 5.1.22621.4249 |
| Hardware | Lenovo 82K2 |
| CPU | AMD Ryzen 5 5600H, 6 cores / 12 logical processors |
| RAM | 14,877,257,728 bytes (approximately 13.9 GiB) |
| Working directory | `C:\Users\user` |
| Project workspace | `C:\Users\user\Documents\02_Projects\IPGuard` |
| Physical workspace location | `D:\Data\Documents\02_Projects\IPGuard` through a Windows Documents junction |

**Path note:** `C:\Users\user\Documents` is a Windows junction whose substitute target is `D:\Data\Documents` (confirmed with `fsutil reparsepoint query`). Commands and documentation continue to use the requested `C:\Users\user\Documents\02_Projects\IPGuard` alias; project files physically consume D: space.

### Disk capacity at inspection time

| Drive | Free | Used |
|---|---:|---:|
| C: | 6.79 GB (after portable PostgreSQL extraction) | 117.4 GB |
| D: | 60.89 GB | 189.7 GB |

**Risk:** free space on C: is limited for tooling. The project itself is physically stored on D: through the Documents junction, so project dependencies use D: space. Android Studio, an SDK, emulator images, Gradle caches, and virtual devices should also be placed on D: during M2 where possible. The portable PostgreSQL runtime and data remain under `C:\Users\user\AppData\Local\IPGuard` and consumed approximately 70 MB of data plus 863 MB of binaries at M0 time.

---

## 3. Workspace Inspection

| Check | Result |
|---|---|
| Workspace exists | Yes |
| Workspace contents before M0 | Empty |
| Existing Git repository | No |
| Existing configuration files | None |
| Existing user changes | None found |
| Hidden files | None found |
| Conflict with existing project structure | None |
| Destructive action taken | None |
| Parent-directory projects modified | No |

The workspace was created at `2026-11-06 07:16 AM` and contained only `.` and `..`. No files were deleted or overwritten.

The absence of a Git repository is recorded. Repository initialization, if performed during M1, does not create a commit without project-owner approval.

---

## 4. Tool Versions

### JavaScript environment

| Tool | Status | Version / source |
|---|---|---|
| Node.js | Available | v24.18.0 (`D:\NodeJs\node.exe`) |
| npm | Available | 11.16.0 (`D:\NodeJs\npm.ps1`) |
| npx | Available | Installed with npm |
| npm registry reachable | Yes | `https://registry.npmjs.org/` returned HTTP 200 |
| npm registry configuration | Default | `https://registry.npmjs.org/` |

### Python environment

| Tool | Status | Version / source |
|---|---|---|
| Python | Available | 3.13.2 |
| Python launcher (`py`) | Available | Python 3.13.2 |
| pip | Available | 26.2.2 |
| venv support | Available | `python -m venv --help` succeeded |
| pip integrity check | Passed | `python -m pip check`: no broken requirements |
| PyPI reachable | Yes | HTTP 200 |

### Git

| Tool | Status | Version |
|---|---|---|
| Git | Available | 2.54.0.windows.1 (`C:\Program Files\Git\cmd\git.exe`) |
| Repository initialized at M0 time | No | Workspace had no `.git` directory |

### Database and container environment

| Tool | Status | Details |
|---|---|---|
| PostgreSQL system installation | Not found | No common install path, service, or registry entry found |
| `psql` in PATH | Not found | System client is not installed |
| Docker | Not found | Command unavailable |
| Docker Compose | Not found | Command/plugin unavailable |
| WSL | Not active | `wsl --status` reported usage/help instead of an installed distribution |
| WinGet | Available | v1.29.380 |
| PostgreSQL portable runtime | Provisioned | 17.11, user-local, not a global installation |

Portable PostgreSQL location:

```text
C:\Users\user\AppData\Local\IPGuard\pgsql\17.11
```

Verified binaries:

```text
postgres (PostgreSQL) 17.11
psql (PostgreSQL) 17.11
initdb (PostgreSQL) 17.11
```

The EDB Windows x64 binaries archive was downloaded and extracted only for local development/testing. No Windows service, PATH entry, registry entry, or global package was created. The archive itself was removed after extraction.

### Android environment

| Tool / component | Status | Details |
|---|---|---|
| Android Studio | Not installed | No `studio64.exe` found in common locations |
| Android SDK | Not found | `ANDROID_HOME` and `ANDROID_SDK_ROOT` are unset |
| Android Platform Tools | Available | ADB 1.0.41, version 37.0.0 |
| ADB | Available | `C:\platform-tools\adb.exe` |
| `sdkmanager` | Not found | No Android SDK command-line tools |
| `avdmanager` | Not found | No Android SDK command-line tools |
| Android emulator | Not found | No emulator package |
| `aapt` / `aapt2` | Not found | No Android build tools |
| `apksigner` | Not found | No Android build tools |
| Gradle | Not found | No global Gradle; Android projects should use a Gradle wrapper in M2 |
| Kotlin CLI | Not found | Android Kotlin builds should use the Gradle Kotlin plugin in M2 |
| Java runtime | Available | Oracle Java 22.0.2 |
| `javac` | Available | 22.0.2 |
| Physical device | Connected | Samsung SM-A546E, Android 16, API 36, arm64-v8a |

ADB result at the end of M0:

```text
List of devices attached
<redacted>    device
```

### Physical-device feature declarations

Observed with `adb shell pm list features`:

```text
android.hardware.biometrics.face
android.hardware.fingerprint
android.hardware.hardware_keystore=200
android.hardware.keystore.app_attest_key
android.software.secure_lock_screen
android.hardware.camera.any
android.hardware.camera.front
```

These are **platform feature declarations**, not proof that every cryptographic or biometric operation will succeed. No IPGuard Authenticator APK exists yet, so hardware-backed key generation, attestation, StrongBox, biometric-gated signing, face detection, QR scanning, and challenge-response were not tested on the device.

A biometric dump showed enrolled biometric modality entries, but this does not establish Class 3 strength for the face modality. M2 must query it at runtime.

---

## 5. Port and Process Check

| Port | Planned use | Status at M0 |
|---|---|---|
| 5173 | Vite frontend | Free |
| 8000 | FastAPI backend | Free |
| 5432 | PostgreSQL | Free |

No local PostgreSQL service was running. No port conflict was found. If these ports become occupied, M1/M2 should document and change the port rather than silently killing the existing process.

---

## 6. Available Dependencies

### Confirmed available

- Node.js and npm
- Python, pip, and `venv`
- Git
- PowerShell 5.1
- WinGet
- ADB and a connected Android device
- Oracle JDK 22
- Portable PostgreSQL 17.11 binaries
- Network access to npm and PyPI

### Missing or incomplete

- PostgreSQL installer/service and `psql` on PATH
- Docker and Docker Compose
- Android Studio
- Android SDK and command-line tools
- Android emulator and AVDs
- Gradle (global); a wrapper will be required for M2
- Android-compatible JDK baseline; Android Studio's bundled JBR or JDK 17/21 should be used in M2
- StrongBox confirmation on the physical device
- Physical Android cryptographic/biometric test capability

### Recommended development dependencies for M1

**Frontend:** React, TypeScript, Vite, Tailwind CSS v4 with the Vite plugin, React Router, TanStack Query, Axios, Lucide React.

**Backend:** FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic 2.x, Pydantic Settings, Alembic, Psycopg 3, Pytest, HTTPX.

**Database:** PostgreSQL 17.x, either local/portable or Docker Compose.

**M2 only:** Android Studio, Android SDK 36 or the selected supported target, Android Platform Tools, a project Gradle wrapper, Kotlin/Android Gradle Plugin, JDK bundled with Android Studio or an explicitly compatible JDK, CameraX, ML Kit Face Detection, ML Kit Barcode Scanning, AndroidX Biometric.

---

## 7. Environment Gaps and Risks

| ID | Gap / risk | Impact | Mitigation |
|---|---|---|---|
| ENV-01 | No Docker or Compose | Cannot currently run the Compose database | Portable PostgreSQL 17.11 is available; Compose remains documented for other environments |
| ENV-02 | No system PostgreSQL / `psql` | Standard developer setup cannot use PATH commands | Use the portable runtime full path or install PostgreSQL later with owner approval |
| ENV-03 | No Android Studio/SDK | M2 cannot compile an Android app yet | Install Android Studio/SDK before M2; not an M1 blocker |
| ENV-04 | No Gradle wrapper/project yet | No reproducible Android build exists yet | Create wrapper in M2 and commit wrapper files |
| ENV-05 | JDK 22 is installed, not an Android Studio-bundled JDK | Android Gradle Plugin compatibility is uncertain with JDK 22 | Use Android Studio JBR or JDK 17/21 for M2 |
| ENV-06 | Device authorization required manual confirmation | Automation could not inspect device initially | Device is now authorized; do not assume it remains connected |
| ENV-07 | Low free space on C: | Android SDK/emulator installs may fail | Put SDK, emulator, and Gradle caches on D: |
| ENV-08 | No physical Android test yet | Keystore/biometric claims remain unverified | Build a minimal M2 proof-of-concept before relying on StrongBox/Class 3 |
| ENV-09 | Portable PostgreSQL is outside the repository | New machines are not automatically ready | `docs/DEVELOPMENT_SETUP.md` will document local and Docker alternatives |

No critical blocker exists for the M1 frontend, backend, or database foundation.

---

## 8. M0 Completion Status

| M0 acceptance item | Status | Evidence |
|---|---|---|
| Workspace inspected | PASS | Empty, no Git, no user files |
| Windows environment inspected | PASS | OS/build/hardware recorded |
| Node.js and npm inspected | PASS | v24.18.0 / 11.16.0 |
| Python and pip inspected | PASS | 3.13.2 / 26.2.2, venv works |
| Git inspected | PASS | 2.54.0.windows.1; no repository yet |
| PostgreSQL or Docker alternative inspected | PASS WITH FALLBACK | No Docker/system PostgreSQL; portable PostgreSQL 17.11 validated |
| Android development tools inspected | PASS WITH GAPS | ADB/device present; SDK/Studio/Gradle absent |
| Smartphone authenticator architecture analyzed | PASS | See `M0_TECHNICAL_FEASIBILITY.md` |
| Android Keystore feasibility analyzed | PASS, RUNTIME UNVERIFIED | Design feasible; hardware claims deferred to M2 |
| Face Gate vs face recognition distinguished | PASS | Detection is not identity verification |
| All constraints documented | PASS | This report and the two companion reports |

**M0 result:** COMPLETED WITH RECORDED LIMITATIONS.

**M1 gate:** OPEN. M1 may proceed without installing Android tooling or Docker. Database verification will use the portable PostgreSQL runtime. Android build and hardware-authenticator validation remain M2 prerequisites.
