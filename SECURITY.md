# Security Policy — IPGuard

Security is the core foundation of IPGuard. We take the security of our codebase, cryptographic implementations, and user data seriously.

---

## 1. Supported Versions

IPGuard is currently in active pre-release development. Only the latest commit on the `main` branch receives official security updates and patches.

| Version / Branch | Supported |
|---|:---:|
| `main` | :white_check_mark: Yes |
| Pre-release feature branches | :x: No |

---

## 2. Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

If you believe you have discovered a vulnerability in IPGuard:

1. **Private GitHub Advisory:** Use the "Report a vulnerability" button under the **Security** tab of the IPGuard GitHub repository.
2. **Direct Contact:** Alternatively, reach out directly to the project lead [@Abhiprayaa29](https://github.com/Abhiprayaa29).

### What to Include in Your Report
To help us investigate and reproduce the issue quickly, please include:
- A clear description of the vulnerability and its potential security impact.
- Affected component(s): Backend (FastAPI), Frontend (React), or Mobile (Android Authenticator).
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Relevant logs, request/response headers, or terminal outputs (ensure all personal secrets/passwords are redacted).

### Response Timeline
- **Acknowledgement:** We will acknowledge receipt of your vulnerability report within **48 hours**.
- **Assessment:** We will provide an initial assessment and timeline within **5 business days**.
- **Resolution:** A security patch will be prepared on a private branch and verified before being merged into `main`.
- **Public Disclosure:** Once the fix is published, credit will be given in the release notes if desired.

---

## 3. Threat Model & Scope Boundaries (Milestone 2)

### In-Scope Security Guarantees
- **ECDSA P-256 Key Pair Generation:** Keys generated inside Android Keystore must be hardware-isolated (TEE / StrongBox) and non-exportable (`privateKey.encoded == null`).
- **Signature Verification:** SHA256withECDSA signatures must be verified on the backend against the registered device public key.
- **Biometric Enforcement:** BiometricPrompt with `CryptoObject` must enforce `BIOMETRIC_STRONG` (Class 3) or `DEVICE_CREDENTIAL` (PIN/pattern/password).
- **Anti QR-Jacking / Shoulder Surfing (SEC-02):** The browser session secret token (`token_hash`) must never be encoded in QR payloads or exposed to unauthenticated parties.
- **Pessimistic Row-Level Locking (SEC-01):** PostgreSQL row locking (`SELECT FOR UPDATE`) prevents concurrent challenge re-use.
- **Origin Validation (SEC-03):** Origin headers are validated against an allowed whitelist.

### Explicitly Out-of-Scope for M2
- Multi-tenant user permission tables (slated for Milestone 3).
- Symmetric asset encryption and key derivation pipelines (slated for Milestone 3).
- Device key revocation lists across federated networks (slated for Milestone 4).

---

## 4. Secret Hygiene Policy

- Any pull request or commit containing credentials, API keys, private keys, or un-redacted `.env` files will be rejected immediately.
- If credentials are inadvertently pushed, they are considered compromised and must be revoked immediately. History rewrite will be evaluated on isolated feature branches only.
