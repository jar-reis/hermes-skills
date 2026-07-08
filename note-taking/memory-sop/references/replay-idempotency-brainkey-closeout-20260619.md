# Replay/Idempotency Boundaries + BRAIN_KEY Rotation Closeout — Session Detail

## Context
- **Session**: Memory sync poll 11 (2026-06-19 ~04:34 CDT)
- **Worker**: Hermes cron job (kimi-k2.7-code via Ollama Cloud)
- **Goal**: Enrich L1 Holographic Memory and OB1/OBn with replay/idempotency boundaries and BRAIN_KEY rotation closeout rules.

## Key Lessons

### Replay/Idempotency Boundaries
- **OBn = broad whole-vault replay surface**: replay boundaries must include last processed timestamp, commit SHA, document ID, cursor, or watermark.
- **OB1 = curated `ob1-core` captures only**: replay must use stable idempotency keys (`source + task_id + content_hash`).
- **Cross-agent handoffs**: use deterministic idempotency keys and upsert/no-op retry behavior to avoid duplicate OB1 thoughts, OBn chunks, Hindsight lessons, vault ledger entries, or ContextForge/Honcho items.
- **Replay closeout rule**: a replay is trusted only at the source plane that owns the write and only after its stable idempotency key re-selects the same active record. Reject cross-plane dedupe or human notes as closeout proof.

### BRAIN_KEY Rotation Closeout
- **OB1 blocker**: do not clear until `ob1-token verify`, MCP capture/search, and scoped `ob1-core` sync with `protect_other_sources=true` all succeed.
- **Completion proof**: requires Holographic Memory L1 `facts_fts` retrieval plus `fact_entities` links. Service health alone is not sufficient.

## Verification Queries

### Holographic Memory (SQLite)
```sql
-- FTS verification for replay/idempotency
SELECT id, content FROM facts_fts WHERE facts_fts MATCH '"Replay boundary OBn OB1 idempotency"';
-- Result: fact #183

-- FTS verification for BRAIN_KEY rotation
SELECT id, content FROM facts_fts WHERE facts_fts MATCH '"BRAIN_KEY rotation closeout OB1 OBn replay boundary"';
-- Result: fact #184

-- Entity links verification
SELECT entity FROM fact_entities WHERE fact_id IN (183, 184);
-- Result: OB1, OBn, Holographic Memory, replay boundary, idempotency keys, BRAIN_KEY, ob1-core-sync, facts_fts, fact_entities
```

### OBn Chroma (v2 API)
```bash
# Health check
curl -s http://localhost:8001/api/v2/heartbeat | jq .
# Result: {"nanosecond heartbeat":1781865739726347000}

# Semantic search for replay/idempotency
curl -s -X POST http://localhost:8001/api/v2/collections/ob1_ob1_core/query -H 'Content-Type: application/json' -d '{"query_texts": ["replay boundary idempotency key"], "n_results": 1, "include": ["metadatas", "documents", "distances"]}' | jq .
# Result: distance 0.321 → score 0.757

# Semantic search for BRAIN_KEY rotation
curl -s -X POST http://localhost:8001/api/v2/collections/ob1_ob1_core/query -H 'Content-Type: application/json' -d '{"query_texts": ["BRAIN_KEY rotation closeout protect_other_sources"], "n_results": 1, "include": ["metadatas", "documents", "distances"]}' | jq .
# Result: distance 0.209 → score 0.827
```

## Provider Quirks
- **OBn Chroma 8001**: v1 endpoints (`/api/v1/heartbeat`, `/api/v1/collections`) return `Unimplemented`. Direct checks must use `/api/v2`.
- **Holographic Memory SQLite**: `PRAGMA trusted_schema=ON` required for direct access.

## Files Modified
- `~/.hermes/memory_store.db` (Holographic Memory SQLite)
- OB1 thoughts (2 captured)
- OBn Chroma `ob1_ob1_core` collection (2 deterministic chunks upserted)

## References
- [OBn Chroma v2 API docs](https://docs.trychroma.com/api)
- [Holographic Memory SQLite schema](https://github.com/nousresearch/hermes-agent/blob/main/docs/memory.md#sqlite-schema)