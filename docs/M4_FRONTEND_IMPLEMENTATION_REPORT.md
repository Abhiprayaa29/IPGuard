# IPGuard Milestone 4 — Frontend Implementation Report
**Document ID:** `docs/M4_FRONTEND_IMPLEMENTATION_REPORT.md`  
**Date:** November 10, 2026  
**Status:** COMPLETE & VERIFIED  
**Branch:** `feature/m4-steganography-backend`  

---

## 1. Executive Summary

Milestone 4 (M4) Image Steganography & Cryptographic Watermarking has been fully implemented into the IPGuard Web Console frontend within the existing Asset Vault architecture.

Rather than creating a disjointed secondary dashboard, M4 seamlessly enhances the existing hardware-authenticated Asset Vault workflow:
1. **Upload:** Users can upload original PNG master images via intuitive drag-and-drop with size validation and preview.
2. **Configure:** A clean modal automatically binds immutable cryptographic properties (Hardware device ID, Ed25519 signing context, IPGW v1 framing, SHA-256 digest) while allowing optional user-defined copyright, license, statement, and description metadata.
3. **Embed:** Watermark embedding is executed atomically on the backend, generating a separate, cryptographically bound derivative asset encrypted under per-device XChaCha20-Poly1305 AEAD, while preserving the master original unmodified.
4. **Download:** The watermarked PNG image can be downloaded directly from the Asset Vault byte-for-byte (`<name>.watermarked.png`).
5. **Verify:** A dedicated verification modal validates the Ed25519 digital signature, SHA-256 payload integrity, and database lineage.
6. **Extract:** Watermark payloads are extracted only upon successful server verification, presenting structured JSON metadata and raw text.

---

## 2. Architecture & Component Mapping

### 2.1 File Changes
| File Path | Role & Changes |
| :--- | :--- |
| `frontend/src/types/assets.ts` | Added `StegoEmbedRequest`, `StegoEmbedResponse`, `WatermarkVerifyResponse`, `WatermarkExtractResponse`, and `WatermarkPayloadData`. Updated `Asset` interface with `source_asset_id`, `derivative_type`, `watermark_id`, and `stego_format_version`. |
| `frontend/src/services/assets.ts` | Implemented `embedWatermark()`, `verifyWatermark()`, and `extractWatermark()` API client functions targeting `/api/v1/assets/{id}/steganography/*` with session bearer tokens. |
| `frontend/src/pages/assets/AssetVaultPage.tsx` | Integrated Steganography embed modal, watermark verification modal, payload extraction viewer, derivative badges, filter tabs, and contextual table actions. |

---

## 3. Step-by-Step User Workflow Implementation

### Step 1 — Upload Image
- **UI Location:** `Upload Asset` button & Drag-and-drop modal.
- **Constraints Enforced:** Supports PNG images (8-bit RGB/RGBA) up to 50 MB.
- **State Preservation:** Uploaded original PNG master is stored with full integrity, receiving an initial SHA-256 baseline and encrypted ciphertext.

### Step 2 — Configure Watermark
- **UI Location:** `Watermark` button on original PNG rows in Asset Vault.
- **Automatic Cryptographic Bindings (Read-Only):**
  - Algorithm: `Ed25519 (256-bit Hardware-backed)`
  - Framing: `IPGW Binary Framing v1`
  - Lineage: Bound to authenticated device context & source asset UUID
  - Digest: `SHA-256 Payload Hash`
- **User-Configurable Metadata:**
  - Copyright Notice (e.g. `© 2026 IPGuard Vault. All rights reserved.`)
  - License Terms (e.g. `Proprietary Commercial License v2`)
  - Custom Watermark Statement (e.g. `Confidential - Client Review Copy`)
  - Asset Description / Notes

### Step 3 — Embed Watermark
- **Trigger:** "Embed Watermark" button inside configuration modal.
- **Execution Flow:**
  1. Frontend bundles metadata into a UTF-8 JSON object and encodes it as Base64.
  2. Dispatches `POST /api/v1/assets/{id}/steganography/embed`.
  3. Server embeds `IPGW` binary frame into 1-bit LSB of row-major RGB channels.
  4. Generates an Ed25519 signature over `DOMAIN + PREFIX + PAYLOAD`.
  5. Computes SHA-256 payload digest.
  6. Creates a new derivative asset record in PostgreSQL (`derivative_type='PNG_LSB'`, `source_asset_id=original.id`).
  7. Encrypts the resulting derivative image using XChaCha20-Poly1305 and stores in Asset Vault.
  8. Records an append-only audit event `ASSET_STEGO_EMBEDDED`.
  9. Frontend dynamically inserts the newly generated derivative into the table with a confirmation banner.

### Step 4 — Download Watermarked Image
- **Seamless Streaming:** Invokes `GET /api/v1/assets/{derivative_id}/download`.
- **Decrypted Byte-for-Byte Delivery:** The backend decrypts the XChaCha20-Poly1305 ciphertext in memory and streams clean PNG bytes to the client.
- **Filename Convention:** Automatically saved with `Content-Disposition: attachment; filename="{stem}.watermarked.png"`.

### Step 5 — Verify Watermark
- **Trigger:** Shield icon button on any watermarked derivative row or inspect panel.
- **API Call:** `POST /api/v1/assets/{derivative_id}/steganography/verify`.
- **Validation Card:**
  - `VERIFIED`: Displays green check badge, Ed25519 signature status, matched Watermark UUID, and confirmed source asset lineage.
  - `TAMPERED / FAILED`: Displays alert badge with failure status (`SIGNATURE_INVALID`, `PAYLOAD_CORRUPT`, `NOT_STEGO_DERIVATIVE`).

### Step 6 — Extract Watermark
- **Trigger:** Code icon on derivative row or "Extract Verified Payload" button inside Verification modal.
- **API Call:** `POST /api/v1/assets/{derivative_id}/steganography/extract`.
- **Security Boundary:** The backend only returns the payload if cryptographic signature verification succeeds. Any tampered image returns HTTP 409 Conflict.
- **Viewer:** Renders structured metadata fields (Copyright, License, Custom text, Timestamp) alongside raw decoded JSON and a one-click clipboard copy button.

---

## 4. UI/UX Enhancements

1. **Vault Filters:** Added a dedicated `Watermarked (M4)` filter tab in addition to `All`, `Image`, `Doc`, and `Archive`.
2. **Derivative Badging:** Clear visual badge `PNG_LSB Derivative` with truncated source asset link (`from 84a1e9c2...`).
3. **Safety Protection:** Source assets with active derivatives cannot be deleted (preventing orphan derivatives; backend returns HTTP 409).
4. **Responsive Preview:** Inspect modal dynamically previews decrypted images with technical specifications (MIME, Dimensions, Cipher Version, SHA-256 baseline).

---

## 5. Security & Cryptographic Invariants Maintained

- **No Key Exposure:** Private Ed25519 signing keys are strictly maintained within the backend/hardware context and are never transmitted to the browser.
- **Clean Decryption:** Watermarked image downloads are streamed as authentic, decrypted PNG files suitable for external distribution.
- **Audit Hash Chain Integrity:** Every embed, verify, and extract action appends an immutable event to the device's cryptographic audit hash chain.
