---
name: memory-sop
version: 1.5.0
created: 2026-06-01
updated: 2026-06-12
author: Hermes
description: >
  Fleet-wide Standard Operating Procedure for the triple memory system.
  Covers what goes where, when to write, when to read, and cross-layer
  hygiene. All fleet agents MUST follow this SOP.
---

# Memory SOP — Triple-Layer Procedure

> **Fleet directive:** This is the canonical procedure for how every agent in the fleet
> reads from and writes to memory. No agent may invent ad-hoc memory workflows.

## Definitions
- **Drift**: When memory (Open Brain 1, agent state) and canonical data sources (Google Calendar, Linear, Obsidian) are out of alignment. Detect drift by cross-referencing sources before claiming priorities or workflows.
- **Canonical four memory systems**: The user-mandated set of systems to maintain and inject into every session: **Holographic Memory** (L1 facts), **Honcho** (L2 context DB), **Hindsight** (L2/L3 lesson memory), and **OB1/OBn** (L3 knowledge graph). Session history and profile memory are auxiliary retrieval layers, not part of the canonical four.

### Config Management

#### Updating Memory Providers

**Tool**: `hermes config set` (not direct file edits).

**Workflow**:
1. List current config:
   ```bash
   hermes config show | grep -A 5 "memory:"
   ```
2. Update providers:
   ```bash
   hermes config set memory.provider holographic,contextforge,honcho,hindsight,ob1
   ```
3. Update L1 file paths:
   ```bash
   hermes config set memory.memory_file ~/.hermes/memories/MEMORY.md
   hermes config set memory.user_file ~/.hermes/memories/USER.md
   ```
4. Verify:
   ```bash
   hermes config show | grep -A 5 "memory:"
   ```

**Pitfall**: `hermes config get` does not exist. Use `hermes config show` or `hermes config set`.

**Pitfall**: Memory provider config can silently drift. On 2026-06-24, `memory.provider` was
found set to only `honcho` instead of `hindsight,holographic,honcho` — meaning Hindsight and
Holographic were not active as Hermes providers even though their daemons/DBs were running.
The config likely reverted during a profile simplification or config reload. Always verify
`memory.provider` at session start with `grep 'provider:' ~/.hermes/config.yaml` and confirm
all expected providers are listed. The canonical set for this fleet is:
`hindsight,holographic,honcho`.

#### Prerequisite Gates for Memory Operations

Before any memory operation, verify:
1. **Hermes config writable**: `hermes config show` does not error.
2. **Memory providers reachable**:
   - L1: `fact_store(action='probe', entity='test')` returns `[]`.
   # Hindsight (L2/L3) — port 9876 (canonical as of 2026-06-24)
   curl -s http://localhost:9876/health  # Returns {"status":"healthy","database":"connected"}
   - L3: `mcp_open_brain_search_thoughts --query "test"` returns `[]`.
3. **L1 files exist**:
   ```bash
   test -f ~/.hermes/memories/MEMORY.md && echo "OK" || echo "Missing"
   ```

If any gate fails, STOP and fix before proceeding.

### Layer Map

| Layer | System | Role | Query Interface | State | Count |
|-------|--------|------|-----------------|-------|-------|
| **L1 — Always-Injected** | `memory` (MEMORY.md / USER.md) | Flat text files, injected every turn | Identity, preferences, stable facts the agent needs *before* thinking | ≤ 2200 chars (MEMORY) / ≤ 1375 chars (USER) | Until overwritten or pruned |
| **L2 — Context DB** | **Cortex / ContextForge L2 bridge** via `mcp_contextforge_memory_*` + Chroma **8002** | Local self-hosted ContextForge/Chroma bridge. Historically nicknamed "Honcho clone" but **not Honcho.dev**. | User-state / context layer, recent durable notes, fleet infra snapshots | Limited by ContextForge free tier (200 docs, 500 queries/month) | Permanent until deleted |
- **L2/L3 — Lesson Memory** | **Hindsight** via daemon `http://localhost:9876` | pgvector + local daemon | Lessons, experience memory, episode synthesis | Unlimited (PG auto-manages) | Permanent until explicitly deleted |
- **L1 — Structured Facts** | **Holographic Memory** via `fact_store` (add/search/probe/reason) + `fact_feedback` | SQLite FTS5 at `~/.hermes/memory_store.db` | Entity-attributed facts with trust scoring, contradiction detection, compositional queries | Unlimited (SQLite auto-manages) | Permanent until explicitly deleted |
| **L3 — Knowledge Graph** | **OB1 / OBn** via `mcp_open_brain_*` + Chroma 8001 | Open Brain (Supabase) + ChromaDB | Long-horizon searchable knowledge graph, cross-session user modeling | Unlimited (Open Brain managed) | Permanent until explicitly deleted |
| **L4 — Cross-Fleet Shared (external)** | ContextForge.dev (`mcp_contextforge_memory_*`) | contextforge.dev SaaS, project "Open Brain 1" | Durable facts shared across **all** fleet lanes (Claude, Codex, Kimi, Antigravity, pi, opencode). Read at start, write at drain | 200-document free tier, 500 queries/month | Permanent until deleted |
| **Auxiliary — Session history** | `session_search` | SQLite message store | Raw conversation retrieval, lineage, debugging | N/A | Config-dependent |
| **Auxiliary — Profile memory** | `memory` tool / system prompt | Runtime-injected every turn | User preferences, environment facts, stable conventions | 6000 chars (MEMORY) / 1375 chars (USER) | Until overwritten or pruned |

### Provider stacking

Hermes supports **comma-separated multiple memory providers** simultaneously. All providers' tools coexist with no conflicts (different tool names). Configure with:

```bash
hermes config set memory.provider holographic,honcho,hindsight,ob1
```

**Current fleet state (2026-06-19):**
- **Holographic Memory (L1)**: ✅ ACTIVE — `fact_store` + `fact_feedback` tools live; 108+ facts stored.
- **Honcho (L2)**: ✅ ACTIVE — **Cortex / ContextForge L2 bridge** tracked on port **8002**; older "Honcho Chroma 8000" snapshots are historical/superseded. Query interface: `mcp_contextforge_memory_*` (subject to ContextForge SaaS quota). **This is not Honcho.dev**; the real Hermes Honcho.dev memory provider is currently not active.
- **Hindsight**: ✅ ACTIVE — daemon at `http://localhost:9876` healthy; lesson/experience memory. The daemon has **no root-path web dashboard** — `/` returns `404`; use `/docs` for Swagger UI and `/health` for the health check. Port 9876 is canonical as of 2026-06-24 (the daemon was moved from 8888 back to 9876). If `:9876` is down, try `:8888` as a fallback before treating Hindsight as down.
- **OB1 / OBn (L3)**: ✅ ACTIVE — Open Brain via `mcp_open_brain_*`; ChromaDB on port **8001**. **v2 API endpoints only** — v1 endpoints (`/api/v1/heartbeat`, `/api/v1/collections`) return `Unimplemented` and are expected failures. Must remain queryable every session. **OBn vault ingestion was overhauled 2026-06-22** — now self-healing, auto-syncs every 30min via launchd, 55K+ docs across 12 pods (as of 2026-06-23). See `references/obn-ultra-robust-architecture-20260622.md` for the full architecture. **CRITICAL: never run two `ingest_chroma.py` processes concurrently** — corrupts HNSW index files. **Dimension mismatch errors** (`Inconsistent dimensions in provided embeddings`) indicate a pod's collection was created with a different embedding model than the current one; the fix is to drop and recreate the affected collection.
- **ContextForge SaaS**: ✅ WORKING — MCP bridge healthy, API key valid. `memory_ingest`/`query`/`list` all work. Free tier: **200-document cap**, **500 queries/month**; proactive distillation required. **Quota exhaustion (500/500) blocks Lane B (Honcho + Hindsight Distillation)** — skip Honcho operations, proceed with Hindsight and OBn. **Quota exhaustion (500/500) blocks Lane B (Honcho + Hindsight Distillation)** — skip Honcho operations, proceed with Hindsight and OBn.

