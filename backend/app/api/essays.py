import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.chat import get_or_create_session
from app.config import settings
from app.agents.skills.ship30 import Ship30EssayGenerator
from app.services.artifacts import ArtifactService, ArtifactType, ArtifactResponse

logger = logging.getLogger("lenny_assistant.api.essays")

router = APIRouter(prefix="/api", tags=["Essays & Artifacts"])


class Ship30Request(BaseModel):
    topic: str = Field(..., description="Essay topic or prompt for Ship30 framework.")
    session_id: Optional[str] = Field(default=None, description="Optional session UUID string.")
    provider: Optional[str] = Field(default=None, description="LLM provider: 'ollama', 'openai', or 'claude'.")
    artifact_type: ArtifactType = Field(default=ArtifactType.MARKDOWN, description="Artifact type: 'markdown' or 'html'.")
    top_k: Optional[int] = Field(default=None, description="Override default retrieval top_k.")
    distance_threshold: Optional[float] = Field(default=None, description="Override default distance threshold.")


class Ship30EssayResponse(BaseModel):
    topic: str = Field(..., description="Essay topic.")
    sufficient: bool = Field(..., description="Whether retrieved evidence met distance threshold (<0.4).")
    essay: str = Field(..., description="Generated essay or fallback string.")
    citations: List[str] = Field(default_factory=list, description="Evidence citations.")
    artifact: Optional[ArtifactResponse] = Field(default=None, description="Persisted artifact if sufficient.")


@router.post("/essays/ship30", response_model=Ship30EssayResponse, status_code=status.HTTP_201_CREATED)
async def generate_ship30_essay_endpoint(
    req: Ship30Request,
    db: AsyncSession = Depends(get_db),
):
    """POST /api/essays/ship30 generates a grounded Ship30 essay and persists it as an Artifact when sufficient."""
    if not req.topic or not req.topic.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Essay topic cannot be empty.",
        )

    # 1. Resolve DB Session
    db_session = await get_or_create_session(db, req.session_id)

    # 2. Generate grounded Ship30 essay
    generator = Ship30EssayGenerator()
    try:
        essay_res = await generator.generate_essay(
            db=db,
            topic=req.topic.strip(),
            provider_name=req.provider,
            top_k=req.top_k,
            distance_threshold=req.distance_threshold,
        )
    except Exception as e:
        logger.error(f"Ship30 generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ship30 essay generation failed: {e}",
        )

    # If insufficient evidence, do NOT create an artifact in DB
    if not essay_res.get("sufficient", True):
        return Ship30EssayResponse(
            topic=req.topic.strip(),
            sufficient=False,
            essay=essay_res["content"],
            citations=[],
            artifact=None,
        )

    # 3. Create & persist sanitized Artifact only when evidence is sufficient
    artifact_service = ArtifactService()
    try:
        artifact = await artifact_service.create_artifact(
            db=db,
            session_id=db_session.id,
            title=essay_res["title"],
            content=essay_res["content"],
            artifact_type=req.artifact_type,
        )
    except Exception as e:
        logger.error(f"Artifact creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist artifact: {e}",
        )

    return Ship30EssayResponse(
        topic=req.topic.strip(),
        sufficient=True,
        essay=essay_res["content"],
        citations=essay_res.get("citations", []),
        artifact=ArtifactResponse.model_validate(artifact),
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact_endpoint(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
):
    """GET /api/artifacts/{artifact_id} retrieves a persisted artifact by UUID."""
    try:
        artifact_uuid = uuid.UUID(artifact_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid artifact UUID string format.",
        )

    artifact_service = ArtifactService()
    artifact = await artifact_service.get_artifact(db, artifact_uuid)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_id}' not found.",
        )

    return artifact


@router.get("/sessions/{session_id}/artifacts", response_model=List[ArtifactResponse])
async def list_session_artifacts_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """GET /api/sessions/{session_id}/artifacts retrieves all artifacts for a session."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session UUID string format.",
        )

    artifact_service = ArtifactService()
    return await artifact_service.list_session_artifacts(db, session_uuid)
