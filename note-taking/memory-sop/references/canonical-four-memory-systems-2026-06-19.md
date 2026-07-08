# Canonical Four Memory Systems — 2026-06-19 Correction

## Source
User corrected agent during memory-sync setup on 2026-06-19. The agent had collapsed memory into a three-system model (Holographic, ContextForge/Hindsight, OB1/Open Brain). The user clarified the canonical four systems that must be maintained and injected into every session.

## Canonical Set

| Layer | System | Role | Query Interface |
|-------|--------|------|-----------------|
| L1 | **Holographic Memory** | Structured facts + entity resolution | `fact_store` |
| L2 | **Honcho** | Context DB / user-state layer | `mcp_contextforge_memory_*` + Chroma 8000 |
| L2/L3 | **Hindsight** | Lesson / experience memory | Hindsight daemon `http://localhost:8888` |
| L3 | **OB1 / OBn** | Open Brain knowledge graph | `mcp_open_brain_*` + Chroma 8001 |

## Auxiliary (not canonical)
- **Session history** (`session_search`) — raw conversation retrieval.
- **Profile memory** (`memory` tool / system prompt) — user preferences + environment facts.

## Operational Implications
1. Session-start checks must cover all four canonical systems.
2. Memory-sync / enrichment workflows must write to all four, not just the most convenient two.
3. Port allocations (2026-06-18): Honcho/Cortex uses 8000 (Chroma), OBn uses 8001, Hindsight daemon uses **8888** (port 9876 is stale).
4. Hindsight has **no web dashboard at root `/`**; use `/docs` for Swagger UI.
5. ContextForge.dev SaaS remains the cross-fleet shared L4; it is separate from the IBM `mcpgateway` at :8090.

## Signal
When a user says a memory system is missing or the architecture is wrong, treat it as a first-class skill update. Patch `memory-sop` immediately and record the correction in `references/`.

