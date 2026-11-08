# IPGuard — Collaborator Onboarding & Engineering Guide

**Project:** IPGuard — Secure Digital Asset Protection  
**Target Repository:** `https://github.com/Abhiprayaa29/IPGuard`  
**Repository Visibility:** `PRIVATE` (Strictly Enforced)  
**Document Version:** 1.0.0  
**Last Updated:** November 8, 2026  

---

## 1. Introduction & Welcome

Welcome to the **IPGuard** engineering team! IPGuard is an enterprise security platform engineered to protect sensitive digital assets (source code, architectural drawings, proprietary media, sensitive credentials) through **hardware-backed Zero-Trust device binding**.

In IPGuard, an Android mobile authenticator functions as an out-of-band hardware security key. The Android Keystore (TEE / StrongBox) generates and protects a non-exportable ECDSA P-256 key pair that signs cryptographic challenges displayed on a React web management console via dynamic QR codes, validated server-side by an asynchronous Python FastAPI backend.

This guide provides everything you need to set up your local development environment, understand the repository workflow, coordinate on upcoming milestones (M3 and M4), and submit high-quality Pull Requests.

---

## 2. GitHub Collaboration & Access Management

### 2.1 Repository Visibility Policy
The IPGuard repository is **strictly PRIVATE**. Never alter repository visibility to public, publish packages, or upload source code/assets to external forums or public mirrors.

### 2.2 Adding Collaborators (Instructions for Repository Owner)
To invite a new developer to this private repository:
1. Navigate to `https://github.com/Abhiprayaa29/IPGuard`.
2. Open **Settings** -> **Collaborators** -> click **Add people**.
3. Search strictly by the developer's exact GitHub username (never use unverified emails).
4. Once sent, the invited developer will receive an invitation email or a notification at `https://github.com/Abhiprayaa29/IPGuard/invitations`.

### 2.3 Personal Repository Permissions vs. GitHub Organization
- **Current Model (Personal Private Repository):**
  In a personal GitHub repository, added collaborators are granted **Write (Push)** access by default. GitHub does not provide granular role-based access control (RBAC) such as "Triage" or "Read-Only" for personal accounts.
- **Enterprise / Organization Path:**
  If granular access controls, custom repository roles, or automated team permissions are required in the future, the repository owner can transfer the repository to a **GitHub Organization** (free or team tier), enabling Read, Triage, Write, Maintain, and Admin roles.

### 2.4 Recommended Branch Protection (Owner Action)
If GitHub Pro or Organization features are active on the account, configure branch protection for `main`:
1. Navigate to **Settings** -> **Branches** -> **Add branch protection rule**.
2. Branch name pattern: `main`.
3. Check **Require a pull request before merging** (Require at least 1 approval).
4. Check **Require status checks to pass before merging** (Select `Backend Tests & Database Migrations`, `Frontend Typecheck & Production Build`, and `Android Unit Tests & Debug APK Build`).
5. Check **Do not allow bypassing the above settings**.
6. Ensure **Allow force pushes** and **Allow deletions** are **UNCHECKED**.

*If operating under GitHub Free for personal accounts where automated branch protection is unavailable, all collaborators must strictly follow the team social agreement: direct pushes to `main` are strictly prohibited.*

### 2.5 Recommended Repository Metadata
- **Description:** `Secure Digital Asset Protection Platform built with React, FastAPI, PostgreSQL, and Kotlin Android Authenticator.`
- **Topics / Tags:** `cybersecurity`, `digital-asset-protection`, `cryptography`, `android`, `fastapi`, `react`, `postgresql`, `kotlin`.

---

## 3. Subsystem Architecture Overview

IPGuard consists of three tightly coupled subsystems residing in a unified monorepo:

```text
+-----------------------+                    +------------------------------------+
|  IPGuard Web Console  |                    |        IPGuard REST API            |
|  (React + TypeScript) | <--- HTTP / REST --|       (Python FastAPI)             |
|  Port: 5173           |                    |       Port: 8000                   |
+-----------------------+                    +------------------------------------+
           ^                                                   |
           | Visual QR Code Display (60s TTL)                  | PostgreSQL 17
           v                                                   v
+----------------------------------------------------+ +--------------------+
|       IPGuard Android Native Authenticator         | |    PostgreSQL      |
|   - Jetpack Compose UI (API 28-36)                 | |    Database        |
|   - CameraX + Google ML Kit QR Scanner             | +--------------------+
|   - Hardware Android Keystore (ECDSA P-256)        |         ^
|   - Adaptive Policy (PIN / Pattern / Biometric)    |         |
|   - Resilient OkHttp Client (Tunnel-Aware)         | --------+ (Out-of-Band Auth)
+----------------------------------------------------+
```

