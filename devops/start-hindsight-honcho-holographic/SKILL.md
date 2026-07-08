---
name: start-hindsight-honcho-holographic
description: Start Hindsight, Honcho (Cortex), and Holographic (OB1 + OBn) simultaneously. Includes verification and troubleshooting.
author: Hermes
created: 2026-06-18
updated: 2026-06-23
---

# Start Hindsight, Honcho, and Holographic

## Overview
Starts and verifies three memory/coordination services:
- **Hindsight**: Session memory (embedded daemon, port `8888` on Aegis).
- **Honcho**: Dialectic memory (Docker Compose, port `8005`).
- **Holographic**: Fact store (SQLite at `~/.hermes/memory_store.db`, HRR vectors).

**Two host architectures**: Aegis (Mac Mini) and Talaris (MacBook Pro) have different setups — see the appropriate section below.

## Aegis Setup (Mac Mini, no vault, no ChromaDB)

Aegis runs a streamlined memory stack without OBn/ChromaDB:

### 1. Hindsight (Embedded Daemon, port 8888)

```bash
curl -s http://127.0.0.1:8888/health
# Expected: {"status":"healthy","database":"connected"}
```

Config at `~/.hermes/hindsight/config.json`. Runs as an embedded daemon
inside the Hermes process — no separate process to start.

### 2. Honcho (Docker Compose, port 8005)

4 containers from `~/ai-dev/honcho-dev/`:

```bash
cd ~/ai-dev/honcho-dev
docker compose -f docker-compose.aegis.yml -f docker-compose.aegis-local.yml up -d --build
```

Verify:
```bash
curl -s http://127.0.0.1:8005/health  # → {"status":"ok"}
docker ps --format "{{.Names}} {{.Status}}" | grep honcho
```

**Pitfall**: If the API container crashes with `dimensions must be the same: 768 vs 1536`, the pgvector DB has the wrong embedding dimension. See `references/honcho-docker-fixes.md` in the `fleet-memory-coordination` skill for the SQL fix.

**Pitfall**: If the deriver container exits immediately, it's missing `DB_CONNECTION_URI` in the compose override. See the same reference.

### 3. Holographic (SQLite, no server process)

Auto-creates `~/.hermes/memory_store.db` on first use. Configured via
`config.yaml` under `plugins.hermes-memory-store`:

```yaml
plugins:
  hermes-memory-store:
    auto_extract: 'true'
    db_path: '~/.hermes/memory_store.db'
    default_trust: '0.5'
    hrr_dim: '1024'
```

Verify round-trip:
```bash
sqlite3 ~/.hermes/memory_store.db "SELECT fact_id, content FROM facts ORDER BY fact_id DESC LIMIT 3;"
```

### 4. Aggregate Provider

Two aggregate providers are available on Aegis:

**Four-provider (current, includes OB1):**
`~/.hermes/plugins/ob1,hindsight,holographic,honcho/__init__.py` — wraps
all four memory planes (OB1, Hindsight, Holographic, Honcho) into one
`MemoryProvider`. 17 tools exposed, tool-name routed to the correct plane.
Fail-open: one unavailable plane does not suppress others.

```bash
hermes config set memory.provider "ob1,hindsight,holographic,honcho"
hermes memory status
# Should show: ob1,hindsight,holographic,honcho <- active
```

**Three-provider (legacy, no OB1):**
`~/.hermes/plugins/hindsight,holographic,honcho/__init__.py` — wraps
Hindsight, Holographic, and Honcho only. Superseded by the four-provider
version on Aegis but still installed as a reference.

Both auto-register when Hermes loads — no `hermes plugins enable` needed.
See the `fleet-memory-coordination` skill for the full composite adapter
pattern and a copy-paste template for creating new combinations.

### 5. Full Verification Suite (Aegis)

