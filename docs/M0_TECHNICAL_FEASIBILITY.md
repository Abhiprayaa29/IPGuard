# M0 Technical Feasibility

**Project:** IPGuard — Secure Digital Asset Protection  
**Milestone:** M0 — Smartphone Authenticator Feasibility  
**Date:** 2026-11-06  
**Status:** DESIGN FEASIBLE — PHYSICAL/HARDWARE VALIDATION DEFERRED TO M2

---

## 1. Purpose and Boundary

This document evaluates the planned smartphone authenticator architecture only. No Android source code, APK, QR flow, Keystore implementation, biometric integration, or backend authentication endpoint was created in M0 or M1.

The proposed concept is a **Face-Gated Mobile Authenticator** that uses:

- Kotlin native Android
- Android Keystore
- ECDSA P-256
- Android BiometricPrompt
- CameraX
- ML Kit Face Detection
- ML Kit Barcode Scanning
- HTTPS
- QR-based device pairing
- Backend challenge-response verification

---

## 2. Conceptual Authentication Architecture

```text
┌────────────────────────┐          ┌─────────────────────────────┐
│ IPGuard Web Frontend   │          │ IPGuard Backend             │
│ React + Axios          │          │ FastAPI                     │
└───────────┬────────────┘          └──────────────┬──────────────┘
            │ HTTPS                                │
            │                                      │ public key registration
            │                                      │ challenge issuance
            │                                      │ signature verification
            │                                      │
┌───────────▼──────────────────────────────────────▼──────────────┐
│ IPGuard Authenticator (Android, M2)                             │
│                                                                  │
│  Face Gate (ML Kit Face Detection; UX presence check)            │
│              │                                                   │
│              ▼                                                   │
│  QR Scanner (CameraX + ML Kit Barcode Scanning)                  │
│              │                                                   │
│              ▼                                                   │
│  Fetch challenge ──► Show approval ──► BiometricPrompt           │
│                                         │                        │
│                                         ▼                        │
│                            Android Keystore ECDSA P-256          │
│                            private key signs challenge           │
│                                         │                        │
│                                         ▼                        │
│                            Signed response over HTTPS            │
└──────────────────────────────────────────────────────────────────┘
```

### Security intent

- The private key is generated inside Android Keystore and must be non-exportable.
- The backend stores only the public key.
- Each authentication uses a fresh, short-lived, one-time challenge.
- A signature proves possession of the private key.
- A biometric authorization can gate use of the key.
- Face detection may gate the UX before QR scanning, but must not be treated as the cryptographic identity proof.

---

## 3. Face Detection, Face Recognition, and Device Authentication

These are separate capabilities and must never be presented as equivalent.

| Capability | What it proves | Planned technology | Security role |
|---|---|---|---|
| Face detection | A face-like region is present; landmarks/orientation may be derived | ML Kit Face Detection | UX gate and camera readiness check; **not identity** |
| Face recognition | A detected face matches a previously enrolled identity | Not planned with ML Kit Face Detection; would require a separate model/service | Identity assertion; high risk and privacy-sensitive |
| Device authentication | The requester possesses a device-bound private key | Android Keystore ECDSA + backend challenge-response | Cryptographic authentication |
| Local biometric authorization | The device's enrolled user approved a key operation | Android BiometricPrompt / Keystore user-auth requirement | Local authorization gate |

### What ML Kit Face Detection can do

- Detect faces in an image/camera frame.
- Return bounding boxes, landmarks, contours, head Euler angles, and optional classifications such as smiling/eyes open.
- Support front-camera framing and basic quality feedback.

### What ML Kit Face Detection cannot do as a security control

- It cannot reliably identify a specific enrolled person.
- It is not a biometric matching system.
- It does not by itself provide robust liveness/anti-spoofing against photos, screens, masks, or deepfakes.
- A face being detected must not unlock credentials or authorize a signature on its own.

### Face Gate decision options

**Option A — UX-only Face Gate (recommended for first implementation):**

- Use ML Kit Face Detection to confirm a real-time camera face is present and reasonably framed.
- Then require system biometric authentication (BiometricPrompt) for security.
- Use fingerprint/device credential as a fallback where appropriate.
- Keep cryptographic authentication separate.

**Option B — System face biometric:**

