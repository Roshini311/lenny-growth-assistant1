# Product Requirements Document (PRD)

## Project: The Lenny Growth Assistant
**Version**: 1.2.0  
**Author**: Lead Forward Deployed Engineer  
**Status**: Approved & Verified (Phases 0–10A Complete)

---

## 1. Product Overview

**The Lenny Growth Assistant** is an enterprise-grade full-stack RAG (Retrieval-Augmented Generation) application designed to transform 260+ episodes (8,637 dialogue chunks) of Lenny's Podcast transcripts into a reliable, interactive product and growth knowledge assistant.

The assistant provides grounded answers to complex product management, growth, leadership, and startup strategy questions using **ONLY** retrieved transcript content. It features exact source episode/guest/timestamp citations, graceful fallback when information is missing from the archive, session-based conversation persistence, a "Ship 30 for 30" style essay generator, and a secure side-panel Artifact Viewer for rendering generated Markdown and sandboxed HTML/CSS content.

---

## 2. Target Persona

### Primary Users
1. **Product Managers (PMs & Senior PMs)**: Seeking tactical frameworks (e.g., product-market fit metrics, prioritization methods, continuous discovery) backed by experienced product leaders (Brian Chesky, Marty Cagan, Shreyas Doshi, Elena Verna).
2. **Growth Leaders & Growth Engineers**: Looking for battle-tested growth playbooks (PLG vs sales-led, retention loops, pricing strategy, viral loops).
3. **Founders & Product-Focused Operators**: Requiring rapid, grounded insights on scaling organizations, hiring, leadership, and fundraising from top VCs and founders.

### User Need & Problem Solution
These professionals need immediate, authoritative answers to tactical product problems without spending hours scrubbing through hundreds of hours of podcast audio or raw transcripts. The assistant delivers exact, grounded advice in seconds, accompanied by verifiable citations and actionable artifacts.

---

## 3. Problem Statement

Lenny's Podcast archive represents one of the highest-density knowledge sources for product management and growth in the software industry. Accessing specific insights across 260+ episodes presents significant challenges:

1. **Information Discovery**: Keyword search fails to capture semantic meaning or nuanced advice.
2. **Hallucination & Misinformation**: Generic LLMs hallucinate product advice or blend unverified internet advice with expert opinions.
3. **Verification & Attribution**: Operators require exact source attribution (guest name, episode title, publication date, timestamp) to trust and share insights.
4. **Actionability**: Raw transcript text is conversational; operators need structured takeaways, strategy frameworks, or ready-to-use artifacts (HTML widgets, strategy essays).

---

## 4. Grounding & Fallback Specification

- **Similarity Distance Threshold**: Cosine distance threshold $< 0.4$ (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions).
- **Exact Approved Fallback String**: When no transcript chunk satisfies distance $< 0.4$, the assistant MUST return:
  > `I do not have sufficient information in Lenny's podcast archive to answer this.`

---

## 5. Functional Requirements Summary

| ID | Feature | Implementation | Status |
| :--- | :--- | :--- | :--- |
| **FR-01** | Grounded Q&A & Streaming | SSE streaming endpoint `POST /api/chat` | **VERIFIED** |
| **FR-02** | Vector Retrieval Grounding | PostgreSQL pgvector (`all-MiniLM-L6-v2`, $<0.4$) | **VERIFIED** |
| **FR-03** | Source Citations | Formatted badges `[Episode: Guest Name, Timestamp]` | **VERIFIED** |
| **FR-04** | Session Persistence | `POST /api/sessions` & `GET /api/sessions/{id}` | **VERIFIED** |
| **FR-05** | Multi-Provider Selection | Ollama (`llama3.2:3b`), OpenAI (`gpt-4o-mini`), Claude Agent SDK | **VERIFIED** |
| **FR-06** | Ship 30 for 30 Essay Generator | Grounded ~1,250-word structured essays | **VERIFIED** |
| **FR-07** | Artifact Engine & Viewer | Markdown & HTML viewer with `sandbox="allow-scripts"` iframe | **VERIFIED** |
| **FR-08** | System Health Diagnostics | `GET /api/health` with secret-safe status | **VERIFIED** |

---

## 6. Security & Operational Requirements

- **HTML Sanitization**: Rust Ammonia (`nh3`) bindings sanitize HTML artifacts on backend before persistence.
- **Iframe Isolation**: HTML artifacts render in an `<iframe>` enforcing `sandbox="allow-scripts"`, strictly omitting `allow-same-origin` and `allow-top-navigation`.
- **Secret Isolation**: Secrets loaded via `.env`; API keys excluded from `/api/health` responses.
- **Test Coverage**: 61 automated tests passing (44 backend + 17 frontend).
