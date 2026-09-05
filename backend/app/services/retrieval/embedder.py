import logging
from typing import List
from app.config import settings
from app.services.ingestion.embedder import EmbedderService, REQUIRED_DIMENSION

logger = logging.getLogger("lenny_assistant.retrieval.embedder")

_query_embedder_instance: EmbedderService = None


def get_query_embedder() -> EmbedderService:
    """Returns singleton EmbedderService instance loaded once per process."""
    global _query_embedder_instance
    if _query_embedder_instance is None:
        logger.info(f"Initializing query embedder singleton with model {settings.EMBEDDING_MODEL}")
        _query_embedder_instance = EmbedderService(model_name=settings.EMBEDDING_MODEL)
    return _query_embedder_instance


def embed_query(query: str, embedder: EmbedderService = None) -> List[float]:
    """Embeds a single natural language user query into a 384-dimensional unit vector."""
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty.")

    service = embedder or get_query_embedder()
    vectors = service.encode_batch([query.strip()])
    if not vectors or len(vectors[0]) != settings.EMBEDDING_DIMENSION:
        actual_dim = len(vectors[0]) if vectors else 0
        raise ValueError(
            f"Query embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSION}, got {actual_dim}"
        )

    return vectors[0]
