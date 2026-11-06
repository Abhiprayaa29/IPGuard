# M2 Test Report

**Project:** IPGuard — Secure Digital Asset Protection  
**Milestone:** M2.2 — On-Device Camera & QR Foundation  
**Date:** 2026-11-06  
**Status:** M2.2 VERIFIED ON PHYSICAL DEVICE — CAMERAX AND ML KIT  
**Overall M2 status:** IN PROGRESS — M2.2 complete; M2.3 is next gate

---

## 1. Result Summary

| Area | Result | Evidence |
|---|---|---|
| Debug build | **PASS** | `:app:assembleDebug` — `BUILD SUCCESSFUL` |
| Android lint | **PASS** | 0 errors, 7 warnings |
| APK installation | **PASS** | `adb install -r` — `Success` (version `0.3.0`, `versionCode 3`) |
| Cold launch | **PASS** | 1,033 ms, `MainActivity` focused |
| Runtime process | **PASS** | Process alive across all flows |
| Camera permissions | **PASS** | Runtime prompt, grant flow, denial UI fallback, and system settings navigation |
| Front CameraX & Face Gate | **PASS** | Front camera preview, ML Kit Face Detection, UI presence check gate (`Detected`), continue action enabled |
| Rear CameraX & QR Scanner | **PASS** | Rear camera preview, ML Kit Barcode scanning (`FORMAT_QR_CODE`), one-shot scan navigation |
| Camera lifecycle & disconnect | **PASS** | Explicit `unbindAll()` / unbind on disposal; verified with `dumpsys media.camera` active clients empty upon back |
| Zero frame persistence / upload | **PASS** | Pure in-memory analysis via `ImageAnalysis`; immediate `imageProxy.close()`; no disk/network transmission |
| Result system back | **PASS** | Terminal back interception returns to Welcome |
| Fatal runtime exception | **PASS** | 0 `FATAL EXCEPTION`, application `Process:`, or app ANR matches |
| Keystore / biometric / signing | **NOT TESTED** | M2.3/M2.4 scope |
| Backend / web integration | **NOT TESTED** | M2.3/M2.4 scope |

M2.2 satisfies the camera lifecycle, face presence detection, and QR scanning gate. This report does not certify IPGuard as a fully integrated authenticator.

---

## 2. Environment

The build used the verified M2.0/M2.1 environment documented in [M2_ANDROID_SETUP.md](M2_ANDROID_SETUP.md):

| Item | Value |
|---|---|
| OS | Windows 11 Home Single Language, 64-bit |
| PowerShell | 5.1 |
| JDK | Eclipse Temurin 17.0.20.1 |
| Android SDK | API 36 |
| Build Tools | 36.0.0 |
| Gradle Wrapper | 8.13 |
| Android Gradle Plugin | 8.13.2 |
| Kotlin | 2.2.21 |
| Compose BOM | 2025.12.01 |
| CameraX | 1.6.2 (`camera-camera2`, `camera-lifecycle`, `camera-view`) |
| ML Kit | `face-detection:16.1.7`, `barcode-scanning:17.3.0` |
| Physical device | Samsung SM-A546E |
| Android version | Android 16 / API 36 |
| Display | 1080 × 2340, density 450 |
| Android Studio / emulator | Not installed; physical device only |

---

## 3. Build

