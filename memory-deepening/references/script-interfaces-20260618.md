# Memory Script Real Interfaces (2026-06-18)

## Problem

All three memory scripts (`session-end-drain.py`, `weekly-memory-maintenance.py`, `monthly-synthesis.py`) were originally created with imports from `hermes_tools` for functions that don't exist in that module:

- `hindsight_retain` — not exported
- `fact_feedback` — not exported
- `session_search` — not exported
- `memory` — not exported
- `hindsight_recall` — not exported
- `fact_store` — not exported
- `mcp_contextforge_memory_query` — not exported
- `mcp_contextforge_memory_delete_batch` — not exported

## Actual hermes_tools exports

Available only inside `execute_code` context:

```
read_file, write_file, search_files, patch, terminal, json_parse, shell_quote, retry
```

That's it. No memory, no hindsight, no fact_store, no MCP tools.

## Real interfaces used in the rewritten scripts

### L3 fact_store (SQLite)

DB path: `~/.hermes/memory_store.db`

Schema:
```sql
CREATE TABLE facts (
    fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content         TEXT NOT NULL UNIQUE,
    category        TEXT DEFAULT 'general',
    tags            TEXT DEFAULT '',
    trust_score     REAL DEFAULT 0.5,
    retrieval_count INTEGER DEFAULT 0,
    helpful_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP
);
```

Operations:
- Read recent facts: `SELECT fact_id, content, category, trust_score FROM facts WHERE deleted_at IS NULL ORDER BY updated_at DESC LIMIT ?`
- Trust feedback: `UPDATE facts SET helpful_count = helpful_count + 1, trust_score = MIN(1.0, trust_score + 0.05) WHERE fact_id = ? AND deleted_at IS NULL`
- Dedup: Group by `substr(content, 1, 80)`, soft-delete all but newest: `UPDATE facts SET deleted_at = ? WHERE fact_id = ?`

### L2 Hindsight (HTTP)

URL: `http://localhost:9876`

- Health: `GET /health`
- Retain: `POST /retain` with JSON body `{"content": "...", "context": "...", "tags": [...]}`
- Memories: `GET /memories?limit=N`

Gracefully skip if connection refused. Do not crash the script.

### L1 Pruning (subprocess)

Script: `~/.hermes/bin/memory-prune.sh`

- Read-only audit: exits 0 (clean), 1 (warnings), 2 (critical)
- With `--fix`: soft-deletes L3 duplicates
- Budget is now config-driven (reads `memory.memory_char_limit` from `~/.hermes/config.yaml`)

### L4 ContextForge

Blacklisted per security policy (exfiltration issue). Scripts skip L4 and log "SKIPPED (ContextForge blacklisted per security policy)". Do not re-enable.

## Verification commands

```bash
# Compile check
python3 -c "import py_compile; py_compile.compile('/Users/jack.reis/.hermes/scripts/session-end-drain.py', doraise=True)"

# Run check
python3 ~/.hermes/scripts/session-end-drain.py test
python3 ~/.hermes/scripts/weekly-memory-maintenance.py
python3 ~/.hermes/scripts/monthly-synthesis.py

# Budget check
~/.hermes/bin/memory-prune.sh | grep "MEMORY.md (injected)"

# L3 health
sqlite3 ~/.hermes/memory_store.db "SELECT count(*), avg(trust_score) FROM facts WHERE deleted_at IS NULL"
```