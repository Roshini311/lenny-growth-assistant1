import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Session(Base):
    """Persistent chat session container."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    artifacts = relationship(
        "Artifact",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Artifact.created_at"
    )


class Message(Base):
    """Dialogue message within a chat session."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String(50), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    provider = Column(String(50), nullable=True)  # "ollama", "openai"
    sources = Column(JSONB().with_variant(JSON(), "sqlite"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="messages")
    artifacts = relationship(
        "Artifact",
        back_populates="message",
        cascade="all, delete-orphan"
    )


class Artifact(Base):
    """Generated Markdown or HTML/CSS visual artifact."""
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    artifact_type = Column(String(50), nullable=False)  # "markdown", "html"
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="artifacts")
    message = relationship("Message", back_populates="artifacts")


class TranscriptChunk(Base):
    """Chunked Lenny's Podcast transcript with vector embedding for RAG retrieval."""
    __tablename__ = "transcript_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_hash = Column(String(64), nullable=False, unique=True, index=True)
    guest = Column(String(255), nullable=False, index=True)
    episode_title = Column(String(255), nullable=False, index=True)
    publish_date = Column(String(50), nullable=True)
    timestamp = Column(String(50), nullable=True)
    speaker = Column(String(255), nullable=True)
    chunk_text = Column(Text, nullable=False)
    source_url = Column(String(500), nullable=True)
    embedding = Column(ARRAY(Float), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