- Use `BiometricPrompt` with `BIOMETRIC_STRONG`.
- The system may offer face if the device's face modality is strong enough.
- The app must not assume face is strong; it must inspect `BiometricManager` capability and the device's actual enrollment.
- BiometricPrompt does not expose raw face data to the app; that is a privacy advantage.

**Option C — Custom face recognition (not recommended without a new requirements decision):**

- Requires an on-device/remote recognition model, enrollment, consent, privacy controls, liveness/anti-spoof testing, threshold calibration, and error-rate analysis.
- Must not be confused with ML Kit Face Detection.
- Adds substantial risk and is outside the M0/M1 scope.

**Recommendation:** implement the Face Gate as a non-security presence/quality step and use Android Keystore + BiometricPrompt for the actual security boundary. If the product requirement is "recognize the specific enrolled face," treat it as a separately approved feature with its own threat model in M2 or later.

---

## 4. Technology Feasibility Matrix

| Technology | Feasibility | Notes / constraints |
|---|---|---|
| Kotlin native Android | HIGH | Standard Android stack; requires SDK and Gradle wrapper in M2 |
| Android Keystore | HIGH, device-dependent | Hardware backing not guaranteed; StrongBox is optional |
| ECDSA P-256 | HIGH | Well supported by Keystore and backend cryptography; use SHA-256 |
| Android BiometricPrompt | HIGH, strength-dependent | Must handle unavailable/not-enrolled/lockout; prefer BIOMETRIC_STRONG for key use |
| CameraX | HIGH | Use front camera for Face Gate and back camera for QR scanning if available |
| ML Kit Face Detection | HIGH for detection only | Not recognition; not a complete liveness control; Play-services dependency/version must be tested |
| ML Kit Barcode Scanning | HIGH | QR scanning is well supported; test camera quality and low-light behavior |
| HTTPS | HIGH | Required for production; no cleartext traffic; certificate validation mandatory |
| QR-based pairing | HIGH | Requires session binding, expiry, user confirmation, and replay protection |
| Challenge-response | HIGH | Needs server-side randomness, TTL, one-time use, device binding, and rate limiting |
| StrongBox | DEVICE-DEPENDENT | Must be probed; cannot be assumed from device model or feature list |
| App attestation | MEDIUM-HIGH | Available only with supported hardware/Google services configuration; verify in M2 |

---

## 5. Android Keystore Feasibility

### Feasible key design

- Algorithm: EC
- Curve: P-256 (secp256r1)
- Key purpose: sign (private key) / verify (public key)
- Signature: ECDSA with SHA-256
- Key generated inside `AndroidKeyStore`
- Private key non-exportable
- Public key exported to backend during pairing
- Key use protected by user authentication

### Android APIs to validate in M2

```text
KeyPairGenerator.getInstance("EC", "AndroidKeyStore")
KeyGenParameterSpec.Builder(
    alias,
    KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
)
.setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
.setDigests(KeyProperties.DIGEST_SHA256)
.setUserAuthenticationRequired(true)
.setUserAuthenticationParameters(...)
.setInvalidatedByBiometricEnrollment(true)
.setIsStrongBoxBacked(true) // only if availability is confirmed
```

The exact validity duration and authentication type must be decided in M2 based on product security requirements.

### Hardware-backed key behavior

| Capability | Feasibility | Verification required |
|---|---|---|
| TEE-backed key | Likely on modern devices | `KeyInfo.isInsideSecureHardware()` |
| StrongBox-backed key | Optional, not universal | `PackageManager.hasSystemFeature(FEATURE_STRONGBOX_KEYSTORE)` and key-generation fallback |
| Non-exportable private key | Expected for AndroidKeyStore EC keys | Attempt export must fail; inspect key material only through KeyStore APIs |
| Biometric-gated key use | Supported where biometrics are enrolled | `BiometricPrompt` + `CryptoObject`; test cancel/lockout/enrollment changes |
| Device-credential fallback | Possible, but security semantics differ | Define policy; device credential may not be sufficient for high-assurance key use |
| Key attestation | Supported on many devices | Validate certificate chain and attestation extension server-side |

### Important caveats

1. **StrongBox cannot be assumed.** It depends on device hardware and OEM implementation. The connected Samsung SM-A546E's feature list does not prove StrongBox support.
2. **Face biometrics may not be Class 3.** The app must inspect the actual biometric capability, not the device's marketing name.
3. **Biometric enrollment changes** may invalidate or change key authorization. Plan for recovery and re-pairing.
4. **Device credential** is not equivalent to strong biometric authorization for high-value signing operations. Decide the policy explicitly.
5. **Attestation** is required if the backend must trust that the key is hardware-backed and belongs to a genuine Android device. Without attestation, public-key registration can be abused by a compromised client.
6. **Lockout and lifecycle** states must be handled; signing failures must be safe and auditable.
7. **Clock skew** affects challenge expiration; the backend should be authoritative for time.

