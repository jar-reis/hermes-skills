---
name: memory-deepening
description: Recurring workflows to deepen and enrich Hermes' memory systems (L1, L2, L3, OBn).
version: 1.0.0
author: Hermes
---

# Memory Deepening & Enrichment

## When to Use
- User requests memory hygiene, enrichment, or deepening across the canonical four memory systems.
- Session-end drain or periodic maintenance is needed.
- L1 budget is near/exceeding limits.
- L2 (Honcho/Hindsight) or L3 (Holographic/OB1) shows staleness/duplicates.

## Canonical four memory systems
All deepening workflows target:
1. **Holographic Memory (L1)** — `fact_store`
2. **Honcho (L2)** — `mcp_contextforge_memory_*` + Chroma 8000
3. **Hindsight (L2/L3)** — daemon at `http://localhost:8888` (NOT 9876 — that port is a legacy/stale daemon)
4. **OB1 / OBn (L3)** — `mcp_open_brain_*` + Chroma 8001

Auxiliary: session history (`session_search`) and profile memory (`memory`).

## Workflows

### 1. Session-End Drain (Daily)
**Purpose**: Retain session summary to Hindsight, train Holographic trust scores, and capture key takeaways to Honcho + OB1.
**Script**: `~/.hermes/scripts/session-end-drain.py`

### 2. New Patterns
**Purpose**: Seed all 4 memory layers when a novel workflow (e.g., Greek chorus) emerges.
**Steps**:
1. **Holographic (L1)**: `memory(target="memory", action="add", ...)`
2. **Hindsight (L2)**: `curl -X POST http://localhost:8888/api/lessons -d '{"content": "..."}'`
3. **OBn (L3)**: `mcp_open_brain_capture_thought(content="...")`
4. **Honcho (L2)**: `honcho_reasoning(query="...")`

**Reference**: See [Greek Chorus Pattern](references/greek-chorus-20260619.md) for session-specific detail.
**Steps**:
1. Run at session end:
   ```bash
   python ~/.hermes/scripts/session-end-drain.py
   ```
2. Verify outputs: L3 trust scores updated, Hindsight retains async-queued, Honcho/OB1 receive top 3 takeaways.

### 2. Weekly Maintenance
**Purpose**: Prune L1, deduplicate L3, distill Honcho (ContextForge), and verify OB1/OBn queryability.
**Script**: `~/.hermes/scripts/weekly-memory-maintenance.py`
**Cron**: `0 9 * * 1` (Mondays at 9 AM)
**Steps**:
1. Run manually:
   ```bash
   python ~/.hermes/scripts/weekly-memory-maintenance.py
   ```
2. Review the distillation report before approving any deletes.

### 3. Monthly Synthesis
**Purpose**: Synthesize canonical memory contents into OBn vault notes and cross-fleet shared brain.
**Script**: `~/.hermes/scripts/monthly-synthesis.py`
**Cron**: `0 9 1 * *` (1st of every month at 9 AM)
**Steps**:
1. Run manually:
   ```bash
   python ~/.hermes/scripts/monthly-synthesis.py
   ```

### 4. User-Driven Enrichment
**Purpose**: Capture "remember this" requests into all four canonical systems.
**Skill**: `enrich-memory`
**Usage**:
```bash
hermes skill run enrich-memory --content "..." --entity "..." --category "general" --tags "..."
```

### 5. Recurring Sugar-Worker Sync
**Purpose**: Lightweight background enrichment every 30 minutes.
**Pattern**: dispatch up to 3 `delegate_task` workers:
- **Lane A**: Holographic enrichment (`fact_store`)
- **Lane B**: Honcho + Hindsight sync
- **Lane C**: OB1/OBn deepening + queryability check
**Coordination**: write a ledger file under `.hermes/state/` and update it each cycle.

### 6. Beads Integration
**Purpose**: Synchronize Beads (Dolt-backed issue tracker) with Hermes memory systems (Holographic, Hindsight, Honcho).
**Steps**:
1. **Hindsight Polling**: Create a cron job to poll Beads every 30 minutes and capture lessons.
   ```bash
   bd export --issues --interactions | mcp_hindsight_capture_lesson
   ```
2. **Holographic Updates**: Update facts to reflect Beads' current status.
3. **Honcho Fallback**: Retry local Honcho deployment on a free port (e.g., 8004) if ContextForge quota blocks sync.
4. **Verification**: Confirm Beads issues are retrievable in all memory systems.

**Pitfalls**:
- **ContextForge Quota**: Blocks Honcho sync (fallback to local Honcho).
- **Port Conflicts**: Use `lsof -i :<port>` to identify and kill conflicting processes.
- **Empty Hooks Directory**: Beads lacks webhooks for memory sync; use cron-based polling.

### 7. OBn Targeted Gap-Fill Micro-Deepening
**Purpose**: Strengthen under-represented OB1/OBn topics without broad memory churn.
**Use when** a worker is assigned a bounded L3 deepening lane such as replay boundaries, idempotency keys, writer-of-record, post-write verification, or BRAIN_KEY rotation closeout.
**Steps**:
1. Verify OBn Chroma v2 health first:
   ```bash
   curl -sS -m 5 http://127.0.0.1:8001/api/v2/heartbeat
   ```
   If down, report and skip the dependent lane.
