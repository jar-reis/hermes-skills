# Holographic L1 provider fallback for fact-store enrichment (2026-06-19)

## When this applies
Use this when a memory-enrichment task specifically targets Holographic Memory L1 / `fact_store`, but the current runtime surface does not expose `fact_store` as a direct callable tool.

This is a fallback pattern, not a claim that `fact_store` is broken. Prefer the native `fact_store` tool when it is available.

## Pattern
1. Treat `~/.hermes/memory_store.db` as the active Holographic SQLite store only after confirming Hermes memory provider is `holographic`.
2. Load the installed provider implementation from `~/.hermes/hermes-agent/plugins/memory/holographic/` and use:
   - `MemoryStore.add_fact(content, category, tags)` for writes.
   - `FactRetriever.search(query, min_trust, limit)` for fact-store-style retrieval.
   - `MemoryStore.record_feedback(fact_id, helpful=True/False)` for trust feedback.
3. Keep new facts declarative and compact; include quoted entity names for durable entity extraction when needed.
4. Post-write verification is mandatory:
   - raw `facts_fts MATCH ...` returns the new `fact_id`;
   - `fact_entities` contains expected entity links;
   - fact-store-style retrieval returns the new fact for the task’s durable keywords.
5. If stale facts are discovered, do not delete them by default. Add or trust-boost superseding facts and mark stale facts unhelpful via feedback when appropriate.

## Minimal verifier shape
```python
from plugins.memory.holographic.store import MemoryStore
from plugins.memory.holographic.retrieval import FactRetriever
store = MemoryStore('/Users/jack.reis/.hermes/memory_store.db')
retriever = FactRetriever(store)
fact_id = store.add_fact(content, category='project', tags=tags)
assert store._conn.execute(
    'SELECT 1 FROM facts_fts JOIN facts f ON facts_fts.rowid=f.fact_id WHERE facts_fts MATCH ? AND f.fact_id=?',
    ('durable keyword', fact_id),
).fetchone()
entities = [r['name'] for r in store._conn.execute(
    'SELECT e.name FROM entities e JOIN fact_entities fe ON fe.entity_id=e.entity_id WHERE fe.fact_id=?',
    (fact_id,),
)]
assert 'Expected Entity' in entities
assert any(r['fact_id'] == fact_id for r in retriever.search('durable keyword', min_trust=0.3, limit=5))
```

## Concrete session learning
A fleet memory enrichment pass found ContextForge quota exhausted and no direct `fact_store` tool in the runtime surface. The successful path used the local Holographic provider API to add one durable L1 fact, verified it through `facts_fts`, verified `fact_entities` links, and used `record_feedback` to raise current facts and lower stale Hindsight `:9876` facts.
