import base64
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.main import app
from app.services.crypto import build_canonical_payload
from app.services.origin import normalize_origin, validate_and_resolve_origin

client = TestClient(app)


def _generate_p256_keypair() -> tuple[ec.EllipticCurvePrivateKey, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    b64_pub = base64.b64encode(der_bytes).decode("ascii")
    return private_key, b64_pub


def _sign(private_key: ec.EllipticCurvePrivateKey, payload: str) -> str:
    sig = private_key.sign(payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode("ascii")


# --- Unit Tests for normalize_origin ---

def test_normalize_origin_valid() -> None:
    assert normalize_origin("http://localhost:5173") == "http://localhost:5173"
    assert normalize_origin("HTTP://LocalHost:5173") == "http://localhost:5173"
    assert normalize_origin("http://localhost:5173/") == "http://localhost:5173"
    assert normalize_origin("https://app.ipguard.io:443") == "https://app.ipguard.io"
    assert normalize_origin("http://app.ipguard.io:80") == "http://app.ipguard.io"
    assert normalize_origin("https://app.ipguard.io:8443") == "https://app.ipguard.io:8443"


@pytest.mark.parametrize(
    "invalid_origin,expected_code",
    [
        ("", "malformed_origin"),
        ("   ", "malformed_origin"),
        ("javascript:alert(1)", "malformed_origin"),
        ("ftp://localhost:5173", "malformed_origin"),
        ("data:text/html,<html>", "malformed_origin"),
        ("http://", "malformed_origin"),
        ("http://localhost:5173/api/v1", "malformed_origin"),
        ("http://localhost:5173?evil=1", "malformed_origin"),
        ("http://localhost:5173#frag", "malformed_origin"),
        ("http://localhost:5173/admin/", "malformed_origin"),
    ],
)
def test_normalize_origin_rejects_malformed(invalid_origin: str, expected_code: str) -> None:
    with pytest.raises(AppError) as exc_info:
        normalize_origin(invalid_origin)
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == expected_code


def test_validate_and_resolve_origin_trusted() -> None:
    trusted = ["http://localhost:5173", "https://app.ipguard.io"]

    # Explicit trusted origin matches
    resolved = validate_and_resolve_origin("http://localhost:5173", trusted)
    assert resolved == "http://localhost:5173"

    # Normalized comparison matches (strips trailing slash, normalizes case)
    resolved_normalized = validate_and_resolve_origin("HTTP://LOCALHOST:5173/", trusted)
    assert resolved_normalized == "http://localhost:5173"

    # None / empty resolves to default primary trusted origin
    default_resolved = validate_and_resolve_origin(None, trusted)
    assert default_resolved == "http://localhost:5173"


def test_validate_and_resolve_origin_untrusted_rejected() -> None:
    trusted = ["http://localhost:5173"]

    untrusted_cases = [
        "http://attacker.com",
        "https://evil.org",
        "http://evil-localhost:5173",
        "http://localhost:3000",
        "https://localhost:5173",  # Scheme mismatch
    ]
    for untrusted in untrusted_cases:
        with pytest.raises(AppError) as exc:
            validate_and_resolve_origin(untrusted, trusted)
        assert exc.value.status_code == 400
        assert exc.value.code == "untrusted_origin"

    # Suffix attack with port syntax corruption raises malformed_origin
    with pytest.raises(AppError) as exc_suffix:
        validate_and_resolve_origin("http://localhost:5173.attacker.com", trusted)
    assert exc_suffix.value.status_code == 400
    assert exc_suffix.value.code == "malformed_origin"


# --- Integration Tests through FastAPI ---

def test_api_session_creation_with_trusted_origin() -> None:
    response = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION", "origin": "http://localhost:5173"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["client_origin"] == "http://localhost:5173"
    assert data["qr_payload"]["origin"] == "http://localhost:5173"


def test_api_session_creation_with_omitted_origin_resolves_default() -> None:
    response = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["client_origin"] == "http://localhost:5173"
    assert data["qr_payload"]["origin"] == "http://localhost:5173"


def test_api_session_creation_rejects_untrusted_domain() -> None:
    response = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION", "origin": "https://malicious-phishing.site"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "untrusted_origin"


def test_api_session_creation_rejects_malformed_origin_with_path() -> None:
    response = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION", "origin": "http://localhost:5173/login?redirect=evil"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "malformed_origin"


def test_api_session_origin_binding_in_verification() -> None:
    # 1. Enroll device
    enroll_sess = client.post("/api/v1/auth/sessions", json={"session_type": "ENROLLMENT"}).json()
    priv, b64_pub = _generate_p256_keypair()
    qr_enr = enroll_sess["qr_payload"]
    enr_payload = build_canonical_payload(qr_enr["session_token"], qr_enr["nonce"], qr_enr["origin"], qr_enr["timestamp"])
    client.post(
        "/api/v1/auth/devices/register",
        json={
            "session_token": enroll_sess["session_token"],
            "device_id": "origin-bound-device-01",
            "device_name": "Test Device",
            "model": "A54",
            "android_version": "16",
            "public_key_x509": b64_pub,
            "canonical_payload": enr_payload,
            "signature": _sign(priv, enr_payload),
        },
    )

    # 2. Create AUTHENTICATION session with trusted origin
    auth_sess = client.post(
        "/api/v1/auth/sessions",
        json={"session_type": "AUTHENTICATION", "origin": "http://localhost:5173"},
    ).json()
    qr_auth = auth_sess["qr_payload"]
    bound_origin = auth_sess["client_origin"]
    assert bound_origin == "http://localhost:5173"

    # 3. An attacker signs a canonical payload using an unauthorized spoofed origin
    spoofed_payload = build_canonical_payload(
        qr_auth["session_token"],
        qr_auth["nonce"],
        "http://attacker.com",  # Attacker tries to replace bound origin
        qr_auth["timestamp"],
    )
    spoofed_sig = _sign(priv, spoofed_payload)

    # Verification must fail because canonical_payload does not match session's bound origin
    verify_res = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": "origin-bound-device-01",
            "canonical_payload": spoofed_payload,
            "signature": spoofed_sig,
        },
    )
    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "invalid_canonical_payload"

    # 4. Legitimate verification with session's bound trusted origin succeeds
    legit_payload = build_canonical_payload(
        qr_auth["session_token"],
        qr_auth["nonce"],
        bound_origin,
        qr_auth["timestamp"],
    )
    legit_sig = _sign(priv, legit_payload)

    verify_ok = client.post(
        f"/api/v1/auth/sessions/{auth_sess['session_token']}/verify",
        json={
            "device_id": "origin-bound-device-01",
            "canonical_payload": legit_payload,
            "signature": legit_sig,
        },
    )
    assert verify_ok.status_code == 200
    assert verify_ok.json()["status"] == "APPROVED"
