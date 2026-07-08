# OBn Vault Ingestion Diagnosis — 2026-06-22

## Symptom
OBn fleet-memory status reported `obn.ok: true` but `last_ingest: 2026-04-14T05:32:08+00:00` — over 2 months stale. OBn search returned zero results for recent queries.

## Diagnosis Pattern

When OBn reports healthy but stale, check these 7 independent failure points:

### 1. ChromaDB database corruption
```bash
# Check historical logs for corruption errors
grep -r "table collections already exists" logs/
# Try opening the DB
.venv/bin/python3 -c "import chromadb; c=chromadb.PersistentClient(path='chroma_db'); c.list_collections()"
```
**Finding:** Historical logs showed `chromadb.errors.InternalError: error returned from database: (code: 1) table collections already exists` on April 14. The DB got into a state where re-initialization conflicted with existing tables. `chroma_db_v2/` was created as a fresh start but the old symlink was never cleaned up.

### 2. launchd job registration
```bash
launchctl list | grep obn    # or ob1
launchctl print gui/$(id -u)/com.jackreis.ob1-core-sync  # Returns "Bad request" if not loaded
ls ~/Library/LaunchAgents/com.jackreis.obn*
```
**Finding:** Plist file existed but was never bootstrapped via `launchctl bootstrap`. `launchctl print` returned "Bad request" (exit 113). The job had never run.

### 3. Log file existence
```bash
ls -la /path/to/logs/obn-sync*.log
```
**Finding:** No log files existed at all — confirming the job never fired.

### 4. State DB contents
```bash
sqlite3 state-*.db ".tables"
sqlite3 state-*.db "SELECT COUNT(*) FROM file_state"
sqlite3 state-*.db "PRAGMA integrity_check"
```
**Finding:** All state DBs had 0 rows (integrity check: ok). Some had no tables. The incremental sync had no baseline to diff against.

### 5. ChromaDB path integrity
```bash
ls -la chroma_db    # Is it a symlink? Where does it point?
readlink chroma_db
ls chroma_db_v2/    # Is there an alternate DB?
```
**Finding:** `chroma_db` was a symlink to `/Users/jack.reis/.gemini/antigravity-cli/bridge/chroma_db` — a fragile cross-tool dependency. `chroma_db_v2/` had the correct current pod structure (8 collections, 31,370 embeddings).

### 6. Competing ingestion scripts
```
ingest.py            → OB1 edge function (Supabase, cloud)
ingest_chroma.py     → local ChromaDB + Ollama (correct for OBn)
ingest_local_batched.py → Supabase + Ollama (hybrid, unused)
```
**Finding:** The launchd wrapper called `ingest.py` (Supabase path), not `ingest_chroma.py` (local ChromaDB path). Even if the job had been loaded, it would have written to the wrong destination.

### 7. Ollama intermittent errors
```bash
# Check historical logs for 400 errors
grep -r "400 Client Error" logs/
# Verify Ollama is stable
curl -s http://localhost:11434/api/tags | jq '.models[] | select(.name|startswith("nomic"))'
```
**Finding:** Historical ingestion logs showed intermittent `400 Client Error: Bad Request for url: http://localhost:11434/api/embed` — Ollama instability during batch embedding calls. No retry logic in the code.

## Verification Commands

```bash
# Check ChromaDB collections (use vault venv for chromadb module)
/Users/jack.reis/Documents/=notes/.venv/bin/python3 -c "
import chromadb
c = chromadb.PersistentClient(path='chroma_db_v2')
for col in c.list_collections():
    print(f'{col.name}: {col.count()} docs')
"

# Check Ollama availability
ollama list | grep nomic

# Check launchd registration
launchctl list | grep obn

# Check state DB integrity
sqlite3 state-core.db "PRAGMA integrity_check"
sqlite3 state-core.db "SELECT COUNT(*) FROM file_state"
```

## Resolution
Plan written to `~/.hermes/plans/2026-06-22-obn-ultra-robust.md` with 24 tasks across 6 phases:
1. **Consolidate** (Tasks 1-5): Designate canonical ChromaDB, add `--all-pods` mode, new wrapper + launchd (30min interval), reset state DBs + backup ChromaDB
2. **Monitor** (Tasks 6-9): Health check script (disk space + freshness + launchd liveness), daily Hermes cron with Telegram digest, git post-commit hook with lockfile, status update
3. **Harden** (Tasks 10-13): Retry with batch splitting for 400 errors, state DB auto-recovery with WAL mode, per-pod error isolation, archive 6 obsolete scripts
4. **Verify** (Tasks 14-16): Full end-to-end sync, README update, MCP status checker with updated baselines
5. **Enhance** (Tasks 17-20): Semantic cache TTL, vault fallback integration, daily brief cron, frontmatter validation
6. **Review-Driven Hardening** (Tasks 21-24): Hermes cron watchdog (every 2h), fallback embedding model (mxbai-embed-large), missing pod configs for new vault dirs, RUNBOOK.md for incident response

## Key Lesson
A system reporting "healthy" can still be completely stale. Health checks must verify **freshness** (last ingest timestamp), not just **reachability** (daemon responding). The OBn status check returned `ok: true` because the ChromaDB pods were queryable — but it didn't flag that no new data had been ingested in 2+ months. This is the "healthy but stale" anti-pattern: reachability ≠ freshness. Any ingestion pipeline health check must include a timestamp-based freshness check, not just a connectivity probe.

## Multi-Agent Diagnosis Technique
The diagnosis was performed by 3 parallel subagents (mistral-large-3:675b) exploring the codebase from different perspectives (reliability, architecture, operations), then 3 more subagents reviewing the resulting plan from the same three perspectives. The explore → write → review two-phase pattern produced a more comprehensive plan than sequential exploration alone. See `multi-model-refinement` skill for the general pattern.