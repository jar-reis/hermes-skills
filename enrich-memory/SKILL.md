---
name: enrich-memory
description: Capture user requests ("remember this") into all four canonical memory systems (Holographic, Honcho, Hindsight, OB1/OBn).
version: 1.2.0
author: Hermes
---

# enrich-memory

Capture a "remember this" request across the canonical four memory systems.

## Canonical four systems
1. **Holographic Memory (L1)** — `fact_store`
2. **Honcho (L2)** — `mcp_contextforge_memory_*`
3. **Hindsight (L2/L3)** — lesson memory daemon
4. **OB1 / OBn (L3)** — `mcp_open_brain_*`

## Usage

```bash
hermes skill run enrich-memory --content "..." --entity "..." --category "general" --tags "tag1,tag2"
```

## Implementation

```python
def enrich_memory(content, entity, category="general", tags=[]):
    from hermes_tools import memory
    
    # L1: Always-injected profile / personal notes
    memory(action="add", target="memory", content=content)
    memory(action="add", target="user", content=content)
    
    # L2: Honcho (ContextForge durable notes)
    mcp_contextforge_memory_ingest(
        content=content,
        title=f"{entity}: {content[:60]}",
        tags=tags + [entity, "enriched"]
    )
    
    # L2/L3: Hindsight (if reachable)
    hindsight_retain(content=content, context=entity, tags=tags, async_=True)
    
    # L1 structured facts
    fact_store(action="add", content=content, entity=entity, category=category, tags=tags)
    
    # L3: OB1 / Open Brain
    mcp_open_brain_capture_thought(
        content=content,
        task_id=f"enrich-{entity}",
        source="hermes"
    )
    
    return f"Enriched memory: {content[:80]}..."
```

## Notes
- If Hindsight is unreachable, skip that layer and continue; do not fail the whole call.
- If ContextForge/Honcho quota is exhausted, skip that layer and continue; do not block L1/Holographic enrichment on L2 SaaS quota.
- Keep `content` declarative and compact (<300 chars). If longer, summarize in the fact store and keep the full text in Honcho/OB1.
- Tags should include the entity name and a domain tag (e.g., `fleet`, `infra`, `user-pref`).

## Holographic L1 fallback and verification

When the task specifically targets Holographic Memory L1 / `fact_store`, prefer the native `fact_store` tool if it is exposed in the current runtime. If it is not exposed, use the installed Holographic provider API against the active `~/.hermes/memory_store.db` instead of treating the work as blocked.

Post-write verification is part of the write contract:
1. Verify `facts_fts MATCH` retrieves the new fact by durable keywords.
2. Verify `fact_entities` links include the intended entities.
3. Verify fact-store-style search/probe returns the new fact.
4. Mark superseding/current facts helpful and stale facts unhelpful when the enrichment pass identifies drift.

Reference: `references/holographic-l1-provider-fallback-2026-06-19.md`.