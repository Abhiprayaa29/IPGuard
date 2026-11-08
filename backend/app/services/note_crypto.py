"""
IPGuard Milestone 3 — Secure Notes Cryptography Service.
Super-Encryption Architecture:
1. Classical Layer: Vigenère Cipher (NIST academic / defense-in-depth requirement).
2. Modern Layer: AES-256-GCM authenticated encryption with associated data (AEAD).
3. Key Derivation: HKDF-SHA256 (RFC 5869) domain separation per owner_id.
4. Envelope Format: v1$<base64(nonce[12] + ciphertext + tag[16])>.

Note: While Vigenère fulfills the project's educational super-encryption design,
the mathematical confidentiality and integrity guarantees rely entirely on AES-256-GCM.
"""

import base64
import binascii
import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings

ENVELOPE_PREFIX_V1 = "v1$"
MIN_PAYLOAD_BYTES = 28  # 12 bytes nonce + 16 bytes authentication tag


def derive_user_key(owner_id: str, master_key: bytes | None = None) -> bytes:
    """
    Derive a 256-bit (32-byte) AES key specific to the owner_id using HKDF-SHA256.
    Ensures cryptographic domain separation so ciphertexts from one owner
    cannot be decrypted by another owner, even under the same master key.
    """
    if not owner_id or not isinstance(owner_id, str):
        raise ValueError("owner_id must be a non-empty string.")

    if master_key is None:
        master_key = get_settings().notes_master_key_bytes

    if len(master_key) != 32:
        raise ValueError("Master key must be exactly 32 bytes (256 bits).")

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=owner_id.encode("utf-8"),
        info=b"ipguard-secure-notes-v1-hkdf-aes256gcm",
    )
    return hkdf.derive(master_key)


def _derive_vigenere_keyword(derived_aes_key: bytes) -> str:
    """Derive deterministic 12-char alphabetic keyword for Vigenère from AES key."""
    return hashlib.sha256(b"vigenere|" + derived_aes_key).hexdigest()[:12]


def _vigenere_shift(text: str, keyword: str, decrypt: bool = False) -> str:
    """
    Classical Vigenère cipher shift.
    Operates strictly on ASCII letters [A-Za-z].
    Leaves numbers, punctuation, spaces, newlines, and non-ASCII Unicode unchanged.
    """
    keyword = keyword.lower()
    k_len = len(keyword)
    res: list[str] = []
    k_idx = 0

    for ch in text:
        if ch.isalpha() and ord(ch) < 128:
            base = ord("a") if ch.islower() else ord("A")
            shift = ord(keyword[k_idx % k_len]) - ord("a")
            if decrypt:
                shift = -shift
            res.append(chr((ord(ch) - base + shift) % 26 + base))
            k_idx += 1
        else:
            res.append(ch)

    return "".join(res)


def encrypt_note(
    plaintext: str,
    owner_id: str,
    custom_master_key: bytes | None = None,
) -> str:
    """
    Super-encrypt a note title or content.
    1. Derives owner-specific 32-byte key via HKDF-SHA256.
    2. Applies Vigenère shift with key-derived keyword.
    3. Encrypts with AES-256-GCM using cryptographically random 12-byte nonce.
    4. Bundles into versioned envelope: v1$<base64(nonce + ct + tag)>.
    """
    if not isinstance(plaintext, str):
        raise ValueError("plaintext must be a string.")

    user_key = derive_user_key(owner_id, custom_master_key)
    keyword = _derive_vigenere_keyword(user_key)

    # 1. Classical layer
    vigenere_text = _vigenere_shift(plaintext, keyword, decrypt=False)

    # 2. Modern AEAD layer
    aesgcm = AESGCM(user_key)
    nonce = os.urandom(12)
    ct_with_tag = aesgcm.encrypt(nonce, vigenere_text.encode("utf-8"), None)

    # 3. Versioned envelope packaging
    raw_payload = nonce + ct_with_tag
    b64_payload = base64.b64encode(raw_payload).decode("ascii")
    return f"{ENVELOPE_PREFIX_V1}{b64_payload}"


def decrypt_note(
    payload: str,
    owner_id: str,
    custom_master_key: bytes | None = None,
) -> str:
    """
    Decrypt and authenticate a note title or content.
    1. Validates envelope version (v1$) or legacy format (v0).
    2. Verifies Base64 encoding and minimum payload length.
    3. Authenticates and decrypts AES-256-GCM (fails closed on tampering).
    4. Reverses Vigenère shift.
    5. Returns verified plaintext.
    """
    if not payload or not isinstance(payload, str):
        raise ValueError("Encrypted payload must be a non-empty string.")

    if payload.startswith(ENVELOPE_PREFIX_V1):
        raw_b64 = payload[len(ENVELOPE_PREFIX_V1):]
    else:
        # Legacy unversioned payload compatibility window
        raw_b64 = payload

    try:
        raw = base64.b64decode(raw_b64, validate=True)
    except (binascii.Error, ValueError) as err:
        raise ValueError("Invalid Base64 encoding in ciphertext payload.") from err

    if len(raw) < MIN_PAYLOAD_BYTES:
        raise ValueError(
            f"Ciphertext payload is truncated: minimum {MIN_PAYLOAD_BYTES} bytes required."
        )

    nonce = raw[:12]
    ct_with_tag = raw[12:]

    user_key = derive_user_key(owner_id, custom_master_key)
    aesgcm = AESGCM(user_key)

    # Decrypt and authenticate: raises InvalidTag if ciphertext or tag was tampered with
    vigenere_bytes = aesgcm.decrypt(nonce, ct_with_tag, None)
    vigenere_text = vigenere_bytes.decode("utf-8")

    keyword = _derive_vigenere_keyword(user_key)
    return _vigenere_shift(vigenere_text, keyword, decrypt=True)
