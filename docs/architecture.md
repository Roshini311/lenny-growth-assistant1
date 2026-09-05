# Architecture Documentation

## Project: The Lenny Growth Assistant
**Version**: 1.2.0  
**Author**: Lead Forward Deployed Engineer  
**Status**: Approved & Complete (Phases 0–10A)

---

## 1. Architecture Overview

**The Lenny Growth Assistant** is built following a decoupled, layered system architecture. The frontend is a React 18 + Vite Single Page Application (SPA) styled with Tailwind CSS, while the backend is an asynchronous Python FastAPI application powering an agent orchestrator (`LennyAgent`) built on the **Anthropic Claude Agent SDK (`claude-agent-sdk==0.2.152`)**.

```mermaid
graph TD
    User([User / Evaluator]) <--> Frontend[React 18 + Vite + TypeScript SPA]
    
    subgraph Frontend Components
        Frontend --> UIState[Chat & Session State]
        Frontend --> ProviderSel[Provider Selector: Ollama / OpenAI / Claude]
        Frontend --> ArtifactViewer[Sandboxed Artifact Viewer <iframe sandbox='allow-scripts'>]
    end

    Frontend <-->|REST & SSE Streaming /api| NginxProxy[Nginx Reverse Proxy /api]
    NginxProxy <--> FastAPI[FastAPI Backend API Router]

    subgraph Backend Core
        FastAPI --> LennyAgent[LennyAgent Orchestrator - Anthropic Claude Agent SDK]
        
        LennyAgent --> Tool1[search_lenny_transcripts MCP Tool]
        LennyAgent --> Tool2[ship30_essay_generator]
        LennyAgent --> Tool3[artifact_service]

        Tool1 --> RetrievalService[Retrieval Service]
        Tool2 --> Ship30Service[Ship 30 for 30 Skill Engine]
        Tool3 --> ArtifactService[Artifact Engine & nh3 Sanitizer]
    end

    subgraph Database Layer
        RetrievalService <--> EmbedEngine[sentence-transformers MiniLM-L6-v2]
        RetrievalService <--> Postgres[(PostgreSQL 16 + pgvector)]
        FastAPI <--> Postgres
    end

    subgraph LLM Provider Abstraction
        LennyAgent <--> BaseLLMProvider[BaseLLMProvider Abstract Interface]
        BaseLLMProvider <--> OllamaProvider[OllamaProvider - llama3.2:3b]
        BaseLLMProvider <--> OpenAIProvider[OpenAIProvider - gpt-4o-mini]
        BaseLLMProvider <--> ClaudeProvider[ClaudeProvider - claude-agent-sdk]
    end

    OllamaProvider -.-> OllamaHost[Local Ollama Service :11434]
    OpenAIProvider -.-> CloudAPI[OpenAI Cloud API Endpoint]
    ClaudeProvider -.-> AnthropicAPI[Anthropic Claude API Endpoint]
```

---

## 2. Component Responsibilities

| Component | Layer | Primary Responsibility |
| :--- | :--- | :--- |
| **React + Vite SPA** | Frontend | Renders the dual-pane workspace, manages active session state, consumes SSE streaming API endpoints (`/api/chat`), formats markdown content, and hosts the sandboxed `<iframe>` artifact viewer. |
| **Nginx Reverse Proxy** | Frontend Container | Proxies `/api/` requests to `http://backend:8000/api/` with `proxy_buffering off;` for SSE streaming in Docker. |
| **FastAPI Router** | Backend API | Exposes REST endpoints (`/api/sessions`, `/api/health`, `/api/artifacts`, `/api/essays/ship30`) and SSE streaming (`/api/chat`), manages CORS, handles request validation. |
| **LennyAgent** | Agent Orchestrator | Anthropic Claude Agent SDK orchestrator that receives conversation state, plans execution, invokes MCP tools (`search_lenny_transcripts`), and enforces grounded responses. |
| **RetrievalService** | RAG / Service | Generates embeddings for user queries using `sentence-transformers/all-MiniLM-L6-v2`, queries PostgreSQL pgvector using cosine distance (`<->`), applies similarity threshold filtering ($\text{distance} < 0.4$), and formats citation metadata. |
| **Ship30EssayGenerator** | Skill Module | Formats structured ~1,250-word essays from grounded retrieval context, applying specific narrative hooks, short paragraphs, bold emphasis, and actionable checklists. |
| **ArtifactService & Sanitizer** | Artifact Module | Sanitizes generated HTML using Rust Ammonia (`nh3`), persists artifacts to PostgreSQL, and formats payloads for frontend iframe rendering. |
| **BaseLLMProvider** | LLM Abstraction | Abstract base class defining async streaming generator interfaces (`generate_stream`) and provider health check contracts. |
| **OllamaProvider** | LLM Implementation | Connects to local Ollama instance (`llama3.2:3b`), handles stream parsing, execution timeouts, and provides health status. |
| **OpenAIProvider** | LLM Implementation | Connects to OpenAI API (`gpt-4o-mini`), handles API key authentication, streaming response parsing, and error recovery. |
| **ClaudeProvider** | LLM Implementation | Connects to Anthropic API via `claude-agent-sdk==0.2.152`. |
| **PostgreSQL + pgvector** | Database | Stores sessions, chat messages, sources, artifacts, and transcript chunk vectors (8,637 chunks) with HNSW index. |
| **Ingestion Pipeline** | Data Pipeline | Download script (`scripts/ingest.py`) that fetches `ChatPRD/lennys-podcast-transcripts`, parses YAML frontmatter, chunks dialogue (500–800 tokens, 100 overlap), computes embeddings, and seeds pgvector. |

