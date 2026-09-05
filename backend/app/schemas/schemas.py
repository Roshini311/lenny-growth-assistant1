from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ArtifactBase(BaseModel):
    artifact_type: str = Field(..., description="'markdown' or 'html'")
    title: str
    content: str


class ArtifactCreate(ArtifactBase):
    session_id: UUID
    message_id: Optional[UUID] = None


class ArtifactResponse(ArtifactBase):
    id: UUID
    session_id: UUID
    message_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageBase(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str
    provider: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None


class MessageCreate(MessageBase):
    session_id: UUID


class MessageResponse(MessageBase):
    id: UUID
    session_id: UUID
    created_at: datetime
    artifacts: Optional[List[ArtifactResponse]] = []

    model_config = ConfigDict(from_attributes=True)


class SessionBase(BaseModel):
    title: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionResponse(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []
    artifacts: List[ArtifactResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TranscriptChunkBase(BaseModel):
    guest: str
    episode_title: str
    publish_date: Optional[str] = None
    timestamp: Optional[str] = None
    speaker: Optional[str] = None
    chunk_text: str
    source_url: Optional[str] = None


class TranscriptChunkResponse(TranscriptChunkBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
