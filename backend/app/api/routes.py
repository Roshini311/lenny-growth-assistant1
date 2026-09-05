import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text, select
from app.config import settings
from app.db.database import AsyncSessionLocal
from app.models.models import Session as DBSession

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health monitoring endpoint with lightweight async database probe."""
    db_status = {"configured": bool(settings.DATABASE_URL), "connected": False}
    
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_status["connected"] = True
    except Exception as e:
        db_status["connected"] = False
        db_status["details"] = str(e)

    return {
        "status": "healthy" if db_status["connected"] else "degraded",
        "environment": settings.APP_ENV,
        "default_provider": settings.DEFAULT_LLM_PROVIDER,
        "database": db_status,
        "providers": {
            "ollama_base_url": settings.OLLAMA_BASE_URL,
            "openai_configured": bool(settings.OPENAI_API_KEY),
        }
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session_endpoint():
    """POST /api/sessions initializes a new session UUID."""
    async with AsyncSessionLocal() as session:
        new_session = DBSession(id=uuid.uuid4())
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)
        return {"id": str(new_session.id), "created_at": new_session.created_at}


@router.get("/sessions/{session_id}")
async def get_session_endpoint(session_id: str):
    """GET /api/sessions/{session_id} retrieves session details by UUID."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session UUID string format.",
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DBSession).where(DBSession.id == session_uuid))
        db_session = result.scalar_one_or_none()
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )
        return {"id": str(db_session.id), "created_at": db_session.created_at}