| Subsystem | Directory | Tech Stack | Responsibility |
|---|---|---|---|
| **Web Console** | `frontend/` | React 19, TypeScript, Vite, Tailwind CSS v4 | Asset management UI, dynamic QR auth display, secure browser channel polling (SEC-02). |
| **Backend API** | `backend/` | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17 | Device registry, pessimistic row locking (`SELECT FOR UPDATE`), origin whitelisting, ECDSA verifier. |
| **Android Authenticator** | `mobile-authenticator/` | Kotlin 2.2+, Jetpack Compose, Android Keystore, CameraX, ML Kit | Barcode parsing, hardware-isolated challenge signing, adaptive authentication. |

---

## 4. Local Development Quickstart

### 4.1 Prerequisites
- **OS:** Windows 10/11, macOS, or Linux.
- **Python:** Python 3.13 (or 3.11+) with virtual environment support.
- **Node.js:** Node.js 22 LTS or newer with npm.
- **JDK:** OpenJDK 17.
- **Android SDK:** API 28–36, Platform-tools (`adb`).
- **Database:** PostgreSQL 17 (local native instance or Docker Compose).

### 4.2 Clone & Environment Initialization
```bash
# 1. Clone repository
git clone https://github.com/Abhiprayaa29/IPGuard.git
cd IPGuard

# 2. Initialize environment configuration files (never commit real .env files!)
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 4.3 Database Initialization
Start PostgreSQL (via Docker Compose or local service) and apply Alembic migrations:
```powershell
# If using Docker Compose:
docker-compose up -d

# Apply schema migrations:
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
```

### 4.4 Running Services

#### Terminal 1 — Backend (Port 8000)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 60
```
Swagger UI available at: `http://localhost:8000/docs`.

#### Terminal 2 — Frontend (Port 5173)
```powershell
cd frontend
npm install
npm run dev
```
Web console available at: `http://localhost:5173`.

#### Terminal 3 — Android Authenticator (via USB + ADB Reverse)
```powershell
# 1. Ensure phone has USB Debugging enabled
adb devices -l

# 2. Reverse port 8000 so the phone can reach the local host backend
adb reverse tcp:8000 tcp:8000

# 3. Build, install, and run
cd mobile-authenticator
.\gradlew.bat installDebug
adb shell am start -n com.ipguard.authenticator/.MainActivity
```

---

## 5. Pre-Push Verification Checklist

Before pushing any branch or submitting a PR, run the automated quality checks across all three subsystems:

```powershell
# 1. Backend Pytest suite (65 tests)
cd backend
python -m pytest -v

# 2. Frontend Typecheck & Production Build
cd ..\frontend
npm run typecheck
npm run build

# 3. Android Unit Tests & Debug APK Compilation
cd ..\mobile-authenticator
.\gradlew.bat testDebugUnitTest assembleDebug --no-daemon
```

---

## 6. Roadmap: Milestone 3 & Milestone 4 Candidate Issues

Collaborators joining for the next development cycles should pick from the following planned architectural candidate issues. **Do not implement these features without creating an issue and feature branch first.**

### Milestone 3 — Core Cryptography & Digital Asset Protection

