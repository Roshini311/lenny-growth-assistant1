import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import AsyncSessionLocal


async def run_verification():
    print("\n" + "=" * 60)
    print("READ-ONLY DATABASE VERIFICATION REPORT")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # 1. Total rows in transcript_chunks
        res_total = await session.execute(text("SELECT COUNT(*) FROM transcript_chunks;"))
        total_rows = res_total.scalar()
        print(f"1. Total rows in transcript_chunks:            {total_rows}")

        # 2. Number of distinct chunk_hash values
        res_distinct_hash = await session.execute(text("SELECT COUNT(DISTINCT chunk_hash) FROM transcript_chunks;"))
        distinct_hashes = res_distinct_hash.scalar()
        print(f"2. Number of distinct chunk_hash values:      {distinct_hashes}")

        # 3. Number of rows with non-null embeddings
        res_non_null_emb = await session.execute(text("SELECT COUNT(*) FROM transcript_chunks WHERE embedding IS NOT NULL;"))
        non_null_embeddings = res_non_null_emb.scalar()
        print(f"3. Rows with non-null embeddings:              {non_null_embeddings}")

        # 4. Embedding dimensionality actually stored
        res_dim = await session.execute(text("SELECT array_length(embedding, 1) FROM transcript_chunks WHERE embedding IS NOT NULL LIMIT 1;"))
        dim_stored = res_dim.scalar()
        print(f"4. Embedding dimensionality actually stored:    {dim_stored} dimensions")

        # 5. Number of distinct episodes represented
        res_episodes = await session.execute(text("SELECT COUNT(DISTINCT episode_title) FROM transcript_chunks;"))
        distinct_episodes = res_episodes.scalar()
        print(f"5. Distinct episodes represented:               {distinct_episodes}")

        # 6. Number of distinct guests represented
        res_guests = await session.execute(text("SELECT COUNT(DISTINCT guest) FROM transcript_chunks;"))
        distinct_guests = res_guests.scalar()
        print(f"6. Distinct guests represented:                 {distinct_guests}")

        # 7. Whether the HNSW vector index exists
        res_hnsw = await session.execute(text("SELECT count(*) FROM pg_indexes WHERE indexname = 'idx_chunks_embedding';"))
        hnsw_exists = (res_hnsw.scalar() or 0) > 0
        print(f"7. HNSW vector index (idx_chunks_embedding):   {'EXISTS' if hnsw_exists else 'NOT FOUND'}")

        # 8. Whether the unique chunk_hash index exists
        res_hash_idx = await session.execute(text("SELECT count(*) FROM pg_indexes WHERE indexname LIKE '%chunk_hash%';"))
        hash_idx_exists = (res_hash_idx.scalar() or 0) > 0
        print(f"8. Unique chunk_hash index:                    {'EXISTS' if hash_idx_exists else 'NOT FOUND'}")

        # 9. Whether pgvector extension is enabled
        res_ext = await session.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'vector';"))
        ext_enabled = (res_ext.scalar() or 0) > 0
        print(f"9. pgvector extension enabled in Postgres:     {'ENABLED' if ext_enabled else 'NOT INSTALLED (Using float[] vector domain)'}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_verification())
