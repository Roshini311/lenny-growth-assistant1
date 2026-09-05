import logging
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.providers.base import BaseLLMProvider, ProviderStreamChunk, ProviderResponse

logger = logging.getLogger("lenny_assistant.providers.openai")


class OpenAIProviderConfigurationError(RuntimeError):
    """Raised when OPENAI_API_KEY is not configured or OpenAI request fails."""
    pass


class OpenAIProvider(BaseLLMProvider):
    """Provider implementation for Cloud OpenAI (gpt-4o-mini)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        client: Optional[AsyncOpenAI] = None,
    ):
        api_key = api_key or settings.OPENAI_API_KEY
        model_name = model_name or settings.OPENAI_MODEL
        super().__init__(name="openai", model_name=model_name)
        self.api_key = api_key
        self.client = client or (AsyncOpenAI(api_key=self.api_key) if self.api_key else None)

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[ProviderStreamChunk, None]:
        """Streams response tokens from Cloud OpenAI model."""
        if not self.api_key or not self.client:
            raise OpenAIProviderConfigurationError(
                "OPENAI_API_KEY is not configured in environment settings."
            )

        formatted_prompt = prompt
        if context_xml:
            formatted_prompt = (
                f"{prompt}\n\nRetrieved Grounded Context:\n{context_xml}\n\n"
                "Please answer using strictly transcript evidence inside <transcript_data>."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": formatted_prompt})

        try:
            stream_res = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
                stream=True,
            )

            async for chunk in stream_res:
                if chunk.choices:
                    choice = chunk.choices[0]
                    delta_text = choice.delta.content or ""
                    finish_reason = choice.finish_reason
                    if delta_text or finish_reason:
                        yield ProviderStreamChunk(delta=delta_text, finish_reason=finish_reason)

        except OpenAIError as e:
            logger.error(f"OpenAI API execution failed: {e}")
            raise OpenAIProviderConfigurationError(f"OpenAI API call failed: {e}") from e

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> ProviderResponse:
        """Generates complete response from Cloud OpenAI model."""
        collected_tokens = []
        async for chunk in self.stream(
            prompt=prompt,
            system_prompt=system_prompt,
            context_xml=context_xml,
            temperature=temperature,
        ):
            if chunk.delta:
                collected_tokens.append(chunk.delta)

        full_text = "".join(collected_tokens).strip()
        return ProviderResponse(
            content=full_text,
            model=self.model_name,
            provider=self.name,
        )
