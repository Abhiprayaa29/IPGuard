# IPGuard M4 — Steganography Encoder, Decoder & Inspector Architecture

**Status:** Implemented & Verified  
**Milestone:** M4 — Integrity & Advanced Protection (Workstream 3: Steganographic Watermarking)  
**Target Subsystem:** Backend FastAPI + React 19 Steganography Lab + Asset Vault M3 Integration

---

## 1. Architecture Overview

The IPGuard Steganographic Watermarking system extends Milestone 3 Asset Vault (`XChaCha20-Poly1305` encrypted file storage) and Milestone 2 Hardware Device Authentication (`ECDSA P-256` Android Keystore sessions) with signed PNG Least Significant Bit (LSB) embedding and a standalone read-only Watermark Inspector.

```text
+-------------------------------------------------------------------------+
|               IPGuard Steganography Lab (/steganography)                |
+-------------------------------------------------------------------------+
        |                                                  |
        | Mode 1: Encode Watermark                         | Mode 2: Inspect (Read-Only)
        v                                                  v
[POST /api/v1/steganography/assets/{id}/encode]   [POST /api/v1/steganography/inspect]
[POST /api/v1/assets/{id}/watermark]              [POST /api/v1/assets/{id}/watermark/inspect]
        |                                                  |
        | (Authenticated M2 Device Context)                | (Authenticated M2 Device Context)
        v                                                  v
+--------------------------------------+     +--------------------------------------+
| 1. Asset Vault Decryption (M3)       |     | External PNG Buffer (No Persistence) |
|    - Verify ownership                |     | OR Vault PNG Decryption (Read-Only)  |
|    - Verify SHA-256 & AEAD tag       |     +--------------------------------------+
| 2. PNG Validation & Capacity Check   |                       |
|    - 8-bit RGB/RGBA, decompression   |                       v
|      bomb & pixel bounds check       |     +--------------------------------------+
| 3. Canonical Payload + Ed25519 Sign  |     | LSB Frame Extraction & Verification  |
| 4. Deterministic RGB LSB Embedding   |     | - Magic Marker (IPGW) & Version Check|
| 5. Derived Asset XChaCha20-Poly1305  |     | - SHA-256 Checksum & Key Lookup      |
|    Encryption & Atomic Disk Write    |     | - Ed25519 Signature Verification     |
+--------------------------------------+     +--------------------------------------+
```

---

## 2. LSB Embedding Method & Packet Framing

### Carrier Constraints & Channel Layout
- **Supported Formats:** Valid 8-bit truecolor PNG (`RGB`, color type 2) or truecolor with alpha (`RGBA`, color type 6).
- **Safety Limits:** Maximum 50 MiB file size, 10,000 px max width/height, 20,000,000 total pixels, and PIL `DecompressionBombWarning` promoted to strict failure.
- **Bit Layout:** Row-major pixel scan, RGB channels only (`R -> G -> B`), MSB-first (bit 7 down to bit 0).
- **Alpha Channel Preservation:** For `RGBA` PNGs, the Alpha (`A`) byte is skipped by `_rgb_component_offset` and preserved byte-for-byte.
- **Capacity Calculation:**
  $$\text{Total Capacity (bytes)} = \left\lfloor \frac{\text{width} \times \text{height} \times 3}{8} \right\rfloor$$
  $$\text{Usable Payload Capacity (bytes)} = \max(0, \text{Total Capacity} - 170)$$

### Packet Format (`IPGW` v1)
Fixed 170-byte big-endian header followed by variable canonical payload:

| Offset | Field | Size | Purpose |
|---:|---|---:|---|
| 0 | Magic Marker (`IPGW`) | 4 B | Fast detection of IPGuard frames (`NO_WATERMARK` if absent) |
| 4 | Version (`1`) | 1 B | Packet format version (`UNSUPPORTED_VERSION` if $\neq 1$) |
| 5 | Flags (`0`) | 1 B | Reserved flags (`CORRUPTED` if $\neq 0$) |
| 6 | Watermark UUID | 16 B | Unique operation/watermark identifier |
| 22 | Source Asset UUID | 16 B | Parent plaintext asset reference |
| 38 | Derivative Asset UUID | 16 B | Derived asset primary key |
| 54 | Payload Length | 4 B | Unsigned 32-bit big-endian length (`>I`) |
| 58 | Payload Checksum | 32 B | `SHA-256(payload)` for structural corruption detection |
| 90 | Signing Key ID | 16 B | First 16 bytes of `SHA-256(raw_ed25519_public_key)` |
| 106 | Digital Signature | 64 B | Ed25519 signature over `STEGO_DOMAIN + prefix[0:106] + payload` |
| 170 | Canonical Payload | $N$ B | UTF-8 deterministically serialized JSON (`sort_keys=True`) |

