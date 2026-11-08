"""
IPGuard Milestone 3 — Secure Notes API Routes.
Provides hardware-authenticated CRUD operations for super-encrypted digital notes.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner_id
from app.db.session import get_db
from app.schemas.common import ErrorResponse
from app.schemas.note import NoteCreateRequest, NoteResponse, NoteUpdateRequest
from app.services import notes as notes_service

router = APIRouter()

STANDARD_ERRORS = {
    401: {"model": ErrorResponse, "description": "Unauthorized. Missing, expired, or unapproved session."},
    403: {"model": ErrorResponse, "description": "Forbidden. Associated device is revoked."},
}

NOT_FOUND_ERRORS = {
    **STANDARD_ERRORS,
    404: {"model": ErrorResponse, "description": "Note not found or does not belong to the authenticated owner."},
}


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new super-encrypted note",
    responses=STANDARD_ERRORS,
)
def create_new_note(
    body: NoteCreateRequest,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_owner_id),
) -> NoteResponse:
    """Create a new note encrypted with AES-256-GCM + Vigenère bound to the authenticated owner."""
    return notes_service.create_note(db=db, owner_id=owner_id, request=body)


@router.get(
    "",
    response_model=list[NoteResponse],
    summary="List all notes owned by the authenticated caller",
    responses=STANDARD_ERRORS,
)
def get_all_notes(
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_owner_id),
) -> list[NoteResponse]:
    """Retrieve and decrypt all notes owned by the caller's authenticated device."""
    return notes_service.list_notes(db=db, owner_id=owner_id)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get and decrypt a single note by ID",
    responses=NOT_FOUND_ERRORS,
)
def get_single_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_owner_id),
) -> NoteResponse:
    """Retrieve and decrypt a specific note with strict owner isolation."""
    return notes_service.get_note(db=db, owner_id=owner_id, note_id=note_id)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update an existing note",
    responses=NOT_FOUND_ERRORS,
)
def update_existing_note(
    note_id: uuid.UUID,
    body: NoteUpdateRequest,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_owner_id),
) -> NoteResponse:
    """Update title and/or content with atomic row-level locking and re-encryption."""
    return notes_service.update_note(db=db, owner_id=owner_id, note_id=note_id, request=body)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a note",
    responses=NOT_FOUND_ERRORS,
)
def delete_existing_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_owner_id),
) -> None:
    """Permanently delete a note with atomic row-level locking."""
    notes_service.delete_note(db=db, owner_id=owner_id, note_id=note_id)
