---
created: 2026-06-20
updated: 2026-06-20
author: Hermes
---

# Hindsight Localhost Verification

## Problem
Tirith's security scan blocks `curl | python3` for `localhost` Hindsight queries:
```
Security scan — [MEDIUM] Schemeless URL in sink context: URL without explicit scheme passed to a command that downloads/executes content; [HIGH] Pipe to interpreter: curl | python3: Command pipes output from 'curl' directly to interpreter 'python3'. Downloaded content will be executed without inspection.
```

## Solution
Use direct `curl` + `jq` for verification:

```bash
curl -s -X POST http://localhost:8888/v1/default/banks/hermes/memories/recall \
  -H 'content-type: application/json' \
  -d '{"query":"drain-20260620T0044", "budget":"low"}' | jq .
```

## Example Output
```json
{
  "results": [
    {
      "id": "8acf30b1-11db-4332-84ac-4eeb44e0e970",
      "text": "Memory-sync poll cycle detected 5 holographic turns from cron jobs..."
    }
  ]
}
```

## Why This Works
- **No pipe to interpreter**: `jq` is a JSON processor, not a general-purpose interpreter.
- **Explicit scheme**: `http://` is hardcoded, avoiding the schemeless URL warning.
- **Canonical**: This is the **recommended verification method** for all Hindsight queries.

## Port Update (2026-06-24)

Hindsight canonical port is now **9876** (not 8888). Replace all `:8888` references with `:9876` in the commands above. Port 8888 remains as a fallback if 9876 is unreachable.

## Retain API Format (2026-06-24)

The retain endpoint `POST /v1/default/banks/hermes/memories` requires an **`items` array**, not a single content object:

```bash
curl -s -X POST http://localhost:9876/v1/default/banks/hermes/memories \
  -H 'Content-Type: application/json' \
  -d '{"items": [{"content": "fact text", "context": "label", "tags": ["tag1"]}], "async": true}'
```

Sending `{"content": "...", "async": true}` (without `items`) returns:
```json
{"detail": [{"type": "missing", "loc": ["body", "items"], "msg": "Field required"}]}
```

Always wrap content in the `items` array, even for a single fact. Use `async: true` — sync mode times out at 30s but LLM extraction takes 10-30s per item.