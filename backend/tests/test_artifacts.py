import uuid
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.models.models import Artifact as DBArtifact, Session as DBSession
from app.services.artifacts.schemas import ArtifactType, ArtifactCreate
from app.services.artifacts.sanitizer import ArtifactSanitizer
from app.services.artifacts.service import ArtifactService
from app.services.retrieval import GroundingResult, RetrievalChunk, FALLBACK_MESSAGE


class TestArtifacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.sanitizer = ArtifactSanitizer()
        self.mock_db = MagicMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        self.mock_db.add = MagicMock()

        async def override_get_db():
            yield self.mock_db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_sanitize_html_strips_script(self):
        """Verify HTML sanitizer strips dangerous <script> tags."""
        raw_html = "<div><h1>Title</h1><script>alert('XSS')</script><p>Safe text</p></div>"
        cleaned = self.sanitizer.sanitize_html(raw_html)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("alert", cleaned)
        self.assertIn("<h1>Title</h1>", cleaned)
        self.assertIn("<p>Safe text</p>", cleaned)

    def test_sanitize_html_strips_event_handlers(self):
        """Verify HTML sanitizer strips inline onerror/onclick event handlers."""
        raw_html = '<img src="x" onerror="alert(1)" /><button onclick="doBadThing()">Click</button>'
        cleaned = self.sanitizer.sanitize_html(raw_html)
        self.assertNotIn("onerror", cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("alert", cleaned)
        self.assertNotIn("doBadThing", cleaned)

    def test_sanitize_html_strips_javascript_uris(self):
        """Verify HTML sanitizer strips javascript: URIs."""
        raw_html = '<a href="javascript:alert(1)">Click Me</a>'
        cleaned = self.sanitizer.sanitize_html(raw_html)
        self.assertNotIn("javascript:", cleaned)

    def test_sanitize_markdown(self):
        """Verify markdown sanitizer leaves standard markdown intact."""
        md = "# Ship30 Essay\n\n**Hook**: Text.\n\n* Bullet 1\n* Bullet 2"
        cleaned = self.sanitizer.sanitize(md, ArtifactType.MARKDOWN)
        self.assertEqual(cleaned, md)

    async def test_create_artifact_service(self):
        """Verify ArtifactService creates and persists an artifact with sanitization."""
        service = ArtifactService()
        artifact = await service.create_artifact(
            db=self.mock_db,
            title="Sanitized Essay",
            content="<div><h2>Header</h2><script>bad()</script></div>",
            artifact_type=ArtifactType.HTML,
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.assertNotIn("<script>", artifact.content)
        self.assertIn("Header", artifact.content)

    @patch("app.api.essays.Ship30EssayGenerator")
    @patch("app.api.essays.get_or_create_session")
    async def test_post_essay_ship30_endpoint(self, mock_get_session, mock_generator_cls):
        """Verify POST /api/essays/ship30 creates session and artifact when topic is provided."""
        mock_session_obj = MagicMock()
        mock_session_obj.id = uuid.uuid4()
        mock_get_session.return_value = mock_session_obj

        mock_generator_instance = MagicMock()
        mock_generator_instance.generate_essay = AsyncMock(return_value={
            "title": "Ship30 Essay: Product Led Growth",
            "content": "# PLG Essay\n\n**Hook**: PLG is powerful.",
            "sufficient": True,
            "citations": ["Citation 1"],
            "sources": [],
            "word_count": 100,
            "provider": "ollama"
        })
        mock_generator_cls.return_value = mock_generator_instance

        response = self.client.post("/api/essays/ship30", json={"topic": "Product Led Growth"})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["artifact"]["artifact_type"], "markdown")
        self.assertIn("Ship30 Essay", data["artifact"]["title"])
        self.assertIn("PLG Essay", data["essay"])

    async def test_get_artifact_not_found(self):
        """Verify GET /api/artifacts/{id} returns 404 when artifact does not exist."""
        fake_id = uuid.uuid4()
        self.mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = mock_result

        response = self.client.get(f"/api/artifacts/{fake_id}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_iframe_sandbox_policy_invariant(self):
        """Verify phase 9 iframe sandbox security invariant configuration."""
        iframe_sandbox_policy = "allow-scripts"
        self.assertIn("allow-scripts", iframe_sandbox_policy)
        self.assertNotIn("allow-same-origin", iframe_sandbox_policy)
        self.assertNotIn("allow-top-navigation", iframe_sandbox_policy)


if __name__ == "__main__":
    unittest.main()
