# Contributing to IPGuard

Thank you for your interest in contributing to **IPGuard — Secure Digital Asset Protection Platform**.

IPGuard is an engineering-first security platform combining hardware-backed Android cryptography, an asynchronous Python FastAPI backend, and a modern React management console. To maintain high code quality and security guarantees, all contributors are required to follow these guidelines.

---

## 1. Branching Strategy

Our repository maintains strict branch hygiene:

- `main`: Protected production-ready branch. Direct pushes to `main` are strictly forbidden. All changes must arrive via reviewed Pull Requests.
- Feature branches: Created off the latest `main`:
  - `feature/<short-description>` (e.g., `feature/audit-hash-chain`, `feature/stego-verification-ui`)
- Bug fix branches:
  - `fix/<short-description>` (e.g., `fix/connection-pool-leak`, `fix/qr-timer-race`)
- Release branches:
  - `release/<release-name>` (e.g., `release/m0-m4-final`)

---

## 2. Commit Message Conventions

We enforce [Conventional Commits v1.0.0](https://www.conventionalcommits.org/):

Format:
```text
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Allowed Types
- `feat`: A new feature or capability.
- `fix`: A bug fix or defect resolution.
- `docs`: Documentation additions or revisions.
- `refactor`: Code reorganization with no functional or API changes.
- `test`: Adding missing tests or improving existing test coverage.
- `chore`: Tooling, build system, or dependencies maintenance.
- `release`: Preparing a formal version release.

### Scopes
- `backend`: Changes to FastAPI routes, models, services, or database migrations.
- `frontend`: Changes to React components, hooks, pages, or styling.
- `android`: Changes to Kotlin authenticator, Keystore, or Compose UI.
- `stego`: Changes to PNG LSB steganography, framing, or Ed25519 signing.
- `vault`: Changes to XChaCha20-Poly1305 storage or key derivation.
- `security`: Security patches, policy enforcements, or cryptographic updates.
- `ci`: Changes to GitHub Actions workflows or automation scripts.

---

## 3. Local Development Setup & Prerequisites

### Prerequisites
- Python 3.13.x
- Node.js >= 22.12.0
- PostgreSQL 17.x
- Android Studio with Android SDK API 28–36 (for mobile development)

### Setup Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Abhiprayaa29/IPGuard.git
   cd IPGuard
   ```
2. Set up Backend:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   cp .env.example .env       # Configure your local database password
   alembic upgrade head       # Apply migrations 0001 through 0009
   ```
3. Set up Frontend:
   ```bash
   cd ../frontend
   npm install
   npm run typecheck
   ```

---

## 4. Testing Requirements Before Submitting a PR

Every pull request must satisfy all automated quality gates:

1. **Backend Test Suite:**
   ```bash
   cd backend
   pytest -v
   ```
   *Requirement:* All unit, integration, and API tests must PASS (0 failures, 0 regressions).

2. **Frontend Typecheck & Build:**
   ```bash
   cd frontend
   npm run typecheck
   npm run build
   ```
   *Requirement:* Zero TypeScript errors and clean production build.

3. **Database Migrations:**
   Ensure new schema modifications have an associated forward and reverse Alembic migration script.

4. **Security Policy:**
   Never commit `.env` files, private cryptographic seeds, or temporary tokens.

---

## 5. Pull Request Submission Checklist

- [ ] Branch is rebased against the latest `main`.
- [ ] Conventional commit messages are used.
- [ ] Backend tests pass completely.
- [ ] Frontend typecheck and build pass completely.
- [ ] No private keys or secrets are committed.
- [ ] Documentation is updated if user workflows or API contracts change.