---

## 6. QR-Based Pairing Feasibility

### Recommended pairing model

1. Web session requests a pairing session from the backend.
2. Backend creates a random, short-lived pairing token and QR payload.
3. QR contains only a session identifier and HTTPS endpoint; no long-lived secret.
4. Android scans the QR.
5. App generates the P-256 key pair in Keystore.
6. App requests an attestation/key-registration challenge.
7. App signs the registration challenge after user approval and biometric authorization.
8. Backend validates signature and, if applicable, attestation.
9. Backend associates the public key with the account/device and marks pairing complete.
10. QR token is single-use and expires quickly.

### Controls

- Random pairing token with sufficient entropy.
- Short expiry (for example, 2–5 minutes; final value in M2).
- One-time consumption.
- Bind pairing to the logged-in web session and intended account.
- Show device metadata and public-key fingerprint to the user for confirmation.
- Rate limiting and anomaly logging.
- No private key or long-lived secret transmitted in the QR.
- HTTPS with certificate validation; production should consider pinning and must handle rotation.

---

## 7. Challenge-Response Authentication Feasibility

### Proposed protocol

1. Client requests a challenge for the paired device.
2. Backend generates a cryptographically random challenge and stores its hash with:
   - device/public-key identifier
   - purpose
   - issue time
   - expiry
   - one-time-use state
   - optional web-session binding
3. Android displays an approval screen.
4. BiometricPrompt authorizes use of the Keystore private key.
5. Android signs `SHA-256(challenge || context)` with ECDSA P-256.
6. Backend verifies the signature using the registered public key.
7. Backend atomically consumes the challenge and establishes the authenticated session.
8. Failures are rate-limited and audited without logging secrets.

### Additional requirements

- Use a canonical encoding for challenge/context.
- Domain-separate pairing, login, and high-risk actions.
- Reject reused, expired, unknown, or mismatched challenges.
- Bind challenges to the user/device/session as appropriate.
- Use a signature format agreed by both sides; Java's default ECDSA encoding is DER, while some browser APIs use raw `r||s`. Normalize at the boundary.
- Do not put sensitive data into the QR code or browser URL.
- Do not rely on SMS/email as the primary second factor.

---

## 8. Camera, ML Kit, and Device Constraints

| Item | Feasibility | M2 validation |
|---|---|---|
| CameraX preview + image analysis | High | Supported API level and camera permission flow |
| Front camera for Face Gate | High | Check device has usable front camera |
| Back camera for QR scanning | High | Check autofocus/low-light performance |
| ML Kit Face Detection bundled/unbundled | High but dependency packaging must be chosen | Test offline behavior and APK size |
| ML Kit Barcode Scanning | High | Test QR detection in real conditions |
| Google Play services availability | Device-dependent | Check on target device |
| Camera permission denial | Must handle | Test denied/permanently denied states |
| Device rotation/lifecycle | Must handle | Test configuration changes and process death |
| Offline network | Must handle | Show safe failure, do not authorize locally |

The connected device declares camera features and has four camera devices. That is a readiness signal, not an end-to-end proof of CameraX/ML Kit behavior.

---

## 9. Threat Model and Technical Risks

