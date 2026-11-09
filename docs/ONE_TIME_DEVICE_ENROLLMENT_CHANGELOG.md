# One-Time Device Enrollment Changelog

- **Repository:** `Abhiprayaa29/IPGuard`
- **Branch:** `feature/m2-one-time-device-enrollment`
- **Base Branch:** `feature/m2.4d-android-integration`
- **Date:** 2026-11-08
- **Status:** COMMITTED — IMPLEMENTATION & DOCUMENTATION

---

## 1. Summary of Changes

This release hardens the IPGuard device authentication lifecycle to enforce the permanent security invariant:
> **A device is registered once. After successful registration, it can only sign in.**

### A. Backend Architecture (`backend/`)
- **Pessimistic Concurrency Locking:** `register_device` applies row-level locking (`with_for_update()`) on both `device_id` and public key fingerprint queries.
- **HTTP 409 Anti-Collision:** Re-enrollment attempts by an already enrolled (`ACTIVE`) or revoked (`REVOKED`) device/key are rejected with HTTP 409 `DEVICE_ALREADY_REGISTERED`.
- **Database Migration 0005:**
  - File: `backend/app/db/migrations/versions/0005_device_unregistered_status.py`
  - Added nullable `unregistered_at` timestamp column to `devices` table without data destruction.
  - Head state: Single head at `0005_device_unregistered_status`.
- **Lifecycle Endpoints:**
  - `GET /api/v1/auth/devices/{device_id}/status`: Returns device lifecycle status (`registration_status`, `access_status`, `public_key_fingerprint`).
  - `POST /api/v1/auth/devices/{device_id}/revoke`: Revokes access while keeping the registration slot locked.
  - `POST /api/v1/auth/devices/{device_id}/unregister`: Unregisters the device binding, invalidates in-flight sessions, and frees the registration slot.
- **M3 Secure Notes Preservation:** Unregistration and re-enrollment preserve the existing `Device` record and `device_id`, ensuring Milestone 3 Secure Notes (`Note.owner_id`) remain intact and accessible upon re-authentication.

### B. Android Native Authenticator (`mobile-authenticator/`)
- **Device Registration Manager (`DeviceRegistrationManager.kt`):**
  - Manages persistent registration state in SharedPreferences (`ipguard_device_registration`).
  - Tracks `DeviceRegistrationStatus` (`UNREGISTERED`, `ACTIVE`, `REVOKED`) and registered public key fingerprint.
- **Key Lifecycle Enforcement (`AuthenticatorViewModel.kt`):**
  - `QrSessionType.ENROLLMENT`: Checks `!registrationManager.isRegistered()`. If unenrolled, safely calls `ensureSigningKey(requireUserAuthentication = true)` and registers with backend.
  - `QrSessionType.AUTHENTICATION`: Requires pre-existing hardware signing key; fails closed if key is missing without generating an unauthorized key.
  - Key operations (`generateSigningKey`, `regenerateSigningKey`, `deleteSigningKey`) throw `SigningKeyPolicyViolationException` if the device is already registered.
  - On launch, invokes `syncRegistrationWithBackend()` to reconcile local state with the backend authority.
- **UI Flow Guards (`WelcomeScreen.kt` & `AppNavHost.kt`):**
  - Unregistered device displays **Set up this device**.
  - Registered device dynamically hides setup and displays **Sign In (Scan QR)**.
  - Accidental enrollment scans trigger an immediate user notice:
    > *"Device Already Registered. This device is already linked to IPGuard. Please use Sign In."*
  - Missing key state displays warning directing the user to unregister via the Web Console.

### C. Frontend Web Console (`frontend/`)
- **Device Management Page (`frontend/src/pages/devices/DeviceManagementPage.tsx`):**
  - Accessible via `/devices` and navigation menu in `AppShell.tsx`.
  - Metrics cards: Total Devices, Active Authenticators, Revoked Devices, Unregistered Slots.
  - Modals for **Revoke Access** and **Unregister Device** with explicit confirmation dialogues.
- **QR Auth Card Improvements (`frontend/src/components/auth/QrAuthCard.tsx`):**
  - Supports switching between `Mobile Sign-In` (`AUTHENTICATION`) and `Register Device` (`ENROLLMENT`).

---

## 2. Test Verification Summary

| Test Level | Scope | Result | Execution Time | Notes |
|---|---|---|---|---|
| **Backend Unit & Integration** | Pytest (102 tests) | **102 / 102 PASS** | 4.36s | Tests all lifecycle endpoints, M1/M2/M3 compatibility, 409 collisions, note preservation |
| **Android Unit Tests** | Gradle `testDebugUnitTest` (10 suites) | **59 / 59 PASS** | 0.45s | Covers `OneTimeDeviceEnrollmentTest`, key lifecycle, policies, QR parsing |
| **Frontend Production Build** | `tsc --noEmit && vite build` | **0 errors (PASS)** | 453ms | 2,195 modules transformed |
| **Database Migrations** | Alembic | **Current matches Head (0005)** | - | Clean single head at `0005_device_unregistered_status` |
| **Physical Hardware E2E** | Samsung Galaxy A54 5G (`SM-A546E`) | **PASS** | Physical run | First-time enrollment, hardware BiometricPrompt signing, duplicate enrollment rejection, M3 vault decryption |

---

## 3. Commit Structure

### Commit 1 — Feature Implementation
- **Hash:** `a8053d8`
- **Message:** `feat(m2): enforce one-time device enrollment and sign-in-only lifecycle`
- **Scope:**
  - Backend models, schemas, routes, services, migration 0005, and test suite.
  - Android `DeviceRegistrationManager`, `AuthenticatorViewModel`, `WelcomeScreen`, `AppNavHost`, strings, and unit tests.
  - Frontend `/devices` management page, service, types, router, and navigation link.

### Commit 2 — Documentation Update
- **Hash:** *(recorded upon commit)*
- **Message:** `docs: update one-time device enrollment documentation`
- **Scope:**
  - `README.md` (root): Added Device Enrollment & Authentication Lifecycle section, updated roadmap, tech stack, API endpoints.
  - `mobile-authenticator/README.md`: Brought up to date for v0.4.0, hardware signing, ADB reverse loopback, test instructions.
  - `docs/ONE_TIME_DEVICE_ENROLLMENT.md`: Synchronized architecture, states, and verification evidence.
  - `docs/ONE_TIME_DEVICE_ENROLLMENT_CHANGELOG.md`: Created release changelog.
