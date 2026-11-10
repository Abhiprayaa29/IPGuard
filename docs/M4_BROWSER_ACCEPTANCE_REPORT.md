# IPGuard Milestone 4 — Real Browser Acceptance Testing Report
**Document ID:** `docs/M4_BROWSER_ACCEPTANCE_REPORT.md`  
**Date:** November 10, 2026  
**Status:** ALL ACCEPTANCE CRITERIA PASSED (100%)  
**Testing Harness:** Playwright Chromium (1366x860) / React 19.3 / FastAPI / PostgreSQL 17.11  

---

## 1. Executive Summary

A comprehensive, real-browser end-to-end acceptance test was executed against the live IPGuard Web Console (`http://127.0.0.1:5173`) and FastAPI backend (`http://127.0.0.1:8000`).

The automated test exercised the entire user journey:
1. Authentic session binding in PostgreSQL for hardware device `origin-bound-device-01`.
2. Browser navigation to the hardware-locked Asset Vault.
3. Master PNG image upload (`master_artwork_256.png`).
4. Custom watermark configuration and Ed25519 hardware signing.
5. In-browser file download of the decrypted watermarked derivative PNG.
6. Independent mathematical and cryptographic analysis of the downloaded binary.
7. Verification and payload extraction modals in the live UI.
8. Active tamper detection on pixel-mutated images.

All 17 acceptance scenario requirements passed with **zero console errors** and **zero failed network requests**.

---

## 2. Test Execution Details

- **Test Script:** [`scripts/m4_browser_acceptance_test.py`](../scripts/m4_browser_acceptance_test.py)
- **Target Browser:** Headless Chromium (1366x860, 24-bit sRGB)
- **Session Token:** Hardware-bound session with `APPROVED` state in PostgreSQL
- **Execution Timestamp:** 2026-11-10T06:55:35Z
- **Duration:** 14.8 seconds
- **Health Metrics:**
  - Page Errors: **0**
  - Failed Requests: **0**
  - Console Messages: 9 (standard Vite client connection & asset status logs)

---

## 3. Step-by-Step Browser Journey & Evidence

### Step 1 — Initial Asset Vault View
- **Action:** Injected hardware-bound session token into `sessionStorage` and navigated to `/assets`.
- **Validation:** Vault unlocked immediately, displaying the `Hardware-Bound Active` status pill and Milestone 4 title: *"Asset Vault & Steganography"*.
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/01_asset_vault_initial.png`](screenshots/m4_acceptance/01_asset_vault_initial.png)

### Step 2 — Upload Master PNG
- **Action:** Clicked `Upload Asset`, selected `master_artwork_256.png` (256x256 truecolor RGB PNG), and submitted `Encrypt & Save`.
- **Validation:** File encrypted via per-device XChaCha20-Poly1305 and recorded in PostgreSQL. Table refreshed immediately showing `master_artwork_256.png` with badge `Original Asset`.
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/02_asset_uploaded.png`](screenshots/m4_acceptance/02_asset_uploaded.png)
-
### Step 3 — Watermark Configuration Modal
- **Action:** Clicked `Watermark` button on the original asset row.
- **Validation:** Modal displayed source image metadata (filename, size), automatic cryptographic parameters (`Ed25519 (Hardware)`, `SHA-256 Digest`), and custom input fields.
- **Inputs Configured:**
  - **Copyright Notice:** `© 2026 IPGuard Vault Acceptance Test. All rights reserved.`
  - **License:** `Enterprise Proprietary License (M4 Verified)`
  - **Custom Statement:** `Confidential - Authorized Production Review Build`
  - **Description:** `Master derivative with hardware-bound Ed25519 digital watermark.`
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/03_watermark_config_modal.png`](screenshots/m4_acceptance/03_watermark_config_modal.png)

### Step 4 — Embed Watermark Execution
- **Action:** Clicked `Embed Watermark`.
- **Validation:** Button entered loading state (`Embedding & Signing...`). Backend embedded `IPGW` binary frame into row-major RGB LSBs, signed with Ed25519, created derivative record `master_artwork_256.watermarked.png`, encrypted under XChaCha20-Poly1305, and appended an audit event to the hash chain.
- **Result:** Success banner displayed Derivative Filename, Derivative Asset ID, Watermark UUID (`380fd58b-7fb2-4ab6-8ea2-40c06c8b31f3`), and `IPGW Version 1`.
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/04_embed_success.png`](screenshots/m4_acceptance/04_embed_success.png)

### Step 5 — In-Browser File Download
- **Action:** Intercepted Playwright download stream triggered by `Download Watermarked Image`.
- **Suggested Filename:** `master_artwork_256.watermarked.png`.
- **Saved Path:** `docs/screenshots/m4_acceptance/master_artwork_256.watermarked.png`.
- **Download Behavior:** Direct browser stream, completely decrypted in memory, zero ciphertext leakage.

