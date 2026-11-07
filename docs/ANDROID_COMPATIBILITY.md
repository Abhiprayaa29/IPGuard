# IPGuard — Android Compatibility & Device Generalization Specification

**Project:** IPGuard — Secure Digital Asset Protection  
**Document Version:** 1.0.0  
**Target Milestone:** Milestone 2 (Authentication & Device Security)  
**Last Updated:** November 8, 2026  

---

## 1. Executive Overview

IPGuard Mobile Authenticator is architected as a **device-agnostic Android application**. It is designed to run across diverse OEM implementations (Samsung, Google Pixel, Xiaomi, OnePlus, Motorola, etc.) adhering to the Android Open Source Project (AOSP) CDD (Compatibility Definition Document) security standards.

The application does not depend on manufacturer-specific APIs, proprietary SDKs, or hardcoded device models. Physical testing on the Samsung Galaxy A54 5G (`SM-A546E`, Android 16) serves as one reference validation target, while the codebase maintains strict adherence to generalized Android platform contracts.

---

## 2. Platform SDK & Runtime Baseline

| Attribute | Configured Level | Target OS Version | Security Rationale |
|---|---|---|---|
| **`minSdkVersion`** | `28` | Android 9.0 (Pie) | Enforces hardware-backed Keymaster 4.0 / Keymint, modern biometric architectures, and strict TLS 1.3 / network security policies. Devices below API 28 lack robust TEE-backed biometric crypto-object binding. |
| **`targetSdkVersion`** | `36` | Android 16 (Baklava) | Targets the latest platform security behaviors, modern permission models, updated photo/camera privacy boundaries, and strict foreground service requirements. |
| **`compileSdkVersion`** | `36` | Android 16 | Compiles against current Android SDK platform APIs and AndroidX libraries. |
| **Java / JVM Target** | `Java 17` (JVM 17) | OpenJDK 17 | Aligned with Gradle 8.13 and Android Gradle Plugin 8.9+. |
| **Kotlin Version** | `2.0+` | Jetpack Compose Compiler | Modern declarative UI engine with zero legacy XML view hierarchy dependencies. |

---

## 3. Hardware Keystore & Cryptographic Invariants

### 3.1 Curve & Algorithm Specifications
- **Key Algorithm:** `KeyProperties.KEY_ALGORITHM_EC` (Elliptic Curve Cryptography).
- **Curve:** NIST P-256 (`secp256r1` / `prime256v1`).
- **Signature Algorithm:** `SHA256withECDSA` (ECDSA with SHA-256 digest).
- **Signature Encoding:** ASN.1 DER (Distinguished Encoding Rules), producing a 70–72 byte binary payload (typically 96 Base64 characters).
- **Public Key Format:** X.509 `SubjectPublicKeyInfo` DER format (91 bytes binary, 124 Base64 characters).

### 3.2 Key Protection & Non-Exportability Invariant
1. **Isolated Key Generation:** Private keys are generated directly inside the device's hardware security boundary (`AndroidKeyStore` provider).
2. **Strict Non-Exportability:**
   ```kotlin
   val privateKey = keyStore.getKey(keyAlias, null) as PrivateKey
   check(privateKey.encoded == null) {
       "CRITICAL SECURITY VIOLATION: Private key must be non-exportable!"
   }
   ```
   The private key material cannot be extracted by the application, root users, or external debugging interfaces.
3. **Hardware Backing Level Inspection:**
   The application dynamically inspects the hardware backing via `KeyInfo`:
   - `STRONGBOX`: Dedicated tamper-resistant hardware security module with discrete CPU and RAM (e.g. Titan M2, Knox Vault).
   - `TRUSTED_ENVIRONMENT`: TEE execution within the primary application processor's secure world (ARM TrustZone).
   - `SOFTWARE`: Emulated fallback (only permitted in mock test suites; rejected by policy in production).

---

## 4. Adaptive Authentication Architecture

Android devices present diverse biometric capabilities ranging from ultrasonic fingerprint sensors to 2D optical cameras. IPGuard enforces an **adaptive, fail-closed authentication policy**:

### 4.1 Modality Evaluation Ladder

```text
[ Incoming Signing Request ]
            │
            ▼
┌──────────────────────────────────────────────┐
│ Evaluate BiometricManager & KeyguardManager  │
└──────────────────────────────────────────────┘
            │
            ├─► BIOMETRIC_STRONG Available? (Class 3)
            │     └─► Use BiometricPrompt with CryptoObject
            │           ├─► Fingerprint Class 3
            │           └─► 3D Face / Iris Class 3
            │
            ├─► BIOMETRIC_STRONG Not Available / Optical Face Class 2 Only?
            │     └─► Fallback to DEVICE_CREDENTIAL (PIN / Pattern / Password)
            │           └─► Authorized via Gatekeeper TEE
            │
            └─► No Secure Lock Screen Configured?
                  └─► FAIL-CLOSED: Refuse Key Generation / Signing
                        └─► Display: "Device secure lock screen required"
```

