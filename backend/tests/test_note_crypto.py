"""
Comprehensive unit tests for IPGuard Milestone 3 Cryptography Service.
Tests AES-256-GCM AEAD, HKDF domain separation, Vigenère shift, and envelope versioning.
"""

import base64
import os
import pytest
from cryptography.exceptions import InvalidTag

from app.core.config import Settings
from app.services.note_crypto import (
    _derive_vigenere_keyword,
    _vigenere_shift,
    decrypt_note,
    derive_user_key,
    encrypt_note,
)


def test_vigenere_shift_basic():
    """Verify standard alphabetic Vigenère shift and un-shift."""
    text = "AttackAtDawn"
    keyword = "secret"
    shifted = _vigenere_shift(text, keyword, decrypt=False)
    assert shifted != text
    assert len(shifted) == len(text)
    decrypted = _vigenere_shift(shifted, keyword, decrypt=True)
    assert decrypted == text


def test_vigenere_preserves_non_alpha():
    """Verify spaces, digits, symbols, newlines, and Unicode are preserved unchanged."""
    text = "Secret-Token #1234: 🚀 Rp 50.000,00\nNext line!"
    keyword = "keymaster"
    shifted = _vigenere_shift(text, keyword, decrypt=False)
    assert "1234" in shifted
    assert "50.000,00" in shifted
    assert "🚀" in shifted
    assert "\n" in shifted
    decrypted = _vigenere_shift(shifted, keyword, decrypt=True)
    assert decrypted == text


def test_hkdf_domain_separation_different_owners():
    """
    Verify that identical master keys produce cryptographically distinct
    AES keys for different owner_ids, preventing cross-tenant decryption.
    """
    master_key = b"A" * 32
    key_owner_1 = derive_user_key("device-alpha", master_key=master_key)
    key_owner_2 = derive_user_key("device-beta", master_key=master_key)

    assert len(key_owner_1) == 32
    assert len(key_owner_2) == 32
    assert key_owner_1 != key_owner_2

    # Determinism: same master key and owner produces identical key
    key_owner_1_repeat = derive_user_key("device-alpha", master_key=master_key)
    assert key_owner_1 == key_owner_1_repeat


def test_encrypt_decrypt_roundtrip_v1():
    """Verify end-to-end super-encryption and decryption with v1$ envelope."""
    plaintext = "Confidential Digital Asset Portfolio Details"
    owner = "samsung-sm-a546e-authenticator"

    ciphertext = encrypt_note(plaintext, owner_id=owner)
    assert ciphertext.startswith("v1$")
    assert plaintext not in ciphertext

    decrypted = decrypt_note(ciphertext, owner_id=owner)
    assert decrypted == plaintext


def test_tampered_ciphertext_fails_invalid_tag():
    """Verify fail-closed behavior when ciphertext bit is tampered."""
    plaintext = "Sensitive Document"
    owner = "device-owner"
    encrypted = encrypt_note(plaintext, owner_id=owner)

    # Corrupt 1 byte in the base64 payload
    prefix, b64_part = encrypted[:3], encrypted[3:]
    raw = bytearray(base64.b64decode(b64_part))
    raw[-1] ^= 0x01  # Flip bit in authentication tag
    tampered_b64 = base64.b64encode(raw).decode("ascii")
    tampered_payload = f"{prefix}{tampered_b64}"

    with pytest.raises(InvalidTag):
        decrypt_note(tampered_payload, owner_id=owner)


def test_tampered_nonce_fails():
    """Verify fail-closed behavior when nonce is modified."""
    plaintext = "Financial Ledger"
    owner = "device-owner"
    encrypted = encrypt_note(plaintext, owner_id=owner)

    prefix, b64_part = encrypted[:3], encrypted[3:]
    raw = bytearray(base64.b64decode(b64_part))
    raw[0] ^= 0x01  # Flip bit in nonce
    tampered_b64 = base64.b64encode(raw).decode("ascii")
    tampered_payload = f"{prefix}{tampered_b64}"

    with pytest.raises(InvalidTag):
        decrypt_note(tampered_payload, owner_id=owner)


def test_wrong_owner_fails_cross_decryption():
    """Verify that Owner 2 cannot decrypt Owner 1's note even under same master key."""
    plaintext = "Personal Vault"
    owner_1 = "device-1"
    owner_2 = "device-2"

    encrypted_by_owner_1 = encrypt_note(plaintext, owner_id=owner_1)

    # Attempting to decrypt with owner_2 must fail closed
    with pytest.raises(InvalidTag):
        decrypt_note(encrypted_by_owner_1, owner_id=owner_2)


def test_wrong_master_key_fails():
    """Verify that changing master key fails decryption (key isolation)."""
    key_v1 = b"1" * 32
    key_v2 = b"2" * 32
    plaintext = "Important Secret"
    owner = "owner-dev"

    encrypted = encrypt_note(plaintext, owner_id=owner, custom_master_key=key_v1)

    with pytest.raises(InvalidTag):
        decrypt_note(encrypted, owner_id=owner, custom_master_key=key_v2)


def test_invalid_base64_fails():
    """Verify malformed Base64 payload is safely rejected."""
    with pytest.raises(ValueError, match="Invalid Base64"):
        decrypt_note("v1$!!!NotValidBase64@@@", owner_id="owner")


def test_truncated_payload_fails():
    """Verify payload shorter than minimum nonce + tag is rejected."""
    short_payload = "v1$" + base64.b64encode(b"short").decode("ascii")
    with pytest.raises(ValueError, match="truncated"):
        decrypt_note(short_payload, owner_id="owner")


def test_legacy_v0_compatibility():
    """Verify that unversioned legacy payloads (v0) can still be decrypted."""
    plaintext = "Legacy Note Content"
    owner = "legacy-owner"

    # Encrypt raw without v1$ prefix
    user_key = derive_user_key(owner)
    keyword = _derive_vigenere_keyword(user_key)
    vigenere_text = _vigenere_shift(plaintext, keyword)

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(user_key)
    nonce = os.urandom(12)
    raw = nonce + aesgcm.encrypt(nonce, vigenere_text.encode("utf-8"), None)
    legacy_payload = base64.b64encode(raw).decode("ascii")

    # Decrypt should handle unversioned payload seamlessly
    decrypted = decrypt_note(legacy_payload, owner_id=owner)
    assert decrypted == plaintext


def test_production_missing_key_fails_closed():
    """Verify that in production environment, missing master key fails startup."""
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://test:test@localhost:5432/test",
        notes_master_key_b64=None,
    )
    with pytest.raises(ValueError, match="NOTES_MASTER_KEY_B64 is mandatory in production"):
        _ = prod_settings.notes_master_key_bytes


def test_production_invalid_length_key_fails_closed():
    """Verify that in production environment, 16-byte key fails validation (must be 32 bytes)."""
    short_key_b64 = base64.b64encode(b"16_bytes_key!!!!").decode("ascii")
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://test:test@localhost:5432/test",
        notes_master_key_b64=short_key_b64,
    )
    with pytest.raises(ValueError, match="must decode to exactly 32 bytes"):
        _ = prod_settings.notes_master_key_bytes
