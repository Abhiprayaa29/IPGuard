# M2 Architecture

**Project:** IPGuard — Secure Digital Asset Protection  
**Milestone:** M2.2 — On-Device Camera & QR Foundation  
**Date:** 2026-11-06  
**Status:** VERIFIED ON PHYSICAL DEVICE — CAMERAX AND ML KIT  
**Scope:** Android application structure, design system, navigation, preview state, the nine authenticator screens, CameraX camera pipeline, ML Kit face detection, and ML Kit barcode QR scanning. Keystore operations, biometrics, backend networking, and signing are deferred to M2.3/M2.4.

---

## 1. Purpose and Gate

M2.2 adds real on-device vision capabilities to the M2.1 authenticator foundation:

- Front-facing camera feed bound to lifecycle for UX presence checking (Face Gate).
- On-device ML Kit Face Detection validating user framing and face presence without persistent biometric enrollment or server transmission.
- Rear-facing camera feed for QR pairing scanning.
- On-device ML Kit Barcode Scanning for instant QR decode.
- Strict hardware lifecycle management: camera unbinds cleanly when navigating away or backgrounding.
- Zero frame persistence or network leakage.

---

## 2. Runtime Composition

```text
MainActivity
    │
    └── IPGuardTheme
            │
            └── IPGuardApp
                    ├── AuthenticatorViewModel (StateFlow<AuthenticatorUiState>)
                    ├── DeviceKeyManager (AndroidKeystoreDeviceKeyManager)
                    ├── rememberNavController()
                    └── AppNavHost
                            ├── AppDestination route table
                            ├── nine screen composables
                            │       ├── FaceGateScreen ──► CameraPreview + FacePresenceAnalyzer (Front Camera)
                            │       ├── QrScannerScreen ──► CameraPreview + QrCodeAnalyzer (Rear Camera)
                            │       └── DeviceInformationScreen ──► Key Diagnostics + Management
                            ├── ui/camera/
                            │       ├── CameraPermission
                            │       ├── CameraPreview
                            │       ├── FacePresenceAnalyzer
                            │       └── QrCodeAnalyzer
                            ├── security/
                            │       ├── DeviceKeyManager
                            │       ├── DeviceKeyExceptions
                            │       ├── KeySecurityLevel
                            │       ├── KeySecurityMetadata
                            │       ├── ExportedPublicKey
                            │       └── DeviceKeyVerificationRunner
                            └── ui/components design system
```

- One `ComponentActivity` hosts the entire UI.
- `MainActivity` enables edge-to-edge drawing and applies the dark system bar style.
- `IPGuardApp` owns the navigation controller and observes `AuthenticatorViewModel.uiState`.
- `AppNavHost` handles screen transitions.
- Camera and ML analysis run on dedicated background executors and bind strictly to Jetpack Compose composable lifecycles.

---

## 3. Navigation Contract

Navigation uses Navigation Compose and string routes. The `AppDestination` sealed class is the single route registry.

| Route | Screen | Purpose |
|---|---|---|
| `welcome` | `WelcomeScreen` | Entry point, current enrollment summary, setup and request actions |
| `registration` | `DeviceRegistrationScreen` | Explain one-active-phone enrollment stages |
| `face_gate` | `FaceGateScreen` | Front CameraX stage + ML Kit face detection presence check |
| `qr_scanner` | `QrScannerScreen` | Rear CameraX stage + ML Kit QR scanner |
| `authentication_request` | `AuthenticationRequestScreen` | Show sample browser/service/origin context |
| `approval` | `ApprovalScreen` | Preview the final approval decision |
| `result/{outcome}` | `ResultScreen` | Terminal preview result for scan, approval, or rejection |
| `device_information` | `DeviceInformationScreen` | Show local device facts and enrollment state |
| `security_settings` | `SecuritySettingsScreen` | Read-only planned security controls |

Supported `outcome` values are `scan_complete`, `approved`, and `rejected`.

---

## 4. Camera & Machine Learning Architecture

### Camera Subsystem (`ui/camera/`)

1. **`CameraPermission.kt`**:
   - Manages runtime `Manifest.permission.CAMERA` requests via Compose ActivityResultContracts.
   - Observes `Lifecycle.Event.ON_RESUME` to reactively update permissions if changed in system settings.
   - Provides direct intent action to open application details in system settings on permanent denial.

