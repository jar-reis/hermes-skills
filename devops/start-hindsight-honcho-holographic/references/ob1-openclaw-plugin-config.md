# OB1 OpenClaw Plugin Configuration — Session Reference

**Bead:** Documents-3x7 (OBn local memory layer)
**Date:** 2026-07-02
**Host:** Aegis (Mac Mini), user hermes

## Context

Configured the `nbj-ob1-agent-memory` plugin (v0.1.6) in the NemoClaw
OpenClaw Docker container to connect to the local OB1 brain at
`http://127.0.0.1:8787`. This enables per-turn memory recall/writeback
from OpenClaw agents.

## Environment

- **OB1 brain:** `http://127.0.0.1:8787` (mxbai-embed-large, 1024 dim, 24,236 thoughts)
- **NemoClaw container:** `openshell-hermes-nemoclaw` (host networking, port 18794)
- **OpenClaw config:** `/tmp/.openclaw/openclaw.json`
- **Hermes env:** `~/.hermes/.env` with `OPENBRAIN_URL`, `OPENBRAIN_KEY`,
  `OPENBRAIN_WORKSPACE_ID=aegis-local`, `OPENBRAIN_WORKSPACE_MODE=per-agent`,
  `OPENBRAIN_WORKSPACE_PREFIX=aegis-`
- **Hermes config:** `~/.hermes/config.yaml` with
  `memory.provider: ob1,hindsight,holographic,honcho`
- **Plugin source:** `OB1/integrations/openclaw-agent-memory/plugin/dist/index.js`
  (npm: `@natebjones/ob1-agent-memory@0.1.6`)

## Hermes Side (Already Configured)

All five `OPENBRAIN_*` env vars were already set in `~/.hermes/.env`.
OB1 was already in the memory provider chain in `config.yaml`.
The Hermes OB1 plugin at `~/.hermes/plugins/ob1/__init__.py` (1452 lines)
was installed and functional. No changes needed.

## OpenClaw Side (Configured This Session)

### Step 1: Install Plugin

```bash
# Plugin files copied to /tmp/.openclaw/plugins/ob1-agent-memory/
# Structure: dist/index.js, package.json, manifest.json
docker exec openshell-hermes-nemoclaw openclaw plugins install --link /.openclaw/plugins/ob1-agent-memory
```

### Step 2: Edit openclaw.json

Added to `plugins.allow`:
```json
"nbj-ob1-agent-memory"
```

Added to `plugins.entries`:
```json
"nbj-ob1-agent-memory": {
  "enabled": true,
  "config": {
    "endpoint": "http://127.0.0.1:8787/agent-memory-api",
    "accessKey": "55082cf9e051bbf14cacbc61de65b26c9ba8050cbd0c12c38e494ebe75d8c250",
    "workspaceId": "aegis-local",
    "requireReviewByDefault": true,
    "includeUnconfirmedRecall": true
  }
}
```

Added to `plugins.slots`:
```json
"memory": "nbj-ob1-agent-memory"
```

### Step 3: Restart Container

```bash
docker restart openshell-hermes-nemoclaw
# Wait for healthy status
docker ps --filter "name=nemoclaw" --format "{{.Names}} {{.Status}}"
# → openshell-hermes-nemoclaw Up (healthy)
```

### Step 4: Verify

```bash
docker exec openshell-hermes-nemoclaw openclaw plugins list | grep nbj-ob1
# → nbj-ob1-agent-memory v0.1.6, enabled, /.openclaw/plugins/ob1-agent-memory/dist/index.js
```

## OB1 Writeback API Schema Discovery

### Failed Attempts (Flat Content)

```bash
# These all returned: {"ok":false,"error":"memory_payload produced no memory rows"}
curl -s -X POST http://127.0.0.1:8787/agent-memory-api/writeback \
  -H "x-brain-key: $OPENBRAIN_KEY" \
  -d '{"workspaceId":"aegis-local","agentId":"hermes","content":"test"}'

curl -s -X POST http://127.0.0.1:8787/agent-memory-api/writeback \
  -H "x-brain-key: $OPENBRAIN_KEY" \
  -d '{"workspace_id":"aegis-local","content":"test","metadata":{}}'
```

