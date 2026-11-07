import base64
import hashlib
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from app.core.errors import AppError
from app.services.crypto import (
    build_canonical_payload,
    compute_public_key_fingerprint,
    generate_secure_token,
    parse_and_validate_public_key,
    verify_ecdsa_signature,
)


def _generate_p256_keypair() -> tuple[ec.EllipticCurvePrivateKey, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    b64_pub = base64.b64encode(der_bytes).decode("ascii")
    return private_key, b64_pub


def test_generate_secure_token() -> None:
    token1 = generate_secure_token(32)
    token2 = generate_secure_token(32)

    assert len(token1) == 64
    assert len(token2) == 64
    assert token1 != token2
    # Verify hex string
    int(token1, 16)


def test_build_canonical_payload() -> None:
    payload = build_canonical_payload(
        session_token="token_abc",
        nonce="nonce_123",
        origin="http://localhost:5173",
        timestamp=1700000000,
    )
    assert payload == "token_abc:nonce_123:http://localhost:5173:1700000000"


def test_valid_p256_public_key_parsing() -> None:
    _, b64_pub = _generate_p256_keypair()

    pubkey, der_bytes = parse_and_validate_public_key(b64_pub)
    assert isinstance(pubkey, ec.EllipticCurvePublicKey)
    assert pubkey.curve.name == "secp256r1"
    assert pubkey.key_size == 256
    assert isinstance(der_bytes, bytes)
    assert len(der_bytes) > 0


def test_reject_invalid_base64_public_key() -> None:
    with pytest.raises(AppError) as exc_info:
        parse_and_validate_public_key("not-valid-base64!@#$")
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "invalid_public_key_encoding"


def test_reject_corrupted_der_bytes() -> None:
    corrupted_b64 = base64.b64encode(b"corrupted-der-payload-12345").decode("ascii")
    with pytest.raises(AppError) as exc_info:
        parse_and_validate_public_key(corrupted_b64)
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "invalid_public_key_format"


def test_reject_rsa_public_key() -> None:
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_der = rsa_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    rsa_b64 = base64.b64encode(rsa_der).decode("ascii")

    with pytest.raises(AppError) as exc_info:
        parse_and_validate_public_key(rsa_b64)
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "unsupported_key_type"


def test_reject_unsupported_elliptic_curve() -> None:
    p384_key = ec.generate_private_key(ec.SECP384R1())
    p384_der = p384_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    p384_b64 = base64.b64encode(p384_der).decode("ascii")

    with pytest.raises(AppError) as exc_info:
        parse_and_validate_public_key(p384_b64)
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "unsupported_curve"
    assert "secp384r1" in exc_info.value.message


def test_compute_public_key_fingerprint() -> None:
    _, b64_pub = _generate_p256_keypair()
    pubkey, der_bytes = parse_and_validate_public_key(b64_pub)

    fp_from_bytes = compute_public_key_fingerprint(der_bytes)
    fp_from_key = compute_public_key_fingerprint(pubkey)

    assert fp_from_bytes == fp_from_key
    assert len(fp_from_bytes) == 95  # 32 hex pairs (64) + 31 colons (31) = 95
    assert all(len(part) == 2 for part in fp_from_bytes.split(":"))
    assert fp_from_bytes == fp_from_bytes.upper()


def test_ecdsa_signature_verification_success() -> None:
    private_key, b64_pub = _generate_p256_keypair()
    pubkey, _ = parse_and_validate_public_key(b64_pub)

    payload = "session_token_1:nonce_1:http://localhost:5173:1700000000"
    signature_bytes = private_key.sign(
        payload.encode("utf-8"),
        ec.ECDSA(hashes.SHA256()),
    )
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    assert verify_ecdsa_signature(pubkey, payload, signature_b64) is True


def test_ecdsa_signature_verification_tampered_payload_rejected() -> None:
    private_key, b64_pub = _generate_p256_keypair()
    pubkey, _ = parse_and_validate_public_key(b64_pub)

    payload = "session_token_1:nonce_1:http://localhost:5173:1700000000"
    tampered_payload = "session_token_1:nonce_1:http://localhost:5173:1700000001"

    signature_bytes = private_key.sign(
        payload.encode("utf-8"),
        ec.ECDSA(hashes.SHA256()),
    )
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    assert verify_ecdsa_signature(pubkey, tampered_payload, signature_b64) is False


def test_ecdsa_signature_verification_wrong_key_rejected() -> None:
    key_alice, _ = _generate_p256_keypair()
    _, b64_bob = _generate_p256_keypair()
    pubkey_bob, _ = parse_and_validate_public_key(b64_bob)

    payload = "session_token_1:nonce_1:http://localhost:5173:1700000000"
    signature_bytes = key_alice.sign(
        payload.encode("utf-8"),
        ec.ECDSA(hashes.SHA256()),
    )
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    assert verify_ecdsa_signature(pubkey_bob, payload, signature_b64) is False


def test_ecdsa_signature_verification_corrupt_signature_rejected() -> None:
    _, b64_pub = _generate_p256_keypair()
    pubkey, _ = parse_and_validate_public_key(b64_pub)

    payload = "session_token_1:nonce_1:http://localhost:5173:1700000000"

    # Not valid base64
    assert verify_ecdsa_signature(pubkey, payload, "invalid!!base64") is False

    # Valid base64 but invalid DER
    invalid_der_b64 = base64.b64encode(b"random-non-der-data").decode("ascii")
    assert verify_ecdsa_signature(pubkey, payload, invalid_der_b64) is False