2. Baseline targeted queryability with `mcp_open_brain_search_thoughts`, using topic-specific queries and expected hit thresholds. If the user asks for exact phrase hits, record before/after counts separately from semantic match scores.
3. Capture only 1-2 high-signal, standalone thoughts with `mcp_open_brain_capture_thought`; prefer stable shared namespaces such as `task_id=fleet/memory` or `task_id=fleet/decision`, and set `source` to the actual writer surface.
4. Re-query with distinctive phrases from the captured thoughts; report top-match percentage and whether the new captures are retrievable. For capture verification, use strict filters when possible: `threshold=0.7`, the chosen `task_id`, and the chosen `source`.
5. Do not infer OBn queryability from OB1 capture success alone — the verification query is part of the contract.
6. When exact phrase coverage matters, verify OBn Chroma v2 directly as well as through MCP semantic search: list collections, identify the target collection (often `ob1_ob1_core`), check count, then use `/api/v2/.../collections/<id>/get` with `where_document: {"$contains": "<phrase>"}`. MCP semantic top-N exact counts and Chroma direct containment counts are different evidence types; report both if they diverge.

See `references/obn-gap-fill-exact-phrase-verification-20260619.md` for a copy-paste verifier and reporting convention.

## Real Script Interfaces (added 2026-06-18)

The three scripts under `~/.hermes/scripts/` were rewritten on 2026-06-18 to use real interfaces after the original versions imported non-existent `hermes_tools` functions and crashed. The actual `hermes_tools` module (available in `execute_code` context) only exports: `read_file`, `write_file`, `search_files`, `patch`, `terminal`, `json_parse`, `shell_quote`, `retry`.

**Do NOT import** `hindsight_retain`, `fact_feedback`, `session_search`, `memory`, `hindsight_recall`, `fact_store`, `mcp_contextforge_memory_query`, or `mcp_contextforge_memory_delete_batch` from `hermes_tools` — these functions do not exist there. They are Hermes agent runtime tools, not Python module exports.

The scripts now use:
- **L3 fact_store**: `sqlite3` direct access to `~/.hermes/memory_store.db` (table `facts`, columns: `fact_id`, `content`, `category`, `trust_score`, `helpful_count`, `deleted_at`)
- **L2 Hindsight**: `urllib.request` HTTP calls to `localhost:8888` (gracefully skips if not running)
- **L1 pruning**: `subprocess` calling `~/.hermes/bin/memory-prune.sh`

## Pitfalls
- **L1 Budget**: Prune proactively (≤ 80%). The budget is config-driven: `memory.memory_char_limit` in `~/.hermes/config.yaml` (currently 6000). Do NOT assume 2200 — that was a hardcoded default in `memory-prune.sh` that was fixed on 2026-06-18.
- **L2 Staleness**: Session-end drain ensures freshness. If Hindsight is down (port 8888 connection refused), the drain script skips L2 and continues with L3 — check daemon status separately.
- **Honcho quota**: ContextForge free tier is 200 documents. Proactive distillation required; see `memory-sop` L4 quota section.
- **L3 Trust Scores**: The drain script bumps `trust_score` by 0.05 per "helpful" call. Without regular runs, scores stay at the 0.5 floor. Run `session-end-drain.py` at every session end to train scores progressively.
- **L4 ContextForge Blacklist**: ContextForge.dev is currently blacklisted per security policy (exfiltration issue). The weekly script skips L4 and logs "SKIPPED (ContextForge blacklisted)". Do not re-enable.
- **OBn queryability**: Sugar workers must confirm Chroma 8001 responds each cycle. If OBn is down, capture the outage but keep running.
- **hermes_tools import trap**: Scripts intended to run as standalone `python3` processes MUST NOT import from `hermes_tools`. Use stdlib (`sqlite3`, `urllib`, `subprocess`, `json`) or installed packages instead. `hermes_tools` is only available inside `execute_code` and exports a limited set.

## References
- [Script Real Interfaces (2026-06-18)](references/script-interfaces-20260618.md)
- [Canonical Four Memory Systems (2026-06-19)](references/canonical-four-memory-systems-2026-06-19.md)
- [Beads Integration (2026-06-19)](references/beads-integration-2026-06-19.md)
- [Memory SOP](references/memory-sop.md)
- [Session-End Drain Script](scripts/session-end-drain.py)
- [Weekly Maintenance Script](scripts/weekly-memory-maintenance.py)
- [Monthly Synthesis Script](scripts/monthly-synthesis.py)
- [Memory SOP Audit](references/memory-sop-audit.md)
- [OBn Gap-Fill Exact-Phrase Verification (2026-06-19)](references/obn-gap-fill-exact-phrase-verification-20260619.md)

## Changelog
- v1.1.0 (2026-06-19): aligned workflows with canonical four memory systems; added sugar-worker pattern; added OBn queryability pitfall.
- v1.0.0 (2026-06-18): initial version with real script interfaces.