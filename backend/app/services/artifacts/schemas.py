from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"


class ArtifactCreate(BaseModel):
    session_id: Optional[UUID] = Field(default=None, description="Parent session UUID.")
    message_id: Optional[UUID] = Field(default=None, description="Optional parent message UUID.")
    artifact_type: ArtifactType = Field(..., description="Artifact content type: 'markdown' or 'html'.")
    title: str = Field(..., max_length=255, description="Artifact title.")
    content: str = Field(..., description="Raw artifact content.")


class ArtifactResponse(BaseModel):
    id: UUID = Field(..., description="Artifact UUID.")
    session_id: UUID = Field(..., description="Parent session UUID.")
    message_id: Optional[UUID] = Field(default=None, description="Parent message UUID.")
    artifact_type: str = Field(..., description="Artifact content type.")
    title: str = Field(..., description="Artifact title.")
    content: str = Field(..., description="Sanitized artifact content.")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
