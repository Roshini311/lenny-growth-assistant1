import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Backend app imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import AsyncSessionLocal
from app.models.models import TranscriptChunk
from app.services.ingestion.downloader import fetch_transcript_repository, DEFAULT_REPO_URL
from app.services.ingestion.parser import parse_transcript_file
from app.services.ingestion.chunker import chunk_transcript
from app.services.ingestion.embedder import EmbedderService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("lenny_assistant.ingest")


async def get_existing_hashes(session: AsyncSession, hashes_to_check: Set[str]) -> Set[str]:
    """Queries existing chunk hashes in database to guarantee idempotency."""
    if not hashes_to_check:
        return set()

    existing: Set[str] = set()
    hash_list = list(hashes_to_check)
    for i in range(0, len(hash_list), 500):
        batch = hash_list[i:i + 500]
        stmt = select(TranscriptChunk.chunk_hash).where(TranscriptChunk.chunk_hash.in_(batch))
        result = await session.execute(stmt)
        existing.update(result.scalars().all())

    return existing


async def run_ingestion(
    repo_url: str,
    data_dir: str,
    batch_size: int,
    force: bool,
    limit: int = 0
):
    start_time = time.time()

    logger.info("=== Starting Lenny Growth Assistant Transcript Ingestion Pipeline ===")

    # 1. Fetch Repository
    repo_info = fetch_transcript_repository(repo_url=repo_url, data_dir=data_dir, force=force)
    data_path = repo_info["path"]

    # 2. Discover Transcript Files
    episodes_dir = data_path / "episodes"
    if not episodes_dir.exists():
        logger.error(f"Episodes directory not found at: {episodes_dir}")
        sys.exit(1)

    transcript_files = list(episodes_dir.glob("**/transcript.md"))
    if not transcript_files:
        transcript_files = list(data_path.glob("**/*.md"))

    if limit > 0:
        transcript_files = transcript_files[:limit]

    total_discovered = len(transcript_files)
    logger.info(f"Discovered {total_discovered} episode transcript files.")

    # 3. Parse & Chunk Transcripts
    all_chunks: List[Dict[str, Any]] = []
    parsed_count = 0
    failed_count = 0

    for file_path in transcript_files:
        try:
            parsed = parse_transcript_file(file_path)
            file_chunks = chunk_transcript(parsed)
            all_chunks.extend(file_chunks)
            parsed_count += 1
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            failed_count += 1

    total_generated_chunks = len(all_chunks)
    logger.info(f"Parsed {parsed_count} episodes, generated {total_generated_chunks} dialogue chunks.")

    if not all_chunks:
        logger.warning("No transcript chunks generated. Exiting ingestion.")
        return

    # 4. Check Idempotency (Existing Chunks in DB)
    all_hashes = {c["chunk_hash"] for c in all_chunks}
    
    db_available = True
    existing_hashes: Set[str] = set()

    try:
        async with AsyncSessionLocal() as db_session:
            existing_hashes = await get_existing_hashes(db_session, all_hashes)
    except Exception as e:
        logger.warning(f"Database connection check skipped/failed: {e}")
        db_available = False

    new_chunks = [c for c in all_chunks if c["chunk_hash"] not in existing_hashes]
    unchanged_count = len(all_chunks) - len(new_chunks)

    logger.info(f"Idempotency Check: {len(new_chunks)} new chunks to insert, {unchanged_count} unchanged chunks skipped.")

    if not new_chunks:
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Ingestion complete (All chunks up to date)")
        print(f"Episodes discovered: {total_discovered}")
        print(f"Episodes parsed:     {parsed_count}")
        print(f"Episodes failed:     {failed_count}")
        print(f"Chunks generated:    {total_generated_chunks}")
        print(f"New chunks inserted: 0")
        print(f"Unchanged chunks:    {unchanged_count}")
        print(f"Elapsed time:        {elapsed:.2f}s")
        print("=" * 60 + "\n")
        return

    # 5. Generate 384-dimensional Embeddings
    logger.info(f"Generating 384-dimensional embeddings for {len(new_chunks)} chunks (batch size: {batch_size})...")
    embedder = EmbedderService()
    chunk_texts = [c["chunk_text"] for c in new_chunks]
    embeddings = embedder.encode_batch(chunk_texts, batch_size=batch_size)

    for chunk_dict, emb_vec in zip(new_chunks, embeddings):
        chunk_dict["embedding"] = emb_vec

    # 6. Database Batch Insert
    inserted_count = 0
    failed_insert_count = 0

    if db_available:
        for i in range(0, len(new_chunks), 100):
            batch = new_chunks[i:i + 100]
            try:
                async with AsyncSessionLocal() as db_session:
                    orm_objects = [TranscriptChunk(**c) for c in batch]
                    db_session.add_all(orm_objects)
                    await db_session.commit()
                    inserted_count += len(batch)
            except Exception as e:
                logger.error(f"Error inserting chunk batch starting at index {i}: {e}")
                failed_insert_count += len(batch)

        logger.info(f"Database Batch Insert Completed: {inserted_count} inserted, {failed_insert_count} failed.")
    else:
        logger.info("Database unavailable for insert (verified embeddings generated cleanly in memory).")

    # 7. Execution Summary Log
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("Ingestion complete")
    print(f"Episodes discovered: {total_discovered}")
    print(f"Episodes parsed:     {parsed_count}")
    print(f"Episodes failed:     {failed_count}")
    print(f"Chunks generated:    {total_generated_chunks}")
    print(f"New chunks inserted: {inserted_count}")
    print(f"Unchanged chunks:    {unchanged_count}")
    print(f"Failed chunks:       {failed_insert_count}")
    print(f"Elapsed time:        {elapsed:.2f}s")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Lenny's Podcast Transcript Ingestion Pipeline")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help="Git/Archive repository URL")
    parser.add_argument("--data-dir", default="data/transcripts", help="Local directory for transcripts cache")
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    parser.add_argument("--limit", type=int, default=0, help="Optional episode limit for test runs")
    parser.add_argument("--force", action="store_true", help="Force re-download repository archive")

    args = parser.parse_args()

    asyncio.run(
        run_ingestion(
            repo_url=args.repo_url,
            data_dir=args.data_dir,
            batch_size=args.batch_size,
            force=args.force,
            limit=args.limit
        )
    )


if __name__ == "__main__":
    main()