### 4.2 Handling Weak Biometrics (Class 2 / Class 1)
- **Strict Prohibition for Cryptographic Keys:** Android security guidelines forbid binding `CryptoObject` to `BIOMETRIC_WEAK` (e.g. standard RGB front camera 2D face unlock).
- **Enforcement:** `DeviceSigningAuthenticator` strictly requests:
  ```kotlin
  builder.setAllowedAuthenticators(
      BiometricManager.Authenticators.BIOMETRIC_STRONG or
      BiometricManager.Authenticators.DEVICE_CREDENTIAL
  )
  ```
  Devices equipped solely with Class 2 face recognition seamlessly and securely route to **Device Credential (PIN / Pattern / Password)**, preventing spoofing bypasses.

### 4.3 API Level Branching (Android 10 vs 11+)
- **API 30+ (Android 11 to 16):** Fully supports `BIOMETRIC_STRONG or DEVICE_CREDENTIAL` alongside `CryptoObject`.
- **API 28–29 (Android 9–10):** AOSP `BiometricPrompt` did not permit combining `DEVICE_CREDENTIAL` with `CryptoObject` in a single prompt. For API < 30, the policy verifies `BIOMETRIC_STRONG` directly, falling back to dedicated `KeyguardManager` challenge flows if biometrics are absent.

---

## 5. Device Identity & Privacy Protection

To ensure privacy and multi-device portability without privacy violations:

1. **Zero Hardware Identifiers:**
   - IPGuard **never** reads, requests, or transmits IMEI, MEID, IMSI, SIM serial, or WiFi MAC addresses.
   - The app does not request `READ_PHONE_STATE` or `READ_PRIVILEGED_PHONE_STATE`.
2. **App-Scoped Device UUID:**
   Device identity is established through an application-scoped, cryptographically random identifier:
   ```kotlin
   val newId = "ipguard-dev-" + UUID.randomUUID().toString().replace("-", "").take(16)
   ```
   Stored in private `SharedPreferences` (`MODE_PRIVATE`). Reinstalling the app generates a clean new identity requiring explicit re-enrollment.
3. **Dynamic Hardware Metadata:**
   Device model and manufacturer are resolved dynamically via standard Android properties:
   - Manufacturer: `Build.MANUFACTURER`
   - Model: `Build.MODEL`
   - OS Version: `Build.VERSION.RELEASE` (API `Build.VERSION.SDK_INT`)
   No OEM or device name is hardcoded in application logic.

---

## 6. Cross-Device Compatibility Test Matrix

| Device Profile / Capability | Primary Auth Path | CryptoObject Authorization | Fail-Closed Fallback | Test Status |
|---|---|---|---|---|
| **Samsung Galaxy A54 5G** (Exynos 1380, Android 16) | Optical Fingerprint (Class 3) / PIN | Yes (TEE-backed ECDSA) | PIN / Pattern | **VERIFIED (Physical Device)** |
| **Google Pixel 7 / 8 / 9** (Tensor, StrongBox) | Under-Display FP / Class 3 Face | Yes (StrongBox / Titan M2) | PIN / Pattern | **VERIFIED (Unit / Architecture)** |
| **Device with 2D Camera Face Only** (Class 2) | PIN / Pattern / Password | Yes (via Gatekeeper TEE PIN) | Bypass Prohibited | **VERIFIED (Unit / Contract)** |
| **Device with No Biometric Hardware** | PIN / Pattern / Password | Yes (via Gatekeeper TEE PIN) | Secure Lock Required | **VERIFIED (Unit / Contract)** |
| **Unsecured Device** (No PIN / Swipe Only) | None | Blocked | `DeviceLockScreenRequiredException` | **VERIFIED (Unit / Negative Test)** |
| **Unregistered Key Sign-In Attempt** | None | Blocked | `Request rejected — key not initialized` | **VERIFIED (Physical Device)** |
| **Camera Sensor Unavailable / Disconnected** | None (Scanner) | N/A | Display error message, zero crash | **VERIFIED (Unit Test)** |
| **Camera Permission Denied by User** | None (Scanner) | N/A | Graceful permission rationale banner | **VERIFIED (Compose Lifecycle)** |
| **Network Disconnected / Server Offline** | N/A | Local signature succeeds | `NetworkError: connection failed` | **VERIFIED (Physical Device)** |

---

## 7. Known Architectural Boundaries & Future Extensions

1. **Remote Key Attestation (M4 Scope):**
   In Milestone 2, public keys are verified via ECDSA proof-of-possession (signing canonical challenge nonces during enrollment). Full hardware root-of-trust certificate chain verification (Google/Samsung Keymaster Attestation root certificates) is slated for Milestone 4.
2. **Multi-User Account Association:**
   Milestone 2 establishes device-level enrollment and cryptographic proof of possession. Association with multi-tenant organizational user accounts is designed for subsequent identity milestones.
3. **Android 9 (API 28) Device Credential Legacy Window:**
   Devices on API 28 without enrolled biometrics require KeyguardManager-mediated challenges. Developers targeting legacy Android 9 devices should recommend biometric enrollment for optimal UX.
