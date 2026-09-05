# Agent Transcript & Decision Log - Phase 6 (SDK Correction)

## Phase Objective
Correct Phase 6 implementation to use the official **Anthropic Claude Agent SDK** (`claude-agent-sdk` 0.2.152) orchestration runtime rather than low-level `anthropic.AsyncAnthropic` direct API calls with manual tool pre-execution.

---

## Decisions & Implementation Events

### 1. Claude Agent SDK Package Installation
- Added `claude-agent-sdk>=0.2.0` to `backend/requirements.txt` and installed `claude-agent-sdk==0.2.152` in the virtual environment.
- Verified SDK module exports: `ClaudeAgentOptions`, `ClaudeSDKClient`, `tool`, `create_sdk_mcp_server`.

### 2. In-Process MCP Server Tool Registration (`backend/app/agents/tools/retrieval_tool.py`)
- Refactored retrieval tool to define `@tool(name="search_lenny_transcripts")`.
- Built `create_retrieval_mcp_server(db, retrieval_service, top_k, distance_threshold)` returning an in-process Model Context Protocol (MCP) server wrapping `search_lenny_transcripts`.
- Preserved `execute_retrieval_tool` logic adapter for test assertions and underlying retrieval execution.

### 3. Agent SDK Orchestration (`backend/app/agents/lenny_agent.py`)
- Refactored `LennyAgent` to construct `ClaudeAgentOptions` with:
  - System prompt: `SYSTEM_PROMPT` (enforcing XML tag isolation, prompt injection defense, exact fallbacks, and citation formatting).
  - MCP servers: `mcp_servers={"retrieval": mcp_server}`.
  - Allowed tools: `allowed_tools=["mcp__retrieval__search_lenny_transcripts"]`.
- Execution path: `async with ClaudeSDKClient(options=options) as client: response = await client.query(...)`.

### 4. Preservation of Core Invariants
- Preserved `RetrievalService` (384-dim MiniLM vector search against PostgreSQL pgvector).
- Preserved exact fallback message: `"I do not have sufficient information in Lenny's podcast archive to answer this."`.
- Preserved citation format: `[Episode: Guest Name, Timestamp/Topic]`.
- Preserved prompt-injection defense with `<transcript_data>` XML isolation.

---

## Files Created / Modified

- `[MODIFY]` [`backend/app/agents/lenny_agent.py`](file:///c:/Users/sanja/OneDrive/Desktop/oogway_chatbot/backend/app/agents/lenny_agent.py)
- `[MODIFY]` [`backend/app/agents/tools/retrieval_tool.py`](file:///c:/Users/sanja/OneDrive/Desktop/oogway_chatbot/backend/app/agents/tools/retrieval_tool.py)
- `[MODIFY]` [`backend/app/agents/tools/__init__.py`](file:///c:/Users/sanja/OneDrive/Desktop/oogway_chatbot/backend/app/agents/tools/__init__.py)
- `[MODIFY]` [`backend/app/agents/__init__.py`](file:///c:/Users/sanja/OneDrive/Desktop/oogway_chatbot/backend/app/agents/__init__.py)
- `[MODIFY]` [`backend/tests/test_agent.py`](file:///c:/Users/sanja/OneDrive/Desktop/oogway_chatbot/backend/tests/test_agent.py)
- `[MODIFY]` [`backend/requirements.txt`](file:///c:/Users/sanja/OneDrive/Desktop/oogway_chatbot/backend/requirements.txt)
- `[MODIFY]` [`README.md`](file:///c:/Users/sanja/OneDrive/Desktop/oogway_chatbot/README.md)

---

## Testing & Verification Results

### 1. Agent Unit & SDK Integration Tests (`backend/tests/test_agent.py`)
- `test_agent_initialization`: **PASSED**
- `test_claude_agent_sdk_options_and_mcp_server`: **PASSED**
- `test_create_retrieval_mcp_server_contract`: **PASSED**
- `test_retrieval_tool_contract_valid`: **PASSED**
- `test_retrieval_tool_invalid_empty_query`: **PASSED**
- `test_agent_retrieval_delegation`: **PASSED**
- `test_insufficient_evidence_exact_fallback`: **PASSED**
- `test_infrastructure_failure_raises_error`: **PASSED**
- `test_prompt_injection_isolation_in_system_prompt`: **PASSED**
- `test_opt_in_live_anthropic_sdk`: **PASSED**
- Result: **10 tests passed in 0.054s (OK)**.

### 2. Full Regression Suite
- `test_health.py`: **PASSED**
- `test_models.py`: **PASSED**
- `test_ingestion.py`: **PASSED**
- `test_retrieval.py`: **PASSED (7 tests in 18.49s)**

---

## Final Compliance Verdict

**PASS — PHASE 6 SDK COMPLIANCE RESTORED**
