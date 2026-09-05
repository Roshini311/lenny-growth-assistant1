# 🎙️ The Lenny Growth Assistant — Demo Script (2–3 Minutes)

This script provides a concise, step-by-step guide for presenting **The Lenny Growth Assistant** during a 2–3 minute camera-on evaluation demonstration.

---

## Demo Overview & Objective

- **Project**: The Lenny Growth Assistant
- **Target Audience**: Evaluation Committee / Engineering Hiring Manager
- **Core Value Proposition**: Grounded product and growth knowledge retrieval from 260+ episodes (8,637 dialogue chunks) of Lenny's Podcast with source citations, strict fallback refusal, and sandboxed artifact rendering.
- **Estimated Duration**: 2 Minutes 30 Seconds

---

## Timeline & Step-by-Step Spoken Script

### 0:00 – 0:30 | Introduction & Architecture (30s)
> *"Hello! Today I'm demonstrating **The Lenny Growth Assistant** — an enterprise-grade full-stack RAG application built to transform 260+ episodes of Lenny's Podcast into a grounded product and growth knowledge assistant.*
> 
> *Our architecture combines a React 18 and Vite SPA frontend, a FastAPI asynchronous Python backend, and PostgreSQL with pgvector for 384-dimensional vector retrieval. For agent orchestration, we integrate the official Anthropic Claude Agent SDK using an in-process MCP server."*

### 0:30 – 1:15 | Grounded Q&A & Source Attribution (45s)
> *"Let's test a grounded product strategy question:*
> 
> **[Action: Type prompt in Chat Panel]**  
> `How did Brian Chesky change product management at Airbnb?`
> 
> *"Notice the Server-Sent Events streaming in real time. The assistant retrieves relevant transcript chunks using pgvector cosine search filtered by a strict distance threshold under 0.4.*
> 
> *Directly beneath the answer, we see clickable source citations — such as `[Episode: Brian Chesky, 00:01:27]`. Opening the Citation Drawer reveals the verified episode title, guest name, timestamp, speaker, and direct link."*

### 1:15 – 1:45 | Out-of-Domain Refusal & Prompt Injection Security (30s)
> *"To ensure zero hallucination, our system enforces hard threshold refusal. Watch what happens when we ask an out-of-domain question:*
> 
> **[Action: Type prompt in Chat Panel]**  
> `What is the current weather in Chennai?`
> 
> *"Because no transcript chunk meets our vector similarity threshold, the model refuses to guess and returns the exact approved fallback string: `I do not have sufficient information in Lenny's podcast archive to answer this.`*
> 
> *Furthermore, transcript contents are isolated inside `<transcript_data>` XML tags, treating transcript text strictly as unprivileged data to defend against prompt injection."*

### 1:45 – 2:15 | Ship 30 for 30 Essay & Sandboxed Artifact Viewer (30s)
> *"Now let's generate a structured leadership artifact using our Ship 30 for 30 Essay Skill:*
> 
> **[Action: Click 'Ship 30 Generator' button $\rightarrow$ Enter topic `PLG Growth Loops` $\rightarrow$ Click Generate]**
> 
> *"The generator produces a ~1,250-word essay with a hook, thesis, bold anchors, actionable checklist, and citations. The generated essay automatically opens in our right-hand side panel Artifact Viewer.*
> 
> *For HTML visual artifacts, the backend sanitizes content using Rust Ammonia (`nh3`), and the frontend renders it inside an isolated iframe configured with `sandbox="allow-scripts"` — strictly omitting `allow-same-origin` and `allow-top-navigation` to prevent XSS or session cookie access."*

### 2:15 – 2:30 | Provider Abstraction & Engineering Trade-off (15s)
> *"Finally, our provider architecture abstracts model execution via a `ProviderFactory`. Users can seamlessly switch between local Ollama (`llama3.2:3b`), Cloud OpenAI (`gpt-4o-mini`), and Anthropic Claude without modifying the core RAG retrieval pipeline.*
> 
> **[Key Trade-off Note]**: *Local Ollama provides 100% offline privacy and zero API cost, while cloud providers offer lower latency. Our design supports both transparently. Thank you!"*

---

## Reliable Demo Prompts Reference Table

| Section | Demo Prompt | Expected Outcome / Citation |
| :--- | :--- | :--- |
| **Grounded Q&A** | `How did Brian Chesky change product management at Airbnb?` | Grounded answer with citation `[Episode: Brian Chesky, 00:01:27]` |
| **Out-of-Domain Refusal** | `What is the current weather in Chennai?` | Exact fallback: `"I do not have sufficient information in Lenny's podcast archive to answer this."` |
| **Ship 30 Essay Generator** | `PLG Growth Loops` | Grounded ~1,250-word essay opening in Artifact Viewer |

---

## Environmental Backup Plan

- **If Ollama is Offline**: Explain provider independence; show that Ollama returns a structured HTTP 503 error with UI warning banner, and switch provider dropdown to Cloud OpenAI/Claude.
- **If Docker is Unavailable**: Explain that container configurations (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`) were statically validated, and run local dev services (`uvicorn` + Vite dev server).
