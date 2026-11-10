# PNG LSB Steganography

## Supported input and limits

The decoder accepts only valid PNG files whose IHDR declares 8-bit truecolor
RGB (color type 2) or truecolor with alpha RGBA (color type 6). IHDR limits are
checked before pixel decoding. Defaults cap encoded size at 50 MiB, dimensions
at 10,000 pixels per axis, total size at 20 million pixels, and payload size at
4 MiB. The frame must also fit the actual carrier capacity.

Embedding writes one bit into each R, G, and B channel in row-major pixel order,
with channels RGB and bits MSB-first. The alpha channel is never modified.
Re-encoding can change ancillary PNG metadata. Resizing, palette conversion,
lossy conversion, and recompression may destroy the watermark.

## Version 1 frame

The fixed header is 170 bytes and uses big-endian integer lengths:

| Offset | Field | Bytes |
|---:|---|---:|
| 0 | Magic `IPGW` | 4 |
| 4 | Version (`1`) | 1 |
| 5 | Flags (`0`) | 1 |
| 6 | Watermark UUID bytes | 16 |
| 22 | Source asset UUID bytes | 16 |
| 38 | Derivative asset UUID bytes | 16 |
| 54 | Payload length | 4 |
| 58 | SHA-256(payload) | 32 |
| 90 | Signing key ID | 16 |
| 106 | Ed25519 signature | 64 |
| 170 | Payload | Declared payload length |

The signature message is the ASCII domain `IPGUARD-PNG-LSB-WATERMARK-V1` plus a
NUL byte, followed by bytes
0 through 105 and the payload. It covers the magic, version, flags, all UUIDs,
length, checksum, and key ID. The signature field itself is excluded. Extraction
does not return payload until checksum, identity bindings, key lookup, and
signature verification all succeed.

## Key configuration and rotation

Provide these settings through deployment secrets/configuration, not source
control:

- `STEGO_SIGNING_PRIVATE_KEY_B64`: Base64 of a raw 32-byte Ed25519 seed.
- `STEGO_ACTIVE_KEY_ID`: lowercase hex of the first 16 bytes of
  `SHA-256(raw_public_key)`.
- `STEGO_PUBLIC_KEYS_JSON`: JSON object mapping every retained key ID to the
  Base64 encoding of its raw 32-byte public key.

At startup/operation, every public key ID is checked against its key bytes. The
active private seed must derive the configured active public key. Embed fails
closed if any required active-key value is missing or inconsistent. Verification
uses only the matching public key and therefore can continue when the active
private key is offline.

For rotation, provision a new seed and public key, add the new public key to the
map, then switch the active private seed and key ID together. Keep previous
public keys for as long as stored derivatives may need verification. Private
keys must be backed up and stored in a secret manager or equivalent protected
deployment system. This signing key is independent of M2 and Asset Vault M3
keys; no fallback is supported.

## Persistence, ownership, and audit

Each derivative receives its UUID before the frame is signed. The same UUID is
used as the Asset primary key. Derivative lineage is stored in nullable
`source_asset_id`, `derivative_type`, `watermark_id`, and
`stego_format_version` columns added by migration `0009_png_lsb_derivatives`.
Source and derivative must belong to the same device. A source asset with
derivatives cannot be deleted until those derivatives are removed.

The derivative row and `ASSET_STEGO_EMBEDDED` audit event share one database
transaction. Ciphertext storage remains a filesystem operation: it is written
atomically before the metadata commit and cleaned up after definite pre-commit
failure. An uncertain database commit leaves the file for reconciliation; the
asset row and audit event themselves still commit or roll back together.

Audit events contain operation result and opaque asset/watermark IDs only. They
never include watermark payload, signature, signing key, plaintext, ciphertext,
or storage path. Verification failures are recorded where the asset is
available and the audit store accepts the event.

## API

- `POST /api/v1/assets/{asset_id}/steganography/embed`
- `POST /api/v1/assets/{asset_id}/steganography/verify`
- `POST /api/v1/assets/{asset_id}/steganography/extract`

All endpoints use the existing authenticated-device dependency and enforce
asset ownership. Extract returns Base64 payload only after full verification
and successful audit recording.