```bash
# Compose config validation
cd ~/ai-dev/honcho-dev && docker compose -f docker-compose.aegis.yml -f docker-compose.aegis-local.yml config --quiet

# Container health
docker compose -f docker-compose.aegis.yml -f docker-compose.aegis-local.yml ps

# API health endpoints
curl -s http://127.0.0.1:8005/health  # Honcho
curl -s http://127.0.0.1:8888/health  # Hindsight
curl -s -H "x-brain-key: $OPENBRAIN_KEY" http://127.0.0.1:8787/agent-memory-api/health  # OB1

# Memory provider
hermes memory status

# Holographic round-trip
sqlite3 ~/.hermes/memory_store.db "SELECT fact_id, content FROM facts ORDER BY fact_id DESC LIMIT 3;"
```

### 6. Four-Plane Sync Verification (Aegis)

After verifying individual services, verify that the composite adapter syncs all four planes:

```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate && python3 -c "
from plugins.memory import load_memory_provider
p = load_memory_provider('ob1,hindsight,holographic,honcho')
p.initialize('sync-verify')

# Plane status — all four should be 'active'
for name, status in p._status.items():
    print(f'  {name}: {status}')

# Tool routing — 17 tools across 4 planes
for tool_name, prov in sorted(p._tool_to_provider.items()):
    print(f'  {tool_name} -> {prov.name}')

# Test prefetch (auto-recall from all planes)
result = p.prefetch('memory sync test', session_id='sync-verify')
print(f'Prefetch: {len(result)} chars' if result else 'Prefetch: empty')

# Test sync_turn (auto-writeback to all planes)
p.sync_turn('test user', 'test assistant', session_id='sync-verify',
            messages=[{'role':'user','content':'test user'},
                      {'role':'assistant','content':'test assistant'}])
print('sync_turn: OK')
"
```

See the `fleet-memory-coordination` skill's "Four-Plane Sync Verification" section for the full procedure including known sync issues (stale OB1 memories, Hindsight writer thread test artifact, Honcho init delay, Hindsight retain body format).

## Talaris Setup (MacBook Pro, with vault + ChromaDB)

## Startup Steps

### 1. Hindsight
Already running as a daemon. Verify:
```bash
ps aux | grep hindsight-api
curl -s http://localhost:9876/health | grep -q 'OK' && echo "✅ Hindsight running" || echo "❌ Hindsight not running"
```

If not running:
```bash
uv tool uvx hindsight-api@0.7.1 --daemon --idle-timeout 0 --port 9876
```

### 2. Honcho (Cortex Backend)
Already running as a Docker container. Verify:
```bash
docker ps | grep cortex-backend
docker logs cortex-backend | tail -5
curl -s http://localhost:8000/api/v1/health | grep -q 'OK' && echo "✅ Cortex (Honcho) running" || echo "❌ Cortex (Honcho) not running"
```

If not running:
```bash
cd ~/Documents/cortex && docker-compose up -d cortex-backend
```

### 3. Holographic (OBn ChromaDB)
Start the local ChromaDB server (HTTP mode, port 8001):
```bash
cd ~/Documents/=notes
./.venv/bin/chroma run --path "~/Documents/=notes/claude/scheduled-tasks/vault-ingest/chroma_db" --port 8001
```

Verify (ChromaDB 1.5.x uses v2 API — v1 endpoints return 400):
```bash
# v2 heartbeat (correct for ChromaDB 1.5+)
curl -sf http://127.0.0.1:8001/api/v2/heartbeat && echo " ✅ ChromaDB v2"

# List collections via venv Python + HttpClient
cd ~/Documents/=notes && .venv/bin/python3 -c "
import chromadb
client = chromadb.HttpClient(host='127.0.0.1', port=8001)
cols = client.list_collections()
print(f'✅ Holographic (OBn): {len(cols)} collections')
for c in cols[:3]:
    print(f'  {c.name}: {c.count()} docs')
"
```

**Pitfall**: Do NOT use `chromadb.PersistentClient` for verification —
it locks the ChromaDB directory and can conflict with the running HTTP
server. Use `chromadb.HttpClient` against port 8001 instead.

**Pitfall**: ChromaDB 1.5.7 moved from v1 to v2 API. The v1 endpoint
`/api/v1/heartbeat` returns 400. Always use `/api/v2/heartbeat`.

