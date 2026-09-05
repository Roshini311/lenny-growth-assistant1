import asyncio
import logging
import time
from sqlalchemy import select, update
from app.db.database import AsyncSessionLocal
from app.models.models import TranscriptChunk
from app.services.ingestion.embedder import EmbedderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reembed_corpus")


async def main():
    start_time = time.time()
    logger.info("=== Starting Corpus Re-embedding with sentence-transformers/all-MiniLM-L6-v2 ===")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TranscriptChunk.id, TranscriptChunk.chunk_text))
        rows = result.all()
        logger.info(f"Loaded {len(rows)} transcript chunks from PostgreSQL.")

        embedder = EmbedderService(use_fallback=False)
        batch_size = 64
        total_updated = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            texts = [r.chunk_text for r in batch]
            ids = [r.id for r in batch]

            embeddings = embedder.encode_batch(texts, batch_size=batch_size)

            async with AsyncSessionLocal() as update_session:
                for chunk_id, emb in zip(ids, embeddings):
                    stmt = update(TranscriptChunk).where(TranscriptChunk.id == chunk_id).values(embedding=emb)
                    await update_session.execute(stmt)
                await update_session.commit()

            total_updated += len(batch)
            if total_updated % 1000 == 0 or total_updated == len(rows):
                logger.info(f"Re-embedded and updated {total_updated} / {len(rows)} chunks...")

    elapsed = time.time() - start_time
    logger.info(f"=== Corpus Re-embedding Complete! Updated {total_updated} chunks in {elapsed:.2f}s ===")


if __name__ == "__main__":
    asyncio.run(main())
