# OBn HNSW Index Corruption — Surgical Repair

## Problem

ChromaDB 1.5.x segfaults (exit 139, SIGSEGV) when calling `.count()` or
querying a collection whose HNSW binary index directory is missing or
corrupted. The SQLite metadata (`chroma.sqlite3`) is intact —
`PRAGMA integrity_check` passes, the `collections` table has rows — but
the UUID-named subdirectory under `chroma_db/` that holds
`data_level0.bin`, `header.bin`, `length.bin`, and `link_lists.bin` is
absent.

## Symptoms

```
import chromadb
c = chromadb.PersistentClient(path='chroma_db')
cols = c.list_collections()     # ✅ works, returns 12 collections
for col in cols:
    col.count()                  # ❌ SIGSEGV on the corrupted one
```

Process exits with code 139. No Python traceback — the segfault happens
in the C extension that reads the HNSW binary files.

The launchd job (`com.jackreis.obn-sync`) crash-loops with exit code 139
every 30 minutes, filling stderr logs with "Segmentation fault: 11".

## Diagnosis

### 1. Confirm SQLite is healthy

```bash
sqlite3 chroma_db/chroma.sqlite3 "PRAGMA integrity_check;"
# → ok
```

### 2. List collections from SQLite directly

```bash
sqlite3 chroma_db/chroma.sqlite3 "SELECT id, name FROM collections;"
```

### 3. Check which UUID directories exist

```bash
ls chroma_db/
# Each collection should have a <uuid>/ subdirectory
# The corrupted collection's directory will be MISSING
```

### 4. Isolate the culprit collection

```python
# Run with vault venv: ~/Documents/=notes/.venv/bin/python3
import chromadb
c = chromadb.PersistentClient(path='chroma_db')
for col in c.list_collections():
    try:
        n = col.count()
        print(f'  {col.name}: {n} OK')
    except Exception as e:
        print(f'  {col.name}: ERROR {e}')
# The corrupted collection will kill the process (segfault)
# The last collection printed before the crash is the culprit
```

## Fix (Surgical — Preferred)

Do NOT `rm -rf` the entire `chroma_db/` directory. 11 of 12 collections
are typically healthy. A full rebuild wastes 15-30 minutes re-embedding
~55K chunks.

### 1. Delete only the corrupted collection

```python
import chromadb
c = chromadb.PersistentClient(path='chroma_db')
c.delete_collection('ob1_ob_ai_systems')  # replace with your culprit
```

### 2. Verify remaining collections are healthy

```python
for col in c.list_collections():
    print(f'  {col.name}: {col.count()} OK')
# All should pass now
```

### 3. Remove the corrupted pod's state DB

```bash
# State DB location depends on ingest_chroma.py version:
# - Config-specified: state-v2-<pod>.db in the ingest dir
# - Default: /tmp/ob1_chroma_<pod>.db
rm -f state-v2-ai-systems.db
rm -f /tmp/ob1_chroma_ai-systems.db
```

### 4. Re-ingest just the corrupted pod

```bash
cd ~/Documents/=notes/claude/scheduled-tasks/vault-ingest
~/Documents/=notes/.venv/bin/python3 ingest_chroma.py \
  --config config-ai-systems.yaml --batch-size 64
```

This takes 5-10 minutes per pod (depending on file count). The
ai-systems pod (the largest) took ~15 minutes for 2,361 files → 20,867
chunks.

### 5. Verify all collections

```python
import chromadb
c = chromadb.PersistentClient(path='chroma_db')
total = 0
for col in c.list_collections():
    n = col.count()  # no segfault
    total += n
    print(f'  {col.name}: {n}')
print(f'Total: {total} docs')
```

### 6. Run healthcheck

```bash
cd ~/Documents/=notes/claude/scheduled-tasks/vault-ingest
~/Documents/=notes/.venv/bin/python3 obn_healthcheck.py
```

### 7. Reload launchd

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jackreis.obn-sync.plist
launchctl list | grep obn
```

## What NOT to Do

- **Do NOT `rm -rf chroma_db/`** — destroys all 12 collections when only
  1 is corrupted. Full rebuild takes 15-30 min vs 5-10 min for single pod.
- **Do NOT use `chromadb.HttpClient`** for the repair — the HTTP server
  won't start if the DB is corrupted. Use `PersistentClient` directly.
- **Do NOT run `--all-pods`** during the repair — only re-ingest the
  corrupted pod. Running all pods re-processes all 12 pods' state DBs.
- **Do NOT leave the launchd job running** during repair — it will
  crash-loop with exit 139 and may interfere with the re-ingest.
  Unload first: `launchctl bootout gui/$(id -u)/com.jackreis.obn-sync`.

## Observed 2026-06-23

- Corrupted collection: `ob1_ob_ai_systems` (UUID c1539265-...)
- Missing directory: `chroma_db/c1539265-351e-4561-9561-1d40f954367c/`
- Root cause: likely an interrupted ingest (process killed mid-write)
  or the launchd job crashing during a sync cycle
- Fix time: ~15 minutes (vs 30+ min for full rebuild)
- Result: 12 collections, 54,663 docs, healthcheck 18/19 passes