from urllib.parse import urlsplit

from app.core.errors import AppError


def normalize_origin(raw_origin: str) -> str:
    """
    Parse and normalize an RFC 6454 Web Origin string (scheme://hostname[:port]).
    Enforces strict scheme, removes default ports (80/443), lowercases scheme and host,
    and rejects paths, queries, or fragments.
    """
    cleaned = raw_origin.strip()
    if not cleaned:
        raise AppError(
            status_code=400,
            code="malformed_origin",
            message="Origin string cannot be empty.",
        )

    try:
        parsed = urlsplit(cleaned)
    except Exception as err:
        raise AppError(
            status_code=400,
            code="malformed_origin",
            message="Failed to parse origin URI.",
        ) from err

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise AppError(
            status_code=400,
            code="malformed_origin",
            message=f"Origin scheme '{parsed.scheme}' is invalid. Only http and https are permitted.",
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise AppError(
            status_code=400,
            code="malformed_origin",
            message="Origin is missing a valid hostname.",
        )

    # Origins must not contain paths, query parameters, or URL fragments
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise AppError(
            status_code=400,
            code="malformed_origin",
            message="Origin must not contain a path, query parameter, or fragment.",
        )

    try:
        port = parsed.port
    except ValueError as err:
        raise AppError(
            status_code=400,
            code="malformed_origin",
            message="Origin contains an invalid port representation.",
        ) from err

    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None

    if port:
        return f"{scheme}://{hostname}:{port}"
    return f"{scheme}://{hostname}"


def validate_and_resolve_origin(
    candidate_origin: str | None,
    trusted_origins: list[str],
) -> str:
    """
    Validate that the candidate origin matches the configured trusted origins whitelist.
    If candidate_origin is omitted or None, defaults to the primary trusted origin.
    Fails closed if the candidate origin is malformed or not in the trusted list.
    """
    if not trusted_origins:
        raise AppError(
            status_code=500,
            code="configuration_error",
            message="No trusted origins are configured on the server.",
        )

    normalized_trusted = [normalize_origin(o) for o in trusted_origins]

    if not candidate_origin:
        return normalized_trusted[0]

    normalized_candidate = normalize_origin(candidate_origin)
    if normalized_candidate not in normalized_trusted:
        raise AppError(
            status_code=400,
            code="untrusted_origin",
            message=f"Origin '{candidate_origin}' is not authorized by the server's trusted origins whitelist.",
        )

    return normalized_candidate
