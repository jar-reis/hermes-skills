# Hindsight Retain HTTP API Format (2026-06-24)

## Endpoint

```
POST /v1/default/banks/{bank_id}/memories
Content-Type: application/json
```

## Correct Request Format

```json
{
  "items": [
    {
      "content": "The fact or lesson to retain",
      "context": "short-label-for-the-session",
      "tags": ["tag1", "tag2"]
    }
  ],
  "async": true
}
```

**Critical**: The `items` field is an array. Sending a single item at the top level
(`{content: "...", context: "..."}`) returns a 422 validation error:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "items"],
      "msg": "Field required"
    }
  ]
}
```

## Why async: true is REQUIRED

LLM extraction takes 10-30s per item. Sync mode (`async: false`) times out at 30s.
Async mode returns immediately with an `operation_id`:

```json
{
  "success": true,
  "bank_id": "hermes",
  "items_count": 3,
  "async": true,
  "operation_id": "76a55ddf-7340-4698-9bc0-64795a479fb0"
}
```

## Verification

Check the operation status:

```
GET /v1/default/banks/hermes/operations/{operation_id}
```

Then confirm the document exists:

```
GET /v1/default/banks/hermes/documents?q={document_id}
```

## Other Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check (returns `{"status":"healthy","database":"connected"}`) |
| GET | `/openapi.json` | Full API schema |
| POST | `/v1/default/banks/{bank_id}/memories/recall` | Semantic search/recall |
| POST | `/v1/default/banks/{bank_id}/reflect` | Synthesized reasoning across memories |
| GET | `/v1/default/banks/{bank_id}/stats` | Document/operation counts |
| GET | `/v1/default/banks/{bank_id}/memories/list` | List all memories |

## Python Example (from execute_code)

```python
import subprocess, json

payload = json.dumps({
    "items": [{
        "content": "Fact to retain",
        "context": "session-label",
        "tags": ["tag1", "tag2"]
    }],
    "async": True
})
result = subprocess.run(
    ["curl", "-s", "-X", "POST",
     "http://127.0.0.1:9876/v1/default/banks/hermes/memories",
     "-H", "Content-Type: application/json",
     "-d", payload],
    capture_output=True, text=True, timeout=15
)
resp = json.loads(result.stdout)
# resp = {"success": true, "operation_id": "...", ...}
```

## Discovery

Discovered 2026-06-24 when calling Hindsight retain directly from `execute_code`.
The Hermes plugin's `hindsight_retain` tool wraps this correctly, but the raw HTTP API
has a different schema than what older skill documentation described.