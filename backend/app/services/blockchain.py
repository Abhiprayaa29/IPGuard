"""M5 Hybrid Batch Audit Anchoring Service (Anvil local + Ethereum Sepolia)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Callable
import uuid

from eth_account import Account
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session
from web3 import Web3
from web3.exceptions import ContractLogicError, TimeExhausted, TransactionNotFound

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.audit import AuditChainHead, AuditEvent
from app.models.auth import Device
from app.models.blockchain import AuditBlockchainAnchor
from app.schemas.blockchain import (
    AnchorVerificationChecks,
    AnchorVerifyResponse,
    BlockchainAnchorRecord,
    BlockchainOverviewResponse,
)
from app.services.audit_chain import verify_audit_chain
from app.services.merkle import MerkleBatchError, build_merkle_batch, compute_audit_chain_id_bytes32

_BYTES32_HEX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")

# Minimal auditable ABI matching blockchain/contracts/BatchAnchorRegistry.sol
BATCH_ANCHOR_REGISTRY_ABI: list[dict[str, Any]] = [
    {
        "inputs": [{"internalType": "address", "name": "initialSigner", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "constructor",
    },
    {
        "inputs": [],
        "name": "authorizedSigner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "name": "lastAnchoredSequence",
        "outputs": [{"internalType": "uint64", "name": "", "type": "uint64"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "auditChainId", "type": "bytes32"},
            {"internalType": "uint64", "name": "fromSequence", "type": "uint64"},
            {"internalType": "uint64", "name": "toSequence", "type": "uint64"},
            {"internalType": "bytes32", "name": "merkleRoot", "type": "bytes32"},
            {"internalType": "bytes32", "name": "headHash", "type": "bytes32"},
        ],
        "name": "anchorBatch",
        "outputs": [{"internalType": "uint256", "name": "batchIndex", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "auditChainId", "type": "bytes32"},
            {"internalType": "uint64", "name": "fromSequence", "type": "uint64"},
            {"internalType": "uint64", "name": "toSequence", "type": "uint64"},
        ],
        "name": "getBatchByRange",
        "outputs": [
            {
                "components": [
                    {"internalType": "bytes32", "name": "auditChainId", "type": "bytes32"},
                    {"internalType": "uint64", "name": "fromSequence", "type": "uint64"},
                    {"internalType": "uint64", "name": "toSequence", "type": "uint64"},
                    {"internalType": "bytes32", "name": "merkleRoot", "type": "bytes32"},
                    {"internalType": "bytes32", "name": "headHash", "type": "bytes32"},
                    {"internalType": "uint64", "name": "blockTimestamp", "type": "uint64"},
                    {"internalType": "address", "name": "signer", "type": "address"},
                ],
                "internalType": "struct BatchAnchorRegistry.BatchAnchor",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "auditChainId", "type": "bytes32"},
            {"internalType": "uint64", "name": "fromSequence", "type": "uint64"},
            {"internalType": "uint64", "name": "toSequence", "type": "uint64"},
            {"internalType": "bytes32", "name": "merkleRoot", "type": "bytes32"},
            {"internalType": "bytes32", "name": "headHash", "type": "bytes32"},
        ],
        "name": "verifyBatch",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "auditChainId", "type": "bytes32"},
            {"indexed": True, "internalType": "uint256", "name": "batchIndex", "type": "uint256"},
            {"indexed": False, "internalType": "uint64", "name": "fromSequence", "type": "uint64"},
            {"indexed": False, "internalType": "uint64", "name": "toSequence", "type": "uint64"},
            {"indexed": False, "internalType": "bytes32", "name": "merkleRoot", "type": "bytes32"},
            {"indexed": False, "internalType": "bytes32", "name": "headHash", "type": "bytes32"},
            {"indexed": False, "internalType": "uint64", "name": "blockTimestamp", "type": "uint64"},
            {"indexed": True, "internalType": "address", "name": "signer", "type": "address"},
        ],
        "name": "BatchAnchored",
        "type": "event",
    },
]


@dataclass(frozen=True)
class BlockchainRuntimeConfig:
    configured: bool
    network: str
    network_label: str
    chain_id: int
    rpc_url: str | None
    contract_address: str | None
    signer_address: str | None
    issues: list[str]


def _network_label(network: str) -> str:
    if network == "sepolia":
        return "ETHEREUM SEPOLIA TESTNET"
    if network in ("anvil", "local", "localhost"):
        return "LOCAL DEVELOPMENT NETWORK"
    return network.upper()


def _build_explorer_url(network: str, tx_hash: str | None) -> str | None:
    if network == "sepolia" and tx_hash and _BYTES32_HEX_RE.match(tx_hash):
        return f"https://sepolia.etherscan.io/tx/{tx_hash}"
    return None


def _redact_secret(text: str, settings: Settings) -> str:
    msg = str(text)
    key = (settings.blockchain_signer_private_key or "").strip()
    if key:
        msg = msg.replace(key, "[REDACTED]")
        raw = key.removeprefix("0x")
        if raw:
            msg = msg.replace(raw, "[REDACTED]")
    return msg


def _normalize_bytes32(hex_value: str) -> bytes:
    clean = hex_value.strip().lower().removeprefix("0x")
    return bytes.fromhex(clean)


def _derive_signer_address(private_key: str | None) -> str | None:
    if not private_key or not private_key.strip():
        return None
    try:
        return Account.from_key(private_key.strip()).address
    except Exception:
        return None


def inspect_blockchain_config(
    settings: Settings, *, require_signer: bool = False
) -> BlockchainRuntimeConfig:
    network = settings.effective_blockchain_network
    chain_id = settings.effective_blockchain_chain_id
    rpc_url = settings.effective_blockchain_rpc_url
    raw_contract = (settings.blockchain_contract_address or "").strip()
    issues: list[str] = []

    if network == "mainnet":
        issues.append("Mainnet deployment is disabled in IPGuard MVP.")

    if not rpc_url:
        issues.append("Blockchain RPC URL is not configured.")

    contract_address: str | None = None
    if not raw_contract:
        issues.append("Blockchain contract address is not configured.")
    elif not Web3.is_address(raw_contract):
        issues.append("Blockchain contract address is invalid.")
    else:
        contract_address = Web3.to_checksum_address(raw_contract)

    signer_address: str | None = None
    if settings.blockchain_signer_private_key:
        signer_address = _derive_signer_address(settings.blockchain_signer_private_key)
        if signer_address is None:
            issues.append("Blockchain signer private key format is invalid.")
    elif require_signer:
        issues.append("Blockchain signer private key is not configured.")

    return BlockchainRuntimeConfig(
        configured=len(issues) == 0,
        network=network,
        network_label=_network_label(network),
        chain_id=chain_id,
        rpc_url=rpc_url,
        contract_address=contract_address,
        signer_address=signer_address,
        issues=issues,
    )


def default_web3_factory(rpc_url: str) -> Web3:
    return Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))


def _to_anchor_schema(row: AuditBlockchainAnchor) -> BlockchainAnchorRecord:
    return BlockchainAnchorRecord(
        id=str(row.id),
        audit_chain_id=row.audit_chain_id,
        from_sequence=row.from_sequence,
        to_sequence=row.to_sequence,
        event_count=row.event_count,
        merkle_root=row.merkle_root,
        head_hash=row.head_hash,
        batch_reference=row.batch_reference,
        network=row.network,
        chain_id=row.chain_id,
        contract_address=row.contract_address,
        signer_address=row.signer_address,
        tx_hash=row.tx_hash,
        block_number=row.block_number,
        block_timestamp=row.block_timestamp,
        status=row.status,
        explorer_url=_build_explorer_url(row.network, row.tx_hash),
        created_at=row.created_at,
        confirmed_at=row.confirmed_at,
        error_message=row.error_message,
    )


def _authorize_chain_scope(caller_device: Device, requested_chain_id: str | None) -> str:
    if requested_chain_id is None or not requested_chain_id.strip():
        return str(caller_device.device_id)
    cleaned = requested_chain_id.strip()
    if cleaned != caller_device.device_id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="audit_chain_forbidden",
            message="You may only access or anchor the audit chain bound to your active device.",
        )
    return cleaned


def get_blockchain_overview(
    db: Session,
    caller_device: Device,
    settings: Settings | None = None,
    requested_chain_id: str | None = None,
) -> BlockchainOverviewResponse:
    cfg_settings = settings or get_settings()
    audit_chain_id = _authorize_chain_scope(caller_device, requested_chain_id)
    rt = inspect_blockchain_config(cfg_settings, require_signer=False)

    chain_res = verify_audit_chain(db, chain_id=audit_chain_id)
    head = db.get(AuditChainHead, audit_chain_id)
    head_seq = head.last_sequence if head is not None else 0

    anchors = list(
        db.scalars(
            select(AuditBlockchainAnchor)
            .where(AuditBlockchainAnchor.audit_chain_id == audit_chain_id)
            .order_by(AuditBlockchainAnchor.created_at.desc(), AuditBlockchainAnchor.to_sequence.desc())
            .limit(10)
        ).all()
    )

    confirmed_anchors = list(
        db.scalars(
            select(AuditBlockchainAnchor).where(
                AuditBlockchainAnchor.audit_chain_id == audit_chain_id,
                AuditBlockchainAnchor.status == "CONFIRMED",
            )
        ).all()
    )
    last_anchored_seq = max((a.to_sequence for a in confirmed_anchors), default=0)
    total_anchored_events = sum(a.event_count for a in confirmed_anchors)
    pending_events = max(0, head_seq - last_anchored_seq)
    latest_anchor = _to_anchor_schema(anchors[0]) if anchors else None

    if not rt.configured:
        ui_status = "NOT_CONFIGURED"
    elif not chain_res.valid:
        ui_status = "INVALID_AUDIT_CHAIN"
    elif latest_anchor and latest_anchor.status == "SUBMITTED":
        ui_status = "SUBMITTED"
    elif pending_events > 0:
        ui_status = "READY"
    elif latest_anchor and latest_anchor.status == "FAILED":
        ui_status = "FAILED"
    elif confirmed_anchors:
        ui_status = "CONFIRMED"
    else:
        ui_status = "UP_TO_DATE"

    return BlockchainOverviewResponse(
        configured=rt.configured,
        network=rt.network,
        network_label=rt.network_label,
        chain_id=rt.chain_id,
        contract_address=rt.contract_address,
        signer_address=rt.signer_address,
        audit_chain_id=audit_chain_id,
        audit_chain_valid=chain_res.valid,
        audit_chain_reason=chain_res.reason_code,
        anchored_batch_count=len(confirmed_anchors),
        total_anchored_events=total_anchored_events,
        pending_events=pending_events,
        last_anchored_sequence=last_anchored_seq,
        latest_anchor=latest_anchor,
        recent_anchors=[_to_anchor_schema(a) for a in anchors],
        status=ui_status,
        configuration_issues=rt.issues,
    )


def anchor_audit_batch(
    db: Session,
    caller_device: Device,
    *,
    requested_chain_id: str | None = None,
    max_events: int | None = None,
    settings: Settings | None = None,
    web3_factory: Callable[[str], Web3] = default_web3_factory,
) -> BlockchainAnchorRecord:
    cfg_settings = settings or get_settings()
    audit_chain_id = _authorize_chain_scope(caller_device, requested_chain_id)

    # 1. Fail closed if blockchain RPC / contract / signer key is not configured
    rt = inspect_blockchain_config(cfg_settings, require_signer=True)
    if not rt.configured or not rt.rpc_url or not rt.contract_address:
        raise AppError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="blockchain_not_configured",
            message="Blockchain anchoring is not configured: " + "; ".join(rt.issues),
        )

    private_key = (cfg_settings.blockchain_signer_private_key or "").strip()
    signer_account = Account.from_key(private_key)

    # 2. Acquire exclusive database row lock on AuditChainHead to prevent concurrent
    #    overlapping batch submissions.
    dialect_name = db.bind.dialect.name if db.bind is not None else ""
    head_stmt = select(AuditChainHead).where(AuditChainHead.chain_id == audit_chain_id)
    if dialect_name == "postgresql":
        head_stmt = head_stmt.with_for_update()
    head = db.scalar(head_stmt)
    if head is None or head.last_sequence <= 0:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="audit_chain_empty",
            message=f"Audit chain '{audit_chain_id}' has no events to anchor.",
        )

    # 3. Verify complete PostgreSQL Audit Hash Chain BEFORE touching blockchain
    chain_verification = verify_audit_chain(db, chain_id=audit_chain_id)
    if not chain_verification.valid:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="audit_chain_invalid",
            message=(
                f"Audit chain verification failed at sequence "
                f"{chain_verification.mismatch_sequence}: {chain_verification.reason_code}. "
                "Invalid audit history cannot be anchored."
            ),
        )

    # 4. Prevent duplicate/overlapping/in-flight batches for the same network & contract
    in_flight = db.scalar(
        select(AuditBlockchainAnchor).where(
            AuditBlockchainAnchor.audit_chain_id == audit_chain_id,
            AuditBlockchainAnchor.network == rt.network,
            AuditBlockchainAnchor.contract_address == rt.contract_address,
            AuditBlockchainAnchor.status.in_(("PENDING", "SUBMITTED")),
        )
    )
    if in_flight is not None:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="anchor_batch_in_flight",
            message=(
                f"Batch {in_flight.from_sequence}-{in_flight.to_sequence} is currently "
                f"{in_flight.status}. Verify or reconcile that transaction before creating another."
            ),
        )

    confirmed_anchors = list(
        db.scalars(
            select(AuditBlockchainAnchor).where(
                AuditBlockchainAnchor.audit_chain_id == audit_chain_id,
                AuditBlockchainAnchor.network == rt.network,
                AuditBlockchainAnchor.contract_address == rt.contract_address,
                AuditBlockchainAnchor.status == "CONFIRMED",
            )
        ).all()
    )
    next_from_seq = max((a.to_sequence for a in confirmed_anchors), default=0) + 1

    batch_limit = max_events or cfg_settings.blockchain_default_batch_size
    events = list(
        db.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.chain_id == audit_chain_id,
                AuditEvent.sequence >= next_from_seq,
            )
            .order_by(AuditEvent.sequence.asc())
            .limit(batch_limit)
        ).all()
    )
    if not events:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="no_unanchored_events",
            message=f"All verified events (up to sequence {next_from_seq - 1}) are already anchored.",
        )

    try:
        batch = build_merkle_batch(
            events,
            expected_chain_id=audit_chain_id,
            expected_from_sequence=next_from_seq,
        )
    except MerkleBatchError as exc:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code=f"merkle_{exc.code}",
            message=exc.message,
        ) from exc

    # Reuse or insert PENDING record cleanly (handles previous FAILED attempt for exact same range)
    existing_failed = db.scalar(
        select(AuditBlockchainAnchor).where(
            AuditBlockchainAnchor.audit_chain_id == audit_chain_id,
            AuditBlockchainAnchor.from_sequence == batch.from_sequence,
            AuditBlockchainAnchor.to_sequence == batch.to_sequence,
            AuditBlockchainAnchor.network == rt.network,
            AuditBlockchainAnchor.contract_address == rt.contract_address,
        )
    )
    if existing_failed is not None:
        if existing_failed.status != "FAILED":
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="duplicate_anchor_batch",
                message="Anchor record for this exact sequence range already exists.",
            )
        anchor_row = existing_failed
        anchor_row.merkle_root = batch.merkle_root
        anchor_row.head_hash = batch.head_hash
        anchor_row.event_count = batch.event_count
        anchor_row.batch_reference = batch.batch_reference
        anchor_row.signer_address = signer_account.address
        anchor_row.tx_hash = None
        anchor_row.block_number = None
        anchor_row.block_timestamp = None
        anchor_row.status = "PENDING"
        anchor_row.error_message = None
    else:
        anchor_row = AuditBlockchainAnchor(
            audit_chain_id=batch.audit_chain_id,
            from_sequence=batch.from_sequence,
            to_sequence=batch.to_sequence,
            event_count=batch.event_count,
            merkle_root=batch.merkle_root,
            head_hash=batch.head_hash,
            batch_reference=batch.batch_reference,
            network=rt.network,
            chain_id=rt.chain_id,
            contract_address=rt.contract_address,
            signer_address=signer_account.address,
            status="PENDING",
        )
        db.add(anchor_row)
    db.commit()
    db.refresh(anchor_row)

    # 5. Connect to EVM RPC, verify chain ID + authorized signer, and submit transaction
    try:
        w3 = web3_factory(rt.rpc_url)
        if not w3.is_connected():
            raise ConnectionError("Unable to reach blockchain JSON-RPC endpoint.")
        rpc_chain_id = int(w3.eth.chain_id)
        if rpc_chain_id != rt.chain_id:
            raise ValueError(
                f"Connected RPC chain_id {rpc_chain_id} does not match expected {rt.chain_id}."
            )

        contract = w3.eth.contract(address=rt.contract_address, abi=BATCH_ANCHOR_REGISTRY_ABI)
        onchain_signer = contract.functions.authorizedSigner().call()
        if str(onchain_signer).lower() != signer_account.address.lower():
            raise PermissionError(
                f"Configured signer {signer_account.address} is not authorized on contract (expected {onchain_signer})."
            )

        audit_chain_b32 = _normalize_bytes32(batch.audit_chain_id_hash)
        merkle_b32 = _normalize_bytes32(batch.merkle_root)
        head_b32 = _normalize_bytes32(batch.head_hash)

        nonce = w3.eth.get_transaction_count(signer_account.address, "pending")
        fn_call = contract.functions.anchorBatch(
            audit_chain_b32,
            batch.from_sequence,
            batch.to_sequence,
            merkle_b32,
            head_b32,
        )
        tx_params: dict[str, Any] = {
            "from": signer_account.address,
            "nonce": nonce,
            "chainId": rt.chain_id,
        }
        gas_estimate = fn_call.estimate_gas(tx_params)
        tx_params["gas"] = int(gas_estimate * 1.2) + 20_000

        latest_block = w3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas")
        if base_fee is not None:
            priority_fee = w3.to_wei(1, "gwei")
            tx_params["maxPriorityFeePerGas"] = priority_fee
            tx_params["maxFeePerGas"] = int(base_fee) * 2 + priority_fee
        else:
            tx_params["gasPrice"] = w3.eth.gas_price

        built_tx = fn_call.build_transaction(tx_params)
        signed_tx = w3.eth.account.sign_transaction(built_tx, private_key=private_key)
        raw_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = "0x" + raw_hash.hex().removeprefix("0x")
    except PermissionError as exc:
        anchor_row.status = "FAILED"
        anchor_row.error_message = _redact_secret(str(exc), cfg_settings)
        db.commit()
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="blockchain_unauthorized_signer",
            message=anchor_row.error_message,
        ) from exc
    except ContractLogicError as exc:
        anchor_row.status = "FAILED"
        anchor_row.error_message = _redact_secret(str(exc), cfg_settings)
        db.commit()
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="blockchain_contract_revert",
            message=f"Smart contract rejected batch anchor: {anchor_row.error_message}",
        ) from exc
    except Exception as exc:
        anchor_row.status = "FAILED"
        anchor_row.error_message = _redact_secret(str(exc), cfg_settings)
        db.commit()
        raise AppError(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="blockchain_submission_failed",
            message=f"Blockchain submission failed: {anchor_row.error_message}",
        ) from exc

    # Persist tx_hash with SUBMITTED state BEFORE waiting for receipt
    anchor_row.tx_hash = tx_hash_hex
    anchor_row.status = "SUBMITTED"
    anchor_row.error_message = None
    db.commit()
    db.refresh(anchor_row)

    # 6. Wait for transaction receipt within bounded timeout
    try:
        receipt = w3.eth.wait_for_transaction_receipt(
            tx_hash_hex, timeout=cfg_settings.blockchain_receipt_timeout_seconds
        )
    except TimeExhausted:
        anchor_row.error_message = (
            "Transaction submitted but receipt confirmation timed out. "
            "Run Verify On-Chain to reconcile status without resubmitting."
        )
        db.commit()
        db.refresh(anchor_row)
        return _to_anchor_schema(anchor_row)
    except Exception as exc:
        anchor_row.error_message = (
            f"Submitted tx {tx_hash_hex}; receipt lookup error: {_redact_secret(str(exc), cfg_settings)}"
        )
        db.commit()
        db.refresh(anchor_row)
        return _to_anchor_schema(anchor_row)

    if int(receipt["status"]) != 1:
        anchor_row.status = "FAILED"
        anchor_row.block_number = int(receipt["blockNumber"])
        anchor_row.error_message = "Blockchain transaction reverted on-chain (receipt status = 0)."
        db.commit()
        raise AppError(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="blockchain_tx_reverted",
            message=anchor_row.error_message,
        )

    block_info = w3.eth.get_block(int(receipt["blockNumber"]))
    block_ts = datetime.fromtimestamp(int(block_info["timestamp"]), tz=timezone.utc)

    # Verify stored on-chain commitment right after confirmation
    onchain_ok = bool(
        contract.functions.verifyBatch(
            _normalize_bytes32(batch.audit_chain_id_hash),
            batch.from_sequence,
            batch.to_sequence,
            _normalize_bytes32(batch.merkle_root),
            _normalize_bytes32(batch.head_hash),
        ).call()
    )
    if not onchain_ok:
        anchor_row.status = "FAILED"
        anchor_row.block_number = int(receipt["blockNumber"])
        anchor_row.block_timestamp = block_ts
        anchor_row.error_message = "On-chain post-confirmation commitment verification returned false."
        db.commit()
        raise AppError(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="blockchain_verification_mismatch",
            message=anchor_row.error_message,
        )

    anchor_row.status = "CONFIRMED"
    anchor_row.block_number = int(receipt["blockNumber"])
    anchor_row.block_timestamp = block_ts
    anchor_row.confirmed_at = datetime.now(timezone.utc)
    anchor_row.error_message = None
    db.commit()
    db.refresh(anchor_row)
    return _to_anchor_schema(anchor_row)


def verify_blockchain_anchor(
    db: Session,
    caller_device: Device,
    anchor_id: uuid.UUID,
    *,
    settings: Settings | None = None,
    web3_factory: Callable[[str], Web3] = default_web3_factory,
) -> AnchorVerifyResponse:
    cfg_settings = settings or get_settings()
    row = db.get(AuditBlockchainAnchor, anchor_id)
    if row is None or row.audit_chain_id != caller_device.device_id:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="anchor_not_found",
            message="Blockchain anchor record not found for your device chain.",
        )

    # 1. Re-verify PostgreSQL audit chain & recompute local Merkle root for this range
    chain_res = verify_audit_chain(db, chain_id=row.audit_chain_id)
    local_match = False
    if chain_res.valid:
        slice_events = list(
            db.scalars(
                select(AuditEvent)
                .where(
                    AuditEvent.chain_id == row.audit_chain_id,
                    AuditEvent.sequence >= row.from_sequence,
                    AuditEvent.sequence <= row.to_sequence,
                )
                .order_by(AuditEvent.sequence.asc())
            ).all()
        )
        if len(slice_events) == row.event_count:
            try:
                recomputed = build_merkle_batch(
                    slice_events,
                    expected_chain_id=row.audit_chain_id,
                    expected_from_sequence=row.from_sequence,
                )
                local_match = (
                    recomputed.merkle_root.lower() == row.merkle_root.lower()
                    and recomputed.head_hash.lower() == row.head_hash.lower()
                )
            except MerkleBatchError:
                local_match = False

    rt = inspect_blockchain_config(cfg_settings, require_signer=False)
    if not rt.rpc_url or not rt.contract_address:
        return AnchorVerifyResponse(
            anchor_id=str(row.id),
            verified=False,
            status=row.status,
            audit_chain_id=row.audit_chain_id,
            from_sequence=row.from_sequence,
            to_sequence=row.to_sequence,
            event_count=row.event_count,
            merkle_root=row.merkle_root,
            head_hash=row.head_hash,
            network=row.network,
            network_label=_network_label(row.network),
            chain_id=row.chain_id,
            contract_address=row.contract_address,
            tx_hash=row.tx_hash,
            block_number=row.block_number,
            explorer_url=_build_explorer_url(row.network, row.tx_hash),
            checks=AnchorVerificationChecks(
                db_record_present=True,
                audit_chain_valid=chain_res.valid,
                local_merkle_recomputed_match=local_match,
                tx_receipt_confirmed=False,
                onchain_contract_match=False,
                reorg_check_passed=False,
            ),
            reason="Blockchain RPC URL or contract address is not configured for on-chain lookup.",
        )

    tx_receipt_ok = False
    onchain_match = False
    reorg_ok = True
    reason: str | None = None

    try:
        w3 = web3_factory(rt.rpc_url)
        if not w3.is_connected():
            raise ConnectionError("Blockchain RPC endpoint is unreachable.")
        if row.tx_hash:
            try:
                receipt = w3.eth.get_transaction_receipt(row.tx_hash)
                if int(receipt["status"]) == 1:
                    tx_receipt_ok = True
                    mined_block = int(receipt["blockNumber"])
                    if row.status == "SUBMITTED":
                        block_info = w3.eth.get_block(mined_block)
                        row.block_number = mined_block
                        row.block_timestamp = datetime.fromtimestamp(
                            int(block_info["timestamp"]), tz=timezone.utc
                        )
                        row.confirmed_at = datetime.now(timezone.utc)
                        row.status = "CONFIRMED"
                        row.error_message = None
                        db.commit()
                    elif row.block_number is not None and row.block_number != mined_block:
                        row.status = "REORGED"
                        reorg_ok = False
                        reason = f"Block number shifted from {row.block_number} to {mined_block}."
                        db.commit()
                else:
                    reason = "On-chain transaction receipt reported status 0 (reverted)."
            except TransactionNotFound:
                if row.status == "CONFIRMED":
                    row.status = "REORGED"
                    reorg_ok = False
                    reason = "Previously confirmed transaction was not found on current canonical chain."
                    db.commit()
                else:
                    reorg_ok = False
                    reason = "Submitted transaction is still pending or not found on RPC."

        chain_b32 = _normalize_bytes32(compute_audit_chain_id_bytes32(row.audit_chain_id))
        merkle_b32 = _normalize_bytes32(row.merkle_root)
        head_b32 = _normalize_bytes32(row.head_hash)
        contract = w3.eth.contract(address=Web3.to_checksum_address(row.contract_address), abi=BATCH_ANCHOR_REGISTRY_ABI)
        onchain_match = bool(
            contract.functions.verifyBatch(
                chain_b32,
                row.from_sequence,
                row.to_sequence,
                merkle_b32,
                head_b32,
            ).call()
        )
        if not onchain_match and reason is None:
            reason = "On-chain contract storage does not match local Merkle root or head hash."
    except Exception as exc:
        reason = f"Verification RPC lookup failed: {_redact_secret(str(exc), cfg_settings)}"
        reorg_ok = False

    verified = (
        chain_res.valid
        and local_match
        and tx_receipt_ok
        and onchain_match
        and reorg_ok
    )
    if not chain_res.valid and reason is None:
        reason = f"Local audit chain invalid ({chain_res.reason_code})."
    elif not local_match and reason is None:
        reason = "Recomputed local Merkle root differs from anchored commitment."

    return AnchorVerifyResponse(
        anchor_id=str(row.id),
        verified=verified,
        status=row.status,
        audit_chain_id=row.audit_chain_id,
        from_sequence=row.from_sequence,
        to_sequence=row.to_sequence,
        event_count=row.event_count,
        merkle_root=row.merkle_root,
        head_hash=row.head_hash,
        network=row.network,
        network_label=_network_label(row.network),
        chain_id=row.chain_id,
        contract_address=row.contract_address,
        tx_hash=row.tx_hash,
        block_number=row.block_number,
        explorer_url=_build_explorer_url(row.network, row.tx_hash),
        checks=AnchorVerificationChecks(
            db_record_present=True,
            audit_chain_valid=chain_res.valid,
            local_merkle_recomputed_match=local_match,
            tx_receipt_confirmed=tx_receipt_ok,
            onchain_contract_match=onchain_match,
            reorg_check_passed=reorg_ok,
        ),
        reason=reason,
    )
