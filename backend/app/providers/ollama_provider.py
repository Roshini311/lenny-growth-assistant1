import logging
from typing import AsyncGenerator, Optional
import httpx
import ollama

from app.config import settings
from app.providers.base import BaseLLMProvider, ProviderStreamChunk, ProviderResponse

logger = logging.getLogger("lenny_assistant.providers.ollama")


class OllamaProviderUnavailableError(RuntimeError):
    """Raised when local Ollama service is unreachable or model is missing."""
    pass


class OllamaProvider(BaseLLMProvider):
    """Provider implementation for local Ollama service (llama3.2:3b)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        client: Optional[ollama.AsyncClient] = None,
    ):
        base_url = base_url or settings.OLLAMA_BASE_URL
        model_name = model_name or settings.OLLAMA_MODEL
        super().__init__(name="ollama", model_name=model_name)
        self.base_url = base_url
        self.client = client or ollama.AsyncClient(host=self.base_url)

    async def check_availability(self) -> bool:
        """Checks if Ollama service is reachable on base_url."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as http_client:
                res = await http_client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[ProviderStreamChunk, None]:
        """Streams response tokens from local Ollama model."""
        formatted_prompt = prompt
        if context_xml:
            formatted_prompt = (
                f"{prompt}\n\nRetrieved Context:\n{context_xml}\n\n"
                "Answer the user's question using ONLY transcript evidence inside <transcript_data>."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": formatted_prompt})

        try:
            response_stream = await self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=True,
                options={"temperature": temperature},
            )

            async for chunk in response_stream:
                delta_text = chunk.get("message", {}).get("content", "")
                done = chunk.get("done", False)
                finish_reason = "stop" if done else None
                if delta_text or done:
                    yield ProviderStreamChunk(delta=delta_text, finish_reason=finish_reason)

        except (httpx.ConnectError, httpx.TimeoutException, ConnectionRefusedError, Exception) as e:
            logger.error(f"Ollama streaming connection failed ({e}).")
            raise OllamaProviderUnavailableError(
                f"Local Ollama service is unavailable at {self.base_url}. Error: {e}"
            ) from e

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context_xml: Optional[str] = None,
        temperature: float = 0.2,
    ) -> ProviderResponse:
        """Generates complete response from local Ollama model."""
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
