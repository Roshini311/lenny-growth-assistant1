import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.agents import LennyAgent
from app.providers.base import BaseLLMProvider, ProviderStreamChunk, ProviderResponse

logger = logging.getLogger("lenny_assistant.providers.claude")


class ClaudeProvider(BaseLLMProvider):
    """Provider implementation wrapping Phase 6 Claude Agent SDK LennyAgent."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        agent: Optional[LennyAgent] = None,
        db: Optional[AsyncSession] = None,
    ):
        model_name = model_name or "claude-3-5-sonnet-20241022"
        super().__init__(name="claude", model_name=model_name)
        self.agent = agent or LennyAgent(model=self.model_name)
        self.db = db

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[ProviderStreamChunk, None]:
        """Streams response tokens from Claude Agent SDK agent."""
        if not self.db:
            # Yield entire result chunk when db session is supplied via generate/chat flow
            res = await self.generate(prompt=prompt, system_prompt=system_prompt, context_xml=context_xml, temperature=temperature)
            yield ProviderStreamChunk(delta=res.content, finish_reason="stop")
            return

        res_dict = await self.agent.run(db=self.db, user_message=prompt)
        text_content = res_dict.get("content", "")
        yield ProviderStreamChunk(delta=text_content, finish_reason="stop")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> ProviderResponse:
        """Generates complete response from Claude Agent SDK agent."""
        if self.db is not None:
            res_dict = await self.agent.run(db=self.db, user_message=prompt)
            content = res_dict.get("content", "")
        else:
            content = f"Claude Agent SDK context: {context_xml or prompt}"

        return ProviderResponse(
            content=content,
            model=self.model_name,
            provider=self.name,
        )
