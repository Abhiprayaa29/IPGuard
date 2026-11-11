"""M5 Blockchain Batch Audit Anchoring API routes."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_authenticated_device
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.auth import Device
from app.schemas.blockchain import (
    AnchorBatchRequest,
    AnchorVerifyResponse,
    BlockchainAnchorRecord,
    BlockchainOverviewResponse,
)
from app.schemas.common import ErrorResponse
from app.services import blockchain as blockchain_service

router = APIRouter()

AUTH_ERRORS = {
    401: {"model": ErrorResponse, "description": "Unauthorized hardware session."},
    403: {"model": ErrorResponse, "description": "Forbidden or revoked device."},
}


@router.get(
    "/anchors",
    response_model=BlockchainOverviewResponse,
    summary="Get M5 blockchain anchoring overview and batch history",
    responses=AUTH_ERRORS,
)
def get_anchors_overview(
    audit_chain_id: str | None = Query(default=None, max_length=64),
    db: Session = Depends(get_db),
    caller_device: Device = Depends(get_current_authenticated_device),
    settings: Settings = Depends(get_settings),
) -> BlockchainOverviewResponse:
    return blockchain_service.get_blockchain_overview(
        db=db,
        caller_device=caller_device,
        settings=settings,
        requested_chain_id=audit_chain_id,
    )


@router.post(
    "/anchors",
    response_model=BlockchainAnchorRecord,
    summary="Verify audit chain, build Merkle batch, and anchor commitment on-chain",
    responses={
        **AUTH_ERRORS,
        409: {"model": ErrorResponse, "description": "Audit chain invalid, empty, or batch conflict."},
        502: {"model": ErrorResponse, "description": "Blockchain RPC or transaction failure."},
        503: {"model": ErrorResponse, "description": "Blockchain integration not configured."},
    },
)
def create_anchor_batch(
    body: AnchorBatchRequest | None = None,
    db: Session = Depends(get_db),
    caller_device: Device = Depends(get_current_authenticated_device),
    settings: Settings = Depends(get_settings),
) -> BlockchainAnchorRecord:
    req = body or AnchorBatchRequest()
    return blockchain_service.anchor_audit_batch(
        db=db,
        caller_device=caller_device,
        requested_chain_id=req.audit_chain_id,
        max_events=req.max_events,
        settings=settings,
    )


@router.get(
    "/anchors/{anchor_id}/verify",
    response_model=AnchorVerifyResponse,
    summary="Verify stored DB anchor commitment against on-chain BatchAnchorRegistry",
    responses={
        **AUTH_ERRORS,
        404: {"model": ErrorResponse, "description": "Anchor record not found."},
    },
)
def verify_anchor_batch(
    anchor_id: uuid.UUID,
    db: Session = Depends(get_db),
    caller_device: Device = Depends(get_current_authenticated_device),
    settings: Settings = Depends(get_settings),
) -> AnchorVerifyResponse:
    return blockchain_service.verify_blockchain_anchor(
        db=db,
        caller_device=caller_device,
        anchor_id=anchor_id,
        settings=settings,
    )
