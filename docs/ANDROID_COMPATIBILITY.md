# IPGuard — Android Compatibility & Device Generalization Specification

**Project:** IPGuard — Secure Digital Asset Protection  
**Target Repository:** `https://github.com/Abhiprayaa29/IPGuard`  
**Document Version:** 1.1.0  
**Target Milestone:** Milestone 2 (Authentication & Device Security)  
**Last Updated:** November 8, 2026  

---

## 1. Executive Overview

The IPGuard Mobile Authenticator is architected as a **device-agnostic Android native security application**. It is designed to operate reliably across diverse Original Equipment Manufacturer (OEM) implementations (Samsung, Google Pixel, Xiaomi, OnePlus, Motorola, Sony, etc.) that comply with the Android Open Source Project (AOSP) Compatibility Definition Document (CDD) security standards.

The application does **not** rely on manufacturer-proprietary SDKs, vendor-exclusive hardware hooks, or hardcoded device models. While physical end-to-end testing on a Samsung Galaxy A54 5G (`SM-A546E`, Android 16 / API 36) serves as our reference verification anchor, the codebase adheres strictly to generalized Android platform contracts.

---

## 2. Platform SDK & Runtime Baseline

| Attribute | Configured Value | Target OS / Spec | Security & Operational Rationale |
|---|---|---|---|
| **`minSdkVersion`** | `28` | Android 9.0 (Pie) | Mandates hardware-backed Keymaster 4.0 / Keymint, modern biometric architectures, and strict TLS 1.3 network security policies. |
| **`targetSdkVersion`** | `36` | Android 16 (Baklava) | Targets current platform security behaviors, modern permission models, updated camera privacy boundaries, and strict foreground execution constraints. |
| **`compileSdkVersion`** | `36` | Android 16 | Compiles against current Android SDK platform APIs and AndroidX libraries. |
| **`buildToolsVersion`** | `36.0.0` | Android Build Tools | Modern AAPT2 resource compiler and D8/R8 dexers. |
| **Java / JVM Target** | `Java 17` (JVM 17) | OpenJDK 17 | Required by Gradle 8.13 and Android Gradle Plugin 8.13+. |
| **Kotlin Version** | `2.2.21` | Jetpack Compose Compiler | Modern declarative UI engine with zero legacy XML view hierarchy dependencies. |
| **Android Gradle Plugin** | `8.13.2` | Gradle 8.13 | Pinned build plugin ensuring deterministic reproducible builds. |
| **AndroidX Biometric** | `1.1.0` | AndroidX Security | Standardized prompt layer abstracting OEM biometric variations. |
| **CameraX Engine** | `1.6.2` | Camera2 Abstraction | Resilient rear QR scanning and front presence analysis. |
| **Google ML Kit** | `16.1.7` (Face) / `17.3.0` (Barcode) | On-Device Vision Engine | Local, zero-network barcode decoding and face presence detection. |
| **OkHttp Networking** | `4.12.0` | Square OkHttp | High-performance HTTP client with explicit connection pooling and timeout management. |
| **Compose BOM** | `2025.12.01` | AndroidX Compose | Material 3 UI components, design tokens, and state flows. |

---

## 3. Hardware Keystore & Cryptographic Invariants

### 3.1 Curve & Algorithm Specifications
- **Key Algorithm:** `KeyProperties.KEY_ALGORITHM_EC` (Elliptic Curve Cryptography).
- **Curve:** NIST P-256 (`secp256r1` / `prime256v1`).
- **Signature Algorithm:** `SHA256withECDSA` (ECDSA with SHA-256 digest).
- **Signature Format:** Standard ASN.1 DER sequence:
  $$\text{SEQUENCE} \{ r\ \text{INTEGER},\ s\ \text{INTEGER} \}$$
  Raw binary size is typically **70 to 72 bytes**, which encodes to **96 Base64 characters**.
- **Public Key Format:** X.509 `SubjectPublicKeyInfo` DER format (**91 bytes binary, 124 Base64 characters**).

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
+-------------------------------------------------------------+
|               Incoming Hardware Signing Request             |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|    Evaluate BiometricManager & KeyguardManager Capabilities |
+-------------------------------------------------------------+
         |                                           |
         | Class 3 Strong Available                  | Class 2 Only or No Biometric
         v                                           v
