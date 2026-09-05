import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from claude_agent_sdk import tool, create_sdk_mcp_server
from app.services.retrieval import RetrievalService, GroundingResult

logger = logging.getLogger("lenny_assistant.agents.tools.retrieval_tool")

RETRIEVAL_TOOL_NAME: str = "search_lenny_transcripts"

RETRIEVAL_TOOL_DEFINITION: Dict[str, Any] = {
    "name": RETRIEVAL_TOOL_NAME,
    "description": (
        "Performs semantic vector retrieval against Lenny's Podcast transcript corpus for product, growth, "
        "leadership, and startup strategy questions. Returns grounded transcript chunks, metadata, and citations."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural-language user query to search in Lenny's Podcast transcript archive."
            }
        },
        "required": ["query"]
    }
}


async def execute_retrieval_tool(
    db: AsyncSession,
    query: str,
    retrieval_service: Optional[RetrievalService] = None,
    top_k: Optional[int] = None,
    distance_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """Executes retrieval tool contract against Phase 5 RetrievalService."""

    if not query or not query.strip():
        raise ValueError("Retrieval tool query cannot be empty.")

    service = retrieval_service or RetrievalService()

    try:
        grounding_res: GroundingResult = await service.search(
            db=db,
            query=query.strip(),
            top_k=top_k,
            distance_threshold=distance_threshold,
        )
    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Retrieval infrastructure failure during tool execution: {e}")
        # Infrastructure error: raise so it is NOT masked as 'insufficient evidence'
        raise RuntimeError(f"Retrieval infrastructure failure: {e}") from e

    # Grounding result to structured tool output payload
    return {
        "query": grounding_res.query,
        "sufficient": grounding_res.sufficient,
        "results": [
            {
                "chunk_id": str(c.chunk_id),
                "episode_title": c.episode_title,
                "guest": c.guest,
                "publish_date": c.publish_date,
                "timestamp": c.timestamp,
                "speaker": c.speaker,
                "chunk_text": c.chunk_text,
                "source_url": c.source_url,
                "distance": c.distance,
                "citation": c.to_citation_string(),
            }
            for c in grounding_res.results
        ],
        "context": grounding_res.context,
        "citations": grounding_res.citations,
        "fallback_message": grounding_res.fallback_message,
    }


def create_retrieval_mcp_server(
    db: AsyncSession,
    retrieval_service: Optional[RetrievalService] = None,
    top_k: Optional[int] = None,
    distance_threshold: Optional[float] = None,
):
    """Creates an in-process MCP server wrapping the search_lenny_transcripts tool for Claude Agent SDK."""

    @tool(
        name=RETRIEVAL_TOOL_NAME,
        description=RETRIEVAL_TOOL_DEFINITION["description"],
        input_schema=RETRIEVAL_TOOL_DEFINITION["input_schema"],
    )
    async def search_lenny_transcripts(args: Dict[str, Any]) -> Dict[str, Any]:
        query_text = args.get("query", "")
        res = await execute_retrieval_tool(
            db=db,
            query=query_text,
            retrieval_service=retrieval_service,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(res),
                }
            ]
        }

    return create_sdk_mcp_server(name="retrieval", tools=[search_lenny_transcripts])
