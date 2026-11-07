import base64
import binascii
import hashlib
import secrets
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.core.errors import AppError


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure hex token."""
    return secrets.token_hex(nbytes)


def parse_and_validate_public_key(
    public_key_x509_b64: str,
) -> tuple[ec.EllipticCurvePublicKey, bytes]:
    """
    Parse a Base64-encoded X.509 SubjectPublicKeyInfo DER public key,
    validate that it is an EC key on the NIST P-256 (secp256r1) curve.

    Returns a tuple of (EllipticCurvePublicKey, raw_der_bytes).
    Fails closed if the key format, type, or curve is invalid.
    """
    try:
        der_bytes = base64.b64decode(public_key_x509_b64, validate=True)
    except (binascii.Error, ValueError) as err:
        raise AppError(
            status_code=400,
            code="invalid_public_key_encoding",
            message="Public key is not valid Base64 encoded DER.",
        ) from err

    try:
        loaded_key = serialization.load_der_public_key(der_bytes)
    except Exception as err:
        raise AppError(
            status_code=400,
            code="invalid_public_key_format",
            message="Public key could not be parsed as X.509 SubjectPublicKeyInfo DER.",
        ) from err

    if not isinstance(loaded_key, ec.EllipticCurvePublicKey):
        raise AppError(
            status_code=400,
            code="unsupported_key_type",
            message="Public key must be an Elliptic Curve (EC) key.",
        )

    if loaded_key.curve.name != "secp256r1":
        raise AppError(
            status_code=400,
            code="unsupported_curve",
            message=f"Curve '{loaded_key.curve.name}' is not supported. Must be NIST P-256 (secp256r1).",
        )

    return loaded_key, der_bytes


def compute_public_key_fingerprint(
    public_key_or_der: ec.EllipticCurvePublicKey | bytes,
) -> str:
    """
    Compute a SHA-256 fingerprint from the raw DER bytes of the SubjectPublicKeyInfo.
    Formatted as uppercase colon-delimited hex (e.g. 95 characters), matching Android Keystore export format:
    `AA:BB:CC:...`
    """
    if isinstance(public_key_or_der, bytes):
        der_bytes = public_key_or_der
    else:
        der_bytes = public_key_or_der.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    digest = hashlib.sha256(der_bytes).digest()
    return ":".join(f"{b:02X}" for b in digest)


def build_canonical_payload(
    session_token: str,
    nonce: str,
    origin: str,
    timestamp: int,
) -> str:
    """
    Construct the canonical challenge payload to be signed by the Android authenticator:
    `{session_token}:{nonce}:{origin}:{timestamp}`
    """
    return f"{session_token}:{nonce}:{origin}:{timestamp}"


def verify_ecdsa_signature(
    public_key: ec.EllipticCurvePublicKey,
    canonical_payload: str,
    signature_b64: str,
) -> bool:
    """
    Verify an ASN.1 DER ECDSA SHA-256 signature against the canonical payload string.
    Returns True if valid, False if verification fails or signature is corrupt.
    Fail-closed on any error.
    """
    try:
        signature_bytes = base64.b64decode(signature_b64, validate=True)
    except (binascii.Error, ValueError):
        return False

    try:
        public_key.verify(
            signature_bytes,
            canonical_payload.encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False
