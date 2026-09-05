import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.retrieval import RetrievalService, GroundingResult, FALLBACK_MESSAGE
from app.providers import ProviderFactory, BaseLLMProvider
from app.agents.skills.ship30.prompts import SHIP30_SYSTEM_PROMPT, build_ship30_user_prompt

logger = logging.getLogger("lenny_assistant.skills.ship30")


class Ship30EssayGenerator:
    """Grounded Ship 30 for 30 essay generator using Lenny's Podcast transcript evidence."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        system_prompt: str = SHIP30_SYSTEM_PROMPT,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.system_prompt = system_prompt

    async def generate_essay(
        self,
        db: AsyncSession,
        topic: str,
        provider_name: Optional[str] = None,
        top_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generates a grounded Ship30 essay (~1,250 words) from retrieved transcript evidence."""
        if not topic or not topic.strip():
            raise ValueError("Essay topic cannot be empty.")

        topic_text = topic.strip()
        provider_name = (provider_name or settings.DEFAULT_LLM_PROVIDER or "ollama").strip().lower()

        logger.info(f"Generating Ship30 essay for topic: '{topic_text[:50]}...' using provider '{provider_name}'")

        # 1. Perform provider-independent retrieval
        grounding_res: GroundingResult = await self.retrieval_service.search(
            db=db,
            query=topic_text,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

        # 2. Check grounding threshold boundary
        if not grounding_res.sufficient:
            logger.info(f"Insufficient evidence for essay topic '{topic_text[:40]}...'. Returning exact fallback.")
            return {
                "title": f"Ship30 Essay: {topic_text[:60]}",
                "content": FALLBACK_MESSAGE,
                "essay": FALLBACK_MESSAGE,
                "sufficient": False,
                "citations": [],
                "sources": [],
                "word_count": len(FALLBACK_MESSAGE.split()),
                "provider": provider_name,
            }

        citations: List[str] = grounding_res.citations
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

        # 3. Format grounded prompt
        formatted_user_prompt = build_ship30_user_prompt(topic_text, grounding_res.context)

        # 4. Resolve provider and generate essay content
        provider_instance: BaseLLMProvider = ProviderFactory.get_provider(provider_name, db=db)

        try:
            res_obj = await provider_instance.generate(
                prompt=formatted_user_prompt,
                system_prompt=self.system_prompt,
                context_xml=grounding_res.context,
            )
            essay_text = res_obj.content.strip()
        except Exception as e:
            logger.error(f"Provider '{provider_name}' generation failed during essay creation: {e}")
            raise RuntimeError(f"Essay generation failure from provider '{provider_name}': {e}") from e

        # Ensure citations list is attached to essay markdown if missing
        if citations and not any(cite in essay_text for cite in citations[:2]):
            cite_section = "\n\n## Sources & Evidence\n" + "\n".join(f"- {c}" for c in citations)
            essay_text += cite_section

        word_count = len(essay_text.split())

        return {
            "title": f"Ship30 Essay: {topic_text[:60]}",
            "content": essay_text,
            "essay": essay_text,
            "sufficient": True,
            "citations": citations,
            "sources": sources,
            "word_count": word_count,
            "provider": provider_name,
        }

    async def generate(
        self,
        db: AsyncSession,
        topic: str,
        provider_name: Optional[str] = None,
        llm_provider: Optional[str] = None,
        top_k: Optional[int] = None,
        distance_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Alias for generate_essay."""
        effective_provider = provider_name or llm_provider
        return await self.generate_essay(
            db=db,
            topic=topic,
            provider_name=effective_provider,
            top_k=top_k,
            distance_threshold=distance_threshold,
        )