**Operational health check (run at session start or before memory work):**
```bash
# Honcho / Cortex
hermes memory status

# Hindsight (L2/L3) — port 9876 (canonical as of 2026-06-24)
curl -s http://localhost:9876/health  # Returns {"status":"healthy","database":"connected"}

# OBn Chroma (Chroma v2; v1 endpoints return Unimplemented and are expected failures)
curl -s http://localhost:8001/api/v2/heartbeat | jq .
```

**Pitfalls**:
- Older notes and skills reference Hindsight on **port 8888**. The live canonical daemon as of 2026-06-24 is on **9876**. If `curl :9876/health` fails, try `:8888` before treating Hindsight as down. Use `:9876` as the canonical write/verification path. The daemon moved back to 9876 after a launchd restart cycle.n path unless a fresh retain+document+recall seal proves otherwise.
- OBn Chroma 8001 **v1 API endpoints return `Unimplemented`**. Direct checks must use `/api/v2`.
- **Memory provider config drift.** The `memory.provider` field in `~/.hermes/config.yaml` can silently revert to a single provider (e.g., just `honcho`) after config edits, profile switches, or Hermes updates. Always verify at session start:
  ```bash
  grep 'provider:' ~/.hermes/config.yaml | grep hindsight
  ```
  If the output doesn't include `hindsight,holographic,honcho`, fix it:
  ```bash
  hermes config set memory.provider hindsight,holographic,honcho
  ```
  Observed 2026-06-24: provider was `honcho` only, missing hindsight and holographic.

- **ContextForge quota exhaustion (500/500) blocks Lane B (Honcho + Hindsight Distillation)** — skip Honcho operations, proceed with Hindsight and OBn.

### Honcho name disambiguation (critical)

The word **"Honcho"** is overloaded across three different systems in this fleet. Confusing them causes incorrect health checks, wrong port expectations, and bad cold-restart verifiers.

| # | System | What it actually is | Port / Interface | Active? |
|---|--------|---------------------|------------------|---------|
| 1 | **Honcho.dev (official)** | Hermes built-in memory provider, Docker Compose `honcho-hermes-local`, local Ollama nomic 768-dim embeddings. Real Honcho.dev service, free tier limitations worked around by self-hosting locally. | `127.0.0.1:8000` | **Yes** — Docker Compose running |
| 2 | **Cortex (DIY clone)** | Local self-hosted L2 memory bridge built on Chroma + ContextForge MCP. Created to bypass Honcho.dev free tier limitations, turned out to be valuable in different ways. Being refined/disambiguated. **Stop calling it Honcho.** | Port **8002** via OrbStack | **Partially** — transition-only |
| 3 | **`honcho` process manager** | Python foreman clone that runs `Procfile` entries (e.g. `web: python -m http.server 8003`) | Port **8003** (static web server) | **Yes** — separate process |

**Correct naming going forward:**
- Use **Honcho.dev** or **Honcho.dev (official)** for the Docker Compose memory provider on :8000.
- Use **Cortex** for port 8002. **Stop calling it Honcho.** It's a DIY clone that turned out to be valuable in different ways — being actively refined and disambiguated alongside the other 4 memory layers.
- Use **`honcho` Procfile runner** or **Honcho process manager** for port 8003.

**Verification:**
```bash
# 1. Honcho.dev plugin status
hermes config show | grep -A 5 'memory\|honcho'

# 2. Procfile runner on 8003
curl -s http://localhost:8003/ | head -5
ps aux | grep '/.venvs/honcho/bin/honcho start'

# 3. Cortex on 8002
curl -s http://localhost:8002/api/v2/heartbeat
ps aux | grep cortex/mcp-server/server.py
```

See `references/honcho-name-disambiguation-2026-06-19.md`.


### ContextForge naming collision (critical)

There are two completely different systems both named "ContextForge":

| | ContextForge SaaS | ContextForge Gateway |
|---|---|---|
| **What it is** | Persistent memory/knowledge graph cloud service | MCP proxy/router (IBM open-source) |
| **URL** | `https://contextforge.dev` | `http://localhost:8090` |
| **Container** | None (cloud SaaS) | `ghcr.io/ibm/mcp-context-forge:latest` |
| **GitHub** | Not open source | `github.com/IBM/mcp-context-forge` |
| **Auth** | API key (Keychain: `contextforge-dev-api-key`) | JWT tokens (generated via Bifrost `:8078`) |
| **Used by** | Hermes + Kimi Cloud for `memory_*` tools | Kimi Cloud as `mcpgateway-a2a` proxy |
| **Launcher** | `contextforge-mcp-keychain.sh` → npm `contextforge-mcp` | Docker Compose in `ai-dev/contextforge-test` |
| **API surface** | `/functions/v1/ingest`, `/query`, `/projects`, `/spaces`, `/relationships` | `/mcp/` (MCP protocol), `/health` |
| **Purpose** | Store and query knowledge items | Route MCP calls to backend services |

The naming collision is historical: IBM named their open-source MCP gateway "mcp-context-forge." The SaaS memory service is also called "ContextForge." They share a name but zero functionality overlap. The L4 layer uses the **SaaS** (contextforge.dev), NOT the Docker gateway at `:8090`.

### L4 Quota Management and Distillation

ContextForge.dev free tier caps at **200 documents**. When the quota is full, new durable facts cannot be ingested. Proactive distillation is required.

**What belongs in L4 (ContextForge):**
- Durable architecture decisions
- Fleet identity and topology
- Security policies
- Current live state snapshots
- Key lessons and pitfalls
- Cross-fleet shared policies

**What does NOT belong in L4:**
- Implementation minutiae (individual script additions, work/bin changes)
- Resolved one-off diagnostics
- Duplicate entries
- Session ephemera (ACT NOW items, auto-capture artifacts)
- YouTube links, creator profiles, reference material (vault is better)
- Facts already stored in Hermes memory or skills

**Distillation workflow:**
1. Export all items to vault backup before any deletes
2. Dry-run delete batches to preview impact
3. Execute deletes in parallel subagent batches
4. Ingest one distilled summary entry documenting the cleanup
5. Verify with `memory_stats`

**Rule of thumb**: If an item describes a single script being added or a resolved issue, it belongs in the vault or session history, not in ContextForge. L4 is the shared brain for what matters across sessions and across agents — keep it curated.

See `mcp/contextforge-mcp/references/bulk-delete-actual-execution-20260618.md` for the full execution pattern.

### Session-start pull — canonical four memory systems

Before any substantive work, verify the canonical four memory systems are reachable and queryable:

