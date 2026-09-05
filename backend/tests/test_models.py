import uuid
from datetime import datetime, timezone
from app.models.models import Session, Message, Artifact, TranscriptChunk
from app.schemas.schemas import (
    SessionCreate,
    SessionResponse,
    MessageCreate,
    MessageResponse,
    ArtifactCreate,
    ArtifactResponse,
)


def test_session_model_instantiation():
    """Verify Session model default fields and attributes."""
    session = Session(title="Growth Playbook Chat")
    assert session.title == "Growth Playbook Chat"
    assert session.id is None or isinstance(session.id, uuid.UUID)


def test_message_model_instantiation():
    """Verify Message model fields and role validation."""
    session_id = uuid.uuid4()
    msg = Message(
        session_id=session_id,
        role="user",
        content="How did Brian Chesky change product management?",
        provider="openai",
        sources=[{"guest": "Brian Chesky", "timestamp": "00:01:27"}]
    )
    assert msg.session_id == session_id
    assert msg.role == "user"
    assert msg.content == "How did Brian Chesky change product management?"
    assert msg.provider == "openai"
    assert len(msg.sources) == 1
    assert msg.sources[0]["guest"] == "Brian Chesky"


def test_artifact_model_instantiation():
    """Verify Artifact model attributes and types."""
    session_id = uuid.uuid4()
    artifact = Artifact(
        session_id=session_id,
        artifact_type="markdown",
        title="Airbnb Growth Summary",
        content="# Airbnb Growth\n\n- Built on word of mouth."
    )
    assert artifact.session_id == session_id
    assert artifact.artifact_type == "markdown"
    assert artifact.title == "Airbnb Growth Summary"
    assert "# Airbnb Growth" in artifact.content


def test_transcript_chunk_embedding_vector_dimensions():
    """Verify TranscriptChunk accepts 384-dimensional embeddings (sentence-transformers/all-MiniLM-L6-v2)."""
    embedding_vector = [0.1] * 384
    chunk = TranscriptChunk(
        guest="Brian Chesky",
        episode_title="Brian Chesky's new playbook",
        publish_date="2023-11-12",
        timestamp="00:01:27",
        speaker="Brian Chesky",
        chunk_text="Leaders should be in the details of the product.",
        source_url="https://www.youtube.com/watch?v=4ef0juAMqoE",
        embedding=embedding_vector
    )
    assert chunk.guest == "Brian Chesky"
    assert len(chunk.embedding) == 384
    assert chunk.embedding[0] == 0.1


def test_pydantic_schemas():
    """Verify Pydantic v2 schemas validation."""
    sess_create = SessionCreate(title="Test Session")
    assert sess_create.title == "Test Session"

    sess_resp = SessionResponse(
        id=uuid.uuid4(),
        title="Test Session",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    assert isinstance(sess_resp.id, uuid.UUID)

    msg_create = MessageCreate(
        session_id=sess_resp.id,
        role="assistant",
        content="Grounded response from transcript context."
    )
    assert msg_create.role == "assistant"
    assert msg_create.session_id == sess_resp.id


if __name__ == "__main__":
    test_session_model_instantiation()
    test_message_model_instantiation()
    test_artifact_model_instantiation()
    test_transcript_chunk_embedding_vector_dimensions()
    test_pydantic_schemas()
    print("[OK] Phase 3 Database & Model unit tests passed successfully!")
