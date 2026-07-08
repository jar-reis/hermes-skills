# OBn Re-Ingest Procedure — Embedding Dimension Mismatch Fix

**Discovered**: 2026-06-23
**Root cause**: Ollama `nomic-embed-text` (768 dims) failed mid-batch
during a full ingest run. The fallback logic in `ingest_chroma.py`
switched to `mxbai-embed-large` (1024 dims) for the failed batches.
This created inconsistent embedding dimensions in ChromaDB
collections — some chunks embedded at 768, others at 1024.

## Symptom

Ingest log shows:
```
⚠ 400 error, splitting batch (35→17) and retrying
⚠ 400 error, splitting batch (18→9) and retrying
⚠ Model nomic-embed-text failed, trying fallback...
✗ Chroma insert failed: Inconsistent dimensions in provided embeddings
```

## Diagnosis

1. Check if Ollama nomic-embed-text is working:
   ```bash
   curl -sf http://localhost:11434/api/embed \
     -d '{"model":"nomic-embed-text","input":"test"}' \
     | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'dims={len(d[\"embeddings\"][0])}')"
   ```
   Expected: `dims=768`. If this fails, Ollama is down or the model
   is not loaded.

2. Check ChromaDB collection health:
   ```bash
   cd ~/Documents/=notes && .venv/bin/python3 -c "
   import chromadb
   client = chromadb.HttpClient(host='127.0.0.1', port=8001)
   for col in client.list_collections():
       try:
           count = col.count()
           print(f'  {col.name}: {count} docs OK')
       except Exception as e:
           print(f'  {col.name}: ERROR — {e}')
   "
   ```

## Fix: Full Re-Ingest

### Step 1: Ensure Ollama nomic-embed-text is available

```bash
# Pull the model if not present
ollama pull nomic-embed-text

# Verify it responds
curl -sf http://localhost:11434/api/embed \
  -d '{"model":"nomic-embed-text","input":"test"}' >/dev/null && echo "OK" || echo "FAILED"
```

### Step 2: Run ingest from the correct directory

**Critical**: The ingest script uses `glob.glob("config-*.yaml")`
relative to CWD. Running from the vault root finds no configs and
exits silently after printing "✓ Ollama available".

```bash
cd ~/Documents/=notes/claude/scheduled-tasks/vault-ingest && \
  ~/Documents/=notes/.venv/bin/python3 ingest_chroma.py --all-pods --batch-size 32
```

The config files live at:
```
config-ai-systems.yaml
config-core.yaml
config-crawlsight.yaml
config-family-therapy.yaml
config-gardening.yaml
config-home-improvement.yaml
config-infra.yaml
config-job-search.yaml
config-property-management.yaml
config-rib-recovery.yaml
config-sea-ranch-ops.yaml
config-session-memory.yaml
```

### Step 3: Verify

```bash
cd ~/Documents/=notes && .venv/bin/python3 -c "
import chromadb
client = chromadb.HttpClient(host='127.0.0.1', port=8001)
total = 0
for col in client.list_collections():
    count = col.count()
    total += count
    print(f'  {col.name}: {count} docs')
print(f'Total: {total} docs across {len(client.list_collections())} pods')
"
```

Also run the status script (must use venv Python):
```bash
cd ~/Documents/=notes && .venv/bin/python3 \
  claude/scheduled-tasks/vault-ingest/obn_status.py
```

## Prevention

- Always verify `nomic-embed-text` is working before starting an
  ingest run.
- If nomic fails mid-ingest, **kill the process immediately** — do
  not let the fallback to `mxbai-embed-large` run.
- The fallback logic in `ingest_chroma.py` (lines with
  `EMBEDDING_MODELS = ["nomic-embed-text", "mxbai-embed-large"]`)
  should ideally be removed or made dimension-aware. Using different
  embedding models with different dimensionalities on the same
  collection is never safe.
- Never run two `ingest_chroma.py` processes concurrently — corrupts
  HNSW index files causing segfaults (exit code 139).

## ChromaDB API Version Note

ChromaDB 1.5.7 moved from v1 to v2 API:
- `/api/v1/heartbeat` → returns 400
- `/api/v2/heartbeat` → returns `{"nanosecond heartbeat": ...}`
- `client.list_collections()` on `HttpClient` returns a list of
  Collection objects with `.name` and `.count()` methods
- `PersistentClient` locks the DB directory and conflicts with the
  running HTTP server — always use `HttpClient`