| Issue ID | Title | Objective & Scope | Acceptance Criteria & Dependencies | Security Considerations |
|---|---|---|---|---|
| **#M3-01** | `feat(crypto): digital asset vault architecture` | Implement core database models and service schemas for securely storing encrypted assets and metadata. | PostgreSQL schema with `assets` table, Alembic migration, asset metadata CRUD endpoints. Dep: M2 auth session. | Asset payloads must never be stored in plaintext. Access restricted to approved device sessions. |
| **#M3-02** | `feat(crypto): file encryption & decryption pipeline` | Implement streaming symmetric file encryption and decryption service in backend and frontend. | Encrypt/decrypt files up to 100MB with streaming chunks, authenticated ciphertext output. | Prevent ciphertext truncation and padding oracle vulnerabilities. |
| **#M3-03** | `feat(vault): secure notes cryptographic storage` | Enable users to create, view, edit, and search end-to-end encrypted markdown notes. | Secure notes CRUD API, client-side encryption/decryption, encrypted full-text search preview. | Zero-knowledge server architecture: server never sees note plaintext. |
| **#M3-04** | `feat(crypto): AES-256-GCM symmetric cipher module` | Implement high-performance AES-256-GCM cipher with random 96-bit IV generation and tag validation. | Authenticated encryption with 128-bit GCM authentication tags; unit tests verifying bit-flip rejection. | Nonce reuse prevention: strictly unique IV for every encryption operation. |
| **#M3-05** | `feat(crypto): XChaCha20-Poly1305 cipher implementation` | Provide alternative authenticated cipher utilizing extended 192-bit nonces for high-volume streaming. | PyCryptodome / cryptography XChaCha20-Poly1305 engine; benchmark vs AES-NI. | Immune to nonce-collision risks from random generation due to 192-bit nonce space. |
| **#M3-06** | `feat(crypto): Argon2id password-based key derivation` | Implement Argon2id KDF to derive asset master encryption keys from user passphrases. | Configurable memory (64MB), time cost (3 iterations), parallelism (4 threads); salt generation. | Resist GPU/ASIC brute-force dictionary attacks. |
| **#M3-07** | `feat(crypto): Vigenère + AES hybrid super-encryption` | Implement layered educational/defense super-encryption combining polyalphabetic pre-whitening with AES-256. | Two-stage reversible encryption pipeline with integrity envelope. | Clear documentation separating educational layered ciphers from pure standard ciphers. |
| **#M3-08** | `feat(stego): PNG LSB robust steganography engine` | Hide encrypted asset hashes or ownership watermarks in PNG image least-significant bits. | Encode/decode binary payload in PNG RGBA pixels without visible visual distortion; PSNR > 40dB. | Fail-closed detection when carrier image is cropped or re-compressed. |
| **#M3-09** | `feat(crypto): envelope key management & rotation` | Implement hierarchical envelope encryption (Master Key -> Data Encryption Keys). | Key wrapping/unwrapping, DEK rotation without re-encrypting whole asset payloads. | DEKs must be stored encrypted using KEKs derived from user/device keystore. |
| **#M3-10** | `feat(db): transparent database field encryption` | Encrypt sensitive database columns (e.g. asset descriptions, IP attribution) at the ORM layer. | SQLAlchemy `TypeDecorator` handling automatic transparent encryption/decryption. | Indexing considerations: encrypted columns cannot be searched with standard `LIKE`. |

---

### Milestone 4 — Integrity & Advanced Protection

| Issue ID | Title | Objective & Scope | Acceptance Criteria & Dependencies | Security Considerations |
|---|---|---|---|---|
| **#M4-01** | `feat(integrity): SHA-256 continuous asset monitoring` | Implement asynchronous background workers calculating asset digest trees and detecting alterations. | Celery or FastAPI background worker polling asset checksums; alert dispatching. | Constant-time digest comparison using `secrets.compare_digest`. |
| **#M4-02** | `feat(integrity): asset integrity verification API` | Provide dedicated REST endpoint for verifying uploaded files against recorded cryptographic hashes. | `POST /api/v1/integrity/verify` accepting file streams or SHA-256 hashes, returning audit proof. | Prevent timing side-channel attacks on hash comparison. |
| **#M4-03** | `feat(audit): cryptographic SHA-256 audit hash chain` | Implement append-only Merkle-linked audit log where each event references previous entry's digest. | Tamper-evident log table: `id`, `timestamp`, `event_type`, `payload`, `prev_hash`, `entry_hash`. | Mathematical impossibility of altering past log entries without invalidating chain. |
| **#M4-04** | `feat(audit): structured audit logging framework` | Standardize structured audit events across all subsystem mutations (device enrollment, login, asset decrypt). | JSON-formatted structured logging with correlation IDs, origin IP, and device fingerprint. | Exclude all cryptographic keys, passwords, and decrypted payloads from logs. |
| **#M4-05** | `feat(web): asset verification history UI` | Build React dashboard view displaying historical verification events and tamper alerts. | Interactive timeline component, search by asset ID, visual status indicators (Verified, Altered, Missing). | Pagination and rate-limiting on history endpoints to prevent DoS. |
| **#M4-06** | `feat(web): interactive hash chain explorer` | Create visual interactive graph in Web Console demonstrating audit chain block linking and integrity. | Visual block sequence showing Merkle tree roots, node expansion, and tamper-simulation toggle. | Educational and enterprise proof-of-work demonstration interface. |
| **#M4-07** | `feat(integrity): automated tampering detection & lockdown` | Trigger automatic session revocation and asset lockdown when an integrity violation is detected. | Automated state transition: `ASSET_COMPROMISED`, immediate notification, audit freeze. | Prevent automated denial-of-service triggers from corrupted upload packets. |

---

## 7. Branch Naming & Contribution Rules

When beginning work on an assigned issue:
1. Ensure your local `main` is fresh:
   ```bash
   git checkout main
   git pull origin main
   ```
2. Create your feature branch using the standard naming format:
   ```bash
   git checkout -b feature/m3-file-encryption
   ```
3. Use [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(crypto): implement AES-256-GCM cipher with 96-bit IV`
   - `test(crypto): add bit-flip authentication tag verification tests`
   - `docs(crypto): document envelope key rotation sequence`
4. Never commit credentials, `.env` files, or private keys.
5. Push to `origin` and open a Pull Request using `.github/PULL_REQUEST_TEMPLATE.md`.