Executed from `mobile-authenticator` after loading the repository environment:

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard
. .\scripts\android-env.ps1
Set-Location mobile-authenticator
.\gradlew.bat :app:assembleDebug :app:lintDebug
```

Result:

```text
BUILD SUCCESSFUL in 50s
50 actionable tasks: 23 executed, 27 from cache
```

The debug APK is generated at:

```text
mobile-authenticator\app\build\outputs\apk\debug\app-debug.apk
```

---

## 4. Lint

```text
0 errors, 7 warnings
```

The warnings are expected informational version/resource notices:

1. Gradle 8.14.6 is available; the project uses the pinned Gradle 8.13.
2. `androidx.core:core-ktx` 1.19.1 is available; the project uses 1.17.0.
3. `androidx.activity:activity-compose` 1.13.0 is available; the project uses 1.11.0.
4. `androidx.lifecycle:lifecycle-runtime-compose` 2.11.0 is available; the project uses 2.9.4.
5. `androidx.lifecycle:lifecycle-viewmodel-compose` 2.11.0 is available; the project uses 2.9.4.
6. `androidx.navigation:navigation-compose` 2.10.2 is available; the project uses 2.9.8.
7. The `mipmap-anydpi-v28` resource folder is marked unnecessary because `minSdk` is 28; the versioned folder is intentionally retained for AAPT resource-linking compatibility.

No lint warning is an error. The full report is at:

```text
mobile-authenticator\app\build\reports\lint-results-debug.html
```

---

## 5. APK Artifact

| Item | Value |
|---|---|
| Package | `com.ipguard.authenticator` |
| Version | `0.3.0` (`versionCode 3`) |
| Size | 102,801,795 bytes |
| SHA-256 | `C33CCB22B1019F685A7743E24B0BB339798F97273F0032C2937CA8CDADF5AC6A` |
| Minimum SDK | 28 |
| Target SDK | 36 |
| Compile SDK | 36 |
| Native libraries | `libbarhopper_v3.so`, `libface_detector_v2_jni.so`, `libimage_processing_util_jni.so`, `libsurface_util_jni.so` |
| Launchable activity | `com.ipguard.authenticator.MainActivity` |
| Signing | Android Debug certificate |
| Release-ready | No |

---

## 6. Installation and Launch

```text
Performing Streamed Install
Success
```

Latest cold launch:

```text
LaunchState: COLD
Status: ok
Activity: com.ipguard.authenticator/.MainActivity
TotalTime: 1033 ms
WaitTime: 1037 ms
```

Foreground verification:

```text
mCurrentFocus=Window{... u0 com.ipguard.authenticator/com.ipguard.authenticator.MainActivity}
```

---

## 7. Camera and QR Verification

Testing used ADB input, UIAutomator dumps, and camera service dumpsys checks on the physical device.

### 7.1 Runtime Permission Flow

1. On first navigation to Face Gate, the application triggers Android's runtime camera permission prompt (`Manifest.permission.CAMERA`).
2. When granted, the preview surfaces immediately.
3. If denied or revoked, `CameraPermissionState` displays:
   - Warning notice card explaining camera requirements.
   - Primary action: "Allow camera access" (re-prompts).
   - Secondary action: "Open system settings" (`ACTION_APPLICATION_DETAILS_SETTINGS`).

### 7.2 Face Gate (Front CameraX + ML Kit Face Detection)

1. Front camera (`CameraSelector.LENS_FACING_FRONT`) binds to lifecycle with `CameraPreview`.
2. Image frames stream to `FacePresenceAnalyzer` with backpressure strategy `KEEP_ONLY_LATEST`.
3. `FaceDetection.getClient` runs on-device fast face detection.
4. UI state transitions:
   - Searching state: "Searching for face...", Continue action disabled (`primaryEnabled = false`).
   - Detected state: "Face detected", Camera badge reports "FACE", Face presence reports "Detected", Continue action enabled (`primaryEnabled = true`).
5. Detection is strictly a presence check and framing aid; copy explicitly states: *"Detection, not recognition. Face Gate checks that a face is present and reasonably framed. It does not identify you."*

### 7.3 QR Scanner (Rear CameraX + ML Kit Barcode Scanning)

1. Rear camera (`CameraSelector.LENS_FACING_BACK`) binds to lifecycle.
2. Image frames stream to `QrCodeAnalyzer` configured for `Barcode.FORMAT_QR_CODE`.
3. Valid QR code triggers atomic callback `onScanComplete()`.
4. Navigates cleanly to `AppDestination.Result` with outcome `scan_complete`.

### 7.4 Camera Lifecycle and Resource Release

Verified through `dumpsys media.camera`:

1. While on Face Gate screen:
   ```text
   Active Camera Clients:
   CONNECT device 1 client for package com.ipguard.authenticator (PID ...)
   ```
2. When pressing back to return to Registration / Welcome:
   ```text
   DISCONNECT device 1 client for package com.ipguard.authenticator (PID ...)
   Active Camera Clients:
   []
   ```
3. Camera unbinding is immediate; no background camera leak occurs.

---

## 8. Screenshot Evidence

All screenshots were captured on the physical Samsung SM-A546E at 1080 × 2340. The complete M2.2 set is stored in [assets/m2.2](assets/m2.2/).

| # | File | State | Bytes |
|---:|---|---|---:|
| 01 | `01-welcome.png` | Welcome with M2.2 scope notice | 395,435 |
| 02 | `02-device-registration.png` | Registration stages with M2.2 note | 401,597 |
| 03 | `03-face-gate-permission-prompt.png` | Camera permission prompt | 242,079 |
| 04 | `13-face-gate-detected-actions.png` | Face Gate: face detected & continue enabled | 425,024 |
| 05 | `09-scanner-rear-fixed.png` | QR scanner live rear camera | 354,821 |
| 06 | `16-final-scan-result.png` | Scan complete terminal result | 1,054,540 |
| 07 | `17-final-welcome.png` | Returned to Welcome from terminal result | 1,054,605 |

Screenshot SHA-256 values:

```text
01-welcome.png                     1F81F3FA49E93058CF3E28FB312D6E3CF7CDC226C59CE9EB1A55B23BC79859AC
02-device-registration.png         57BE33E48DADC974682728054CEC9755AC193217B0FC9F7B16B93D63F36EA7E2
03-face-gate-permission-prompt.png E4382A4CACB95CA32CE2CB5A81837AE8A40079327EE7B706F3C7A8DBD2D140E7
09-scanner-rear-fixed.png          0C68E6B78857B2854A57862CE82F95B009D7AA9193E55D75CBA080709E5D629C
12-permission-prompt.png           DDAEC6039AACD460FFC284F6CE7B90B60FB51D394D6DD4E2D87F50B48A92619B
13-face-gate-detected-actions.png  3F2AB828E873EBF75578E67EEC047772A97030C703568DFECDCE0BF3483ED426
16-final-scan-result.png           782C2009C955424CDB52E3EA066FE5EB74B0BAB95E368DF9670C36B7685F5B0B
17-final-welcome.png               F7BBE317C7A8609A98A2575FE0FBC96B119C07B80C7F61945A9E1B88C4017086
```

---

## 9. Security and Privacy Checks

| Check | Result |
|---|---|
| Real authentication implemented | No — preview/gating only |
| Biometric prompt requested | No (deferred to M2.3) |
| Camera opened | Yes — front on Face Gate, rear on QR Scanner |
| Camera unbind on leave | Yes — verified active camera clients empty |
| QR decoded | Yes — ML Kit barcode scanner |
| Keystore key created | No (deferred to M2.3) |
| Signature created | No (deferred to M2.4) |
| Network request made by the app | No |
| Face frames or QR images stored | No — analyzed in memory, closed immediately |
| Device serial displayed | No |
| Secret/private key displayed | No |
| Application backup enabled | No |
| Device-transfer extraction enabled | No |
| Cleartext HTTP enabled in main manifest | No |
| Release signing configured | No |
| Real credentials or environment secrets added | No |

---

## 10. Acceptance and Next Gate

| Requirement | Result |
|---|---|
| Android app builds with CameraX and ML Kit | **PASS** |
| Lint has no errors | **PASS** |
| APK installs on the physical device | **PASS** |
| Runtime camera permission flow functions properly | **PASS** |
| Front CameraX + ML Kit Face Detection operates live | **PASS** |
| Rear CameraX + ML Kit Barcode QR scanning operates live | **PASS** |
| Explicit camera lifecycle unbinding releases hardware | **PASS** |
| Zero frame persistence and zero network leak | **PASS** |
| No fatal runtime exception during full flow | **PASS** |

M2.2 is accepted as verified on physical device.

### Next Gate — Milestone M2.3:

1. Android Keystore integration for hardware-backed ECDSA P-256 keypair generation.
2. BiometricPrompt / device credential authorization integration.
3. Backend device registration endpoint (`/api/v1/auth/device/register`) to receive and verify enrolled public keys.
4. Local device enrollment state persistence.