2. **`CameraPreview.kt`**:
   - Embeds Android `PreviewView` with `COMPATIBLE` implementation mode and `FILL_CENTER` scaling.
   - Binds `Preview` and `ImageAnalysis` (strategy `KEEP_ONLY_LATEST`) to the composable's `LocalLifecycleOwner`.
   - On composable disposal, automatically unbinds camera use cases and shuts down single-threaded analysis executor.

3. **`FacePresenceAnalyzer.kt`**:
   - Integrates Google ML Kit `FaceDetection.getClient(...)`.
   - Uses `PERFORMANCE_MODE_FAST` and `minFaceSize = 0.15f`.
   - Closes each `ImageProxy` immediately upon completion or failure.
   - Reports presence boolean to UI; zero storage or upload of camera frames.

4. **`QrCodeAnalyzer.kt`**:
   - Integrates Google ML Kit `BarcodeScanning.getClient(...)` restricted to `Barcode.FORMAT_QR_CODE`.
   - Closes each `ImageProxy` immediately.
   - Atomic one-shot detection trigger ensures callback fires once per code.

---

## 5. Dependency Set

| Component | Version |
|---|---|
| Kotlin | 2.2.21 |
| Android Gradle Plugin | 8.13.2 |
| Gradle Wrapper | 8.13 |
| Compose BOM | 2025.12.01 |
| Navigation Compose | 2.9.8 |
| Lifecycle runtime/viewmodel Compose | 2.9.4 |
| Activity Compose | 1.11.0 |
| Core KTX | 1.17.0 |
| Material 3 | Compose BOM-managed |
| Material Icons Core | Compose BOM-managed |
| CameraX | 1.6.2 (`camera-camera2`, `camera-lifecycle`, `camera-view`) |
| ML Kit Face Detection | 16.1.7 |
| ML Kit Barcode Scanning | 17.3.0 |

The application uses `compileSdk 36`, `targetSdk 36`, `minSdk 28`, Java 17 bytecode, and version `0.3.0` (`versionCode 3`).

---

## 6. Security & Privacy Boundary

- **Ephemeral In-Memory Frames**: All camera frames exist solely in volatile memory during the analysis pipeline. No frames are written to disk, cached, or transmitted over network.
- **Presence vs Recognition**: Face Gate enforces a UX presence check only. It does not perform biometric matching or identity verification.
- **Hardware Isolation**: Cameras are disconnected whenever the user leaves the Face Gate or QR Scanner screens.
- **No Keystore or Biometrics in M2.2**: Android Keystore private key generation and BiometricPrompt authorization are deferred to M2.3.

---

## 7. Planned Expansion

| Milestone | Status | Scope |
|---|---|---|
| M2.0 | **COMPLETE** | Android build toolchain, Gradle wrapper, physical device probe |
| M2.1 | **COMPLETE** | Single-activity Compose authenticator, 9-screen navigation, theme |
| M2.2 | **COMPLETE** | Front CameraX + ML Kit Face presence check; rear CameraX + ML Kit Barcode QR scanning; explicit lifecycle release |
| M2.3-A | **COMPLETE** | Android Keystore EC P-256 device signing key foundation, non-exportable private key, KeyInfo security level, X.509 Base64 export, unit test suite |
| M2.1 | COMPLETE | Baseline shell, navigation, 9 preview screens |
| M2.2 | COMPLETE | CameraX, ML Kit Face presence detection, ML Kit QR scanner, on-device verified |
| M2.3-A | COMPLETE | Android Keystore ECDSA P-256 keypair, TEE verified, non-exportable, X.509 export, physical device tested |
| M2.3-B | COMPLETE | Authentication Policy Revision, BiometricPrompt + CryptoObject with DEVICE_CREDENTIAL per-operation signing, non-mandatory fingerprint, physical device verified |
| M2.4 | **NEXT GATE** | Live challenge retrieval, QR payload verification, backend enrollment & signature validation, browser session unlock |

---

## 8. Source Map

