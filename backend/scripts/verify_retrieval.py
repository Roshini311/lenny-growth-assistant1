import asyncio
import logging
from app.db.database import AsyncSessionLocal
from app.services.retrieval import RetrievalService, FALLBACK_MESSAGE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_retrieval")

TEST_QUERIES = [
    "What does Lenny's podcast say about product-market fit?",
    "How do successful product teams prioritize their roadmap?",
    "What are common mistakes founders make when scaling?",
    "What is the current weather in Chennai?",
]


async def run_verification():
    service = RetrievalService()
    print("=" * 70)
    print("REAL CORPUS RETRIEVAL VERIFICATION AUDIT")
    print("=" * 70)

    async with AsyncSessionLocal() as db:
        for idx, query in enumerate(TEST_QUERIES, 1):
            print(f"\n--- QUERY {idx}: '{query}' ---")
            raw_res = await service.search_raw(db=db, query=query, top_k=5)
            grounded_res = await service.search(db=db, query=query, top_k=5)

            print(f"Retrieval Latency: {raw_res.execution_time_ms:.2f} ms")
            print(f"Top 5 Raw Distance Scores:")
            for c in raw_res.results:
                print(f"  - Distance: {c.distance:.4f} | Guest: {c.guest} | Episode: '{c.episode_title}' | Timestamp: {c.timestamp or 'N/A'}")

            print(f"Sufficient Evidence (< 0.4 threshold): {grounded_res.sufficient}")
            if grounded_res.sufficient:
                print(f"Filtered Grounded Results Count: {len(grounded_res.results)}")
                print(f"Generated Citations:")
                for cite in grounded_res.citations:
                    print(f"  * {cite}")
            else:
                print(f"Fallback Output: '{grounded_res.fallback_message}'")
                assert grounded_res.fallback_message == FALLBACK_MESSAGE

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETED CLEANLY")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_verification())
