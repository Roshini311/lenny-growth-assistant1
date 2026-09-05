import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.providers.base import BaseLLMProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.claude_provider import ClaudeProvider

logger = logging.getLogger("lenny_assistant.providers.factory")


class ProviderFactory:
    """Factory for selecting and instantiating LLM providers."""

    @staticmethod
    def get_provider(
        provider_name: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> BaseLLMProvider:
        name = (provider_name or settings.DEFAULT_LLM_PROVIDER or "ollama").strip().lower()

        if name == "ollama":
            return OllamaProvider()
        elif name == "openai":
            return OpenAIProvider()
        elif name == "claude":
            return ClaudeProvider(db=db)
        else:
            raise ValueError(
                f"Unsupported LLM provider '{name}'. Valid providers are 'ollama', 'openai', or 'claude'."
            )