```text
mobile-authenticator/app/src/main/java/com/ipguard/authenticator/
├── MainActivity.kt (FragmentActivity)
├── IPGuardApp.kt
├── navigation/
│   ├── AppDestination.kt
│   └── AppNavHost.kt
├── security/
│   ├── DeviceAuthenticationPolicy.kt
│   ├── DeviceKeyExceptions.kt
│   ├── DeviceKeyManager.kt
│   ├── DeviceKeyVerificationRunner.kt
│   ├── DeviceSigningAuthenticator.kt
│   ├── ExportedPublicKey.kt
│   ├── KeySecurityLevel.kt
│   └── KeySecurityMetadata.kt
├── ui/
│   ├── camera/
│   │   ├── CameraPermission.kt
│   │   ├── CameraPreview.kt
│   │   ├── FacePresenceAnalyzer.kt
│   │   └── QrCodeAnalyzer.kt
│   ├── components/
│   │   ├── AppChrome.kt
│   │   ├── Controls.kt
│   │   └── InfoElements.kt
│   ├── screens/
│   │   ├── approval/ApprovalScreen.kt
│   │   ├── deviceinfo/DeviceInformationScreen.kt
│   │   ├── facegate/FaceGateScreen.kt
│   │   ├── registration/DeviceRegistrationScreen.kt
│   │   ├── request/AuthenticationRequestScreen.kt
│   │   ├── result/ResultScreen.kt
│   │   ├── scanner/QrScannerScreen.kt
│   │   ├── settings/SecuritySettingsScreen.kt
│   │   └── welcome/WelcomeScreen.kt
│   ├── state/
│   │   ├── AuthenticatorUiState.kt
│   │   ├── AuthenticatorViewModel.kt
│   │   └── PreviewResult.kt
│   └── theme/Theme.kt
└── res/values/strings.xml

mobile-authenticator/app/src/test/java/com/ipguard/authenticator/
└── security/
    └── ExportedPublicKeyTest.kt

mobile-authenticator/app/src/androidTest/java/com/ipguard/authenticator/
└── security/
    ├── DeviceAuthenticationPolicyTest.kt
    └── DeviceKeyPhysicalInstrumentationTest.kt
```

Build, lint, installation, and physical-device evidence are recorded in [M2_TEST_REPORT.md](M2_TEST_REPORT.md), [M2.3A_KEYSTORE_REPORT.md](M2.3A_KEYSTORE_REPORT.md), [M2.3A_SECURITY_REVIEW.md](M2.3A_SECURITY_REVIEW.md), and [M2.3B_AUTHENTICATION_REPORT.md](M2.3B_AUTHENTICATION_REPORT.md).

---

## 8. Milestone 2.4 Architecture — QR Authentication & Backend Core Engine

Milestone 2.4 establishes the cryptographic bridge between the Android hardware authenticator and the IPGuard web management console:

- **M2.4-A:** Architecture & Cryptographic Challenge-Response Design (Complete).
- **M2.4-B:** Backend Core Engine & PostgreSQL Schema (Complete & Verified):
  - Database schema: `devices` and `auth_sessions` with Alembic migration `0002_devices_and_auth_sessions`.
  - Cryptographic engine (`app/services/crypto.py`): X.509 DER SubjectPublicKeyInfo parsing, curve NIST P-256 (`secp256r1`) enforcement, and `SHA256withECDSA` ASN.1 DER signature verification.
  - Concurrency protection: PostgreSQL `SELECT ... FOR UPDATE` pessimistic row-level locking preventing duplicate consumption of single-use challenges.
  - Origin normalization: RFC 6454 validation and strict whitelist resolution (`app/services/origin.py`).
  - Protected device registry: `GET /api/v1/auth/devices` guarded by `X-Dev-Admin-Key` in development and strictly disabled in production (HTTP 403).
- **M2.4-C:** Frontend QR Display, Polling Hook, and Anti QR-Jacking Channel Binding (`DESIGNED — IMPLEMENTATION PENDING (M2.4-C)`).
- **M2.4-D:** Android Authenticator QR Parser & OkHttp Network Client Integration (Pending M2.4-C).

Detailed API contracts and remediation verification are documented in [M2.4_API_CONTRACT.md](M2.4_API_CONTRACT.md) and [M2.4B_SECURITY_REMEDIATION_REPORT.md](M2.4B_SECURITY_REMEDIATION_REPORT.md).
