"""
IPGuard Milestone 3 — Secure Notes Service Layer.
Handles database persistence, row-level locking, and super-encryption orchestration.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.note import Note
from app.schemas.note import NoteCreateRequest, NoteResponse, NoteUpdateRequest
from app.services.note_crypto import decrypt_note, encrypt_note


def create_note(
    db: Session,
    owner_id: str,
    request: NoteCreateRequest,
) -> NoteResponse:
    """Create a new super-encrypted note for the authenticated owner."""
    title_enc = encrypt_note(request.title, owner_id=owner_id)
    content_enc = encrypt_note(request.content, owner_id=owner_id)

    note = Note(
        owner_id=owner_id,
        title_enc=title_enc,
        content_enc=content_enc,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return NoteResponse(
        id=note.id,
        title=request.title,
        content=request.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def list_notes(
    db: Session,
    owner_id: str,
) -> list[NoteResponse]:
    """Retrieve and decrypt all notes owned by the authenticated owner."""
    stmt = (
        select(Note)
        .where(Note.owner_id == owner_id)
        .order_by(desc(Note.updated_at))
    )
    notes = db.scalars(stmt).all()

    results: list[NoteResponse] = []
    for note in notes:
        title = decrypt_note(note.title_enc, owner_id=owner_id)
        content = decrypt_note(note.content_enc, owner_id=owner_id)
        results.append(
            NoteResponse(
                id=note.id,
                title=title,
                content=content,
                created_at=note.created_at,
                updated_at=note.updated_at,
            )
        )
    return results


def get_note(
    db: Session,
    owner_id: str,
    note_id: uuid.UUID,
) -> NoteResponse:
    """Retrieve and decrypt a single note by ID with strict ownership validation."""
    stmt = select(Note).where(Note.id == note_id, Note.owner_id == owner_id)
    note = db.scalar(stmt)
    if not note:
        raise AppError(
            status_code=404,
            code="note_not_found",
            message="Note not found.",
        )

    title = decrypt_note(note.title_enc, owner_id=owner_id)
    content = decrypt_note(note.content_enc, owner_id=owner_id)

    return NoteResponse(
        id=note.id,
        title=title,
        content=content,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def update_note(
    db: Session,
    owner_id: str,
    note_id: uuid.UUID,
    request: NoteUpdateRequest,
) -> NoteResponse:
    """
    Update an existing note with row-level locking (SELECT ... FOR UPDATE).
    Re-encrypts modified fields and updates timestamp.
    """
    stmt = (
        select(Note)
        .where(Note.id == note_id, Note.owner_id == owner_id)
        .with_for_update()
    )
    note = db.scalar(stmt)
    if not note:
        raise AppError(
            status_code=404,
            code="note_not_found",
            message="Note not found.",
        )

    updated_title = (
        request.title
        if request.title is not None
        else decrypt_note(note.title_enc, owner_id=owner_id)
    )
    updated_content = (
        request.content
        if request.content is not None
        else decrypt_note(note.content_enc, owner_id=owner_id)
    )

    if request.title is not None:
        note.title_enc = encrypt_note(request.title, owner_id=owner_id)
    if request.content is not None:
        note.content_enc = encrypt_note(request.content, owner_id=owner_id)

    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)

    return NoteResponse(
        id=note.id,
        title=updated_title,
        content=updated_content,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def delete_note(
    db: Session,
    owner_id: str,
    note_id: uuid.UUID,
) -> None:
    """
    Permanently delete a note with row-level locking (SELECT ... FOR UPDATE).
    Fails closed if the note does not exist or belongs to another owner.
    """
    stmt = (
        select(Note)
        .where(Note.id == note_id, Note.owner_id == owner_id)
        .with_for_update()
    )
    note = db.scalar(stmt)
    if not note:
        raise AppError(
            status_code=404,
            code="note_not_found",
            message="Note not found.",
        )

    db.delete(note)
    db.commit()
