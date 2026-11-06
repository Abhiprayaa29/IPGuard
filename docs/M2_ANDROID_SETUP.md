# M2 Android Setup

**Project:** IPGuard — Secure Digital Asset Protection  
**Milestone:** M2.0 — Android Environment and Build Foundation  
**Date:** 2026-11-06  
**Status:** COMPLETED ON PHYSICAL DEVICE  
**Scope:** Android toolchain, Gradle Wrapper, minimal Compose build, APK installation, and launch verification. No authentication feature is implemented in M2.0.

> This document remains the historical M2.0 setup and build-probe report. The current application is M2.1 (`0.2.0`, `versionCode 2`); its architecture and physical verification are recorded in [M2_ARCHITECTURE.md](M2_ARCHITECTURE.md) and [M2_TEST_REPORT.md](M2_TEST_REPORT.md).

---

## 1. Purpose

M2.0 establishes a reproducible Android build path for the device-bound authenticator. It proves that this workstation can build, install, and launch an APK on the connected physical phone before M2.1 adds authenticator screens and application structure.

The M2.0 gate is satisfied:

- Android build tools are installed.
- A pinned Gradle Wrapper builds a Kotlin/Jetpack Compose application.
- A debug APK is produced.
- The APK installs and launches in the foreground on the physical Samsung SM-A546E.
- Build, install, launch, UI, and crash checks passed.

Detailed evidence is in [M2_ENVIRONMENT_REPORT.md](M2_ENVIRONMENT_REPORT.md).

---

## 2. Toolchain

| Component | Version | Location |
|---|---|---|
| Android Studio | Not installed | Not used; command-line SDK only |
| Android SDK Platform | API 36, revision 2 | `D:\Android\Sdk\platforms\android-36` |
| Android SDK Build Tools | 36.0.0 (pinned); 35.0.0 also present | `D:\Android\Sdk\build-tools` |
| Android SDK Platform Tools | 37.0.1 | `D:\Android\Sdk\platform-tools` |
| Android SDK Command-line Tools | 22.0, build 15859902 | `D:\Android\Sdk\cmdline-tools\latest` |
| JDK | Eclipse Temurin 17.0.20.1+1 | `D:\Android\jdk-17` |
| Gradle | 8.13, wrapper and local distribution | `D:\Android\gradle-8.13` |
| Android Gradle Plugin | 8.13.2 | Gradle dependency |
| Kotlin | 2.2.21 | Gradle plugin |
| Compose BOM | 2025.12.01 | Gradle dependency |
| Gradle user home | Local project cache | `D:\Android\.gradle` |
| Android user home | Local Android tool state | `D:\Android\.android` |

The global Java installation remains Java 22. Do not build with the global Java. Always load the M2 environment script before Android commands.

Android Studio, an emulator, and AVD images are intentionally absent. The CLI toolchain uses less disk space and is sufficient for the M2.0 build/install/launch gate. Physical-device testing is mandatory.

---

## 3. Disk Layout

```text
D:\Android\
├── Sdk\                   Android SDK
├── jdk-17\                Temurin JDK 17
├── gradle-8.13\           Local Gradle distribution
├── .gradle\               Gradle caches and wrapper distribution
├── .android\              Android user state
└── downloads\             Verified installation archives and logs
```

Project sources remain under:

```text
C:\Users\user\Documents\02_Projects\IPGuard\mobile-authenticator
```

The C: Documents alias is a junction to `D:\Data\Documents`. Project files physically use D: space.

C: free space is low. Keep Gradle and SDK caches on D: through the environment script. Do not build with `GRADLE_USER_HOME` unset.

---

## 4. Session Environment

The repository includes a local-only environment script:

```text
scripts\android-env.ps1
```

Load it into the current PowerShell session:

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard
. .\scripts\android-env.ps1
```

The leading dot is required so the variables persist in the current shell.

The script sets:

```text
JAVA_HOME          = D:\Android\jdk-17
ANDROID_HOME       = D:\Android\Sdk
ANDROID_SDK_ROOT   = D:\Android\Sdk
ANDROID_USER_HOME  = D:\Android\.android
GRADLE_USER_HOME   = D:\Android\.gradle
```

It also prepends the JDK, command-line tools, platform-tools, build-tools 36.0.0, and Gradle to the current process PATH.

The script modifies only the current PowerShell process. It does not write user or system environment variables, install services, or change the registry.

Verify the environment:

```powershell
java -version
javac -version
gradle --version
adb version
aapt version
apksigner version
sdkmanager --list_installed
```

Expected highlights:

```text
java 17.0.20.1
adb 1.0.41 / platform-tools 37.0.1
Gradle 8.13
Android SDK Platform 36
Build Tools 36.0.0
```

---

## 5. Android Project

```text
mobile-authenticator/
├── settings.gradle.kts
├── build.gradle.kts
├── gradle.properties
├── gradle/wrapper/
│   ├── gradle-wrapper.jar
│   └── gradle-wrapper.properties
├── gradlew
├── gradlew.bat
├── local.properties          ignored; local SDK path only
└── app/
    ├── build.gradle.kts
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/com/ipguard/authenticator/
        └── res/
