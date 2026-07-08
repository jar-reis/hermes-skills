# OBn Ultra-Robust Architecture (2026-06-22, updated 2026-06-23)

## Status: HEALTHY — 55,324 docs across 12 pods (as of 2026-06-23T18:33)

> Previous snapshot (2026-06-22): 39,421 docs across 11 pods. Growth
> driven by AI Exec Circle integration (1578 files ingested) and continued
> vault sync. The `gardening` pod is the only known empty pod (0 docs).

## Architecture

The OBn vault ingestion system was overhauled on 2026-06-22 from a stale, manually-triggered, three-competing-scripts mess into a self-healing, continuously-syncing, monitored knowledge graph.

### Canonical Path
- **Single script**: `ingest_chroma.py --all-pods` → local ChromaDB + Ollama nomic-embed-text
- **No cloud dependency**: Zero Supabase, zero edge functions
- **ChromaDB**: `chroma_db/` directory (was `chroma_db_v2/`, renamed, symlink removed)

### Sync Pipeline
1. `run-obn-sync.sh` — unified wrapper, verifies Ollama + nomic-embed-text, runs all pods
2. `com.jackreis.obn-sync` launchd plist — every 30 minutes (StartInterval 1800), `RunAtLoad: true`
3. **Python wrapper** at `~/.local/bin/obn-sync-launchd.py` — bypasses macOS TCC (see cron-automation pitfall #41)
4. Git post-commit hook — immediate sync on vault commits (lockfile-protected)
5. Hermes cron watchdog — every 2h, auto-restarts dead launchd, alerts via Telegram

### Hardening
- **Retry logic**: Ollama 400s → batch splitting (32→16→8) → fallback model (mxbai-embed-large)
- **State DB**: WAL mode + auto-recovery on corruption
- **Per-pod error isolation**: one pod failure doesn't abort the run
- **Frontmatter validation**: `obn: exclude` and `obn: vault-only` tags checked at runtime
- **Semantic cache**: 24h TTL + flush capability
- **Vault fallback**: `obn_query.py` degrades to filename search if ChromaDB is down

### Monitoring
- `obn_healthcheck.py` — 18 checks across Ollama, ChromaDB, state DBs, disk, launchd, sync logs
  - **Note**: The healthcheck script lives at
    `~/Documents/=notes/claude/scheduled-tasks/vault-ingest/obn_healthcheck.py`,
    NOT at `~/.local/bin/obn_healthcheck.py` (memory entry had wrong path — corrected 2026-06-23).
- Hermes cron: daily health digest at 9 AM (Telegram), morning brief at 8 AM
- `RUNBOOK.md` — 4 incident playbooks (ChromaDB corruption, Ollama down, launchd dead, state DB corruption)

### Pod Layout (12 pods, as of 2026-06-23)
| Pod | Collection | Docs (approx) |
|-----|-----------|------|
| core | ob1_ob1_core | 22,700+ |
| ai_systems | ob1_ob_ai_systems | 6,600+ |
| sea_ranch | ob1_ob_sea_ranch | 6,200+ |
| ai_exec_circle | (new) | 1,500+ |
| property_management | ob1_ob_property_management | 1,300+ |
| job_search | ob1_ob_job_search | 700+ |
| rib_recovery | ob1_ob_rib_recovery | 400+ |
| home_improvement | ob1_ob_home_improvement | 400+ |
| family_therapy | ob1_ob_family_therapy | 300+ |
| crawlsight | ob1_ob_crawlsight | 300+ |
| infra | ob1_ob_infra | 70+ |
| gardening | ob1_ob_gardening | 0 (empty — known issue) |
| session_memory | session_memory | 19 |

> Exact counts change with every 30-min sync; use
> `mcp_fleet_memory_fleet_memory_status` for live numbers.

### Critical Pitfall
**Never run two `ingest_chroma.py` processes concurrently** — corrupts HNSW index files causing segfaults. See `cron-automation/references/chromadb-concurrent-write-corruption-20260622.md`.

### Archived (2026-06-22)
- `ingest.py` (Supabase path — superseded)
- `ingest_local.py` (older local path — superseded)
- `ingest_local_batched.py` (hybrid Supabase+Ollama — superseded)
- `run-ob1-core-sync.sh` (called wrong script)
- `com.jackreis.ob1-core-sync.plist` (never loaded)
- `sync_to_supabase.py` (Supabase sync — not needed)

### What Changed vs Pre-2026-06-22
- Was: 22,467 docs frozen at April 14, 3 competing scripts, never-loaded launchd, empty state DBs, broken symlink
- Now (2026-06-23): 55,324 docs across 12 pods, single canonical path, launchd every 30min, git hook, health monitoring, self-healing. AI Exec Circle content integrated hourly.