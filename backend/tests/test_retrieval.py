import uuid
import unittest
from app.services.retrieval import (
    RetrievalChunk,
    RetrievalResult,
    GroundingResult,
    FALLBACK_MESSAGE,
    RetrievalService,
    build_grounding_context,
)
from app.services.retrieval.embedder import embed_query, get_query_embedder


class TestRetrievalAndGrounding(unittest.TestCase):

    def test_embedder_dimension_and_singleton(self):
        """Verify query embedder singleton initialization and 384-dim vector guarantee."""
        embedder1 = get_query_embedder()
        embedder2 = get_query_embedder()
        self.assertIs(embedder1, embedder2, "Query embedder must be a singleton instance")

        vec = embed_query("Product strategy playbook")
        self.assertEqual(len(vec), 384, f"Query vector must be 384-dimensional, got {len(vec)}")

    def test_invalid_query_embedding(self):
        """Verify empty or whitespace query strings are rejected."""
        with self.assertRaises(ValueError):
            embed_query("")

        with self.assertRaises(ValueError):
            embed_query("   ")

    def test_retrieval_chunk_citation_formatting(self):
        """Verify citation string format: [Episode: Guest Name, Timestamp/Topic]."""
        chunk1 = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Brian Chesky Playbook",
            guest="Brian Chesky",
            timestamp="00:01:27",
            speaker="Brian Chesky",
            chunk_text="We eliminated traditional product management...",
            distance=0.25,
        )
        self.assertEqual(chunk1.to_citation_string(), "[Episode: Brian Chesky, 00:01:27]")

        chunk2 = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="General Growth Tactics",
            guest="Elena Verna",
            timestamp=None,
            speaker="Elena Verna",
            chunk_text="PLG loops drive scalable growth...",
            distance=0.30,
        )
        self.assertEqual(chunk2.to_citation_string(), "[Episode: Elena Verna, Topic]")

    def test_grounding_context_sufficient_evidence(self):
        """Verify that chunks with distance < 0.4 produce sufficient grounding context."""
        c1 = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Brian Chesky Playbook",
            guest="Brian Chesky",
            publish_date="2023-11-01",
            timestamp="00:01:27",
            speaker="Brian Chesky",
            chunk_text="We eliminated traditional product management...",
            source_url="https://youtube.com/watch?v=123",
            distance=0.25,
        )
        c2 = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Marty Cagan Leadership",
            guest="Marty Cagan",
            publish_date="2023-05-15",
            timestamp="00:15:30",
            speaker="Marty Cagan",
            chunk_text="Empowered product teams focus on outcomes...",
            source_url="https://youtube.com/watch?v=456",
            distance=0.35,
        )

        raw_result = RetrievalResult(
            query="What is product leadership?",
            top_k=5,
            distance_threshold=0.4,
            results=[c1, c2],
            execution_time_ms=12.5,
        )

        grounded = build_grounding_context(raw_result)
        self.assertTrue(grounded.sufficient)
        self.assertEqual(len(grounded.results), 2)
        self.assertEqual(len(grounded.citations), 2)
        self.assertIn("[Episode: Brian Chesky, 00:01:27]", grounded.citations)
        self.assertIn("[Episode: Marty Cagan, 00:15:30]", grounded.citations)
        self.assertIsNone(grounded.fallback_message)
        self.assertIn("<transcript_data>", grounded.context)
        self.assertIn("</transcript_data>", grounded.context)

    def test_grounding_context_threshold_boundary(self):
        """Verify strict boundary check: distance < 0.4 (0.3999 accepted, 0.4000 rejected, 0.4001 rejected)."""
        accepted_chunk = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Boundary Episode 1",
            guest="Guest A",
            timestamp="00:05:00",
            chunk_text="Just inside boundary text",
            distance=0.3999,
        )
        exact_boundary_chunk = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Boundary Episode 2",
            guest="Guest B",
            timestamp="00:10:00",
            chunk_text="Exact boundary text",
            distance=0.4000,
        )
        rejected_chunk = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Boundary Episode 3",
            guest="Guest C",
            timestamp="00:15:00",
            chunk_text="Outside boundary text",
            distance=0.4001,
        )

        raw_result = RetrievalResult(
            query="Test boundary query",
            top_k=5,
            distance_threshold=0.4,
            results=[accepted_chunk, exact_boundary_chunk, rejected_chunk],
            execution_time_ms=10.0,
        )

        grounded = build_grounding_context(raw_result)
        self.assertTrue(grounded.sufficient)
        self.assertEqual(len(grounded.results), 1)
        self.assertEqual(grounded.results[0].guest, "Guest A")
        self.assertEqual(grounded.results[0].distance, 0.3999)

    def test_grounding_context_insufficient_evidence_fallback(self):
        """Verify that if all chunks have distance >= 0.4, exact approved fallback is returned."""
        c1 = RetrievalChunk(
            chunk_id=uuid.uuid4(),
            episode_title="Unrelated Episode",
            guest="Guest X",
            timestamp="00:01:00",
            chunk_text="Unrelated information...",
            distance=0.55,
        )

        raw_result = RetrievalResult(
            query="What is quantum computing?",
            top_k=5,
            distance_threshold=0.4,
            results=[c1],
            execution_time_ms=15.0,
        )

        grounded = build_grounding_context(raw_result)
        self.assertFalse(grounded.sufficient)
        self.assertEqual(len(grounded.results), 0)
        self.assertEqual(len(grounded.citations), 0)
        self.assertEqual(grounded.context, "")
        self.assertEqual(grounded.fallback_message, FALLBACK_MESSAGE)
        self.assertEqual(
            grounded.fallback_message,
            "I do not have sufficient information in Lenny's podcast archive to answer this."
        )

    def test_retrieval_service_configuration_bounds(self):
        """Verify top_k and distance_threshold parameter bound checks."""
        with self.assertRaises(ValueError):
            RetrievalService(default_top_k=0)

        with self.assertRaises(ValueError):
            RetrievalService(default_top_k=50)

        with self.assertRaises(ValueError):
            RetrievalService(default_threshold=-0.1)


if __name__ == "__main__":
    unittest.main()