---

## 3. RAG Retrieval & Grounding Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as React Frontend
    participant API as FastAPI Router
    participant Agent as LennyAgent (Agent SDK)
    participant Tool as search_lenny_transcripts (MCP)
    participant RAG as RetrievalService
    participant DB as Postgres + pgvector
    participant LLM as BaseLLMProvider

    User->>FE: Ask question ("What is Brian Chesky's product playbook?")
    FE->>API: POST /api/chat {session_id, message, provider}
    API->>Agent: Run agent loop with prompt & session context
    Agent->>Tool: Execute search_lenny_transcripts(query)
    Tool->>RAG: search(query="What is Brian Chesky's product playbook?")
    RAG->>RAG: Embed query using MiniLM-L6-v2 (384-dim vector)
    RAG->>DB: SELECT chunk_text, metadata, (embedding <-> query_vec) AS distance FROM transcript_chunks ORDER BY distance LIMIT 5
    DB-->>RAG: Return top chunks with distance scores
    
    alt Min Vector Distance >= 0.4 (Insufficient Information)
        RAG-->>Tool: Return insufficient info signal
        Tool-->>Agent: Signal empty retrieval context
        Agent-->>API: Stream Fallback: "I do not have sufficient information in Lenny's podcast archive to answer this."
        API-->>FE: SSE Stream fallback response
    else Min Vector Distance < 0.4 (Relevant Chunks Found)
        RAG-->>Tool: Return filtered chunks + metadata (guest, title, date, timestamp, speaker)
        Tool-->>Agent: Grounded context payload (<transcript_data>)
        Agent->>LLM: Stream completion with system prompt + grounded context
        LLM-->>Agent: SSE response chunks + citations [Episode: Guest Name, Timestamp/Topic]
        Agent-->>API: Stream formatted text + sources payload
        API-->>FE: SSE Stream chunks to UI
    end
```

---

## 4. Claude Agent SDK Path (Phase 6 Architecture)

The Phase 6 agent integration uses the official **Anthropic Claude Agent SDK**:

```text
User Query
  ↓
LennyAgent.run() (backend/app/agents/lenny_agent.py)
  ↓
ClaudeSDKClient & ClaudeAgentOptions
  ↓
In-Process MCP Server (create_retrieval_mcp_server)
  ↓
@tool(name="search_lenny_transcripts")
  ↓
RetrievalService.search()
  ↓
PostgreSQL pgvector (HNSW Index, distance < 0.4)
  ↓
Grounded Transcript Evidence
  ↓
Claude Agent Response & Citations
```

---

## 5. Database Schema & Data Model

```mermaid
erDiagram
    Session ||--o{ Message : "contains"
    Session ||--o{ Artifact : "owns"
    Message ||--o{ Artifact : "generates"
    Session {
        uuid id PK
        string title
        timestamp created_at
        timestamp updated_at
    }
    Message {
        uuid id PK
        uuid session_id FK
        string role
        text content
        jsonb sources
        timestamp created_at
    }
    Artifact {
        uuid id PK
        uuid session_id FK
        uuid message_id FK
        string artifact_type
        string title
        text content
        timestamp created_at
    }
    TranscriptChunk {
        uuid id PK
        string chunk_hash UK
        string guest
        string episode_title
        string youtube_url
        string publish_date
        string timestamp
        string speaker
        text chunk_text
        vector_384 embedding
        timestamp created_at
    }
```

---

## 6. Security & Sandboxed Iframe Architecture

1. **Backend HTML Sanitization**: All HTML artifacts pass through `ArtifactSanitizer` wrapping `nh3` (Rust Ammonia Python bindings) before persistence. Dangerous tags (`<script>`, `<iframe>`, `object`), inline event attributes (`onerror`, `onclick`), and `javascript:` URIs are stripped.
2. **Frontend Iframe Isolation**: HTML artifacts render in an `<iframe>` with strict sandbox flags:
   ```html
   <iframe sandbox="allow-scripts" srcdoc="..." title="Artifact Preview" />
   ```
3. **Security Directives Omitted**:
   - `allow-same-origin`: **Omitted** to assign a unique opaque origin, blocking access to parent DOM, `document.cookie`, `localStorage`, or session tokens.
   - `allow-top-navigation`: **Omitted** to prevent untrusted scripts from navigating the parent browser window.
4. **Prompt Injection Defense**: Retrieved transcript content is placed inside `<transcript_data>` XML tags and treated as unprivileged source data.

---

## 7. Verification & Automated Test Status

```text
Backend Unit Test Suite: 44 / 44 PASSED
Frontend Vitest Suite:    17 / 17 PASSED
Total Automated Tests:   61 / 61 PASSED (100% Pass Rate)
Frontend Build:          PASS (npm run build)
```
