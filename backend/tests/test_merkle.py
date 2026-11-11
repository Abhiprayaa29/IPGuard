"""Unit tests for deterministic Keccak-256 Merkle batch construction (M5)."""

from dataclasses import dataclass
import hashlib

import pytest

from app.services.merkle import (
    MerkleBatchError,
    build_merkle_batch,
    compute_audit_chain_id_bytes32,
    compute_merkle_root_from_hashes,
    hash_merkle_leaf,
    hash_merkle_node,
)


@dataclass
class FakeAuditEvent:
    chain_id: str
    sequence: int
    prev_hash: str
    event_hash: str


def _make_chain(count: int, *, chain_id: str = "device-chain-1", start_seq: int = 1) -> list[FakeAuditEvent]:
    prev = "0" * 64
    events: list[FakeAuditEvent] = []
    for offset in range(count):
        seq = start_seq + offset
        digest = hashlib.sha256(f"{chain_id}:{seq}:{prev}".encode("utf-8")).hexdigest()
        events.append(FakeAuditEvent(chain_id=chain_id, sequence=seq, prev_hash=prev, event_hash=digest))
        prev = digest
    return events


def test_empty_input_rejected():
    with pytest.raises(MerkleBatchError) as exc_info:
        build_merkle_batch([])
    assert exc_info.value.code == "empty_batch"

    with pytest.raises(MerkleBatchError) as exc_info2:
        compute_merkle_root_from_hashes([])
    assert exc_info2.value.code == "empty_batch"


def test_single_event_root_equals_domain_separated_leaf():
    events = _make_chain(1)
    batch = build_merkle_batch(events)

    expected_leaf = "0x" + hash_merkle_leaf(bytes.fromhex(events[0].event_hash)).hex()
    assert batch.merkle_root == expected_leaf
    assert batch.from_sequence == 1
    assert batch.to_sequence == 1
    assert batch.event_count == 1
    assert batch.head_hash == "0x" + events[0].event_hash
    assert batch.audit_chain_id == "device-chain-1"
    assert batch.audit_chain_id_hash == compute_audit_chain_id_bytes32("device-chain-1")


def test_even_and_odd_event_counts_follow_documented_duplication_rule():
    # Even (4)
    even_hashes = [hashlib.sha256(f"e-{i}".encode()).hexdigest() for i in range(4)]
    leaves4 = [hash_merkle_leaf(bytes.fromhex(h)) for h in even_hashes]
    n01 = hash_merkle_node(leaves4[0], leaves4[1])
    n23 = hash_merkle_node(leaves4[2], leaves4[3])
    expected4 = "0x" + hash_merkle_node(n01, n23).hex()
    assert compute_merkle_root_from_hashes(even_hashes) == expected4

    # Odd (3) -> duplicate final leaf at leaf level before internal node pairing
    odd_hashes = even_hashes[:3]
    leaves3 = leaves4[:3]
    l01 = hash_merkle_node(leaves3[0], leaves3[1])
    l22 = hash_merkle_node(leaves3[2], leaves3[2])
    expected3 = "0x" + hash_merkle_node(l01, l22).hex()
    assert compute_merkle_root_from_hashes(odd_hashes) == expected3


def test_identical_inputs_are_deterministic_and_tamper_changes_root():
    events = _make_chain(5)
    b1 = build_merkle_batch(events)
    b2 = build_merkle_batch(events)
    assert b1.merkle_root == b2.merkle_root
    assert b1.batch_reference == b2.batch_reference

    tampered_hashes = [e.event_hash for e in events]
    tampered_hashes[2] = hashlib.sha256(b"tampered").hexdigest()
    assert compute_merkle_root_from_hashes(tampered_hashes) != b1.merkle_root

    reordered_hashes = [events[1].event_hash, events[0].event_hash, events[2].event_hash]
    original_slice = [events[0].event_hash, events[1].event_hash, events[2].event_hash]
    assert compute_merkle_root_from_hashes(reordered_hashes) != compute_merkle_root_from_hashes(original_slice)


def test_sequence_gap_and_broken_chain_links_rejected():
    events = _make_chain(4)

    with pytest.raises(MerkleBatchError) as gap_err:
        build_merkle_batch([events[0], events[1], events[3]])
    assert gap_err.value.code == "sequence_gap"

    events[2].prev_hash = "f" * 64
    with pytest.raises(MerkleBatchError) as link_err:
        build_merkle_batch(events)
    assert link_err.value.code == "broken_chain_link"

    with pytest.raises(MerkleBatchError) as mixed_err:
        other = _make_chain(1, chain_id="other-chain")[0]
        build_merkle_batch([events[0], other])
    assert mixed_err.value.code == "mixed_chain_ids"
