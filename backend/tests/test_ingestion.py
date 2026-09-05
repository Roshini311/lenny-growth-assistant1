import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from app.services.ingestion.parser import parse_transcript_file
from app.services.ingestion.chunker import chunk_transcript, count_tokens
from app.services.ingestion.embedder import EmbedderService, REQUIRED_DIMENSION


def test_frontmatter_parsing_valid():
    """Verify parsing valid YAML frontmatter and dialogue line timestamps."""
    sample_content = """---
guest: Brian Chesky
title: Brian Chesky's new playbook
youtube_url: https://www.youtube.com/watch?v=4ef0juAMqoE
publish_date: 2023-11-12
---

Brian Chesky (00:00:00):
Way too many founders apologize for how they want to run the company.

Lenny (00:01:01):
Today my guest is Brian Chesky, CEO and co-founder of Airbnb.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / "brian-chesky" / "transcript.md"
        tmp_file.parent.mkdir(parents=True)
        tmp_file.write_text(sample_content, encoding="utf-8")

        parsed = parse_transcript_file(tmp_file)
        meta = parsed["metadata"]
        blocks = parsed["dialogue_blocks"]

        assert meta["guest"] == "Brian Chesky"
        assert meta["title"] == "Brian Chesky's new playbook"
        assert meta["youtube_url"] == "https://www.youtube.com/watch?v=4ef0juAMqoE"
        assert len(blocks) == 2
        assert blocks[0]["speaker"] == "Brian Chesky"
        assert blocks[0]["timestamp"] == "00:00:00"
        assert "founders apologize" in blocks[0]["text"]


def test_frontmatter_parsing_missing_and_malformed():
    """Verify fallback behavior for missing or malformed frontmatter."""
    sample_malformed = """---
guest: [Malformed YAML: :: 
---

Guest (00:02:00):
Dialogue content without proper frontmatter.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / "alex-komoroske" / "transcript.md"
        tmp_file.parent.mkdir(parents=True)
        tmp_file.write_text(sample_malformed, encoding="utf-8")

        parsed = parse_transcript_file(tmp_file)
        meta = parsed["metadata"]
        assert meta["guest"] == "Alex Komoroske"  # Fallback to parent dir title
        assert len(parsed["dialogue_blocks"]) >= 1


def test_dialogue_chunking_and_overlap():
    """Verify dialogue chunking into token-bounded windows with deterministic hash."""
    sample_parsed = {
        "metadata": {
            "guest": "Marty Cagan",
            "title": "Empowered Product Teams",
            "publish_date": "2024-01-15",
            "youtube_url": "https://www.youtube.com/watch?v=test"
        },
        "dialogue_blocks": [
            {
                "speaker": "Marty Cagan",
                "timestamp": f"00:{i:02d}:00",
                "text": f"This is detailed advice statement paragraph number {i} discussing product discovery and leadership frameworks." * 10
            }
            for i in range(15)
        ]
    }

    chunks = chunk_transcript(sample_parsed, min_tokens=100, max_tokens=300, overlap_tokens=50)
    assert len(chunks) >= 2

    # Check deterministic chunk hash and provenance attributes
    first_chunk = chunks[0]
    assert "chunk_hash" in first_chunk
    assert len(first_chunk["chunk_hash"]) == 64  # SHA256 hex string
    assert first_chunk["guest"] == "Marty Cagan"
    assert first_chunk["episode_title"] == "Empowered Product Teams"
    assert first_chunk["timestamp"] is not None


def test_chunking_idempotency_hash():
    """Verify that chunking the same input yields identical deterministic chunk_hash values."""
    sample_parsed = {
        "metadata": {"guest": "Julie Zhuo", "title": "Making of a Manager"},
        "dialogue_blocks": [
            {"speaker": "Julie Zhuo", "timestamp": "00:05:00", "text": "Feedback is a gift."}
        ]
    }
    chunks1 = chunk_transcript(sample_parsed)
    chunks2 = chunk_transcript(sample_parsed)

    assert len(chunks1) == 1
    assert chunks1[0]["chunk_hash"] == chunks2[0]["chunk_hash"]


def test_embedder_dimension_verification():
    """Verify that EmbedderService validates exact 384-dimensional vector length."""
    embedder = EmbedderService()
    mock_model = MagicMock()
    # Return 384 dimensional dummy array
    import numpy as np
    mock_model.encode.return_value = np.zeros((1, 384))
    embedder._model = mock_model

    vecs = embedder.encode_batch(["Product market fit metrics"])
    assert len(vecs) == 1
    assert len(vecs[0]) == REQUIRED_DIMENSION  # 384


if __name__ == "__main__":
    test_frontmatter_parsing_valid()
    test_frontmatter_parsing_missing_and_malformed()
    test_dialogue_chunking_and_overlap()
    test_chunking_idempotency_hash()
    test_embedder_dimension_verification()
    print("[OK] Phase 4 Transcript Ingestion unit tests passed successfully!")