+------------------------------------+   +------------------------------------+
|  BiometricPrompt with CryptoObject |   | Fallback to DEVICE_CREDENTIAL      |
|  - Fingerprint (Class 3)           |   | - PIN / Pattern / Password         |
|  - 3D Face / Iris (Class 3)        |   | - Authorized via Gatekeeper TEE    |
+------------------------------------+   +------------------------------------+
                               |                         |
                               +------------+------------+
                                            |
                                            v
                         +------------------------------------+
                         | Secure Lock Screen Configured?     |
                         +------------------------------------+
                               |                     |
                               | Yes                 | No
                               v                     v
                         +------------+  +----------------------------+
                         | Unlock Key |  | FAIL-CLOSED: Reject Auth   |
                         | & Sign     |  | Throw DeviceLockScreen     |
                         | Challenge  |  | RequiredException          |
                         +------------+  +----------------------------+
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

### 4.3 API Level Compatibility
- **API 30+ (Android 11 to 16):** Native platform support for `BIOMETRIC_STRONG or DEVICE_CREDENTIAL` with `CryptoObject`.
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

## 6. Device Compatibility & Verification Classification

To provide an honest and accurate view of compatibility across the Android ecosystem, we distinguish five verification tiers:

| Device Profile / Platform | Hardware Isolation | Supported Modalities | Verification Classification |
|---|---|---|:---:|
| **Samsung Galaxy A54 5G (`SM-A546E`)**<br>(Exynos 1380, Android 16 / API 36) | Samsung Knox TEE / Keymint | Optical Fingerprint (Class 3), PIN, Pattern | :white_check_mark: **PHYSICALLY VERIFIED**<br>(Full Enrollment, Sign-In, and Negative Tests PASS) |
| **Google Pixel 7 / 8 / 9**<br>(Tensor G2/G3/G4, Android 13–15 / API 33–35) | Titan M2 StrongBox Keymaster | Under-display FP, Class 3 3D Face, PIN, Pattern | :large_blue_diamond: **ARCHITECTURALLY SUPPORTED & UNIT TESTED** |
| **Xiaomi / Redmi (MIUI / HyperOS)**<br>(Snapdragon / MediaTek, Android 10–14) | ARM TrustZone TEE | Side-mounted Fingerprint, PIN, Pattern | :large_blue_diamond: **ARCHITECTURALLY SUPPORTED & UNIT TESTED** |
| **OnePlus / OPPO / Realme (ColorOS)**<br>(Snapdragon, Android 11–15) | Qualcomm / MediaTek TEE | In-display Fingerprint, PIN, Pattern | :large_blue_diamond: **ARCHITECTURALLY SUPPORTED & UNIT TESTED** |
| **Android Virtual Device (AVD Emulator)**<br>(x86_64, API 28–36) | Software Keystore Emulation | Emulated Fingerprint gesture, PIN | :white_check_mark: **DEV & CI TESTED** |
| **Legacy Android 9.0 Pie (API 28)** | Keymaster 4.0 TEE | Fingerprint (Class 3), Keyguard PIN | :large_blue_diamond: **ARCHITECTURALLY SUPPORTED** |
| **Unlisted Commercial OEMs** | Varies by manufacturer | Conforming to AOSP CDD | :hourglass: **PENDING COMMUNITY VERIFICATION** |

---

## 7. Known Architectural Boundaries & Future Extensions

1. **Remote Key Attestation (M4 Scope):**
   In Milestone 2, public keys are verified via ECDSA proof-of-possession (signing canonical challenge nonces during enrollment). Full hardware root-of-trust certificate chain verification (Google/Samsung Keymaster Attestation root certificates) is slated for Milestone 4.
2. **Multi-User Account Association:**
   Milestone 2 establishes device-level enrollment and cryptographic proof of possession. Association with multi-tenant organizational user accounts is designed for subsequent identity milestones.
3. **Android 9 (API 28) Device Credential Legacy Window:**
   Devices on API 28 without enrolled biometrics require KeyguardManager-mediated challenges. Developers targeting legacy Android 9 devices should recommend biometric enrollment for optimal UX.