| Risk | Impact | Required treatment |
|---|---|---|
| Face detection treated as authentication | Critical | Separate detection from identity; document UX-only role |
| No liveness/anti-spoofing | Critical if face is used for security | Use BiometricPrompt/Keystore for security; if custom face auth is required, add dedicated liveness design and testing |
| Weak face biometrics on device | High | Prefer strong biometrics; enforce fallback policy |
| StrongBox assumption | High | Probe capability and gracefully use TEE/software-backed key; report assurance level |
| Key/device theft | High | Require biometric authorization, short challenge TTL, rate limiting, remote revocation |
| QR phishing/session fixation | High | Bind pairing to authenticated web session; expiry; one-time tokens; user confirmation |
| Replay of signed challenge | Critical | Nonce, expiry, one-time consumption, context binding |
| Public-key substitution during pairing | High | Authenticated pair initiation + attestation where possible + fingerprint confirmation |
| Man-in-the-middle | High | TLS validation; consider pinning with rotation plan; no cleartext |
| Malware/rooted device | High | Attestation/Play Integrity evaluation; do not rely on client-only checks |
| Biometric lockout | Medium | Clear error handling and documented recovery |
| Enrollment change | Medium | Invalidate keys and force re-pairing |
| Lost/offline phone | Medium | Recovery path that does not weaken the cryptographic factor |
| Clock skew | Medium | Server-authoritative expiration and clock-skew tolerance |
| Log leakage | High | Never log private keys, challenges, tokens, passwords, or full DATABASE_URL |
| ML Kit dependency changes | Medium | Pin versions and test at M2 integration |
| Camera permission/UX friction | Low–Medium | Clear onboarding, states, and fallback |
| ECDSA signature format mismatch | Medium | Explicit wire format and tests at the Android/backend boundary |
| Attestation chain validation errors | High | Server-side chain and challenge validation with tested failure modes |

---

## 10. Feasibility of the Planned M2 Mobile Stack

| Component | Feasibility | Recommendation |
|---|---|---|
| Kotlin native app | Feasible | Use modern Android Gradle setup and a committed wrapper |
| Android Keystore ECDSA P-256 | Feasible | Prototype first; record hardware-backing and StrongBox results |
| BiometricPrompt | Feasible | Require strong biometrics for key use; design fallback explicitly |
| CameraX | Feasible | Validate front/back camera flows and lifecycle |
| ML Kit Face Detection | Feasible for detection | Do not market it as recognition |
| ML Kit Barcode Scanning | Feasible | Validate QR payload and error handling |
| HTTPS | Feasible | Enforce TLS; never allow cleartext in production |
| QR pairing | Feasible | Short-lived, single-use, session-bound token; show key fingerprint |
| Challenge-response ECDSA | Feasible | Canonical payload, TTL, nonce, replay protection, server verification |

**Conclusion:** the smartphone authenticator is technically feasible as a **device-bound cryptographic authenticator**. Its security depends on not overstating Face Detection, validating Keystore/StrongBox capabilities at runtime, and implementing challenge-response and pairing correctly.

---

## 11. M2 Readiness Checklist

The following are prerequisites for starting M2 implementation, not M1 blockers:

- [ ] Install Android Studio and Android SDK.
- [ ] Install/select an Android-compatible JDK (prefer Android Studio JBR).
- [ ] Create and verify a Gradle wrapper.
- [ ] Confirm the physical device remains authorized and connected.
- [ ] Build and install a minimal Android proof-of-concept.
- [ ] Query biometric capability and enrolled modalities.
- [ ] Query StrongBox availability.
- [ ] Generate an EC P-256 key in AndroidKeyStore; prove private key is non-exportable.
- [ ] Prove a biometric-gated signing operation.
- [ ] Test key invalidation after biometric enrollment changes.
- [ ] Test CameraX preview and ML Kit Face Detection.
- [ ] Test ML Kit Barcode Scanning with a real QR code.
- [ ] Define the authentication challenge wire format and signature encoding.
- [ ] Define device pairing, revocation, and recovery flows.
- [ ] Define the Face Gate's exact security role and user messaging.
- [ ] Decide whether face recognition is actually required; if yes, create a separate approved design.
- [ ] Review threat model and privacy/consent requirements.
- [ ] Provide HTTPS development setup and production TLS policy.

---

## 12. M0 Feasibility Conclusion

| Question | Conclusion |
|---|---|
| Is the mobile authenticator concept feasible? | Yes, as a device-bound ECDSA challenge-response authenticator |
| Is ML Kit sufficient for Face Recognition? | No; it is face detection and must not be represented as recognition |
| Is Android Keystore suitable? | Yes, with device-dependent hardware-backing and StrongBox verification |
| Is QR pairing feasible? | Yes, with short-lived session-bound tokens |
| Can hardware claims be made now? | No; no APK or hardware test was performed |
| Is Android development ready? | No; Android Studio/SDK/Gradle are missing |
| Does this block M1? | No |
| Is M2 startable immediately? | Not until Android build tooling and a hardware proof-of-concept are prepared |

**Final status:** M0 authenticator feasibility is **FEASIBLE WITH M2 VALIDATION REQUIRED**. No implementation or hardware assertion is made in M0/M1.
