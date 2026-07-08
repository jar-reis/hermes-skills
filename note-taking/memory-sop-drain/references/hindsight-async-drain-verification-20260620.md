---
created: 2026-06-20
updated: 2026-06-20
author: Hermes
---

# Hindsight Async Drain Verification

## Problem
The `memory-demo.sh recall` script fails with:
```
(parse error) Expecting value: line 1 column 1 (char 0)
```
This occurs when the Hindsight daemon returns non-JSON text (e.g., HTTP 500, network errors, or malformed responses). The script uses Python's `json.loads()` on raw daemon output, which is fragile.

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
      "text": "Memory-sync poll cycle detected 5 holographic turns from cron jobs...",
      "document_id": "drain-20260620T004407Z-53436-0"
    }
  ]
}
```

## Why This Works
- **No intermediate parsing**: `curl` pipes directly to `jq`, which handles JSON validation.
- **Async-safe**: Works even if the daemon is still processing the `async: true` retain request.
- **Canonical**: This is the **recommended verification method** for all async drains.

## When to Use
- After any `memory-drain.sh` call with `async: true`.
- If `memory-demo.sh recall` fails with a parse error.
- For debugging Hindsight daemon responses.