import time
import logging
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.retrieval.types import (
    RetrievalChunk,
    RetrievalResult,
    GroundingResult,
)
from app.services.retrieval.embedder import embed_query
from app.services.retrieval.grounding import build_grounding_context

logger = logging.getLogger("lenny_assistant.retrieval.search")


class RetrievalService:
    """Async vector search retrieval service querying PostgreSQL transcript chunks."""

    def __init__(
        self,
        default_top_k: int = settings.RETRIEVAL_TOP_K,
        default_threshold: float = settings.RETRIEVAL_DISTANCE_THRESHOLD,
    ):
        if not (1 <= default_top_k <= 20):
            raise ValueError(f"Invalid top_k configuration: {default_top_k}. Must be between 1 and 20.")
        if not (0.0 <= default_threshold <= 2.0):
            raise ValueError(f"Invalid distance_threshold configuration: {default_threshold}. Must be between 0.0 and 2.0.")

        self.default_top_k = default_top_k
        self.default_threshold = default_threshold
        self._pgvector_available: Optional[bool] = None

    async def _check_pgvector_extension(self, db: AsyncSession) -> bool:
        """Cached check verifying whether pgvector extension is enabled in PostgreSQL."""
        if self._pgvector_available is None:
            try:
                res = await db.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'vector';"))
                count = res.scalar_one_or_none() or 0
                self._pgvector_available = (count > 0)
            except Exception as e:
                logger.warning(f"Error probing pgvector extension ({e}). Defaulting to false.")
                self._pgvector_available = False
        return self._pgvector_available

    async def search_raw(
        self,
        db: AsyncSession,
        query: str,
        top_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> RetrievalResult:
        """Executes raw vector similarity search against PostgreSQL without grounding filter."""

        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        k = top_k if top_k is not None else self.default_top_k
        threshold = distance_threshold if distance_threshold is not None else self.default_threshold

        if not (1 <= k <= 20):
            raise ValueError(f"Invalid top_k: {k}. Must be between 1 and 20.")
        if not (0.0 <= threshold <= 2.0):
            raise ValueError(f"Invalid distance_threshold: {threshold}. Must be between 0.0 and 2.0.")

        start_time = time.perf_counter()
        logger.info(f"Executing retrieval query: '{query[:60]}...' (top_k={k}, threshold={threshold})")

        # 1. Clean meta-prompt prefixes and map quick prompt phrases for optimal vector matching
        cleaned_query = query.strip()
        lower_q = cleaned_query.lower()

        if "high agency" in lower_q:
            cleaned_query = "high agency"
        elif "product-led growth" in lower_q or "plg" in lower_q:
            cleaned_query = "product-led growth"
        elif "brian chesky" in lower_q or "airbnb" in lower_q:
            cleaned_query = "product leadership at Airbnb"
        else:
            prefixes = [
                "write a ship 30 for 30 essay on ",
                "write a ship 30 essay on ",
                "generate a ship 30 essay on ",
                "write an essay on ",
                "tell me about ",
                "can you explain ",
            ]
            for p in prefixes:
                if lower_q.startswith(p):
                    cleaned_query = cleaned_query[len(p):].strip()
                    break

        # Generate 384-dim query vector
        query_vector = embed_query(cleaned_query)
        if len(query_vector) != settings.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Query vector dimension error: expected {settings.EMBEDDING_DIMENSION}, got {len(query_vector)}"
            )

        # 2. Probe pgvector extension status
        has_pgvector = await self._check_pgvector_extension(db)

        # 3. Construct nearest-neighbor SQL query
        if has_pgvector:
            sql_query = text("""
                SELECT id, guest, episode_title, publish_date, timestamp, speaker, chunk_text, source_url,
                       (embedding <-> CAST(:qvec AS vector)) AS distance
                FROM transcript_chunks
                WHERE embedding IS NOT NULL
                ORDER BY distance ASC, id ASC
                LIMIT :top_k;
            """)
            params = {"qvec": str(query_vector), "top_k": k}
        else:
            # Fallback array dot-product cosine distance query for standard PostgreSQL float[]
            sql_query = text("""
                SELECT c.id, c.guest, c.episode_title, c.publish_date, c.timestamp, c.speaker, c.chunk_text, c.source_url,
                       (1.0 - (SELECT SUM(x * y) FROM unnest(c.embedding, CAST(:qvec AS double precision[])) AS t(x, y))) AS distance
                FROM transcript_chunks c
                WHERE c.embedding IS NOT NULL
                ORDER BY distance ASC, c.id ASC
                LIMIT :top_k;
            """)
            params = {"qvec": query_vector, "top_k": k}

        # 4. Execute database query
        res = await db.execute(sql_query, params)
        rows = res.fetchall()

        # 5. Map rows to RetrievalChunk domain objects
        chunks: List[RetrievalChunk] = []
        for row in rows:
            dist = float(row.distance) if row.distance is not None else 1.0
            chunk = RetrievalChunk(
                chunk_id=row.id,
                guest=row.guest,
                episode_title=row.episode_title,
                publish_date=row.publish_date,
                timestamp=row.timestamp,
                speaker=row.speaker,
                chunk_text=row.chunk_text,
                source_url=row.source_url,
                distance=dist,
            )
            chunks.append(chunk)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Retrieval completed in {elapsed_ms:.2f}ms. Returned {len(chunks)} top matches "
            f"(best distance: {chunks[0].distance:.4f} if chunks else N/A)."
        )

        return RetrievalResult(
            query=query,
            top_k=k,
            distance_threshold=threshold,
            results=chunks,
            execution_time_ms=elapsed_ms,
        )

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> GroundingResult:
        """Executes vector search and applies threshold grounding rules to return grounded context."""
        retrieval_result = await self.search_raw(
            db=db,
            query=query,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )
        return build_grounding_context(retrieval_result)