1. **Holographic** — `fact_store(action='probe', entity='test')` returns `[]` or facts.
2. **Honcho** — `mcp_contextforge_memory_query --query "test"` returns results or empty list.
3. **Hindsight** — `curl -s http://localhost:9876/health` returns `{"status":"healthy","database":"connected"}`. If this fails, try port 8888 as fallback.
4. **OB1/OBn** — `mcp_open_brain_search_thoughts --query "test"` returns results. If OB1 MCP tools are unavailable, use the CLI: `python3 ~/Documents/=notes/bin/ob1-pull --recent --limit 3`. If the CLI fails with `Errno 8: nodename nor servname provided`, the OB1 DNS fallback patch in ob1-pull should handle it automatically — see `turn-sync/references/ob1-dns-fallback-2026-06-24.md` for the Tailscale MagicDNS issue.

If any canonical system is down, note it in one line, skip dependent lanes, and continue. Never block on a single memory source.

Never block on L4 — if a source is unreachable, note it in one line and continue.
Canonical directive: `=notes/claude/memory/fleet-brain-brief.md`.

Never block on L4 — if a source is unreachable, note it in one line and continue.
Canonical directive: `=notes/claude/memory/fleet-brain-brief.md`.

### L1 file location (profile-dependent)

On the Hermes/MacBook Pro profile, **L1 lives in TWO places**:

  1. `~/.hermes/memories/MEMORY.md` and `~/.hermes/memories/USER.md`
     — the runtime canonical, **injected every turn**. THIS is
     the file the SOP budget caps apply to. Any audit that reads
     the wrong path will produce a false "all healthy" report.
  2. `~/MEMORY.md` and `~/USER.md` — auxiliary copies, less
     frequently edited, kept as a backup

Both sets are within budget. Drift between them is tolerated but
should be reconciled when one side is updated. Other agents in
the fleet may have a single L1 path — always check your profile
config before assuming `~/MEMORY.md` is the canonical location.

The audit skill `note-taking/memory-sop-audit` ships a script
(`memory-prune.sh`) that checks both paths on this profile.

### When NOT to use

- **Lane B (Honcho + Hindsight Distillation)**: Skip when ContextForge query/write quota is exhausted (**500/500**). Proceed with Hindsight and OBn operations; skip Honcho. Use the **deferred-planes manifest** (`~/.hermes/deferred-planes.json`) to track deferred verifications and automatically reverify after quota reset — see `references/deferred-planes-manifest.md` for the JSON schema and workflow.
- **Retrieval-surface outage tolerance**: If ContextForge, Open Brain, Hindsight, or OBn are unreachable or quota-blocked, document the blocker and continue with available retrieval surfaces. Do not block on a single memory source.

### L1 — Always-Injected (MEMORY.md / USER.md)

**USE FOR:**
- User preferences and corrections ("I prefer concise responses")
- Stable environment facts that every turn needs (model config, Tailscale proxy mapping)
- Recurring pitfalls discovered across sessions ("Don't write presence JSON without a verified process")
- Author identity, role, and routing rules

**RULES:**
1. Write **declarative facts**, not instructions to yourself. ❌ "Always respond concisely" → ✅ "User prefers concise responses"
2. Use `§` as section delimiters — the memory system uses them for chunking
3. Keep entries under 200 chars each. If you need more, it belongs in L2.
4. When MEMORY.md hits **80% capacity** (≥1760 chars), proactively prune stale entries to L2 before they're silently dropped
5. NEVER save task progress, session logs, PR numbers, commit SHAs, or ephemeral state here — those belong in session files or daily notes
6. NEVER duplicate facts that are already stable in L2 or L3 — L1 is for *injection priority*, not storage

**USER.md** is identical but for user-profile facts: communication style, preferences, pet peeves.

### L2 — Knowledge Graph (Hindsight)

**USE FOR:**
- Durable facts worth keeping across sessions (7+ days of value)
- Multi-entity relationships
- Episode memory: "On 2026-05-29, user corrected agent verification workflow"
- Semantic search queries: "What do we know about fleet model routing?"

**RULES:**
1. `hindsight_retain(content, context, tags)` — always provide a short `context` label
2. Use `hindsight_recall(query)` for keyword/semantic search
3. Use `hindsight_reflect(query)` for synthesized reasoning across memories
4. Hindsight runs on **port 9876** (canonical as of 2026-06-24). The daemon at `http://localhost:9876` is healthy; `http://localhost:8888` is a fallback.
5. **Primary LLM provider: `ollama-cloud` / `kimi-k2.6:cloud`** (preferred over Moonshot for data-sovereignty). Cerebras or OpenAI as fallback.
- **Hindsight retain HTTP API format.** The `POST /v1/default/banks/{bank_id}/memories`
  endpoint requires `{"items": [{content, context, tags}], "async": true}` — a list
  under `items`, NOT a single item at the top level. Sending `{content: "..."}` returns
  `{"detail": [{"type": "missing", "loc": ["body", "items"], "msg": "Field required"}]}`.
  The Hermes plugin's `hindsight_retain` tool wraps this correctly, but if you're calling
  the HTTP API directly (from `execute_code` or `terminal`), use the `items` array format.
  Async mode (`"async": true`) is REQUIRED — sync mode times out at 30s because LLM
  extraction takes 10-30s per item. Verify retention via the operation endpoint:
  `GET /v1/default/banks/hermes/operations/{operation_id}`.

- **Hindsight retain HTTP API format.** The POST `/v1/default/banks/{bank_id}/memories` endpoint requires an `items` array (not a single content blob). Request schema:
  ```json
  {
    "items": [
      {"content": "...", "context": "...", "tags": ["tag1","tag2"]}
    ],
    "async": true
  }
  ```
  The response returns `{"success": true, "bank_id": "hermes", "items_count": N, "async": true, "operation_id": "..."}`. The old `/memories/retain` path returns `{"detail":"Method Not Allowed"}` — use `/memories` (POST). Check the OpenAPI spec at `http://localhost:9876/openapi.json` for the full schema.

- **Do not confuse bank-wide Hindsight failure counters with per-operation failure.** The stats endpoint's `failed_operations` can include pre-existing daemon failures. A new async retain is successful only when its own operation is `completed` with `result_metadata.extraction_errors_count=0`, `/documents?q=<document_id>` finds the retained document, and semantic recall returns the retained memory; bank-wide historical `failed_operations>0` alone does not invalidate the new write.

- **Tirith security scan blocks `curl | python3` for `localhost` Hindsight queries.** The pattern `curl http://localhost:9876/... | python3 -m json.tool` is flagged as a pipe-to-interpreter risk. **Workaround**: Use direct `curl` + `jq` for verification:
  ```bash
  curl -s -X POST http://localhost:9876/v1/default/banks/hermes/memories/recall \
    -H 'content-type: application/json' \
    -d '{"query":"drain-20260620T0044", "budget":"low"}' | jq .
  ```
  See `references/hindsight-localhost-verification-20260620.md` for details.
