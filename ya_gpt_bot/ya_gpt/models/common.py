"""Common models for art and text generation are defined here."""

from typing import Any

from pydantic import BaseModel, Field


class AsyncGenerationOperationResponse(BaseModel):
    """Asyncronous generation request polling result."""

    id: str
    description: str
    created_at: str | None = Field(alias="createdAt")
    created_by: str | None = Field(alias="createdBy")
    modified_at: str | None = Field(alias="modifiedAt")
    done: bool
    metadata: dict[str, Any] | None
    response: dict[str, Any] | None = None
