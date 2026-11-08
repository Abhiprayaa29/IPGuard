"""Application services."""

from app.services.auth import (
    create_auth_session,
    get_auth_session_status,
    list_devices,
    mark_session_scanned,
    register_device,
    revoke_device,
    verify_session_signature,
)
from app.services.crypto import (
    build_canonical_payload,
    compute_public_key_fingerprint,
    generate_secure_token,
    parse_and_validate_public_key,
    verify_ecdsa_signature,
)
from app.services.health import check_database_connection
from app.services.note_crypto import (
    decrypt_note,
    derive_user_key,
    encrypt_note,
)
from app.services.notes import (
    create_note,
    delete_note,
    get_note,
    list_notes,
    update_note,
)
from app.services.origin import normalize_origin, validate_and_resolve_origin

__all__ = [
    "build_canonical_payload",
    "check_database_connection",
    "compute_public_key_fingerprint",
    "create_auth_session",
    "create_note",
    "decrypt_note",
    "delete_note",
    "derive_user_key",
    "encrypt_note",
    "generate_secure_token",
    "get_auth_session_status",
    "get_note",
    "list_devices",
    "list_notes",
    "mark_session_scanned",
    "normalize_origin",
    "parse_and_validate_public_key",
    "register_device",
    "revoke_device",
    "update_note",
    "validate_and_resolve_origin",
    "verify_ecdsa_signature",
    "verify_session_signature",
]
