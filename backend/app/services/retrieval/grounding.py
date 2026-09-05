import logging
from typing import List
from app.services.retrieval.types import (
    RetrievalResult,
    RetrievalChunk,
    GroundingResult,
    FALLBACK_MESSAGE,
)

logger = logging.getLogger("lenny_assistant.retrieval.grounding")


def build_grounding_context(retrieval_result: RetrievalResult) -> GroundingResult:
    """Converts raw vector retrieval results into a grounded context payload for LLM/Agent consumption."""

    threshold = retrieval_result.distance_threshold
    # Strict boundary check: distance < threshold (0.3999 is accepted, 0.4000 is rejected)
    valid_chunks: List[RetrievalChunk] = [
        chunk for chunk in retrieval_result.results
        if chunk.distance < threshold
    ]

    if not valid_chunks:
        logger.info(
            f"Insufficient retrieval evidence for query '{retrieval_result.query[:50]}...'. "
            f"Zero chunks passed distance threshold < {threshold}."
        )
        return GroundingResult(
            query=retrieval_result.query,
            sufficient=False,
            results=[],
            context="",
            citations=[],
            fallback_message=FALLBACK_MESSAGE,
        )

    # Build citation-ready list
    citations: List[str] = []
    seen_citations = set()
    for chunk in valid_chunks:
        cite_str = chunk.to_citation_string()
        if cite_str not in seen_citations:
            seen_citations.add(cite_str)
            citations.append(cite_str)

    # Format deterministic grounded transcript context XML block
    context_blocks: List[str] = ["<transcript_data>"]
    for i, chunk in enumerate(valid_chunks, 1):
        spk = f" (Speaker: {chunk.speaker})" if chunk.speaker else ""
        context_blocks.append(
            f"--- Source Chunk {i} {chunk.to_citation_string()}{spk} ---\n"
            f"Episode: {chunk.episode_title}\n"
            f"Guest: {chunk.guest}\n"
            f"Publish Date: {chunk.publish_date or 'N/A'}\n"
            f"Timestamp: {chunk.timestamp or 'N/A'}\n"
            f"Distance Score: {chunk.distance:.4f}\n"
            f"Content:\n{chunk.chunk_text}\n"
        )
    context_blocks.append("</transcript_data>")

    formatted_context = "\n".join(context_blocks)

    logger.info(
        f"Grounded context built successfully: {len(valid_chunks)} chunks passed threshold < {threshold}."
    )

    return GroundingResult(
        query=retrieval_result.query,
        sufficient=True,
        results=valid_chunks,
        context=formatted_context,
        citations=citations,
        fallback_message=None,
    )
