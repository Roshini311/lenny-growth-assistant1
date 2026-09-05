import uuid
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Artifact as DBArtifact
from app.services.artifacts.schemas import ArtifactType, ArtifactCreate
from app.services.artifacts.sanitizer import ArtifactSanitizer

from datetime import datetime, timezone

logger = logging.getLogger("lenny_assistant.services.artifacts.service")


class ArtifactService:
    """Service for managing, sanitizing, and persisting backend Artifacts."""

    def __init__(self, sanitizer: Optional[ArtifactSanitizer] = None):
        self.sanitizer = sanitizer or ArtifactSanitizer()

    async def create_artifact(
        self,
        db: AsyncSession,
        title: str,
        content: str,
        session_id: Optional[uuid.UUID] = None,
        artifact_type: ArtifactType | str = ArtifactType.MARKDOWN,
        message_id: Optional[uuid.UUID] = None,
    ) -> DBArtifact:
        """Sanitizes content and persists Artifact into database."""
        if not title or not title.strip():
            raise ValueError("Artifact title cannot be empty.")
        if not content or not content.strip():
            raise ValueError("Artifact content cannot be empty.")

        # Sanitize content
        sanitized_content = self.sanitizer.sanitize(content, artifact_type)

        type_str = artifact_type.value if hasattr(artifact_type, "value") else str(artifact_type)

        now = datetime.now(timezone.utc)
        artifact = DBArtifact(
            id=uuid.uuid4(),
            session_id=session_id,
            message_id=message_id,
            artifact_type=type_str.lower(),
            title=title.strip(),
            content=sanitized_content,
            created_at=now,
            updated_at=now,
        )

        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)

        logger.info(f"Persisted artifact '{artifact.id}' (type={artifact.artifact_type}) for session '{session_id}'")
        return artifact

    async def get_artifact(
        self,
        db: AsyncSession,
        artifact_id: uuid.UUID,
    ) -> Optional[DBArtifact]:
        """Retrieves artifact by primary key UUID."""
        result = await db.execute(select(DBArtifact).where(DBArtifact.id == artifact_id))
        return result.scalar_one_or_none()

    async def list_session_artifacts(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> List[DBArtifact]:
        """Retrieves all artifacts for a given session ordered by created_at DESC."""
        result = await db.execute(
            select(DBArtifact)
            .where(DBArtifact.session_id == session_id)
            .order_by(DBArtifact.created_at.desc())
        )
        return list(result.scalars().all())