## Verification
Run all checks:
```bash
# Hindsight
curl -s http://localhost:9876/health | grep -q 'OK' && echo "✅ Hindsight" || echo "❌ Hindsight"

# Honcho (Cortex)
curl -s http://localhost:8000/api/v1/health | grep -q 'OK' && echo "✅ Honcho (Cortex)" || echo "❌ Honcho (Cortex)"

# Holographic (OBn) — v2 API
curl -sf http://127.0.0.1:8001/api/v2/heartbeat >/dev/null && echo "✅ ChromaDB" || echo "❌ ChromaDB"
cd ~/Documents/=notes && .venv/bin/python3 -c "
import chromadb
client = chromadb.HttpClient(host='127.0.0.1', port=8001)
print(f'✅ Holographic (OBn): {len(client.list_collections())} collections')
"
```

## Troubleshooting

### Hindsight
- **Port conflict**: Change `--port 9876` to an unused port.
- **PostgreSQL not running**: Start it manually:
  ```bash
  pg_ctl -D ~/.pg0/instances/hindsight-embed-hermes/data start
  ```

### Honcho (Cortex)
- **Docker not running**: Start Docker Desktop.
- **Port conflict**: Change `ports` in `docker-compose.yml`.
- **Logs**:
  ```bash
  docker logs cortex-backend
  ```

### Holographic (OBn)

- **ChromaDB not starting**: Check logs in `/tmp/chroma_server.log`.
- **Python error**: Ensure `chromadb` is installed:
  ```bash
  cd ~/Documents/=notes && ./.venv/bin/pip install chromadb
  ```
- **v1 API returns 400**: ChromaDB 1.5.7 uses v2 API exclusively.
  Use `/api/v2/heartbeat` and `chromadb.HttpClient`, not
  `PersistentClient` or v1 endpoints.
- **Status script needs venv Python**: `obn_status.py` imports
  `chromadb` which is only in the vault venv. Run with
  `~/Documents/=notes/.venv/bin/python3`, not system `python3`.
- **Ingest script silent exit**: `ingest_chroma.py --all-pods` uses
  `glob.glob("config-*.yaml")` relative to CWD. Running from the
  vault root finds no configs and exits silently after printing
  "✓ Ollama available". Always run from
  `claude/scheduled-tasks/vault-ingest/`:
  ```bash
  cd ~/Documents/=notes/claude/scheduled-tasks/vault-ingest && \
    ~/Documents/=notes/.venv/bin/python3 ingest_chroma.py --all-pods --batch-size 32
  ```
