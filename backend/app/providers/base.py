from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ProviderStreamChunk(BaseModel):
    """Chunk emitted during streaming response."""
    delta: str = Field(default="", description="Token delta content.")
    finish_reason: Optional[str] = Field(default=None, description="Finish reason if stream completed.")


class ProviderResponse(BaseModel):
    """Structured complete response from an LLM provider."""
    content: str = Field(..., description="Full generated answer text.")
    model: str = Field(..., description="Model identifier used.")
    provider: str = Field(..., description="Provider name (ollama, openai, claude).")
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, name: str, model_name: str):
        self.name = name
        self.model_name = model_name

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[ProviderStreamChunk, None]:
        """Asynchronously streams response token chunks."""
        yield ProviderStreamChunk(delta="")

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> ProviderResponse:
        """Asynchronously generates complete response."""
        pass