7. **Hindsight has no root-path web dashboard.** The daemon returns `{"detail":"Not Found"}` at `/`. Use `/docs` for Swagger UI and `/health` for health checks.
8. If Hindsight is unreachable, fall back to L3. Do NOT fall back to L1 for knowledge-graph queries.
9. The `hindsight` package is split into `hindsight-client` and `hindsight-embed`. The Hermes plugin imports `HindsightEmbedded` from `hindsight`, which is provided by a compatibility shim at `site-packages/hindsight/__init__.py` that composes `DaemonEmbedManager` + `Hindsight` into `HindsightEmbedded`. If you see `ImportError: cannot import name 'HindsightEmbeded'`, re-verify the shim exists and both sub-packages are at matching versions (0.7.1+).

### L3 — Entity-Resolved FTS (Holographic / fact_store)

**USE FOR:**
- Attributed facts about entities: "Dramatis ratified 2026-05-26 as fleet actor model"
- Structured data with trust scoring: factual claims that might be contradicted later
- Compositional queries linking multiple entities: `fact_store(action='reason', entities=['dramatis', 'fleet'])`
- Contradiction detection: `fact_store(action='contradict')` for memory hygiene
- Probe queries: "Everything we know about X" — `fact_store(action='probe', entity='X')`

**RULES:**
1. `fact_store(action='add', content, entity, category, tags)` — always provide an `entity` for attribution
2. Use `category` one of: `user_pref`, `project`, `tool`, `general`
3. Use `tags` comma-separated for cross-cutting queries
4. After using a fact from `fact_store`, rate it with `fact_feedback(action='helpful', fact_id=N)` or `fact_feedback(action='unhelpful', fact_id=N)` — this trains trust scores
5. **L3 trust floor = silent corruption.** If all facts sit at trust_score=0.5
   and `retrieval_count=0`, the L3 store is write-only and
   `reason` / `contradict` queries have no signal. See
   `note-taking/memory-sop-feedback-loop` for the fix.
6. Prefer `fact_store` for entity-attributed claims; prefer `hindsight` for narrative/episodic memory
7. During Holographic audits, filter generic `[TURN]` hook summaries, memory-profile verifier tokens, and other operational telemetry out of durable fact counts. They may live in the raw SQLite store for traceability, but curated-memory verification should count active structured facts that pass `facts_fts` retrieval and `fact_entities` link checks.

### Cross-Layer Hygiene Rules

#### Deduplication
- If a fact exists in L3 with high trust score (> 0.8), do NOT re-add it to L1. L1 is the injection shortcut, not a second store.
- If a fact is in L2, reference it from L1 with a pointer ("Hindsight has fleet config details") rather than duplicating the full content.
- Prune L1 entries that have a stable L2/L3 home every 7 days.

#### Replay/Idempotency Boundaries
- **OBn = broad whole-vault replay surface**: replay boundaries must include last processed timestamp, commit SHA, document ID, cursor, or watermark.
- **OB1 = curated `ob1-core` captures only**: replay must use stable idempotency keys (`source + task_id + content_hash`).
- **Cross-agent handoffs**: use deterministic idempotency keys and upsert/no-op retry behavior to avoid duplicate OB1 thoughts, OBn chunks, Hindsight lessons, vault ledger entries, or ContextForge/Honcho items.
- **Replay closeout rule**: a replay is trusted only at the source plane that owns the write and only after its stable idempotency key re-selects the same active record. Reject cross-plane dedupe or human notes as closeout proof.
- **Holographic Memory L1 as writer-of-record**: completion proof requires `fact_store` write + `facts_fts` retrieval + `fact_entities` links.
- **Source-plane replay fence**: OBn = broad whole-vault replay surface; OB1 = curated `ob1-core` only; deterministic idempotency keys = `source + task_id + content_hash`; retries must upsert/no-op by reselecting the same active source-plane row.

#### BRAIN_KEY Rotation Closeout
- **OB1 blocker**: do not clear until `ob1-token verify`, MCP capture/search, and scoped `ob1-core` sync with `protect_other_sources=true` all succeed.
- **Completion proof**: requires Holographic Memory L1 `facts_fts` retrieval plus `fact_entities` links. Service health alone is not sufficient.
- **Rotation closeout proof-lock**: OB1 BRAIN_KEY blocker closes only after `ob1-token` verification, MCP capture/search, and scoped `ob1-core` sync with `protect_other_sources=true`; completion proof requires Holographic Memory L1 `facts_fts` retrieval plus `fact_entities` links.

### Wiki-Based Knowledge Graphs
- **Trigger**: After saving to L3, ask:
  > *"Save this as a wiki note in `=notes/agent-quiz/` for deeper context? (Y/n)"*
- **If yes**:
  1. Generate a **wiki note** (e.g., `mcp-registration-failures.md`) with:
     - Frontmatter (metadata, sources, confidence).
     - Synthesis (core answer).
     - Related notes (e.g., `[[MCP]]`, `[[bifrost-troubleshooting]]`).
  2. Link to existing notes and skills.
  3. Use `smart_graph` to validate connections.
- **If no**: Skip the wiki layer.
- **Principles**:
  - **Core simplicity**: Flat facts saved to memory.
  - **Wiki is additive**: Only if the user opts in.
  - **No forced complexity**: Wiki notes are standalone (no dependencies).

