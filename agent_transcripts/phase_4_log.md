# Agent Transcript & Decision Log - Phase 4

## Phase Objective
Implement a reliable, repeatable, idempotent transcript ingestion pipeline for the official Lenny's Podcast transcript repository (`https://github.com/ChatPRD/lennys-podcast-transcripts`).

---

## Decisions & Implementation Events

### 1. Ingestion Pipeline Architecture (`backend/app/services/ingestion/`)
- Created modular ingestion pipeline components:
  - `downloader.py`: `fetch_transcript_repository()` downloads the official `ChatPRD/lennys-podcast-transcripts` repository archive zip, extracts to `data/transcripts/`, and reuses local cache unless `--force` is specified.
  - `parser.py`: `parse_transcript_file()` extracts YAML frontmatter metadata (`guest`, `title`, `youtube_url`, `video_id`, `publish_date`, `description`, `duration`, `keywords`) and line-by-line dialogue blocks preserving speaker names and timestamp markers (e.g. `Brian Chesky (00:00:00):`).
  - `chunker.py`: `chunk_transcript()` performs token-bounded dialogue chunking (~500–800 tokens, ~100-token overlap) preserving speaker/timestamp provenance and calculating deterministic SHA-256 `chunk_hash` string values for idempotency.
  - `embedder.py`: `EmbedderService` generates 384-dimensional vector embeddings using `sentence-transformers/all-MiniLM-L6-v2` with deterministic vectorization fallback for offline evaluation.

### 2. Idempotency & Schema Update
- Created migration `002_add_chunk_hash.py` adding `chunk_hash` string column (length 64, unique=True, index=True) to `transcript_chunks` table.
- Ingestion queries existing `chunk_hash` values in database prior to inserting, skipping unchanged chunks and preventing duplicate record generation.

### 3. CLI Executable Script (`backend/scripts/ingest.py`)
- CLI entrypoint supporting parameters:
  - `--repo-url` (default `https://github.com/ChatPRD/lennys-podcast-transcripts`)
  - `--data-dir` (default `data/transcripts`)
  - `--batch-size` (default `32`)
  - `--limit` (optional integer episode limit)
  - `--force` (force archive re-download)
- Emits structured progress logging and final execution summary metrics.

---

## Verification & Execution Results

### 1. Ingestion Unit Test Suite (`tests/test_ingestion.py`)
- Executed `.\venv\Scripts\python.exe -m tests.test_ingestion`:
  - `test_frontmatter_parsing_valid`: **PASSED** (YAML frontmatter metadata & timestamp dialogue).
  - `test_frontmatter_parsing_missing_and_malformed`: **PASSED** (Parent folder fallback & resilience).
  - `test_dialogue_chunking_and_overlap`: **PASSED** (~500–800 token target, 100 overlap, deterministic hash).
  - `test_chunking_idempotency_hash`: **PASSED** (Identical input yields identical `chunk_hash`).
  - `test_embedder_dimension_verification`: **PASSED** (Embedding dimension verified as 384).

### 2. Full Corpus Ingestion Verification & Read-Only Database Audit
- Executed full ingestion script `python scripts/ingest.py` against active PostgreSQL database:
  - **Episodes discovered & parsed**: 303 files (271 valid transcript episodes with dialogue).
  - **Total chunks inserted into DB**: 8,637 chunks.
  - **Idempotency check**: Re-running ingestion skips all 8,637 unchanged chunks in 7.07 seconds.

### 3. PostgreSQL Database State Verification (`scripts/verify_db.py`)
- **Total rows in `transcript_chunks`**: 8,637
- **Distinct `chunk_hash` values**: 8,637 (100% unique)
- **Rows with non-null embeddings**: 8,637 (100% embedded)
- **Embedding dimensionality**: 384 dimensions (`sentence-transformers/all-MiniLM-L6-v2`)
- **Distinct episodes**: 271 episodes
- **Distinct guests**: 298 guests
- **Index status**: Unique `chunk_hash` index active; HNSW vector index configured in schema migration
- **Health Check (`/api/health`)**: HTTP 200 OK (`"database": {"configured": true, "connected": true, "status": "healthy"}`)

### 4. Explanation of Initial Dry-Run Metric Log
- The initial dry-run log output (`New chunks inserted: 0, Unchanged chunks: 0`) occurred because the default container password in `.env` did not match local host Postgres credentials.
- The pipeline correctly detected database unreachability (`db_available = False`), completed parsing and chunk hashing in dry-run mode, and did not commit partial records.
- Once `.env` was configured with active database credentials (`postgresql+asyncpg://postgres:postgres@localhost:5432/lennys_growth_db`), the full corpus was ingested into PostgreSQL.

---

## Deviations & Notes
- No Phase 5 vector retrieval, RAG search endpoints, LLM providers, or Agent SDK logic were implemented during Phase 4.

