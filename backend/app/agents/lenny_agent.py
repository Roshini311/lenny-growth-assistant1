import os
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
)

from app.config import settings
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools.retrieval_tool import (
    RETRIEVAL_TOOL_NAME,
    RETRIEVAL_TOOL_DEFINITION,
    execute_retrieval_tool,
    create_retrieval_mcp_server,
)
from app.services.retrieval import RetrievalService, FALLBACK_MESSAGE

logger = logging.getLogger("lenny_assistant.agents.lenny_agent")


class LennyAgent:
    """Orchestration agent using official Anthropic Claude Agent SDK (claude-agent-sdk)."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        system_prompt: str = SYSTEM_PROMPT,
        retrieval_service: Optional[RetrievalService] = None,
        options: Optional[ClaudeAgentOptions] = None,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.retrieval_service = retrieval_service or RetrievalService()
        self.custom_options = options

    def get_agent_options(
        self,
        db: AsyncSession,
        top_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> ClaudeAgentOptions:
        """Constructs ClaudeAgentOptions configured with system prompt and retrieval MCP server."""
        if self.custom_options is not None:
            return self.custom_options

        mcp_server = create_retrieval_mcp_server(
            db=db,
            retrieval_service=self.retrieval_service,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

        return ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            mcp_servers={"retrieval": mcp_server},
            allowed_tools=[f"mcp__retrieval__{RETRIEVAL_TOOL_NAME}"],
            model=self.model,
        )

    async def run_retrieval_tool(
        self,
        db: AsyncSession,
        query: str,
        top_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Executes registered retrieval_tool contract."""
        logger.info(f"LennyAgent delegating to retrieval_tool: '{query[:50]}...'")
        return await execute_retrieval_tool(
            db=db,
            query=query,
            retrieval_service=self.retrieval_service,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

    async def run(
        self,
        db: AsyncSession,
        user_message: str,
        top_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Executes agent query via official Claude Agent SDK runtime with grounded vector search."""

        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty.")

        logger.info(f"LennyAgent run started for query: '{user_message[:60]}...'")

        # 1. Delegate retrieval execution to check grounding sufficiency & citations
        tool_result = await self.run_retrieval_tool(
            db=db,
            query=user_message,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

        # 2. Enforce strict evidence boundary
        if not tool_result.get("sufficient", False):
            logger.info("Insufficient evidence retrieved (< 0.4 distance). Emitting exact fallback response.")
            return {
                "role": "assistant",
                "content": FALLBACK_MESSAGE,
                "sufficient": False,
                "citations": [],
                "sources": [],
                "tool_invoked": True,
                "model": self.model,
            }

        citations: List[str] = tool_result.get("citations", [])
        sources: List[Dict[str, Any]] = tool_result.get("results", [])

        # 3. Live Claude Agent SDK execution if Anthropic API Key is available
        if settings.ANTHROPIC_API_KEY:
            try:
                options = self.get_agent_options(
                    db=db,
                    top_k=top_k,
                    distance_threshold=distance_threshold,
                )
                async with ClaudeSDKClient(options=options) as client:
                    response_obj = await client.query(user_message)
                    content_str = str(response_obj).strip() if response_obj else ""
                    if content_str:
                        return {
                            "role": "assistant",
                            "content": content_str,
                            "sufficient": True,
                            "citations": citations,
                            "sources": sources,
                            "tool_invoked": True,
                            "model": self.model,
                        }
            except Exception as e:
                logger.error(f"Claude Agent SDK runtime execution failed ({e}). Returning grounded context payload.")

        # 4. Deterministic grounded response output (for offline/unauthenticated environments)
        summary_claims = []
        for src in sources[:3]:
            summary_claims.append(f"- {src['guest']} ({src['episode_title']}): {src['chunk_text'][:120]}...")
        claims_text = "\n".join(summary_claims)
        cite_str = " ".join(citations)

        return {
            "role": "assistant",
            "content": f"Based on Lenny's Podcast archive:\n\n{claims_text}\n\nSources: {cite_str}",
            "sufficient": True,
            "citations": citations,
            "sources": sources,
            "tool_invoked": True,
            "model": self.model,
        }
