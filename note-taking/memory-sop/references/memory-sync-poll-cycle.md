---
name: memory-sync-poll-cycle
created: 2026-06-19
updated: 2026-06-19
author: Hermes
---

# Memory-Sync Poll Cycle — Coordination Workflow

## Overview
- **Purpose**: Enrich the canonical four memory systems (Holographic, Honcho, Hindsight, OB1/OBn) via lightweight background workers dispatched every 30 minutes.
- **Duration**: 9 hours (18 polls).
- **Model**: `kimi-k2.7-code` via Ollama Cloud.
- **Coordination file**: `/Users/jack.reis/Documents/=notes/.hermes/state/memory-sync-2026-06-19.md`.

## Poll Cycle Tasks
1. **Read the coordination ledger**: Determine current poll number by counting completed entries in the `Poll Schedule` table.
2. **Check run status**: If poll 18 or status says "completed", emit `"RUN COMPLETE — no action"` and exit silently.
3. **Health check**:
   - **Honcho (Chroma 8000)**: Skip if quota exhausted (500/500).
   - **OBn (Chroma 8001)**: Verify `/api/v2/heartbeat` → `200 OK`.
   - **Hindsight (Port 8888)**: Verify `http://localhost:8888/health` → `200 {"status":"healthy","database":"connected"}`.
4. **Dispatch workers**: Up to 3 parallel `delegate_task` workers:
   - **Lane A (Holographic Enrichment)**: Add 1-2 concise facts via `fact_store` (or direct SQLite if unavailable).
   - **Lane B (Honcho + Hindsight Distillation)**: Retain 1-2 durable notes into Hindsight (skip Honcho if quota exhausted).
   - **Lane C (OB1/OBn Deepening)**: Capture 1-2 high-signal thoughts via `mcp_open_brain_capture_thought`.
5. **Update ledger**: Append a `Poll Results` section with poll number, timestamp, lane status, and facts/thoughts created.
6. **Update Poll Schedule**: Mark the current poll as `completed`.

## Constraints
- **Honcho/ContextForge quota**: Skip Lane B if quota exhausted (500/500).
- **OBn Chroma v2 API**: Use `/api/v2/heartbeat`; v1 endpoints return `Unimplemented`.
- **Hindsight port**: Use `8888`; `9876` is stale/outdated.
- **Holographic Memory**: Use direct SQLite access if `fact_store` tool is unavailable in subagents.

## Key Topics to Enrich
- Replay boundaries and deterministic idempotency keys (`source + task_id + content_hash`).
- BRAIN_KEY rotation closeout criteria (`ob1-token verify`, MCP capture/search, scoped `ob1-core` sync with `protect_other_sources=true`).
- Memory-plane writer-of-record and post-write verification contract.

## Example Poll Results
```markdown
### Poll 11 — 2026-06-19 ~05:04 CDT

#### Lane A — Holographic Enrichment (completed)
- **Facts added**: #216 (replay boundary/idempotency), #217 (BRAIN_KEY rotation closeout).

#### Lane B — L2 Honcho + Hindsight Distillation (hindsight-only)
- **Notes retained**: 2 durable notes about replay/idempotency and BRAIN_KEY rotation closeout.

#### Lane C — OB1/OBn Deepening (completed)
- **Thoughts captured**: 2 high-signal thoughts; verified OBn queryability at **80.7%** and **83.0%** match.
```