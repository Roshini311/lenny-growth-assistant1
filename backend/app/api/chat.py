import json
import uuid
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db, AsyncSessionLocal
from app.models.models import Session as DBSession, Message as DBMessage
from app.config import settings
from app.services.retrieval import RetrievalService, GroundingResult, FALLBACK_MESSAGE
from app.agents.prompts import SYSTEM_PROMPT
from app.providers import (
    ProviderFactory,
    BaseLLMProvider,
    OllamaProviderUnavailableError,
    OpenAIProviderConfigurationError,
)

logger = logging.getLogger("lenny_assistant.api.chat")

router = APIRouter(prefix="/api", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or prompt.")
    session_id: Optional[str] = Field(default=None, description="Session UUID string. Auto-created if omitted.")
    provider: Optional[str] = Field(default=None, description="LLM provider: 'ollama', 'openai', or 'claude'.")
    stream: bool = Field(default=True, description="Whether to stream response via Server-Sent Events (SSE).")
    top_k: Optional[int] = Field(default=None, description="Override default retrieval top_k.")
    distance_threshold: Optional[float] = Field(default=None, description="Override default distance threshold.")


class ChatResponse(BaseModel):
    session_id: str
    message: str
    role: str = "assistant"
    provider: str
    sufficient: bool
    citations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)


async def get_or_create_session(db: AsyncSession, session_id_str: Optional[str]) -> DBSession:
    """Retrieves existing database session or creates a new session."""
    session_uuid = None
    if session_id_str:
        try:
            session_uuid = uuid.UUID(session_id_str)
        except ValueError:
            pass

    if session_uuid:
        result = await db.execute(select(DBSession).where(DBSession.id == session_uuid))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Create new session
    new_session = DBSession(id=session_uuid or uuid.uuid4())
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


@router.post("/chat")
async def chat_endpoint(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """POST /api/chat endpoint handling grounded RAG queries across multi-LLM providers with SSE streaming."""
    if not req.message or not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty.",
        )

    user_query = req.message.strip()
    provider_name = (req.provider or settings.DEFAULT_LLM_PROVIDER or "ollama").strip().lower()

    # Validate provider factory resolution before executing expensive tasks
    try:
        provider_instance: BaseLLMProvider = ProviderFactory.get_provider(provider_name, db=db)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )

    # 1. Resolve DB Session
    db_session = await get_or_create_session(db, req.session_id)

    # 2. Perform provider-independent vector retrieval
    retrieval_service = RetrievalService()
    try:
        grounding_res: GroundingResult = await retrieval_service.search(
            db=db,
            query=user_query,
            top_k=req.top_k,
            distance_threshold=req.distance_threshold,
        )
    except Exception as e:
        logger.error(f"Retrieval error in /api/chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database retrieval failure: {e}",
        )

    # Convert retrieved chunks to serializable source dictionaries
    sources = [
        {
            "chunk_id": str(c.chunk_id),
            "episode_title": c.episode_title,
            "guest": c.guest,
            "timestamp": c.timestamp,
            "speaker": c.speaker,
            "chunk_text": c.chunk_text[:200],
            "source_url": c.source_url,
            "distance": round(c.distance, 4),
            "citation": c.to_citation_string(),
        }
        for c in grounding_res.results
    ]
    citations = grounding_res.citations

    # 3. Handle Grounding Fallback (< 0.4 threshold check)
    if not grounding_res.sufficient:
        logger.info(f"Insufficient evidence for query: '{user_query[:50]}...'. Returning exact fallback string.")

        # Persist user & assistant messages
        user_msg = DBMessage(
            session_id=db_session.id,
            role="user",
            content=user_query,
        )
        assistant_msg = DBMessage(
            session_id=db_session.id,
            role="assistant",
            content=FALLBACK_MESSAGE,
        )
        db.add_all([user_msg, assistant_msg])
        await db.commit()

        if not req.stream:
            return ChatResponse(
                session_id=str(db_session.id),
                message=FALLBACK_MESSAGE,
                role="assistant",
                provider=provider_name,
                sufficient=False,
                citations=[],
                sources=[],
            )

        async def fallback_stream_generator() -> AsyncGenerator[str, None]:
            event_payload = {
                "event": "message",
                "delta": FALLBACK_MESSAGE,
                "session_id": str(db_session.id),
                "provider": provider_name,
                "sufficient": False,
                "citations": [],
                "sources": [],
            }
            yield f"data: {json.dumps(event_payload)}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'finish_reason': 'stop'})}\n\n"

        return StreamingResponse(
            fallback_stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # 4. Sufficient evidence -> Execute LLM generation or streaming
    # Persist user message
    user_msg = DBMessage(
        session_id=db_session.id,
        role="user",
        content=user_query,
    )
    db.add(user_msg)
    await db.commit()

    if not req.stream:
        try:
            res_obj = await provider_instance.generate(
                prompt=user_query,
                system_prompt=SYSTEM_PROMPT,
                context_xml=grounding_res.context,
            )
            # Persist assistant message
            assistant_msg = DBMessage(
                session_id=db_session.id,
                role="assistant",
                content=res_obj.content,
            )
            db.add(assistant_msg)
            await db.commit()

            return ChatResponse(
                session_id=str(db_session.id),
                message=res_obj.content,
                role="assistant",
                provider=provider_name,
                sufficient=True,
                citations=citations,
                sources=sources,
            )
        except (OllamaProviderUnavailableError, OpenAIProviderConfigurationError) as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE if isinstance(err, OllamaProviderUnavailableError) else status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            )

    # Streaming SSE Response Generator
    async def sse_event_generator() -> AsyncGenerator[str, None]:
        accumulated_chunks = []
        try:
            async for chunk in provider_instance.stream(
                prompt=user_query,
                system_prompt=SYSTEM_PROMPT,
                context_xml=grounding_res.context,
            ):
                if chunk.delta:
                    accumulated_chunks.append(chunk.delta)
                    payload = {
                        "event": "delta",
                        "delta": chunk.delta,
                        "session_id": str(db_session.id),
                        "provider": provider_name,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

            full_answer = "".join(accumulated_chunks).strip()

            # Save completed assistant message into DB if AsyncSessionLocal is available
            try:
                async with AsyncSessionLocal() as stream_db:
                    assistant_msg = DBMessage(
                        session_id=db_session.id,
                        role="assistant",
                        content=full_answer,
                    )
                    stream_db.add(assistant_msg)
                    await stream_db.commit()
            except Exception as db_save_err:
                logger.warning(f"Message persistence warning during streaming: {db_save_err}")

            done_payload = {
                "event": "done",
                "finish_reason": "stop",
                "session_id": str(db_session.id),
                "provider": provider_name,
                "sufficient": True,
                "citations": citations,
                "sources": sources,
            }
            yield f"data: {json.dumps(done_payload)}\n\n"

        except Exception as stream_err:
            logger.error(f"Error during stream generation for provider '{provider_name}': {stream_err}")
            err_payload = {
                "event": "error",
                "error": str(stream_err),
                "provider": provider_name,
                "code": "PROVIDER_ERROR",
            }
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