### Escalation Path
1. **Session starts** → L1 (auto-injected) + `hindsight_recall` for relevant context
2. **During task** → L2 `retain` for major discoveries; L3 `add` for entity-attributed facts
3. **User correction** → Update L1 immediately (it's the one the agent reads next turn). Also `retain` to L2 for durability.
4. **Session ends** → Review: prune L1 if > 80%, `fact_feedback` on all L3 facts used this session, drain durable facts to L2 with `memory-drain.sh`
## Memory Hygiene

### Consolidation Workflow
1. **Remove stale entries**: Delete outdated or redundant entries.
   ```bash
   hermes memory remove --old_text "stale entry"
   ```
2. **Merge related entries**: Combine overlapping entries into a single concise entry.
   ```bash
   hermes memory replace --old_text "old entry" --new_text "merged entry"
   ```
3. **Add new lessons**: Persist new insights immediately after task completion.
   ```bash
   hermes memory add --content "new lesson"
   ```

### Pitfalls
- **Threat patterns**: Avoid paths like `~/.hermes/.env` in memory entries (flagged by consent guard).
- **Size limits**: Memory is capped at **6,000 chars**. Consolidate proactively.
- **MEMORY.md**: ≤ 2200 chars (default; check `memory.memory_char_limit` in `~/.hermes/config.yaml`).
- **USER.md**: ≤ 1375 chars.
- **Proactive Pruning**: At **80% capacity** (≥1760 chars for MEMORY.md), prune stale entries to L2/L4 before they're silently dropped.

### Round-Trip Drift Resolution
- **Delimiter**: Use exact `\n§\n` (no blank lines before/after `§`).
- **Pre-Write Check**: Before adding an entry, read MEMORY.md and ensure:
  - No tables, code blocks, or nested bullet hierarchies.
  - No blank lines around `§`.
  - Total length + new entry ≤ 2200 chars.
- **Drift Fix**: If `memory` tool rejects with "content that wouldn't round-trip":
  1. Backup: `cp MEMORY.md MEMORY.md.bak.$(date +%s)`.
  2. Rewrite MEMORY.md to flat §-delimited format (one entry per section, no tables/code blocks).
  3. Verify: `raw.strip() == '\n§\n'.join(entries)`.
  4. Retry `memory(action='add')`.

See `references/memory-drift-roundtrip-resolution-2026-06-14.md` for worked examples.

---


- **L1 USER.md**: Hard limit 1,375 chars. Proactive pruning at 80% (1,100 chars).
- **L2 Hindsight**: No hard limit. PG auto-manages. Trust the vector index.
- **L3 fact_store**: No hard limit. SQLite auto-manages. Use `contradict` to find and resolve conflicts quarterly.
### Concurrent Memory Edits

**Signal**: `write_file` returns `_warning: was modified since you last read it on disk` when writing to `MEMORY.md` or `USER.md`.

**Root Cause**: Two Hermes sessions (e.g., cron + interactive + headless Codex) are **writing to the same L1 file simultaneously**.

**Pitfalls**:
1. **Silent Overwrite**: The second writer can **overwrite the first’s additions**.
2. **Stale State**: The `memory` tool may reject writes due to **budget limits** if the file was modified by another session.

**Workaround**:
1. **Prefer L2 for Races**: Use `hindsight_retain` for new facts during concurrent sessions.
2. **Consolidate Later**: Merge L2 facts into L1 in a **single-agent cleanup pass** after the race.
3. **Document the Race**: Note the conflict in the session handoff.

**Drift Resolution**:
1. **Backup Drift**:
   ```bash
   cp MEMORY.md MEMORY.md.bak.$(date +%s)
   ```
2. **Merge Manually**:
   ```bash
   diff MEMORY.md MEMORY.md.bak
   ```
3. **Add via `memory` Tool**:
   ```python
   memory(action="add", content="...")
   ```

### Concurrent Git Edits (Fleet Sessions)

**Signal**: `patch` or `write_file` returns `_warning: was modified by sibling subagent '<session_id>' but this agent never read it` when editing a file in the vault or `.hermes/` state.

**Root Cause**: Two or more agents (e.g., Hermes interactive session + cron subagent + headless Codex/Claude Code lane) are editing the same git-tracked file simultaneously. The second writer has a stale in-memory copy.

**Pitfalls**:
1. **Silent overwrite**: the second `patch` can clobber the first agent's additions if the old_string still matches a stale region.
2. **Amend/rebase loops**: attempts to `git commit --amend` and force-push fail because the remote has moved on.
3. **Dirty working tree**: unrelated concurrent edits accumulate, making it unsafe to commit only the intended files.

**Workaround**:
1. **Stop and re-read**: do not patch a file that has a sibling-subagent warning. Re-read the whole file first.
2. **Treat live documents as source of truth**: coordination ledgers, handoffs, or fleet inbox files modified by a cron/sibling agent should be read fresh each time; do not overwrite them blindly.
3. **Safe git workflow**:
   ```bash
   git fetch origin main
   git stash push <only-your-files>
   git pull origin main
   git stash pop
   git add <only-your-files>
   git commit -m "..."
   git push origin main
   ```
4. **Avoid `--amend --no-edit` + force push** when the remote may have concurrent commits. Make a new commit and push normally.
5. **Commit only owned files**: explicitly `git add` the files this session owns; do not `git add -A` when other agents have unrelated dirty state.
6. **Document the conflict**: note concurrent edits in the session handoff and, if needed, append a coordination message to the daily note or fleet inbox instead of overwriting sibling evidence.

See `references/concurrent-git-conflict-resolution-2026-06-19.md`.


**Root Cause**: Two Hermes sessions (e.g., cron + interactive + headless Codex) are **writing to the same L1 file simultaneously**.

**Pitfalls**:
1. **Silent Overwrite**: The second writer can **overwrite the first’s additions**.
2. **Stale State**: The `memory` tool may reject writes due to **budget limits** if the file was modified by another session.

**Workaround**:
1. **Prefer L2 for Races**: Use `hindsight_retain` for new facts during concurrent sessions.
2. **Consolidate Later**: Merge L2 facts into L1 in a **single-agent cleanup pass** after the race.
3. **Document the Race**: Note the conflict in the session handoff.

**Drift Resolution**:
1. **Backup Drift**:
   ```bash
   cp MEMORY.md MEMORY.md.bak.$(date +%s)
   ```
2. **Merge Manually**:
   ```bash
diff MEMORY.md MEMORY.md.bak
   ```
3. **Add via `memory` Tool**:
   ```python
memory(action="add", content="...")
   ```

### References
- [`references/memory-drift.md`](references/memory-drift.md): General drift-resolution workflow.
- [`references/memory-drift-roundtrip-resolution-2026-06-14.md`](references/memory-drift-roundtrip-resolution-2026-06-14.md): Exact `\n§\n` delimiter round-trip failure pattern and verifier.
- [`references/memory-drift-examples.md`](references/memory-drift-examples.md): Example drift scenarios and resolutions.
- [`references/memory-sync-poll-cycle.md`](references/memory-sync-poll-cycle.md): Memory-sync poll cycle workflow, including health checks, lane-specific goals, and quota exhaustion handling.
- [`references/cold-restart-verifier-2026-06-19.md`](references/cold-restart-verifier-2026-06-19.md): Exact verifier commands, port reality, and "ready" criteria for memory systems after a cold restart or fleet handoff.
- [`references/hindsight-port-8888-ui-reality-2026-06-19.md`](references/hindsight-port-8888-ui-reality-2026-06-19.md): Hindsight port history and current canonical (9876 as of 2026-06-24), UI quirks, and retain API format.
- [`references/hindsight-retain-api-format-2026-06-24.md`](references/hindsight-retain-api-format-2026-06-24.md): Hindsight retain HTTP API requires `{items: [...], async: true}` format — not single-item. Includes full endpoint reference and Python examples.
- [`references/memory-sync-sugar-workers-2026-06-19.md`](references/memory-sync-sugar-workers-2026-06-19.md): Sugar-worker poll-cycle session reference with lane goals, quota behavior, and concurrent-edit guard.
- [`references/canonical-four-memory-systems-2026-06-19.md`](references/canonical-four-memory-systems-2026-06-19.md): Reference for the canonical four memory systems.
- [`references/memory-entry-size-limits.md`](references/memory-entry-size-limits.md): L1/L2/L3 budget and size limits.
- [`references/replay-idempotency-brainkey-closeout-20260619.md`](references/replay-idempotency-brainkey-closeout-20260619.md): Replay boundaries, idempotency keys, and BRAIN_KEY rotation closeout.
- [`references/ob1-dns-fallback-20260624.md`](references/ob1-dns-fallback-20260624.md): OB1 Supabase edge function DNS resolution failure on macOS — Tailscale MagicDNS blocks specific subdomains. Fix: socket.getaddrinfo fallback to resolved IPs in ob1-pull script.
- [`references/obn-ingestion-diagnosis-2026-06-22.md`](references/obn-ingestion-diagnosis-2026-06-22.md): OBn "healthy but stale" diagnosis pattern — 5 independent failure points to check when OBn reports ok=true but search returns no recent results. **Note: the staleness described here was RESOLVED on 2026-06-22** — see `references/obn-ultra-robust-architecture-20260622.md` for the current state. This diagnosis reference is kept for future troubleshooting if OBn goes stale again.
- [`references/obn-ultra-robust-architecture-20260622.md`](references/obn-ultra-robust-architecture-20260622.md): OBn post-overhaul architecture — 11 pods, 39K docs, launchd every 30min, retry/fallback logic, health monitoring, RUNBOOK. The system was transformed from stale/frozen to self-healing on 2026-06-22.
- [`references/obn-dimension-mismatch-20260623.md`](references/obn-dimension-mismatch-20260623.md): OBn ChromaDB "Inconsistent dimensions in provided embeddings" error — diagnosis, root cause (embedding model change), and fix (drop + recreate collection).
   ```markdown
   - Memory Conflict: L1 (`MEMORY.md`) was modified by another session. New facts saved to L2 (`hindsight_retain`).
   ```
## Anti-Patterns (DON'T)
### Anti-Patterns (DON'T)

- ❌ **Don't treat L1 as a log.** "Fixed bug #1234 on Tuesday" is ephemeral — it belongs in daily notes, not MEMORY.md
- ❌ **Don't use L2 for real-time state.** "Currently running PID 12345" is stale in 5 minutes — it belongs in process checks, not knowledge graph
- ❌ **Don't skip L3 feedback.** Every fact you retrieve from L3 should get a `fact_feedback` rating — the trust scores are useless without training data
- ❌ **Don't duplicate across all three layers.** Write once to the right layer, reference from others
- ❌ **Don't save API keys, tokens, or secrets in ANY layer.** Those belong in SOPS-encrypted `.env` files only
- ❌ **Don't save procedural instructions in L1.** "Always run pytest before committing" is a skill, not a memory. Put it in `~/.hermes/skills/`
- ❌ **Don't ignore the `§` delimiter.** It's how L1 entries are chunked and retrieved. Omitting it degrades retrieval quality
- ❌ **Don't store audit deltas or session-specific findings in L1.** "Audit v6: 8 CRITICAL, 119% capacity" is a snapshot that becomes stale within hours. It belongs in the audit plan file (`~/.hermes/plans/`) or a daily note, not in MEMORY.md. Stale audit data in L1 is actively harmful — it wastes the 2200-char budget on facts that are wrong by the next session and misleads future agents. If you must reference an audit, store a pointer ("See plans/ for latest fleet audit") not the findings themselves.
- ❌ **Don't act on a plan reference that doesn't exist.** When a user says "the X plan" or "Phase 2 of Y", ground-truth it before responding. Search `~/.hermes/plans/`, search Linear by relevant terms, search session history. If no such artifact exists, say so and ask which of the candidate interpretations they meant. Inventing a plan to fill the gap is fabrication. See `verification-before-completion/references/phantom-artifact-jac165-20260604.md` for the pattern.
- ❌ **Don't keep retrying a memory write that exceeds budget.** The `memory` tool rejects writes that would push L1 over the 2200-char limit, with the response showing the *current* usage count. If you see "Adding this entry (N chars) would exceed the limit", do **not** retry the same patch — first read MEMORY.md, find an entry to compress or remove (e.g., merge two related facts, drop a stale one), then re-apply. Multiple retries with the same new content waste turns and never succeed. Pattern from 2026-06-04: a 994-char new entry was rejected 5+ times because nothing was pruned first.
- ❌ **Don't race-write L1 from parallel sessions.** When two Hermes sessions run concurrently (e.g., cron + interactive + headless Codex on the same machine), they can both target `~/.hermes/memories/MEMORY.md`. The `write_file` tool returns a `_warning: was modified since you last read it on disk` and the second writer can silently overwrite the first's additions. If a parallel session is suspected, prefer L2 (`hindsight_retain`) for new facts during the race, then consolidate into L1 in a single-agent cleanup pass.
- ❌ **Don't write only to L1 when the cold-restart auto-brief reads from OBn.** The Hermes `memory` tool targets `~/.hermes/memories/MEMORY.md` (L1, runtime-injected every turn). The AGENTS.md auto-brief at session start reads a different file first: `~/Documents/=notes/claude/memory/HERMES-MEMORY.md` (OBn, vault-local, survives fleet agent handoffs). For project-level facts that should surface in the **next** session's auto-brief regardless of which agent picks it up, you must also append to OBn. The `memory` tool won't do this for you; use `write_file` (or `execute_code`) to append to HERMES-MEMORY.md explicitly. L1 is for *this* session's reasoning context; OBn is for *next* session's startup briefing. Both are needed for cold-restart resilience. Pattern observed 2026-06-04: red-team project summarized in L1 (memory tool), but the AGENTS.md auto-brief surface (OBn) was empty for that project; a cold-restart session would only have found it by reading the handoff file, and only if the work was cross-referenced there. Fix: dual-write. `references/l1-vs-obn-cold-restart-2026-06-04.md` carries the worked example.
- ❌ **Don't let non-§-delimited content accumulate in MEMORY.md.** The `memory` tool's round-trip guard rejects writes when the file contains content it can't parse back — tables, nested bullet hierarchies, markdown code blocks, raw JSON, or visually harmless blank lines around delimiters. The delimiter must be exactly `\n§\n`; `entry\n\n§\nnext` is not round-trippable. Once the file is in this state, ALL `memory(action='add')` calls fail with "content that wouldn't round-trip through the memory tool." The fix: refresh relevant context first, back up the file, rewrite MEMORY.md to clean §-delimited format (one compact entry per section, flat bullet lists only, no tables, no code blocks, no blank lines around `§`), verify `raw.strip() == '\n§\n'.join(entries)`, then retry with a real `memory(action='add')`. Backups are auto-saved as `.bak.<timestamp>` — integrate any novel entries from the latest backup. Patterns observed: 2026-06-12 nested/table content; 2026-06-14 extra delimiter whitespace plus oversized consolidated entries. See `references/memory-drift-roundtrip-resolution-2026-06-14.md`.
- ❌ **Don't treat skill updates as optional.** **Be ACTIVE — most sessions produce at least one skill update, even if small.** This is a **standing requirement**, not an afterthought. If a signal fired (correction, technique, pitfall, missing step), update the relevant skill immediately. Prefer patching an existing skill (loaded or umbrella) over creating a new one. If no skill covers the class, create a new CLASS-LEVEL umbrella skill. Never leave a skill update for "later" — later never comes. **Signals that warrant action:**
  - User corrected your style, tone, format, legibility, or verbosity
  - User corrected your workflow, approach, or sequence of steps
  - Non-trivial technique, fix, workaround, or tool-usage pattern emerged
  - A loaded skill turned out to be wrong, missing a step, or outdated
  - User explicitly said "remember this" or "don’t do that again"
- ❌ **Don't create session-specific skills.** Skills must be at the **class level** (e.g., "Debugging Memory Consolidation Workflows"), not tied to one-off sessions (e.g., "debug-X-today"). If the proposed name only makes sense for today's task, it's wrong — fall back to updating an existing skill or adding a support file.
- ❌ **Don't ignore ContextForge quota exhaustion (500/500).** Lane B (L2 Honcho + Hindsight Distillation) is skipped when ContextForge query/write quota is exhausted. Proceed with Hindsight and OBn operations; skip Honcho. This is a **durable constraint** that belongs in the skill's "When NOT to use" section.
- ❌ **Don't ignore retrieval-surface outages (ContextForge, Open Brain, Hindsight, OBn).** If any canonical memory system is unreachable or quota-blocked, document the blocker and continue with available retrieval surfaces. Do not block on a single memory source. This is a **durable constraint** that belongs in the skill's "Anti-Patterns" section.
- ❌ **Don't assume OBn Chroma 8001 v1 API is still active.** v1 endpoints (`/api/v1/heartbeat`, `/api/v1/collections`) return `Unimplemented`. Direct checks must use `/api/v2`. This is a **durable provider quirk** that belongs in the skill's pitfalls section.
- ❌ **Don't clear the BRAIN_KEY rotation blocker prematurely.** OB1 `ob1-core-sync` remains blocked until `ob1-token verify`, MCP capture/search, and scoped sync with `protect_other_sources=true` all succeed. Completion proof requires Holographic Memory L1 `facts_fts` retrieval plus `fact_entities` links. Service health alone is not sufficient. This is a **durable constraint** that belongs in the skill's "Anti-Patterns" section.
- ❌ **Don't let replay boundaries or idempotency keys be implicit.** Every retryable cross-agent handoff must record its replay boundary (last processed timestamp, commit SHA, document ID, cursor, or watermark) and use a deterministic idempotency key (`source + task_id + content_hash`). Repeated runs must upsert or no-op on conflict rather than duplicate OB1 thoughts, OBn chunks, Hindsight lessons, vault ledger entries, or ContextForge/Honcho items. Memory-plane writers-of-record are: vault ledger as SSOT, OB1 for curated facts, OBn for semantic corpus, Hindsight for lessons, ContextForge/Honcho for project L2. Do not promote handoff narrative state as durable until the exact post-write verification query and result for each affected plane are recorded, otherwise stale narrative state can leak into memory.
- ❌ **Don't ignore ContextForge quota exhaustion (500/500).** Lane B (L2 Honcho + Hindsight Distillation) is skipped when ContextForge query/write quota is exhausted. Proceed with Hindsight and OBn operations; skip Honcho. This is a **durable constraint** that belongs in the skill's "When NOT to use" section.
- ❌ **Don't ignore retrieval-surface outages (ContextForge, Open Brain, Hindsight, OBn).** If any canonical memory system is unreachable or quota-blocked, document the blocker and continue with available retrieval surfaces. Do not block on a single memory source. This is a **durable constraint** that belongs in the skill's "Anti-Patterns" section.
- ❌ **Don't assume OBn Chroma 8001 v1 API is still active.** v1 endpoints (`/api/v1/heartbeat`, `/api/v1/collections`) return `Unimplemented`. Direct checks must use `/api/v2`. This is a **durable provider quirk** that belongs in the skill's pitfalls section.
- ❌ **Don't clear the BRAIN_KEY rotation blocker prematurely.** OB1 `ob1-core-sync` remains blocked until `ob1-token verify`, MCP capture/search, and scoped sync with `protect_other_sources=true` all succeed. Completion proof requires Holographic Memory L1 `facts_fts` retrieval plus `fact_entities` links. Service health alone is not sufficient. This is a **durable constraint** that belongs in the skill's "Anti-Patterns" section.
- ❌ **Don't let replay boundaries or idempotency keys be implicit.** Every retryable cross-agent handoff must record its replay boundary (last processed timestamp, commit SHA, document ID, cursor, or watermark) and use a deterministic idempotency key (`source + task_id + content_hash`). Repeated runs must upsert or no-op on conflict rather than duplicate OB1 thoughts, OBn chunks, Hindsight lessons, vault ledger entries, or ContextForge/Honcho items. Memory-plane writers-of-record are: vault ledger as SSOT, OB1 for curated facts, OBn for semantic corpus, Hindsight for lessons, ContextForge/Honcho for project L2. Do not promote handoff narrative state as durable until the exact post-write verification query and result for each affected plane are recorded, otherwise stale narrative state can leak into memory.
- ❌ **Don't clear the BRAIN_KEY rotation blocker prematurely.** OB1 `ob1-core-sync` remains blocked until `ob1-token verify`, MCP capture/search, and scoped sync with `protect_other_sources=true` all succeed. Completion proof requires Holographic Memory L1 `facts_fts` retrieval plus `fact_entities` links. Service health alone is not sufficient. This is a **durable constraint** that belongs in the skill's "Anti-Patterns" section.
- ❌ **Don't conflate reachability with freshness for ingestion pipelines.** OBn's status check returned `ok: true` because ChromaDB pods were queryable, but no new data had been ingested in 2+ months. Any pipeline health check must include a **timestamp-based freshness check** (last ingest, last sync log, state DB row count), not just a connectivity probe. The "healthy but stale" anti-pattern is especially dangerous because green status lights mask complete data freezes. See `references/obn-ingestion-diagnosis-2026-06-22.md`.
- ❌ **Don't let cron jobs lose lessons when memory providers are unavailable.** Cron jobs must capture lessons even when primary memory providers (e.g., ContextForge Hindsight, Open Brain) are unreachable or quota-limited. Use **fallback memory providers** (Open Brain, session transcript, local file) to ensure lessons are not lost. See `references/cron-memory-fallback.md` for the fallback hierarchy and quota handling.
- ❌ **Don't clear the BRAIN_KEY rotation blocker prematurely.** OB1 `ob1-core-sync` remains blocked until `ob1-token verify`, MCP capture/search, and scoped sync with `protect_other_sources=true` all succeed. Completion proof requires Holographic Memory L1 `facts_fts` retrieval plus `fact_entities` links. Service health alone is not sufficient. This is a **durable constraint** that belongs in the skill's "Anti-Patterns" section.

## Quick Health Check

Run this at session start or before memory work to verify the canonical four memory systems are reachable and queryable:

```bash
# Holographic Memory (L1)
fact_store(action='probe', entity='test')  # Returns [] or facts

# Honcho (L2) — ContextForge SaaS (quota-dependent)
mcp_contextforge_memory_query --query "test"  # Returns results or empty list

# Hindsight (L2/L3) — port 9876 (canonical as of 2026-06-24)
curl -s http://localhost:9876/health  # Returns {"status":"healthy","database":"connected"}

# OBn (L3) — Chroma 8001, v2 API only
curl -s http://localhost:8001/api/v2/heartbeat  # Returns {"nanosecond heartbeat":...}
```

If any system is down, note it in one line, skip dependent lanes, and continue. Never block on a single memory source.

```
WHAT                        → WHERE          → TOOL
─────────────────────────────────────────────────────────────
"User hates X"              → L1 USER.md     → memory(action='add', target='user')
"User prefers Y"            → L1 USER.md     → memory(action='add', target='user')
"Environment: Z runs on :P" → L1 MEMORY.md   → memory(action='add', target='memory')
"Correction: don't do W"    → L1 + L2/L3     → memory + fact_store / hindsight_retain
"Fleet runtime pattern"     → L2 + L3        → hindsight_retain + fact_store
"Dramatis ratified 05-26"  → L3             → fact_store(action='add', entity='dramatis')
"Every session needs XYZ"   → SKILL          → skill_manage(action='create')
"Today I fixed bug X"      → daily note      → write_file(memory/YYYY-MM-DD.md)
"User said Z, then we did Y" → L2/L3 (async)  → hindsight_retain / fact_store
"Project X built in 2026-06" → L1 + OBn      → memory + mcp_open_brain_capture_thought
"Update memory providers"   → Hermes config  → hermes config set memory.provider holographic,honcho,hindsight,ob1
"Canonical memory systems"  → SKILL + L1/L2/L3 → memory-sop skill + all four stores
```

## Automated Memory Sync — Sugar-Worker Poll Cycles

For long-running memory hygiene (e.g., overnight or multi-hour runs), use **lightweight background subagent polls** rather than one big synchronous sweep. This pattern keeps memory systems enriched without exceeding model context thresholds or monopolizing the interactive session.

### When to use
- User asks to "synchronize and enrich all memory systems" over an extended window.
- You need to balance depth against context/performance limits.
- Multiple memory layers (Holographic, Honcho, Hindsight, OB1/OBn) need periodic attention.

### Poll-cycle shape
| Lane | Target layer | Typical goal |
|------|--------------|--------------|
| **Lane A** | L1 Holographic Memory | `fact_store` probe/enrich one high-value entity |
| **Lane B** | L2 Honcho + Hindsight | ContextForge distillation + Hindsight retention |
| **Lane C** | L3 OB1/OBn | Capture + verify searchable thoughts |

### Procedure
1. **Baseline**: record counts for all four canonical systems and current port/health state.
2. **Schedule**: create a cron job (e.g., `every 30m`, 18 repetitions for 9 hours) that dispatches up to 3 concurrent `delegate_task` workers per cycle.
3. **Bound workers**: each worker must be narrow (1–2 memory writes max), avoid destructive deletes, and report exact IDs/verifications.
4. **Quota awareness**: when ContextForge query/write quota is exhausted (500/500), skip Lane B Honcho operations; continue with Hindsight and OBn.
5. **Concurrent-edit guard**: the coordination ledger may be modified by the cron itself. Treat it as a live document; re-read before patching and never overwrite it blindly.
6. **Verification**: every cycle should confirm at least Hindsight (`:9876/health`) and OBn (`:8001/api/v2/heartbeat`) are reachable.

### Artifacts
- Coordination ledger: `.hermes/state/memory-sync-YYYY-MM-DD.md`
- Handoff at wrap: `.hermes/handoffs/session-<id>.md`
- Verifier script: `scripts/verify-memory-sync-state.sh`
- Session reference: `references/memory-sync-sugar-workers-2026-06-19.md`

## Companion skills (this fleet)

  - `note-taking/memory-sop-audit`          — one-shot L1/L2/L3 audit
  - `note-taking/memory-sop-drain`          — L2 session-end retain
  - `note-taking/memory-sop-feedback-loop`  — L3 fact_feedback procedure
  - `note-taking/hindsight-memory-provider` — daemon setup + multithreading

## Fleet Notification Protocol

When this SOP is updated:
1. Save the updated skill to `~/.hermes/skills/note-taking/memory-sop/SKILL.md`
2. If live fanout is explicitly requested, post a summary through a verified Hermes `messaging` target: "Memory SOP vN updated — [key changes]. All agents must follow the triple-layer procedure."
3. Append to fleet inbox: `=notes/claude/coordination/inbox-fleet.md`
4. Update L2 with `hindsight_retain` noting the version change
5. If L1 MEMORY.md references the SOP, update the pointer

## Changelog

- v1.9.0 (2026-06-24): added deferred-planes manifest pattern (`~/.hermes/deferred-planes.json`) for tracking deferred memory-plane verifications and automatically reverifying after quota reset. See `references/deferred-planes-manifest.md`.
- v1.8.0 (2026-06-24): corrected Hindsight port from 8888 back to **9876** (daemon moved during launchd restart cycle); updated all 8 port references in SKILL.md; added Hindsight retain HTTP API format documentation (`items` array schema, correct `/memories` endpoint); added memory provider config drift pitfall; added OB1 DNS fallback reference for Tailscale MagicDNS issue; updated hindsight-port reference file with port history and retain API docs.
- v1.7.2 (2026-06-23): updated OBn state to 55K+ docs across 12 pods; added dimension mismatch pitfall and reference `references/obn-dimension-mismatch-20260623.md` for "Inconsistent dimensions in provided embeddings" error pattern.
- v1.7.1 (2026-06-19): added cold-restart verifier reference `references/cold-restart-verifier-2026-06-19.md` with exact commands, port reality, and "ready" criteria; clarified that OB1 must be *connected*, not just listed, and that Honcho/Cortex 8002 instability blocks full cold-restart readiness.
- v1.7.0 (2026-06-19): added "Automated Memory Sync — Sugar-Worker Poll Cycles" section with lane definitions, quota exhaustion handling, and concurrent-edit guard; added reference `references/memory-sync-sugar-workers-2026-06-19.md` and verifier script `scripts/verify-memory-sync-state.sh`.
- v1.6.0 (2026-06-19): corrected Hindsight port from 9876 to **8888** based on live verification; added note that Hindsight has no root-path web dashboard (use `/docs` for Swagger, `/health` for health); updated canonical-four-memory-systems reference and session-start health check; added `references/hindsight-port-8888-ui-reality-2026-06-19.md`.
- v1.5.0 (2026-06-12): added **L4 — Cross-Fleet Shared (external)** layer to the Layer Map
  (OB1 + contextforge.dev) and a **Session-start pull** directive. Hermes already *reaches*
  contextforge.dev via the bifrost `contextforge` client (60 tools); this makes pulling it
  at session start a hard step and de-conflates contextforge.dev (persistent-memory SaaS,
  project "Open Brain 1") from the IBM `mcpgateway` at `:8090`. Part of the fleet-wide
  memory-injection rollout across the HACcK quintet (Hermes/Antigravity/Claude/Codex/Kimi).
  Canonical directive: `=notes/claude/memory/fleet-brain-brief.md`.
- v1.4.0 (2026-06-04): anti-pattern #13 added (L1 vs OBn cold-restart
  surface mismatch). L1 (`~/.hermes/memories/MEMORY.md`) is
  runtime-injected every turn; OBn
  (`~/Documents/=notes/claude/memory/HERMES-MEMORY.md`) is the
  file the AGENTS.md auto-brief reads FIRST at session start. The
  `memory` tool only writes to L1. For project-level facts that
  should surface in the next session's auto-brief regardless of
  which agent picks it up, you must also append to OBn explicitly
  via `write_file`. Pattern observed 2026-06-04 (red-team project:
  in L1, not in OBn, would have been invisible to a cold-restart
  session). New reference:
  `references/l1-vs-obn-cold-restart-2026-06-04.md`.
- v1.3.0 (2026-06-04): anti-pattern #11 (L1 budget retry loop) and #12
  (parallel-session write race on L1) added. The retry-loop
  pattern was observed repeatedly in one session — five `memory`
  tool calls in a row rejected because no pruning step was
  interleaved. The parallel-write pattern is the cause of the
  recurring "external edit warning" in `write_file` when
  multiple Hermes sessions share a machine.
- v1.2.0 (2026-06-04): anti-pattern #10 added (phantom-artifact
  trap on plan/ticket references); L1 file location note sharpened
  to call out the runtime canonical is `~/.hermes/memories/`, not
  `~/`, and any audit reading the wrong path produces false
  "all healthy" reports.
- v1.1.0 (2026-06-03): L1 dual-location (memories/ + ~/) added; LLM provider
  corrected to `kimi-k2.6:cloud`; Hindsight retain `async: true` rule
  promoted to MUST; anti-pattern #9 added; fact-count note dropped (was
  per-store, not per-SOP); companion-skills section added.
- v1.0.0 (2026-06-01): initial ratification.
