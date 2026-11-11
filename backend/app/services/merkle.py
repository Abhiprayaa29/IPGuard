"""Deterministic Keccak-256 Merkle tree builder for verified IPGuard audit batches."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol, Sequence

from eth_utils import keccak

_HEX_64_RE = re.compile(r"^(?:0x)?[0-9a-fA-F]{64}$")


class AuditEventLike(Protocol):
    """Minimal protocol required from AuditEvent ORM rows or test doubles."""

    chain_id: str
    sequence: int
    prev_hash: str
    event_hash: str


class MerkleBatchError(ValueError):
    """Raised when audit events cannot form a valid contiguous Merkle batch."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class MerkleBatchResult:
    """Cryptographic commitments and metadata produced from a contiguous audit batch."""

    audit_chain_id: str
    audit_chain_id_hash: str
    from_sequence: int
    to_sequence: int
    event_count: int
    merkle_root: str
    head_hash: str
    batch_reference: str


def _parse_hash32(value: str, field_name: str) -> bytes:
    if not isinstance(value, str) or not _HEX_64_RE.match(value.strip()):
        raise MerkleBatchError(
            "invalid_hash",
            f"{field_name} must be a 64-character hexadecimal SHA-256/32-byte digest.",
        )
    normalized = value.strip().lower().removeprefix("0x")
    return bytes.fromhex(normalized)


def compute_audit_chain_id_bytes32(audit_chain_id: str) -> str:
    """Map an off-chain audit chain identifier string to a deterministic Solidity bytes32 key."""
    cleaned = audit_chain_id.strip()
    if not cleaned:
        raise MerkleBatchError("invalid_chain_id", "Audit chain ID must be non-empty.")
    return "0x" + keccak(cleaned.encode("utf-8")).hex()


def hash_merkle_leaf(event_hash_bytes: bytes) -> bytes:
    """Leaf commitment with explicit 0x00 domain separation: keccak256(0x00 || event_hash)."""
    if len(event_hash_bytes) != 32:
        raise MerkleBatchError("invalid_leaf", "Merkle leaf hash input must be 32 bytes.")
    return bytes(keccak(b"\x00" + event_hash_bytes))


def hash_merkle_node(left: bytes, right: bytes) -> bytes:
    """Internal node commitment with explicit 0x01 domain separation: keccak256(0x01 || left || right)."""
    if len(left) != 32 or len(right) != 32:
        raise MerkleBatchError("invalid_node", "Merkle child hashes must be 32 bytes.")
    return bytes(keccak(b"\x01" + left + right))


def compute_merkle_root_from_hashes(event_hashes: Sequence[str | bytes]) -> str:
    """
    Compute the deterministic Keccak-256 Merkle root from ordered event hashes.

    Convention (matching BatchAnchorRegistry.computeMerkleRoot in Solidity):
    - Leaf: keccak256(0x00 || event_hash)
    - Internal node: keccak256(0x01 || left || right)
    - Odd node count rule: duplicate the final node at that tree level.
    """
    if not event_hashes:
        raise MerkleBatchError("empty_batch", "Cannot compute a Merkle root from an empty batch.")

    level: list[bytes] = []
    for raw in event_hashes:
        if isinstance(raw, bytes):
            if len(raw) != 32:
                raise MerkleBatchError("invalid_hash", "Raw event hash bytes must be 32 bytes.")
            digest = raw
        else:
            digest = _parse_hash32(raw, "event_hash")
        level.append(hash_merkle_leaf(digest))

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        next_level: list[bytes] = []
        for idx in range(0, len(level), 2):
            next_level.append(hash_merkle_node(level[idx], level[idx + 1]))
        level = next_level

    return "0x" + level[0].hex()


def build_merkle_batch(
    events: Sequence[AuditEventLike],
    *,
    expected_chain_id: str | None = None,
    expected_from_sequence: int | None = None,
) -> MerkleBatchResult:
    """
    Validate a contiguous sequence slice of verified audit events and build its Merkle batch.
    """
    if not events:
        raise MerkleBatchError("empty_batch", "No audit events supplied for Merkle batch construction.")

    chain_id = expected_chain_id or events[0].chain_id
    chain_id_hash = compute_audit_chain_id_bytes32(chain_id)

    first_seq = events[0].sequence
    if first_seq < 1:
        raise MerkleBatchError("invalid_sequence", "Audit sequence numbers must start at >= 1.")
    if expected_from_sequence is not None and first_seq != expected_from_sequence:
        raise MerkleBatchError(
            "sequence_mismatch",
            f"Expected batch to start at sequence {expected_from_sequence}, got {first_seq}.",
        )

    ordered_hashes: list[bytes] = []
    prev_event_hash: str | None = None

    for idx, ev in enumerate(events):
        if ev.chain_id != chain_id:
            raise MerkleBatchError(
                "mixed_chain_ids",
                f"Batch contains mixed chain_id '{ev.chain_id}' (expected '{chain_id}').",
            )
        expected_seq = first_seq + idx
        if ev.sequence != expected_seq:
            raise MerkleBatchError(
                "sequence_gap",
                f"Sequence gap or out-of-order event detected: expected {expected_seq}, got {ev.sequence}.",
            )

        _parse_hash32(ev.prev_hash, "prev_hash")
        raw_event_hash = _parse_hash32(ev.event_hash, "event_hash")

        if prev_event_hash is not None and ev.prev_hash.lower() != prev_event_hash.lower():
            raise MerkleBatchError(
                "broken_chain_link",
                f"prev_hash mismatch at sequence {ev.sequence}.",
            )

        ordered_hashes.append(raw_event_hash)
        prev_event_hash = ev.event_hash

    from_seq = first_seq
    to_seq = events[-1].sequence
    merkle_root = compute_merkle_root_from_hashes(ordered_hashes)
    head_hash = "0x" + _parse_hash32(events[-1].event_hash, "head_hash").hex()
    batch_ref = f"{chain_id}:{from_seq}-{to_seq}:{merkle_root[2:14]}"

    return MerkleBatchResult(
        audit_chain_id=chain_id,
        audit_chain_id_hash=chain_id_hash,
        from_sequence=from_seq,
        to_sequence=to_seq,
        event_count=len(events),
        merkle_root=merkle_root,
        head_hash=head_hash,
        batch_reference=batch_ref,
    )
