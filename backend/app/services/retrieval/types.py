from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field

FALLBACK_MESSAGE: str = "I do not have sufficient information in Lenny's podcast archive to answer this."


class RetrievalChunk(BaseModel):
    """Structured representation of a retrieved transcript chunk with provenance metadata."""

    chunk_id: UUID
    episode_title: str
    guest: str
    publish_date: Optional[str] = None
    timestamp: Optional[str] = None
    speaker: Optional[str] = None
    chunk_text: str
    source_url: Optional[str] = None
    distance: float = Field(..., description="Cosine distance value (smaller = better match)")

    def to_citation_string(self) -> str:
        """Returns citation-ready format: [Episode: Guest Name, Timestamp/Topic]."""
        ts_part = self.timestamp if self.timestamp else "Topic"
        return f"[Episode: {self.guest}, {ts_part}]"


class RetrievalResult(BaseModel):
    """Raw vector search retrieval result prior to threshold grounding."""

    query: str
    top_k: int
    distance_threshold: float
    results: List[RetrievalChunk]
    execution_time_ms: float


class GroundingResult(BaseModel):
    """Grounding context payload delivered to future LLM / Agent layer."""

    query: str
    sufficient: bool
    results: List[RetrievalChunk]
    context: str
    citations: List[str]
    fallback_message: Optional[str] = None
