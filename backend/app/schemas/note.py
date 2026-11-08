import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NoteCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Plaintext title of the note before client/server super-encryption",
    )
    content: str = Field(
        min_length=1,
        max_length=50000,
        description="Plaintext content of the note before client/server super-encryption",
    )


class NoteUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated plaintext title",
    )
    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=50000,
        description="Updated plaintext content",
    )

    @model_validator(mode="after")
    def at_least_one_field(self) -> "NoteUpdateRequest":
        if self.title is None and self.content is None:
            raise ValueError("At least one field ('title' or 'content') must be provided for update.")
        return self


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Unique note identifier (UUID)")
    title: str = Field(description="Decrypted plaintext title returned to authorized owner")
    content: str = Field(description="Decrypted plaintext content returned to authorized owner")
    created_at: datetime = Field(description="Timestamp when note was created")
    updated_at: datetime = Field(description="Timestamp when note was last updated")
