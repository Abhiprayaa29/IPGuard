"""
IPGuard Milestone 3 — Asset Vault Cryptography Service.
Provides true XChaCha20-Poly1305 AEAD authenticated encryption using PyNaCl/libsodium:
1. Cipher: XChaCha20-Poly1305 (IETF variant)
2. Nonce: 24 bytes (192 bits) generated via CSPRNG (secrets.token_bytes)
3. Key: 32 bytes (256 bits)
4. Authentication Tag: 16 bytes (128 bits) appended to ciphertext
5. Key Derivation: HKDF-SHA256 (RFC 5869) per-device domain separation
6. Associated Data (AAD): Deterministic binding of (version, device_id, asset_id)
"""

import base64
import secrets
from uuid import UUID

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from nacl.bindings import (
    crypto_aead_xchacha20poly1305_ietf_decrypt,
    crypto_aead_xchacha20poly1305_ietf_encrypt,
)
from nacl.exceptions import CryptoError

from app.core.config import get_settings

KEY_SIZE = 32
NONCE_SIZE = 24
TAG_SIZE = 16
DOMAIN_SEPARATION_V1 = b"ipguard-asset-vault-v1-xchacha20poly1305"
ENCRYPTION_VERSION_V1 = "v1"
ENCRYPTION_VERSION_LEGACY = "v0"


class AssetDecryptionError(ValueError):
    """Raised when ciphertext authentication or decryption fails."""
    pass


def derive_asset_key(device_id: str, master_key: bytes | None = None) -> bytes:
    """
    Derive a 256-bit (32-byte) encryption key specific to the device_id using HKDF-SHA256.
    Ensures cryptographic domain separation so ciphertexts from one device cannot
    be decrypted or tampered with by another device, even under the same master key.
    """
    if not device_id or not isinstance(device_id, str):
        raise ValueError("device_id must be a non-empty string.")

    if master_key is None:
        master_key = get_settings().asset_vault_master_key_bytes

    if len(master_key) != KEY_SIZE:
        raise ValueError(f"Master key must be exactly {KEY_SIZE} bytes.")

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=device_id.encode("utf-8"),
        info=DOMAIN_SEPARATION_V1,
    )
    return hkdf.derive(master_key)


def build_asset_aad(
    asset_id: str | UUID,
    device_id: str,
    version: str = ENCRYPTION_VERSION_V1,
) -> bytes:
    """
    Build deterministic Associated Authenticated Data (AAD) for XChaCha20-Poly1305.
    Cryptographically binds the ciphertext to the asset ID, owning device, and format version.
    """
    return f"{version}|{device_id}|{str(asset_id)}".encode("utf-8")


def encrypt_asset_bytes(
    data: bytes,
    key: bytes,
    aad: bytes | None = None,
) -> tuple[bytes, str]:
    """
    Encrypt file data using XChaCha20-Poly1305 with CSPRNG 24-byte nonce.
    Returns (ciphertext_with_poly1305_tag, nonce_base64).
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Encryption key must be exactly {KEY_SIZE} bytes.")

    nonce = secrets.token_bytes(NONCE_SIZE)

    ciphertext = crypto_aead_xchacha20poly1305_ietf_encrypt(
        data,
        aad,
        nonce,
        key,
    )

    nonce_b64 = base64.b64encode(nonce).decode("utf-8")
    return ciphertext, nonce_b64


def decrypt_asset_bytes(
    ciphertext: bytes,
    nonce_b64: str,
    key: bytes,
    aad: bytes | None = None,
) -> bytes:
    """
    Decrypt file data and verify Poly1305 authentication tag.
    Raises AssetDecryptionError if key, nonce, AAD, or ciphertext is corrupted/invalid.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Encryption key must be exactly {KEY_SIZE} bytes.")

    try:
        nonce = base64.b64decode(nonce_b64, validate=True)
    except Exception as exc:
        raise AssetDecryptionError("Invalid Base64 nonce format.") from exc

    if len(nonce) != NONCE_SIZE:
        raise AssetDecryptionError(
            f"Invalid nonce length: expected {NONCE_SIZE} bytes, got {len(nonce)}."
        )

    try:
        return crypto_aead_xchacha20poly1305_ietf_decrypt(
            ciphertext,
            aad,
            nonce,
            key,
        )
    except CryptoError as exc:
        raise AssetDecryptionError(
            "Asset decryption failed: Poly1305 authentication tag mismatch or corrupted ciphertext."
        ) from exc
