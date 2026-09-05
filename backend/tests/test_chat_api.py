import uuid
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.models.models import Session as DBSession
from app.services.retrieval import GroundingResult, RetrievalChunk, FALLBACK_MESSAGE


class TestChatAPI(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.add = MagicMock()
        self.mock_db.add_all = MagicMock()
        
        # Override get_db FastAPI dependency with mock_db
        async def override_get_db():
            yield self.mock_db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    async def test_chat_empty_message_rejected(self):
        """Verify empty or whitespace message returns HTTP 400 Bad Request."""
        res = self.client.post("/api/chat", json={"message": "   "})
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot be empty", res.json()["detail"])

    async def test_chat_invalid_provider_rejected(self):
        """Verify invalid provider name returns HTTP 400 Bad Request."""
        res = self.client.post("/api/chat", json={"message": "What is PLG?", "provider": "invalid_llm_99"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unsupported LLM provider", res.json()["detail"])

    @patch("app.api.chat.get_or_create_session")
    @patch("app.api.chat.RetrievalService")
    async def test_chat_insufficient_evidence_exact_fallback(self, mock_retrieval_cls, mock_get_session):
        """Verify insufficient retrieval evidence produces exact approved fallback message."""
        mock_session_obj = MagicMock()
        mock_session_obj.id = uuid.uuid4()
        mock_get_session.return_value = mock_session_obj

        mock_service = MagicMock()
        mock_service.search = AsyncMock(return_value=GroundingResult(
            query="What is the weather in Chennai?",
            sufficient=False,
            results=[],
            context="",
            citations=[],
            fallback_message=FALLBACK_MESSAGE,
        ))
        mock_retrieval_cls.return_value = mock_service

        res = self.client.post(
            "/api/chat",
            json={
                "message": "What is the weather in Chennai?",
                "stream": False,
                "provider": "ollama",
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["sufficient"])
        self.assertEqual(data["message"], FALLBACK_MESSAGE)
        self.assertEqual(
            data["message"],
            "I do not have sufficient information in Lenny's podcast archive to answer this."
        )

    @patch("app.api.chat.get_or_create_session")
    @patch("app.api.chat.ProviderFactory.get_provider")
    @patch("app.api.chat.RetrievalService")
    async def test_chat_non_streaming_success(self, mock_retrieval_cls, mock_factory_get, mock_get_session):
        """Verify non-streaming chat request returns structured ChatResponse JSON."""
        mock_session_obj = MagicMock()
        mock_session_obj.id = uuid.uuid4()
        mock_get_session.return_value = mock_session_obj

        mock_chunk = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="PLG Deep Dive",
            guest="Elena Verna",
            timestamp="00:05:00",
            chunk_text="Product led growth scales through self-serve acquisition.",
            distance=0.25,
        )
        mock_service = MagicMock()
        mock_service.search = AsyncMock(return_value=GroundingResult(
            query="Tell me about PLG",
            sufficient=True,
            results=[mock_chunk],
            context="<transcript_data>...</transcript_data>",
            citations=["[Episode: Elena Verna, 00:05:00]"],
            fallback_message=None,
        ))
        mock_retrieval_cls.return_value = mock_service

        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "PLG is driven by self-serve loops [Episode: Elena Verna, 00:05:00]."
        mock_provider.generate = AsyncMock(return_value=mock_response)
        mock_factory_get.return_value = mock_provider

        res = self.client.post(
            "/api/chat",
            json={
                "message": "Tell me about PLG",
                "stream": False,
                "provider": "ollama",
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["sufficient"])
        self.assertIn("PLG is driven by self-serve loops", data["message"])
        self.assertEqual(len(data["citations"]), 1)
        self.assertEqual(data["citations"][0], "[Episode: Elena Verna, 00:05:00]")

    @patch("app.api.chat.get_or_create_session")
    @patch("app.api.chat.ProviderFactory.get_provider")
    @patch("app.api.chat.RetrievalService")
    async def test_chat_sse_streaming_response(self, mock_retrieval_cls, mock_factory_get, mock_get_session):
        """Verify SSE streaming chat endpoint returns event-stream data."""
        mock_session_obj = MagicMock()
        mock_session_obj.id = uuid.uuid4()
        mock_get_session.return_value = mock_session_obj

        mock_chunk = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Roadmap Strategy",
            guest="Shreyas Doshi",
            timestamp="00:12:30",
            chunk_text="Good product managers focus on leverage.",
            distance=0.20,
        )
        mock_service = MagicMock()
        mock_service.search = AsyncMock(return_value=GroundingResult(
            query="Shreyas Doshi on leverage",
            sufficient=True,
            results=[mock_chunk],
            context="<transcript_data>...</transcript_data>",
            citations=["[Episode: Shreyas Doshi, 00:12:30]"],
            fallback_message=None,
        ))
        mock_retrieval_cls.return_value = mock_service

        mock_provider = MagicMock()

        async def mock_stream_gen(*args, **kwargs):
            mock_c1 = MagicMock()
            mock_c1.delta = "Focus on "
            mock_c2 = MagicMock()
            mock_c2.delta = "leverage."
            yield mock_c1
            yield mock_c2

        mock_provider.stream = mock_stream_gen
        mock_factory_get.return_value = mock_provider

        res = self.client.post(
            "/api/chat",
            json={
                "message": "Shreyas Doshi on leverage",
                "stream": True,
                "provider": "ollama",
            }
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers["content-type"])
        body = res.text
        self.assertIn("data: ", body)
        self.assertIn("Focus on ", body)

    async def test_health_endpoint_provider_info(self):
        """Verify GET /api/health endpoint includes safe provider diagnostic information."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("providers", data)
        self.assertIn("ollama_base_url", data["providers"])
        self.assertIn("openai_configured", data["providers"])
        self.assertNotIn("OPENAI_API_KEY", str(data))
        self.assertNotIn("sk-", str(data))


if __name__ == "__main__":
    unittest.main()
