"""Pydantic schemas for M5 Blockchain Batch Audit Anchoring."""

from datetime import datetime
from pydantic import BaseModel, Field


class AnchorBatchRequest(BaseModel):
    audit_chain_id: str | None = Field(
        default=None,
        max_length=64,
        description="Optional audit chain identifier. Defaults to the caller's active device chain.",
    )
    max_events: int | None = Field(
        default=None,
        ge=1,
        le=5000,
        description="Optional cap on contiguous unanchored events included in this batch.",
    )


class BlockchainAnchorRecord(BaseModel):
    id: str
    audit_chain_id: str
    from_sequence: int
    to_sequence: int
    event_count: int
    merkle_root: str
    head_hash: str
    batch_reference: str
    network: str
    chain_id: int
    contract_address: str
    signer_address: str | None = None
    tx_hash: str | None = None
    block_number: int | None = None
    block_timestamp: datetime | None = None
    status: str
    explorer_url: str | None = None
    created_at: datetime
    confirmed_at: datetime | None = None
    error_message: str | None = None


class BlockchainOverviewResponse(BaseModel):
    configured: bool
    network: str
    network_label: str
    chain_id: int
    contract_address: str | None = None
    signer_address: str | None = None
    audit_chain_id: str
    audit_chain_valid: bool
    audit_chain_reason: str | None = None
    anchored_batch_count: int
    total_anchored_events: int
    pending_events: int
    last_anchored_sequence: int
    latest_anchor: BlockchainAnchorRecord | None = None
    recent_anchors: list[BlockchainAnchorRecord] = Field(default_factory=list)
    status: str
    configuration_issues: list[str] = Field(default_factory=list)


class AnchorVerificationChecks(BaseModel):
    db_record_present: bool
    audit_chain_valid: bool
    local_merkle_recomputed_match: bool
    tx_receipt_confirmed: bool
    onchain_contract_match: bool
    reorg_check_passed: bool


class AnchorVerifyResponse(BaseModel):
    anchor_id: str
    verified: bool
    status: str
    audit_chain_id: str
    from_sequence: int
    to_sequence: int
    event_count: int
    merkle_root: str
    head_hash: str
    network: str
    network_label: str
    chain_id: int
    contract_address: str
    tx_hash: str | None = None
    block_number: int | None = None
    explorer_url: str | None = None
    checks: AnchorVerificationChecks
    reason: str | None = None
