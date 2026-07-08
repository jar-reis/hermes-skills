# OBn gap-fill exact-phrase verification pattern (2026-06-19)

## Context
A targeted OB1/OBn L3 deepening pass captured two high-signal facts around replay/idempotency boundaries and BRAIN_KEY rotation closeout, then had to prove both semantic retrieval and exact phrase coverage.

## Durable lesson
For OBn/OB1 gap-fill work, do **not** rely on a single search surface for phrase-hit reporting:

1. **OB1/Open Brain MCP semantic search** proves the captured thought is retrievable by intended phrasing, especially when run with `threshold=0.7`, `source=<writer>`, and `task_id=<namespace>`.
2. **OBn Chroma v2 direct document filtering** proves that exact phrases are present/queryable in the indexed corpus, and can catch phrases that MCP semantic top-N windows do not surface as exact-hit counts.

## Recommended verifier shape

### Health and collection presence
```bash
curl -sS -m 5 http://localhost:8001/api/v2/heartbeat
curl -sS -m 5 http://localhost:8001/api/v2/tenants/default_tenant/databases/default_database/collections
```

Identify the target collection, commonly `ob1_ob1_core`, then verify count:
```bash
curl -sS -m 5 \
  http://localhost:8001/api/v2/tenants/default_tenant/databases/default_database/collections/<collection-id>/count
```

### Direct exact-phrase query against OBn Chroma v2
```python
import json, urllib.request
BASE = "http://localhost:8001/api/v2/tenants/default_tenant/databases/default_database/collections/<collection-id>"
phrases = [
    "replay boundary",
    "idempotency key",
    "writer-of-record",
    "post-write verification",
    "protect_other_sources=true",
]
for phrase in phrases:
    req = urllib.request.Request(
        BASE + "/get",
        data=json.dumps({
            "where_document": {"$contains": phrase},
            "limit": 100,
            "include": ["documents", "metadatas"],
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    print(phrase, len(data.get("ids", [])))
```

## Reporting convention
Report both surfaces explicitly:

- **Semantic queryability:** threshold, filters (`source`, `task_id`), top match percentage, and whether each new capture was retrieved.
- **Exact phrase hits:** before/after MCP semantic-window exact counts if requested; plus direct OBn Chroma v2 `where_document.$contains` counts for the target collection.

If the MCP semantic-window exact count stays at 0 while direct Chroma returns hits, say so plainly: semantic top-N retrieval and direct indexed-document containment are different evidence types.
