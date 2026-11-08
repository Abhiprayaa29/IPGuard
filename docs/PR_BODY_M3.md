## IPGuard — Milestone 3: Secure Notes & Hardware-Backed Vault Integration

### 1. Executive Summary
This Pull Request delivers **Milestone 3 (Secure Notes)**, integrating end-to-end hardware-authenticated digital asset protection into IPGuard. Remediated and adapted from collaborator Anisa's initial prototype, this implementation binds Secure Notes strictly to Milestone 2 Android Keystore QR sessions, introduces owner-isolated cryptographic key derivation (HKDF-SHA256), applies modern authenticated encryption (AES-256-GCM) with an educational defense-in-depth classical layer (Vigenère), migrates PostgreSQL safely via Alembic, and provides a production-grade React vault UI.

---

### 2. Implemented Features & Architecture

#### 2.1 Hardware-Backed Authentication Integration (M2)
- Replaced vulnerable prototype authentication bypasses (`dev-user`) with [`get_current_authenticated_device`](docs/../backend/app/api/deps.py) dependency guard.
- Enforces Bearer token verification matching valid `auth_sessions.session_token` and browser channel prefixes (`ipguard_sess_`).
- Hexadecimal sanitization regex (`^[0-9a-fA-F]+$`) and ambiguity detection.
- Requires session status to be strictly `APPROVED` (cryptographically validated via Android Keystore ECDSA signature).
- Validates session expiration bounds (`expires_at > current_utc_time`).
- Validates authenticator device status (`device.status == "ACTIVE"`); revoked devices fail closed with HTTP 403 Forbidden.
- Extracts `owner_id` directly from the authenticated `device.device_id`. Client payloads cannot supply or spoof `owner_id`.
- Strict owner isolation: Any request targeting foreign or non-existent notes fails closed with HTTP 404 (`note_not_found`).

#### 2.2 Super-Encryption Cryptography Service
- **Key Derivation (RFC 5869 HKDF-SHA256):**
  - Salt: `owner_id.encode("utf-8")`
  - Info: `b"ipguard-secure-notes-v1-hkdf-aes256gcm"`
  - Generates unique 256-bit AES key per owner, preventing cross-device decryption even under a common system master key.
- **Modern Authenticated Encryption (AES-256-GCM):**
  - 96-bit cryptographically random nonces via `os.urandom(12)`.
  - 128-bit authentication tag appended to ciphertext.
  - Fail-closed integrity verification (`InvalidTag` on 1-bit tampering).
- **Educational Classical Layer (Vigenère):**
  - Keyword deterministically derived from `sha256(b"vigenere|" + user_key)[:12]`.
  - Operates strictly on ASCII letters `[A-Za-z]`. Preserves numbers, punctuation, whitespace, and multi-byte UTF-8 Unicode characters (Indonesian, emojis, symbols) intact.
- **Envelope Format:**
  - `v1$<base64(nonce[12] + ciphertext + tag[16])>`
  - Backwards-compatible parser for legacy unversioned payloads (`v0`).
  - Zero plaintext stored in database; zero key or plaintext leakage in logs.

#### 2.3 PostgreSQL Schema & Concurrency
- Model `Note` registered with SQLAlchemy metadata.
- Linear Alembic migration `0004_secure_notes.py` revising `0003_auth_browser_channel`. Single head verified.
- Row-level locking (`with_for_update()`) on note updates and deletions to prevent concurrent race conditions.

#### 2.4 Secure Notes Frontend (React 19 + TypeScript + Vite)
- Route `/notes` integrated into navigation and layout (`AppShell`).
- Seamless handoff from `QrLoginPage` after successful mobile authentication.
- Ephemeral session security: Session tokens kept in `sessionStorage` (cleared automatically on tab close).
- Full CRUD modals: Create, Read (view decrypted content), Update, and Delete confirmation modal.
- Search and filtering across decrypted in-memory titles and content.
- Complete XSS prevention: React JSX text escaping, zero `dangerouslySetInnerHTML`.
- Dedicated Sign Out button clearing session storage and redirecting to `/login`.

---

### 3. API Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/notes` | Create a new super-encrypted note | Bearer (APPROVED) |
| `GET` | `/api/v1/notes` | List and decrypt all notes owned by caller | Bearer (APPROVED) |
| `GET` | `/api/v1/notes/{id}` | Read and decrypt a specific note | Bearer (APPROVED) |
| `PUT` | `/api/v1/notes/{id}` | Update title/content with row lock & re-encrypt | Bearer (APPROVED) |
| `DELETE` | `/api/v1/notes/{id}` | Permanently delete note with row lock | Bearer (APPROVED) |

---

### 4. Verification & Test Evidence

- **Backend Pytest Suite:** **90 passed in 4.19s (100% green)**
  - 65 Core M1/M2 authentication & session tests
  - 13 Cryptography unit tests (`test_note_crypto.py`)
  - 12 Note API integration & isolation tests (`test_notes_api.py`)
- **PostgreSQL 17 Database Migration:**
  - Tested downgrade to `0003` and clean upgrade to `0004_secure_notes`.
  - Single head confirmed (`0004_secure_notes (head)`).
- **Frontend Production Build:**
  - `tsc --noEmit && vite build` passed with 0 errors (2,193 modules transformed in 316ms).
- **Live 10-Step End-to-End Test (`test_e2e_live.py`):**
  - Verified 10/10 live steps against PostgreSQL 17: ECDSA device enrollment $\rightarrow$ Keystore session approval $\rightarrow$ browser token retrieval $\rightarrow$ note creation $\rightarrow$ DB ciphertext audit (`v1$`) $\rightarrow$ read & decrypt $\rightarrow$ update $\rightarrow$ cross-device isolation (404) $\rightarrow$ delete $\rightarrow$ revoked device rejection (403).
- **Code Quality & Secret Scan:**
  - `git diff --check` clean.
  - Zero `.env`, `.venv`, credentials, or production keys committed.

---

### 5. Security Review Reference & Limitations

- **Security Review Report:** [docs/M3_FINAL_SECURITY_REVIEW.md](M3_FINAL_SECURITY_REVIEW.md)
- **Integration Report:** [docs/M3_ANISA_INTEGRATION_REPORT.md](M3_ANISA_INTEGRATION_REPORT.md)
- **Official Verdict:** **`APPROVED FOR PR`**
- **Known Scope Boundaries / Future Enhancements:**
  1. *Keyring Management (Planned for M5):* The `v1$` envelope format supports versioning; dynamic multi-generation master keyrings will be introduced in M5 key rotation workflows.
  2. *Session Sliding Expiry:* Sesi notes saat ini terikat pada TTL sesi M2 QR (60s auth window / default session expiry). Sliding token refresh dapat ditambahkan pada Milestone berikutnya jika dibutuhkan sesi panjang.

---

### 6. Review Checklist

- [x] Source branch: `feature/m3-secure-notes-integration`
- [x] Target branch: `feature/m2.4d-android-integration`
- [x] Backend tests pass (90/90)
- [x] Frontend production build succeeds (0 errors)
- [x] Database migration safe & single head verified
- [x] No M4 or Aliza code included
- [x] No credentials or secrets committed
- [ ] PR will NOT be merged automatically.