### Correct Schema (Category Arrays in memory_payload)

```bash
curl -s -X POST http://127.0.0.1:8787/agent-memory-api/writeback \
  -H "Content-Type: application/json" \
  -H "x-brain-key: $OPENBRAIN_KEY" \
  -d '{
    "workspace_id": "aegis-local",
    "memory_payload": {
      "outputs": ["Summary of completed work"]
    },
    "runtime": {"name": "hermes-coordinator"},
    "provenance": {
      "default_status": "generated",
      "confidence": 0.95,
      "requires_review": true
    },
    "task_id": "Documents-3x7",
    "flow_id": "hermes-coordinator"
  }'
```

Response:
```json
{
  "schema_version": "openbrain.agent_memory.writeback_response.v1",
  "memories": [{
    "memory_id": "227848c6-...",
    "summary": "...",
    "content": "...",
    "provenance": {"status": "generated", "confidence": 0.95, ...},
    "scope": {"workspace_id": "aegis-local", "visibility": "personal"},
    ...
  }]
}
```

## Auth Header Discovery

- `x-brain-key: <key>` — works (this is the OB1 contract, used by both plugins)
- `Authorization: Bearer <key>` — also works
- `x-api-key: <key>` — returns `{"ok":false,"error":"unauthorized"}`

## Hermes Plugin Code Reference

The Hermes OB1 plugin (`~/.hermes/plugins/ob1/__init__.py`) uses
`x-brain-key` header at line 457 and 833:
```python
self._headers = {
    "Content-Type": "application/json",
    "x-brain-key": self._access_key,
}
```

The writeback tool maps user-friendly args to `memory_payload` categories:
```python
category_map = {
    "decision": "decisions",
    "output": "outputs",
    "lesson": "lessons",
    "constraint": "constraints",
    "question": "unresolved_questions",
    "next_step": "next_steps",
    "failure": "failures",
}
category = category_map.get(memory_type, "outputs")
memory_payload = {category: [line]}
```

## OpenClaw Plugin Code Reference

The OpenClaw OB1 plugin (`/tmp/.openclaw/plugins/ob1-agent-memory/dist/index.js`)
also uses `x-brain-key`:
```javascript
this.accessKey = config.accessKey;
// ...
headers = {
    "x-brain-key": this.accessKey
}
```

Config schema (camelCase, not snake_case):
- `endpoint` — OB1 API URL
- `accessKey` — OB1 access key
- `workspaceId` — workspace ID
- `requireReviewByDefault` — boolean
- `includeUnconfirmedRecall` — boolean

## Pitfalls Encountered

1. **SecretRef pattern** — Adding a `secrets` provider block inside `plugins`
   in openclaw.json caused config validation failure
   (`plugins: Invalid input`). Fix: use plaintext `accessKey` in the config.

2. **Writeback API** — Sending flat `content` field returns
   "memory_payload produced no memory rows". Fix: use structured
   `memory_payload` with category arrays.

3. **Tirith security scanner** — `cat file | python3` pipe pattern blocked
   by Tirith. Fix: use `read_file` tool instead of piping to Python.

## Files Modified

- `/tmp/.openclaw/openclaw.json` — Added OB1 plugin to allowlist, entries, slots
- `/tmp/.openclaw/plugins/ob1-agent-memory/` — Plugin dist + manifest + package.json
- `/tmp/.openclaw/secrets/ob1-access-key.json` — Created but unused (SecretRef failed)

## Plan File

Full implementation plan at `/Users/hermes/Documents/plan-obn-3x7.md`
(27.5KB, 13 tasks + prerequisite gates + verification cheat sheet + pitfalls).