---

## 3. Canonical Watermark Payload Design (`IPGUARD_WATERMARK` v1)

Built by `app/services/stego_payload.py` using sorted-key, zero-whitespace JSON serialization:

```json
{
  "asset_reference": "5d65f4fb-dfa6-411d-956d-8c43c7ce2735",
  "created_at": "2026-11-10T13:59:42Z",
  "format": "IPGUARD_WATERMARK",
  "metadata": {
    "copyright": "© 2026 IPGuard M4 Lab",
    "license": "Proprietary",
    "note": "Browser E2E Canonical Watermark"
  },
  "owner_reference": "owner-38a851c30c475dfbd7e1",
  "signature_algorithm": "Ed25519",
  "signing_key_id": "56475aa75463474c0285df5dbf2bcab7",
  "source_sha256": "746cf64791948fddfb7e12a26355c54de24310c77f6fa8316db48c05f3f75497",
  "version": 1,
  "watermark_id": "9bbf3351-5b97-453b-bd27-527ddb922437"
}
```

### Privacy & Security Properties
- **Opaque Owner Reference:** Derived deterministically via `owner-{SHA-256("IPGUARD-OWNER-REF-V1|" + device_id)[:20]}`. Raw device hardware IDs, PII, passwords, master encryption keys, and session tokens are never embedded.
- **Hidden $\neq$ Encrypted:** LSB pixels can be read by any decoder aware of the `IPGW` layout. Asset confidentiality at rest is strictly enforced by Asset Vault's `XChaCha20-Poly1305` encryption, NOT by LSB steganography.

---

## 4. Digital Signature & Trust Boundaries

- **Algorithm:** Ed25519 (`cryptography.hazmat.primitives.asymmetric.ed25519`).
- **Key Separation:** Steganography signing keys (`STEGO_SIGNING_PRIVATE_KEY_B64`, `STEGO_ACTIVE_KEY_ID`, `STEGO_PUBLIC_KEYS_JSON`) are completely independent of Milestone 2 Android Keystore ECDSA P-256 authentication keys and Milestone 3 XChaCha20-Poly1305 storage keys.
- **Trust Boundary:** The Ed25519 signature proves that the watermark payload was issued by the trusted IPGuard server-side signing service holding `STEGO_ACTIVE_KEY_ID`. It does not constitute standalone user-authorship non-repudiation or prove that non-LSB image pixels remained completely untouched unless `source_sha256` is verified against a trusted original image digest.
- **Offline Verification & Key Rotation:** `STEGO_PUBLIC_KEYS_JSON` supports retaining historical public keys indexed by `key_id` so previously watermarked PNGs verify as `VALID` even after rotating the active private signing key or running an inspection-only node without a private seed.

---

## 5. Inspector Status Classification

The Inspector explicitly classifies every outcome without conflating signer trust or corruption states, and **withholds unverified metadata whenever `status != "VALID"`**:

| Status | Framing / Magic | Checksum | Key Lookup | Signature | Meaning |
|---|---|---|---|---|---|
| `VALID` | Valid (`IPGW` v1) | Valid | Trusted | Valid | Authentic, verified IPGuard watermark |
| `INVALID_SIGNATURE` | Valid | Valid | Trusted | Invalid | Ed25519 signature failed (forged/tampered) |
| `CORRUPTED` | Marker present | Failed / Truncated | N/A | Invalid | Damaged pixels, altered payload, or truncated file |
| `UNKNOWN_SIGNER` | Valid | Valid | Not found | Invalid | Valid structure signed by untrusted/unknown key ID |
| `UNSUPPORTED_VERSION` | `IPGW` v $\neq 1$ | N/A | N/A | Invalid | Frame version not supported by decoder |
| `NO_WATERMARK` | Absent | N/A | N/A | Invalid | Clean PNG without IPGuard LSB marker |
