# Contributing to IPGuard

Thank you for your interest in contributing to **IPGuard — Secure Digital Asset Protection**. 

IPGuard is an engineering-first security platform combining hardware-backed Android cryptography, an asynchronous Python FastAPI backend, and a modern React management console. To maintain high code quality and security guarantees, all contributors are required to follow these guidelines.

---

## 1. Branching Strategy

Our repository maintains strict branch hygiene:

- `main`: Protected production-ready branch. Direct pushes to `main` are strictly forbidden. All changes must arrive via reviewed Pull Requests.
- Feature branches: Created off the latest `main`:
  - `feature/<short-description>` (e.g., `feature/argon2id-key-derivation`, `feature/qr-visual-feedback`)
- Bug fix branches:
  - `fix/<short-description>` (e.g., `fix/connection-pool-leak`, `fix/qr-timer-race`)
- Documentation / Maintenance:
  - `docs/<short-description>` or `chore/<short-description>`

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

### Scopes
- `backend`: Changes to FastAPI routes, models, services, or database migrations.
- `frontend`: Changes to React components, hooks, pages, or styling.
- `android`: Changes to Kotlin authenticator, Keystore, or Compose UI.
- `security`: Security patches, policy enforcements, or cryptographic updates.
- `ci`: Changes to GitHub Actions workflows or automation scripts.

### Examples
- `feat(backend): implement origin whitelisting for auth session creation`
- `fix(android): close OkHttp connections immediately over ADB reverse`
- `docs(m2): update cross-device android compatibility matrix`

---

## 3. Pull Request Process

1. **Sync with Main:** Before starting, ensure your local `main` is up to date:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```
2. **Implement & Test Locally:** Write tests alongside your implementation. All tests must pass before opening a PR.
3. **Local Pre-Push Verification:** Run the full validation suite:
   ```powershell
   # Backend test suite
   cd backend && python -m pytest -v

   # Frontend build & typecheck
   cd ../frontend && npm run build

   # Android unit tests
   cd ../mobile-authenticator && .\gradlew.bat testDebugUnitTest --no-daemon
   ```
4. **Open Pull Request:**
   - Push your branch to `origin`.
   - Open a PR against `main`.
   - Fill out the provided **Pull Request Template** completely.
   - Attach test evidence, terminal outputs, or screenshots when relevant.
5. **Code Review:** Every PR requires at least one approving review from a core maintainer. Address review comments promptly.

---

## 4. Zero Secrets & Security Hygiene Policy

**IPGuard handles sensitive cryptographic operations and security tokens. Committing secrets will result in immediate PR rejection.**

- **Never commit `.env` files:** Only update `.env.example` templates with sanitized placeholder values.
- **Never commit keystores or keys:** Never commit `.jks`, `.keystore`, private keys (`.pem`, `.key`), or client secrets.
- **No hardware identifiers:** Never collect or transmit IMEI, MAC addresses, or hardware serial numbers in mobile code.
- **Review unstaged files:** Always run `git status` and `git diff` before staging to verify that no temporary or sensitive files are included.

---

## 5. Engineering & Code Standards

### Python (Backend)
- Adhere to PEP 8 style standards.
- Use strict type annotations (`typing`, Pydantic v2 schemas).
- Database operations involving state modification must use transactions and pessimistic row locking where concurrent manipulation is possible (`with_for_update()`).
- Keep controllers thin and place business logic into `app/services/`.

### TypeScript / React (Frontend)
- Enable TypeScript strict mode; avoid the use of `any`.
- Keep components focused and modular.
- Extract complex side-effects and asynchronous polling loops into reusable hooks (e.g., `useQrAuth.ts`).
- Handle request cancellations and clean up all `setInterval` / `setTimeout` timers on component unmount.

### Kotlin (Android Authenticator)
- Follow standard Kotlin coding conventions and Android Jetpack guidelines.
- Target modern Android versions (minSdk 28, compileSdk/targetSdk 36).
- Use Android Keystore for key generation; never store raw private keys in SharedPreferences, SQLite, or memory dumps.
- Always require user authentication (`setUserAuthenticationRequired(true)`) for cryptographic keys.
- Ensure all networking calls over OkHttp explicitly manage connection lifecycles and handle connection resets cleanly.

---

## 6. Need Help?

If you have questions about architectural decisions, milestone boundaries, or how to set up your local environment, feel free to open a GitHub Discussion or reach out to the project lead [@Abhiprayaa29](https://github.com/Abhiprayaa29).
