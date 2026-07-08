# Memory Search Interface API Reference

Structured reference for all memory search interfaces available to `cited_recall.py`.

## 1. OB1 (Open Brain) — `mcp_open_brain_search_thoughts`

| Field | Value |
|---|---|
| **MCP Tool** | `mcp_open_brain_search_thoughts` |
| **CLI** | `ob1-pull` (bridge script) |
| **Returns** | JSON array: `result` (text), `match_score` (0–100%), `captured`, `type`, `vault_path` |
| **Citations** | Via `vault_path` + `captured` timestamp |
| **Auth** | Token from `~/.hermes/bin/ob1-token.sh export` → `OB1_API_KEY` |
| **Rate limits** | None documented |
| **Status** | ⚠️ Token path needs fixing — "no API key available" in live test |

## 2. OBn (Federated ChromaDB) — `mcp_fleet_memory_fleet_memory_obn_search`

| Field | Value |
|---|---|
| **MCP Tool** | `mcp_fleet_memory_fleet_memory_obn_search` |
| **Returns** | JSON: `ok`, `returncode`, `stdout` (federated results from pods) |
| **Citations** | Via `source` field (pod identifier: `[core]`, `[rib_recovery]`) |
| **Auth** | Local (no auth) |
| **Rate limits** | None |
| **Status** | ⚠️ Direct HTTP to localhost:8001 returns 405 — needs MCP bridge path |

## 3. Session History — `session_search` / SQLite FTS5

| Field | Value |
|---|---|
| **Hermes tool** | `session_search` |
| **CLI** | SQLite FTS5 on `~/.hermes/state.db` (table: `messages_fts`) |
| **Returns** | Rows: `id`, `content`, `role`, `session_id`, `title` |
| **Citations** | Via `session_id` + message `id` |
| **Auth** | Local filesystem |
| **Rate limits** | None |
| **Pitfall** | Content is raw text including serialized JSON from tool calls — noisy for LLM synthesis |

## 4. Hindsight — localhost:8888

| Field | Value |
|---|---|
| **MCP Tool** | `mcp_fleet_memory_fleet_memory_hindsight_retain` (write only) |
| **API** | `GET http://127.0.0.1:8888/search?q=<query>&limit=<N>` |
| **Returns** | JSON array: `content`, `score`, `id`/`fact_id`, `created_at`, `tags` |
| **Citations** | Via `fact_id` |
| **Auth** | Local (no auth) |
| **Rate limits** | None |
| **Status** | ⚠️ Returns 404 — daemon may not be running or endpoint path differs |

## 5. Hermes memory_store — SQLite FTS5

| Field | Value |
|---|---|
| **DB** | `~/.hermes/memory_store.db` (table: `facts_fts`, backed by `facts`) |
| **Returns** | `fact_id`, `content`, `category`, `tags`, `trust_score` |
| **Citations** | Via `fact_id` |
| **Auth** | Local filesystem |
| **Rate limits** | None |
| **Note** | 2826 facts indexed as of 2026-06-22 |

## 6. Honcho — `honcho_search` / `honcho_reasoning`

| Field | Value |
|---|---|
| **MCP Tools** | `honcho_search`, `honcho_reasoning`, `honcho_context`, `honcho_conclude` |
| **Returns** | `honcho_search`: raw excerpts. `honcho_reasoning`: synthesized answers (closest to cited-recall output) |
| **Citations** | No structured citation support |
| **Auth** | Honcho API at localhost (port 8000 in config) |
| **Rate limits** | None documented |
| **Status** | ⚠️ localhost:8000 not reachable in live test |

## 7. ContextForge — `mcp_contextforge_memory_query`

| Field | Value |
|---|---|
| **MCP Tool** | `mcp_contextforge_memory_query` |
| **Returns** | Semantic search results with score, title, content |
| **Citations** | Via `title` + `source_uri` |
| **Auth** | ContextForge MCP token (expires every 30 days) |
| **Rate limits** | 500 queries/month |
| **Status** | ❌ Quota exhausted (500/500, resets 2026-07-01) |

## Source Priority Weighting

| Source | Priority Weight | Rationale |
|---|---|---|
| OB1 | 1.0 | Curated, Supabase-backed, 25K+ thoughts |
| OBn | 0.9 | Federated local ChromaDB pods |
| Hindsight | 0.8 | Durable lesson memory, PostgreSQL-backed |
| Session | 0.7 | Raw conversation history, noisy |
| Honcho | 0.6 | Dialectic context, less structured |
| memory_store | 0.5 | Hermes built-in facts, lower trust scores |

*Reference date: 2026-06-22. Statuses reflect live testing during cited_recall.py development.*