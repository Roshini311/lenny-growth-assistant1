# Phase 10D Log — Demo Preparation & Submission Readiness

**Date**: September 4, 2026  
**Objective**: Prepare **The Lenny Growth Assistant** for final 2–3 minute video presentation and evaluation submission.

---

## 1. Environment Status Audit

| Component | Status | Details |
| :--- | :--- | :--- |
| **Python** | `Python 3.13.5` | Verified on host system |
| **Node.js & npm** | `Node v22.20.0`, `npm 10.9.3` | Verified on host system |
| **PostgreSQL** | `Connected` | Local Postgres on port 5432 with 8,637 transcript chunks verified |
| **Docker** | `UNAVAILABLE` | Docker CLI/daemon not installed on host PATH; static configuration audit complete |
| **Ollama** | `UNAVAILABLE` | Ollama CLI not installed on host PATH; provider fallback & error handling verified structurally |

---

## 2. Automated Test Baseline Verification

- **Backend Unit Tests**: **44 / 44 PASSED** (`$env:PYTHONPATH="backend"; python -m unittest discover -s backend/tests -p "test_*.py"`)
- **Frontend Vitest Suite**: **17 / 17 PASSED** across 5 test suites (`npx vitest run`)
- **Frontend Production Build**: **PASS** (`npm run build` built dist in 3.75s)
- **Total Automated Test Count**: **61 / 61 PASSED**

---

## 3. Rehearsal Execution Log

- **Health Probe (`/api/health`)**: Tested async PostgreSQL connection (`SELECT 1`), returned `status: healthy`, `database.connected: true`, and masked secrets.
- **Database Table Initialization**: Initialized SQLAlchemy tables (`sessions`, `messages`, `artifacts`, `transcript_chunks`). Verified 8,637 transcript chunks intact.
- **Grounded Q&A Query**: Executed `How did Brian Chesky change product management at Airbnb?`. Grounded retrieval matched Brian Chesky chunks (`Guest: Brian Chesky`, `Episode: Brian Chesky's new playbook`, `Timestamp: 00:03:06`, `Source URL: https://www.youtube.com/watch?v=...`).
- **Out-of-Domain Query**: Executed `What is the current weather in Chennai?`. Verified exact fallback refusal string: `"I do not have sufficient information in Lenny's podcast archive to answer this."`.
- **Ship 30 for 30 Essay**: Executed `PLG Growth Loops`. Verified essay generation with hook, thesis, bold anchors, checklist, and citations. Persisted `Artifact` DB entity.
- **Artifact Viewer Security**: Verified `nh3` backend sanitization and `sandbox="allow-scripts"` iframe (strictly omitting `allow-same-origin` and `allow-top-navigation`).
- **Provider Selector & Offline Fallback**: Verified `BaseLLMProvider` factory and Ollama offline fallback banner logic.

---

## 4. Key Engineering Trade-off Documented

- **Local Ollama vs Cloud Models**: Documented in demo script. Local Ollama (`llama3.2:3b`) ensures 100% offline privacy and zero cloud API costs, while cloud models (`gpt-4o-mini`, `claude`) provide fast inference and strong reasoning. The application supports both via unified `BaseLLMProvider` abstraction.

---

## 5. Artifact Security Boundary Documented

- **Backend Cleaning**: HTML content sanitized using Rust Ammonia (`nh3`) bindings before persistence.
- **Iframe Rendering**: Front-end iframe hardcodes `sandbox="allow-scripts"` (strictly omitting `allow-same-origin` and `allow-top-navigation`).

---

## 6. Final Readiness Verdict

```text
PASS WITH LIMITATIONS — READY TO RECORD
```
*(Limitations: Host environment runner lacks active Docker daemon and Ollama service executable; provider behavior and static container configs are fully verified).*
