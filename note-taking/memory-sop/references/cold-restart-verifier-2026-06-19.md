# Cold-Restart Verifier for Memory Systems

Session reference: 2026-06-19.

## Why this verifier exists
After a fresh Hermes session, system reboot, or fleet agent handoff, you need a fast way to confirm the canonical four memory systems are alive and queryable before claiming the session is "warm". This reference records the exact commands and the port reality discovered during the memory-sync wrap.

## Canonical four systems and their verifier commands

| Layer | System | Port / Tool | Command | Expected |
|-------|--------|-------------|---------|----------|
| L1 | Holographic Memory | `fact_store` | `fact_store(action='probe', entity='test')` | `[]` or facts |
| L2 | Honcho | Cortex / ContextForge bridge | `hermes memory status` + `mcp_contextforge_memory_query --query "test"` | results or empty list (quota-dependent) |
| L2/L3 | Hindsight | `localhost:9876` (canonical 2026-06-24; fallback 8888) | `curl -s http://localhost:9876/health` | {"status":"healthy","database":"connected"} |
| L3 | OBn | Chroma `localhost:8001` | `curl -s http://localhost:8001/api/v2/heartbeat` | `{"nanosecond heartbeat":...}` |
| L3 | OB1 | `mcp_open_brain_*` | `hermes mcp list \| grep open-brain` | `open-brain` enabled |

## Port reality (verified 2026-06-24)
- **9876** = Hindsight (canonical as of 2026-06-24), healthy. Root `/` returns `{"detail":"Not Found"}` — there is **no root dashboard**. Use `/docs` for Swagger UI and `/health` for the health check. Fallback port: 8888.
- **8001** = OBn Chroma, healthy, **v2 API only**. v1 endpoints such as `/api/v1/heartbeat` and `/api/v1/collections` return `Unimplemented`.
- **8000** = legacy Honcho Chroma, **down / stale**. Do not use.
- **8002** = Cortex/Honcho via OrbStack, **not yet stable** (binds but returns 404). Monitor; do not treat as verified until it returns a valid Chroma heartbeat.

## What "ready" means
A memory system is cold-restart ready when:
1. Hindsight responds healthy on **9876** (fallback: 8888).
2. OBn Chroma responds on **8001** with a v2 heartbeat.
3. Open Brain MCP is connected (not just listed — the server must respond to a tool call).
4. Holographic Memory can probe an entity.
5. ContextForge MCP is reachable (note: Honcho writes may still be blocked by the 500/500 query quota until the monthly reset).

If **Open Brain MCP is disconnected** or **Honcho/Cortex 8002 is not stable**, the restart is **not fully ready** for OB1 queryability or L2 writes, even if Hindsight and OBn are healthy.

## Verifier script
See `note-taking/memory-sop/scripts/verify-memory-sync-state.sh` for the runnable version. A minimal inline check is:

```bash
curl -s http://localhost:9876/health | grep healthy && \
curl -s http://localhost:8001/api/v2/heartbeat | grep heartbeat && \
hermes mcp list 2>/dev/null | grep -E 'contextforge|open-brain'
```

## Recovery commands
- Hindsight down: restart the daemon on port **9876** (fallback: 8888).
- OBn Chroma down: `chroma run --path ~/.hermes/obn_chroma --port 8001`
- Open Brain MCP disconnected: `hermes mcp configure open-brain` or restart the Hermes gateway.
- ContextForge quota exhausted: wait for monthly reset (2026-07-01) or upgrade; skip Honcho writes, proceed with Hindsight + OBn.

## Related references
- `references/hindsight-port-8888-ui-reality-2026-06-19.md`
- `references/memory-sync-sugar-workers-2026-06-19.md`
- `scripts/verify-memory-sync-state.sh`