```

Application identity:

| Setting | Value |
|---|---|
| Application ID | `com.ipguard.authenticator` |
| Version | `0.1.0` (`versionCode 1`) |
| Minimum SDK | 28 |
| Target SDK | 36 |
| Compile SDK | 36 |
| Java bytecode target | 17 |
| UI | Kotlin + Jetpack Compose + Material 3 |

The Gradle Wrapper distribution URL is pinned to Gradle 8.13 and includes its SHA-256 checksum. Use the wrapper for all project builds.

`local.properties` contains a machine-specific SDK path and is ignored by Git. New clones can rely on `ANDROID_HOME` from the environment script or create their own ignored `local.properties`.

---

## 6. Build

```powershell
Set-Location C:\Users\user\Documents\02_Projects\IPGuard\mobile-authenticator
. ..\scripts\android-env.ps1

.\gradlew.bat --version
.\gradlew.bat :app:assembleDebug
.\gradlew.bat :app:lintDebug
```

Debug APK:

```text
mobile-authenticator\app\build\outputs\apk\debug\app-debug.apk
```

Lint report:

```text
mobile-authenticator\app\build\reports\lint-results-debug.html
```

The current build result is `BUILD SUCCESSFUL`. Lint has 0 errors and 4 informational warnings. The APK is a debug-signed artifact and is not suitable for release distribution.

---

## 7. Install and Launch

Confirm the physical device is connected:

```powershell
adb devices -l
adb get-state
```

Do not copy the device serial number into project documentation.

Install the existing debug APK and launch its main activity:

```powershell
$apk = 'app\build\outputs\apk\debug\app-debug.apk'
adb install -r $apk
adb shell am start -W -n com.ipguard.authenticator/.MainActivity
```

Verify the foreground activity and process:

```powershell
adb shell dumpsys window | Select-String 'mCurrentFocus|mFocusedApp'
adb shell pidof com.ipguard.authenticator
```

Capture a screenshot without writing a remote file to the repository:

```powershell
adb shell screencap -p /sdcard/ipguard-build-probe.png
adb pull /sdcard/ipguard-build-probe.png logs\ipguard-build-probe.png
adb shell rm /sdcard/ipguard-build-probe.png
```

`logs\` is ignored. M2.0 verification evidence is stored in the environment report.

---

## 8. M2.0 Acceptance

| Criterion | Result |
|---|---|
| Android toolchain installed | PASS |
| SDK licenses accepted | PASS |
| Gradle Wrapper available and pinned | PASS |
| Kotlin/Compose project builds | PASS |
| Debug APK generated | PASS |
| APK installed on physical device | PASS |
| App launched in foreground | PASS |
| UI content readable on device | PASS |
| No fatal runtime exception | PASS |
| Lint | PASS — 0 errors, 4 warnings |

Authentication, biometrics, camera, QR, Keystore, enrollment, and challenge-response are **not tested** because they are not part of M2.0.

---

## 9. Troubleshooting

### Java 22 is used instead of JDK 17

Load the environment script in the same PowerShell session and verify:

```powershell
. .\scripts\android-env.ps1
$env:JAVA_HOME
java -version
```

### Device is not listed

Check the USB cable and USB debugging authorization. Run `adb devices -l`. Do not share or commit the serial number.

### Gradle startup reports a loopback bind error

A transient `java.net.BindException: Address already in use: bind` was observed once at Gradle startup. Stop stale daemons and retry:

```powershell
.\gradlew.bat --stop
.\gradlew.bat --no-daemon :app:assembleDebug
```

Check for unrelated processes using the same development ports before killing anything.

### Maven Central DNS failure

The first dependency download encountered a transient `UnknownHostException` for `repo.maven.apache.org`. Retrying the build succeeded. If it repeats, check DNS/VPN/proxy configuration rather than changing dependency versions.

### APK signature mismatch

The debug APK uses the Android Debug certificate. If an incompatible debug installation exists, remove it only after confirming it contains no needed app data, then reinstall.

### C: free space is low

Do not unset `GRADLE_USER_HOME`. The environment script stores new Gradle caches on D:. Do not copy `build/`, `.gradle/`, `local.properties`, APKs, or Android user state into the repository.

---

## 10. Security Notes

- M2.0 contains no authentication logic and must not be presented as a working authenticator.
- The installed APK is debuggable and debug-signed.
- Cleartext HTTP is disabled in the main manifest.
- Backup and device-transfer extraction are disabled for application data.
- Camera and biometric permissions are declared for later M2 work but are not requested or exercised yet.
- `local.properties`, `.gradle/`, build outputs, APKs, keystores, and logs are ignored by Git.
- Android SDK licenses were accepted locally; no SDK component was added to a global PATH.

---

## 11. Next Gate

M2.0 is complete. M2.1 has since introduced the authenticator application structure, navigation, design system, and nine required screens, and has been verified on the physical device without claiming authentication, biometric, QR, or cryptographic capability.

M2.2 is the next permitted step. See [M2_TEST_REPORT.md](M2_TEST_REPORT.md) for current evidence and limitations.