- **Embedding 400 retry exhaustion (5/12 pods failing)**: The
  `get_embeddings_batch` function in `ingest_chroma.py` had a bug
  where 400 errors from Ollama (batch too large or text exceeding
  nomic's 2048-token context) were only handled when
  `attempt < max_retries - 1`. On the last retry, the 400 fell through
  to the general error handler and raised `RuntimeError`, killing the
  entire pod with 1670 errors.
  **Symptom**: Sync log shows pods failing with `rc=1` and hundreds/thousands
  of errors, but Ollama is up and nomic-embed-text is available.
  **Root cause**: `if response.status_code == 400 and attempt < max_retries - 1:`
  — the `and attempt < max_retries - 1` guard prevents splitting on the
  last attempt, so the final 400 raises instead of degrading gracefully.
  **Fix** (commit 964bd5b7e): Remove the attempt guard from the 400
  handler. Always split on 400 regardless of attempt count, and give
  recursive calls `max(1, max_retries - 1)` retries so they always have
  at least one attempt. Single texts that still 400 after truncation
  get zero-vector placeholders (dims preserved at 768).
  See `references/obn-embedding-400-retry-fix.md` for the full diff
  and reproduction steps.
- **Embedding dimension mismatch**: The fallback chain in
  `ingest_chroma.py` tries `mxbai-embed-large` (1024 dims) when
  `nomic-embed-text` (768 dims) fails mid-batch. This corrupts the
  ChromaDB collection with inconsistent dimensions. **Symptom**:
  "Inconsistent dimensions in provided embeddings" in ingest log.
  **Fix**: ensure Ollama `nomic-embed-text` is loaded and available
  before starting ingest (`curl -sf http://localhost:11434/api/embed
  -d '{"model":"nomic-embed-text","input":"test"}'`). If nomic
  fails, do NOT let the fallback run — kill the ingest and restart
  after fixing Ollama.
- **HNSW index corruption (segfault on .count())**: ChromaDB 1.5.x
  can segfault (exit 139) when calling `.count()` on a collection
  whose HNSW binary index directory is missing or corrupted. The
  SQLite metadata is fine (integrity_check passes, collections
  table has rows) but the UUID-named subdirectory under `chroma_db/`
  that holds `data_level0.bin`, `header.bin`, etc. is absent.
  **Diagnosis**: `list_collections()` works but `.count()` on a
  specific collection kills the process with SIGSEGV. Iterate
  collections one-by-one to isolate the culprit.
  **Fix (surgical — preferred over full rebuild)**:
  1. Delete only the corrupted collection: `c.delete_collection('ob1_ob_ai_systems')`
  2. Remove its state DB: `rm state-v2-<pod>.db` (or `/tmp/ob1_chroma_<pod>.db`)
  3. Re-ingest just that pod: `ingest_chroma.py --config config-<pod>.yaml --batch-size 64`
  4. Verify all 12 collections with `.count()` — no segfaults.
  Do NOT `rm -rf` the entire `chroma_db/` directory — 11 of 12
  collections were healthy and a full rebuild wastes 15-30 minutes.
  See `references/obn-hnsw-corruption-repair.md` for the full
  diagnostic and repair procedure.

## OpenClaw (NemoClaw) OB1 Plugin Integration

NemoClaw and other OpenClaw containers need the `nbj-ob1-agent-memory` plugin
configured to connect to the local OB1 brain. This is the OpenClaw-side
complement to the Hermes OB1 plugin.

### Prerequisites
- OB1 brain running at `http://127.0.0.1:8787` (verified via `/health`)
- NemoClaw container running with host networking (so `127.0.0.1` reaches the host)
- Plugin dist available at a source path (e.g. `OB1/integrations/openclaw-agent-memory/plugin/dist/index.js`)

### Installation

```bash
# Copy plugin files into the container's plugin directory
docker exec openshell-hermes-nemoclaw openclaw plugins install --link /.openclaw/plugins/ob1-agent-memory
```

The plugin directory must contain `dist/index.js`, `package.json`, and any
`manifest.json` matching the plugin's declared entry point.

### Config (openclaw.json)

Add three things to `/tmp/.openclaw/openclaw.json` → `plugins`:

1. **Allow list** — add `"nbj-ob1-agent-memory"` to `plugins.allow`
2. **Entries** — add config block with `endpoint`, `accessKey`, `workspaceId`:

```json
"nbj-ob1-agent-memory": {
  "enabled": true,
  "config": {
    "endpoint": "http://127.0.0.1:8787/agent-memory-api",
    "accessKey": "<OB1 access key>",
    "workspaceId": "aegis-local",
    "requireReviewByDefault": true,
    "includeUnconfirmedRecall": true
  }
}
```

3. **Slots** — assign the memory slot: `"memory": "nbj-ob1-agent-memory"`

### Pitfalls (OpenClaw OB1)

- **SecretRef pattern fails.** Putting a `secrets` provider block inside
  `plugins` causes OpenClaw config validation failure (`plugins: Invalid input`).
  Use plaintext `accessKey` in the config instead.
- **Container networking.** NemoClaw uses **host networking** mode, so
  `127.0.0.1:8787` reaches OB1 directly from inside the container. No
  `host.docker.internal` needed.
- **Config key naming.** OpenClaw plugin config uses **camelCase**
  (`accessKey`, `workspaceId`, `requireReviewByDefault`), NOT snake_case.
- **Auth header.** Both the Hermes plugin and the OpenClaw plugin use the
  `x-brain-key` header (NOT `Authorization: Bearer`). The OB1 API accepts
  both, but `x-brain-key` is the contract.
- **Restart after config change.** After editing `openclaw.json`, restart
  the container: `docker restart openshell-hermes-nemoclaw`. Verify plugin
  shows as `enabled` in `openclaw plugins list`.

### Verification

```bash
# Plugin enabled?
docker exec openshell-hermes-nemoclaw openclaw plugins list | grep nbj-ob1

# OB1 reachable from container?
docker exec openshell-hermes-nemoclaw curl -s http://127.0.0.1:8787/health

# Recall test (x-brain-key auth)
curl -s -X POST http://127.0.0.1:8787/agent-memory-api/recall \
  -H "Content-Type: application/json" \
  -H "x-brain-key: $OPENBRAIN_KEY" \
  -d '{"query":"test","workspaceId":"aegis-local","limit":3}'
```

See `references/ob1-openclaw-plugin-config.md` for the full session transcript
including the writeback API schema, plugin source paths, and step-by-step
config edits.

## OB1 HTTP API Writeback Schema

The OB1 writeback endpoint (`POST /agent-memory-api/writeback`) requires a
structured `memory_payload` — NOT a flat `content` field.

**Schema:**
```json
{
  "workspace_id": "aegis-local",
  "memory_payload": {
    "outputs": ["Summary of what was done/produced"],
    "decisions": ["Key decision made and why"],
    "lessons": ["Lesson learned during this work"]
  },
  "runtime": {"name": "hermes-coordinator"},
  "provenance": {
    "default_status": "generated",
    "confidence": 0.95,
    "requires_review": true
  },
  "task_id": "optional-task-id",
  "flow_id": "optional-agent-identity"
}
```

**Category keys** (pick the one that fits, all optional):
| Key | Use for |
|-----|---------|
| `outputs` | What was produced, built, or completed |
| `decisions` | Choices made and rationale |
| `lessons` | Insights gained during work |
| `constraints` | Limitations discovered |
| `unresolved_questions` | Open questions |
| `next_steps` | Follow-up actions |
| `failures` | What went wrong |

**Pitfall:** Sending `{"content": "..."}` as the top-level body returns
`{"ok":false,"error":"memory_payload produced no memory rows"}` silently.
The `memory_payload` field with at least one category array is required.

**Auth:** Use `x-brain-key: <key>` header. `Authorization: Bearer <key>`
also works but `x-brain-key` is the OB1 contract.

## Notes
- OB1 (Supabase) is cloud-hosted and requires no local setup.
- **ChromaDB (OBn) has TWO runtime modes** — know which one is active:
  - **HTTP server mode**: `chroma run --port 8001` starts a standalone
    server. Verify with `curl -sf http://127.0.0.1:8001/api/v2/heartbeat`.
    Use `chromadb.HttpClient(host='127.0.0.1', port=8001)` for queries.
  - **Embedded PersistentClient mode**: `ingest_chroma.py` uses
    `chromadb.PersistentClient(path=...)` — no server process, no port.
    The :8001 heartbeat will fail (connection refused). This is NOT a
    bug — there is simply no HTTP server running. Verify by running
    `obn_healthcheck.py` instead (uses PersistentClient internally).
  - The launchd job `com.jackreis.obn-sync` runs the ingest script
    periodically in PersistentClient mode. It does NOT start a server.
  - **Pitfall**: A handoff or health check that curls :8001 will report
    "OBn DOWN" when OBn is actually fine in embedded mode. Always check
    `obn_healthcheck.py` output, not just the port.
- OBn status script (`obn_status.py`) and ingest script
  (`ingest_chroma.py`) require the vault venv Python
  (`~/Documents/=notes/.venv/bin/python3`), not system `python3`.
- Ingest script must be run from `claude/scheduled-tasks/vault-ingest/`
  (it globs for `config-*.yaml` relative to CWD).
- All services are now running and verified.

## Reference files

- `references/obn-embedding-400-retry-fix.md` — diagnosing and fixing
  the 400-error retry exhaustion bug where `get_embeddings_batch` only
  split on 400 when `attempt < max_retries - 1`, causing 5/12 pods to
  fail with RuntimeError on the last retry. Includes the full diff,
  reproduction steps, and verification commands.
- `references/obn-hnsw-corruption-repair.md` — HNSW index corruption
  diagnosis and surgical repair (delete single collection, re-ingest
  just that pod, not the entire chroma_db directory).
- `references/obn-re-ingest-embedding-fix-20260623.md` — full procedure
  for diagnosing and fixing embedding dimension mismatch (nomic 768
  vs mxbai 1024), including the correct ingest working directory and
  ChromaDB v2 API verification.