# IPGuard M4 — Steganography Encoder, Decoder & Inspector Implementation Report

**Branch:** `feature/m4-steganography`  
**Base Commit:** `cd062b4` (`main` after M0–M4 merge)  
**Target Milestone:** M4 — Integrity & Advanced Protection (Workstream 3: Steganographic Watermarking)

---

## 1. Summary of Implemented Artifacts

### Backend
- [`backend/app/services/stego_payload.py`](../backend/app/services/stego_payload.py): Canonical `IPGUARD_WATERMARK` v1 JSON serialization, deterministic opaque `owner_reference` derivation, control-character sanitization, and backward-compatible metadata parser.
- [`backend/app/services/png_steganography.py`](../backend/app/services/png_steganography.py): Added `calculate_png_capacity`, `inspect_png_bytes`, `PngCapacityInfo`, and `WatermarkInspectionResult` supporting read-only full inspection across all 6 status categories without breaking existing embedding/verification contracts.
- [`backend/app/services/stego_lab.py`](../backend/app/services/stego_lab.py): Orchestration layer bridging M3 Asset Vault encryption (`XChaCha20-Poly1305`), M2 device ownership checks, canonical encoding (`encode_canonical_asset_watermark`), Vault PNG inspection (`inspect_vault_asset_png`), and zero-persistence external PNG inspection (`inspect_external_png`).
- [`backend/app/schemas/steganography.py`](../backend/app/schemas/steganography.py): Strict Pydantic schemas (`StegoEncodeRequest`, `StegoEncodeResponse`, `StegoCapacityResponse`, `WatermarkInspectResponse`, `AssetInspectRequest`).
- [`backend/app/api/routes/steganography.py`](../backend/app/api/routes/steganography.py) & [`backend/app/api/routes/assets.py`](../backend/app/api/routes/assets.py): Mounted `/api/v1/steganography/*` endpoints alongside `/api/v1/assets/{asset_id}/watermark*` aliases, all guarded by `get_current_authenticated_device`.

### Frontend (`/steganography` — IPGuard Steganography Lab)
- [`frontend/src/types/steganography.ts`](../frontend/src/types/steganography.ts): Complete TypeScript contracts matching the backend Inspector & Encoder schemas.
- [`frontend/src/services/steganography.ts`](../frontend/src/services/steganography.ts): Typed API service with M2 Bearer authentication headers.
- [`frontend/src/pages/steganography/SteganographyLabPage.tsx`](../frontend/src/pages/steganography/SteganographyLabPage.tsx): Dual-mode workspace featuring:
  - **Encode Watermark Mode:** Vault PNG picker, in-memory decrypted preview, RGB LSB capacity meter, canonical payload attribution inputs, privacy notice, derived encrypted asset creation, direct PNG download, and immediate handoff to Inspector.
  - **Decode / Inspect Watermark Mode:** Supports both **External PNG Upload** (drag-and-drop/file picker, inspection-only) and **Asset Vault PNG** selection (read-only decrypted inspection), optional source SHA-256 digest matching, color-coded 6-status banner, separated Watermark Information / Cryptographic Verification / Integrity Status cards, and strict withholding of untrusted metadata.
- [`frontend/src/app/router.tsx`](../frontend/src/app/router.tsx) & [`frontend/src/components/layout/AppShell.tsx`](../frontend/src/components/layout/AppShell.tsx): Registered `/steganography` route and `Stego Lab` top navigation tab.

---

## 2. API Endpoints

| Method | Endpoint | Auth | Persistence | Purpose |
|---|---|---|---|---|
| `GET` | `/api/v1/steganography/assets/{asset_id}/capacity` | M2 Bearer | Read-only | Decrypt PNG in-memory & compute RGB LSB capacity |
| `POST` | `/api/v1/steganography/assets/{asset_id}/encode` | M2 Bearer | Derived Asset (`XChaCha20-Poly1305`) | Embed signed canonical watermark into new encrypted asset |
| `POST` | `/api/v1/assets/{asset_id}/watermark` | M2 Bearer | Derived Asset (`XChaCha20-Poly1305`) | Alias for canonical watermark encoding |
| `POST` | `/api/v1/steganography/inspect` | M2 Bearer | **Zero Persistence** | Read-only inspection of external uploaded PNG |
| `POST` | `/api/v1/steganography/assets/{asset_id}/inspect` | M2 Bearer | Read-only | Inspect existing Vault PNG (source or derivative) |
| `POST` | `/api/v1/assets/{asset_id}/watermark/inspect` | M2 Bearer | Read-only | Alias for Vault PNG watermark inspection |

---

## 3. Security Review Findings & Mitigations

1. **Concurrent Integrity Check Race (Fixed):** During Playwright E2E testing, calling `downloadAsset` for UI image preview concurrently with `inspectVaultAssetPng` / `getAssetStegoCapacity` triggered a race in `asset_integrity.py` (`last_checked_at` timestamp overwrite returning HTTP 503). Mitigated by serializing UI capacity/inspect requests ahead of preview blob downloads in `SteganographyLabPage.tsx`.
2. **Untrusted Partial Data Suppression:** Whenever `status != "VALID"` (`INVALID_SIGNATURE`, `CORRUPTED`, `UNKNOWN_SIGNER`, `UNSUPPORTED_VERSION`, `NO_WATERMARK`), extracted payload fields are strictly omitted (`None`) on both backend and UI so forged metadata is never displayed as trusted.
3. **Zero Plaintext Persistence:** Derived watermarked PNGs are encoded in-memory, encrypted immediately using M3 `XChaCha20-Poly1305` with a fresh 24-byte nonce and derived asset AAD (`v1|device_id|derivative_id`), and stored atomically. External Inspector uploads are read from `UploadFile` in-memory capped at 50 MiB and discarded immediately after inspection.
4. **Input & XSS Safety:** PNG headers and IHDR dimensions are checked before full decoding (`DecompressionBombWarning` promoted to error). Text attribution metadata strips control characters and renders exclusively via safe React JSX escaping.
5. **Known Limitations:**
   - LSB steganography in RGB channels is sensitive to lossy JPEG compression, resizing, cropping, palette quantization, and pixel editing.
   - Only 8-bit `RGB` and `RGBA` PNGs are supported.
   - Payload size is bounded by host image dimensions (`floor(W * H * 3 / 8) - 170` bytes) and `stego_max_payload_bytes` (4 MiB).