### Step 6 — Table Inspection with Derivative Asset
- **Action:** Navigated to Asset Vault table.
- **Validation:** Table showed both original master and derivative asset. Derivative row displayed the `PNG_LSB Derivative` badge with parent lineage link (`from 5dfe779a...`).
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/05_vault_with_derivative.png`](screenshots/m4_acceptance/05_vault_with_derivative.png)

### Step 7 — Live Watermark Verification Modal
- **Action:** Clicked `Verify Watermark` shield icon on the derivative row.
- **Validation:** Triggered `POST /api/v1/assets/{id}/steganography/verify`. Modal rendered `Watermark Verified & Authentic` with green checkmark, confirming Ed25519 signature validity, SHA-256 integrity, Watermark UUID, and Source Asset ID.
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/06_verify_success_modal.png`](screenshots/m4_acceptance/06_verify_success_modal.png)

### Step 8 — Watermark Payload Extraction Modal
- **Action:** Clicked `Extract Verified Payload` from within the verification modal.
- **Validation:** Triggered `POST /api/v1/assets/{id}/steganography/extract`. Modal rendered structured metadata cards:
  - Copyright: `© 2026 IPGuard Vault Acceptance Test. All rights reserved.`
  - License: `Enterprise Proprietary License (M4 Verified)`
  - Custom Statement: `Confidential - Authorized Production Review Build`
  - Description: `Master derivative with hardware-bound Ed25519 digital watermark.`
- **Action Test:** Clicked `Copy` button; UI displayed `Copied` confirmation.
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/07_extract_payload_modal.png`](screenshots/m4_acceptance/07_extract_payload_modal.png)

### Step 9 — Inspect Modal Details
- **Action:** Clicked `Inspect Metadata & Preview` (Eye icon) on derivative row.
- **Validation:** Displayed decrypted image preview, MIME type `image/png`, size (3,498 bytes), Cipher Suite `XChaCha20-Poly1305`, Source Asset ID, Watermark UUID, and SHA-256 baseline hash.
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/08_derivative_inspect_modal.png`](screenshots/m4_acceptance/08_derivative_inspect_modal.png)

### Step 10 — Watermarked Filter Tab
- **Action:** Clicked `Watermarked (M4)` filter tab.
- **Validation:** Table immediately filtered to show exclusively the `PNG_LSB Derivative` assets, isolating derivative work.
- **Screenshot Evidence:** [`docs/screenshots/m4_acceptance/09_watermarked_filter_tab.png`](screenshots/m4_acceptance/09_watermarked_filter_tab.png)

---

## 4. Independent Binary & Cryptographic Validation

The downloaded file `master_artwork_256.watermarked.png` was evaluated outside the browser using low-level binary tools and Pillow:

| Metric / Check | Value / Result | Acceptance Criterion | Status |
| :--- | :--- | :--- | :--- |
| **Magic Header Bytes** | `89 50 4E 47 0D 0A 1A 0A` | Not ciphertext; valid PNG signature | **PASS** |
| **Pillow Decodability** | Format: PNG, Mode: RGB | Valid truecolor decodable raster | **PASS** |
| **Dimensions** | 256 x 256 pixels | Exact match to source image | **PASS** |
| **Visual Distortion (MSE)** | `0.009471` | Mean squared error $< 0.1$ | **PASS** |
| **Visual Fidelity (PSNR)** | **68.37 dB** | Peak Signal-to-Noise Ratio $> 45$ dB | **PASS (Imperceptible)** |
| **LSB Magic Header** | `IPGW` (ASCII) | Valid binary framing | **PASS** |
| **Framing Version** | `1` | Matches specification | **PASS** |
| **Ed25519 Signature** | Validated via `ed25519.verify()` | Cryptographically authentic | **PASS** |
| **SHA-256 Payload Digest** | Matched | Zero bit drift in payload | **PASS** |
| **Extracted Payload Equality**| Exact 100% string match | Metadata intact | **PASS** |

---

## 5. Tamper Resistance Validation

1. **Pixel Bit-Flip Experiment:**
   - Modified 1 bit (red channel LSB) at pixel `(0, 0)` of `master_artwork_256.watermarked.png`.
   - Saved as `tampered_artwork.png`.
   - Executed `verify_png_watermark()` on the altered image.
   - **Result:** Verification rejected with `WATERMARK_NOT_FOUND` (magic bytes mismatch).
2. **Extraction Protection:**
   - Calling `/steganography/extract` on an unverified asset returns **HTTP 409 Conflict** (`watermark_verification_failed`). Payloads are strictly never released without a valid signature.

---

## 6. Acceptance Verification Summary

```json
{
  "status": "PASS",
  "browser": "Chromium 1366x860",
  "visual_psnr_db": 68.37,
  "magic_bytes_valid": true,
  "signature_valid": true,
  "sha256_digest_valid": true,
  "metadata_exact_match": true,
  "tamper_detected": true,
  "page_errors": 0,
  "failed_requests": 0
}
```
All Milestone 4 real-browser acceptance criteria are completely fulfilled.
