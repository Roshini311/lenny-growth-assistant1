import unittest
from unittest.mock import AsyncMock, MagicMock

from app.providers import (
    BaseLLMProvider,
    ProviderStreamChunk,
    ProviderResponse,
    OllamaProvider,
    OllamaProviderUnavailableError,
    OpenAIProvider,
    OpenAIProviderConfigurationError,
    ClaudeProvider,
    ProviderFactory,
)


class TestProviderArchitecture(unittest.IsolatedAsyncioTestCase):

    def test_provider_models_contract(self):
        """Verify Pydantic models for provider chunks and responses."""
        chunk = ProviderStreamChunk(delta="Hello", finish_reason=None)
        self.assertEqual(chunk.delta, "Hello")
        self.assertIsNone(chunk.finish_reason)

        response = ProviderResponse(
            content="Full answer text",
            model="llama3.2:3b",
            provider="ollama",
        )
        self.assertEqual(response.content, "Full answer text")
        self.assertEqual(response.provider, "ollama")

    def test_ollama_provider_configuration(self):
        """Verify OllamaProvider configuration and defaults."""
        provider = OllamaProvider()
        self.assertEqual(provider.name, "ollama")
        self.assertEqual(provider.model_name, "llama3.2:3b")

    async def test_ollama_provider_streaming_mocked(self):
        """Verify OllamaProvider streams token chunks from mocked async client."""
        mock_client = MagicMock()

        async def mock_chat_stream(*args, **kwargs):
            yield {"message": {"content": "Product "}, "done": False}
            yield {"message": {"content": "strategy"}, "done": True}

        mock_client.chat = AsyncMock(side_effect=mock_chat_stream)

        provider = OllamaProvider(client=mock_client)
        chunks = []
        async for chunk in provider.stream(prompt="What is product strategy?"):
            if chunk.delta:
                chunks.append(chunk.delta)

        self.assertEqual("".join(chunks), "Product strategy")

    async def test_ollama_provider_unavailable_error(self):
        """Verify unavailable Ollama service raises OllamaProviderUnavailableError."""
        mock_client = MagicMock()
        mock_client.chat = AsyncMock(side_effect=RuntimeError("Connection refused"))

        provider = OllamaProvider(client=mock_client)

        with self.assertRaises(OllamaProviderUnavailableError):
            async for _ in provider.stream(prompt="Test prompt"):
                pass

    def test_openai_provider_configuration(self):
        """Verify OpenAIProvider initialization and missing API key error."""
        provider_no_key = OpenAIProvider(api_key="")
        self.assertEqual(provider_no_key.name, "openai")
        self.assertEqual(provider_no_key.model_name, "gpt-4o-mini")

    async def test_openai_missing_key_raises_error(self):
        """Verify streaming without OPENAI_API_KEY raises OpenAIProviderConfigurationError."""
        provider = OpenAIProvider(api_key="")
        with self.assertRaises(OpenAIProviderConfigurationError):
            async for _ in provider.stream(prompt="Test prompt"):
                pass

    async def test_openai_provider_streaming_mocked(self):
        """Verify OpenAIProvider streams token chunks from mocked AsyncOpenAI client."""
        mock_choice_1 = MagicMock()
        mock_choice_1.delta.content = "Growth "
        mock_choice_1.finish_reason = None
        mock_chunk_1 = MagicMock()
        mock_chunk_1.choices = [mock_choice_1]

        mock_choice_2 = MagicMock()
        mock_choice_2.delta.content = "loops"
        mock_choice_2.finish_reason = "stop"
        mock_chunk_2 = MagicMock()
        mock_chunk_2.choices = [mock_choice_2]

        async def mock_stream_create(*args, **kwargs):
            yield mock_chunk_1
            yield mock_chunk_2

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_stream_create)

        provider = OpenAIProvider(api_key="sk-fake-test-key", client=mock_client)
        chunks = []
        async for chunk in provider.stream(prompt="What are growth loops?"):
            if chunk.delta:
                chunks.append(chunk.delta)

        self.assertEqual("".join(chunks), "Growth loops")

    async def test_claude_provider_generate_mocked(self):
        """Verify ClaudeProvider delegates generate to underlying LennyAgent."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "role": "assistant",
            "content": "Claude Agent answer",
            "sufficient": True,
            "citations": ["[Episode: Test, 00:01:00]"],
        })
        mock_db = MagicMock()
        provider = ClaudeProvider(agent=mock_agent, db=mock_db)

        res = await provider.generate(prompt="Test prompt")
        self.assertEqual(res.provider, "claude")
        self.assertEqual(res.content, "Claude Agent answer")
        mock_agent.run.assert_called_once()

    def test_provider_factory_resolution(self):
        """Verify ProviderFactory resolves provider instances correctly."""
        ollama_p = ProviderFactory.get_provider("ollama")
        self.assertIsInstance(ollama_p, OllamaProvider)

        openai_p = ProviderFactory.get_provider("openai")
        self.assertIsInstance(openai_p, OpenAIProvider)

        claude_p = ProviderFactory.get_provider("claude")
        self.assertIsInstance(claude_p, ClaudeProvider)

        with self.assertRaises(ValueError):
            ProviderFactory.get_provider("unsupported_provider_xyz")



if __name__ == "__main__":
    unittest.main()
