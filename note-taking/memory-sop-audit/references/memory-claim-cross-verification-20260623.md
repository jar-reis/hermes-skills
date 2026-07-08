# Memory-Claim Cross-Verification Audit (2026-06-23)

## Problem

Memory facts go stale silently. A session that reads its own injected MEMORY.md
will see quantitative claims (doc counts, pod counts, port numbers, graph node
counts, script paths) that were accurate when written but have since drifted.
Acting on stale facts produces incorrect conclusions — e.g., the fleet-agent-
investigation plan (2026-06-23) was created because an agent read 11-day-old
gateway logs and presented them as current state.

## Technique

### Step 1: Enumerate quantitative claims in MEMORY.md

Read `~/.hermes/memories/MEMORY.md` and list every claim that includes a
number, path, port, or status:

```
- "39,421 docs across 11 pods as of 2026-06-22"  → OBn
- "873 graph nodes"                              → skills map
- "launchd job com.jackreis.obn-sync runs every 30min" → schedule
- "Health check via obn_healthcheck.py"          → script path
- "5 OBn pods failing: ..."                       → pod health
- "MEMORY.md at 59%"                              → capacity
```

### Step 2: Probe each claim against the live source

| Claim type | Live probe |
|-----------|-----------|
| OBn doc/pod count | `mcp_fleet_memory_fleet_memory_status` |
| Graph node count | `jq '.nodes \| length' knowledge-graph.json` |
| Port/service health | `lsof -i :PORT` + `curl -s -o /dev/null -w "%{http_code}" URL` |
| Cron health | `hermes cron list` (check `error:` fields) |
| Script path exists | `find ~/.local/bin -name 'pattern*'` |
| Memory capacity | `wc -c ~/.hermes/memories/MEMORY.md` vs config limit |
| Hindsight freshness | `curl -s http://localhost:8888/health` + check `last_document_at` |
| Holographic L3 duplicates | `~/.hermes/bin/memory-prune.sh` (read-only) |
| Plan completion status | `grep -l 'status:\|Status:' ~/.hermes/plans/YYYY-MM-DD-*.md` |

### Step 3: Flag discrepancies and categorize

For each stale fact, categorize the severity:
- **CRITICAL**: the stale fact would cause an agent to take wrong action
  (e.g., "5 pods failing" when only 1 is empty; "59% full" when actually 99%)
- **STALE**: the fact is outdated but not dangerous (e.g., old doc count)
- **WRONG PATH**: the cited path doesn't exist; agent will get "file not found"

### Step 4: Fix both MEMORY.md and reference files

A stale fact in MEMORY.md must be corrected in MEMORY.md. But if the same
fact is duplicated in a skill's `references/` file, fix that too — the
reference file is what subagents load with `skill_view(file_path=...)`.

### Step 5: Check for root causes, not just symptoms

- If Hindsight `last_document_at` is 3 days stale despite drain cron running
  "ok", the root cause is an empty drain queue, not a cron failure.
- If the system prompt says "10,000 char limit" but config says 6,000, the
  root cause is a mismatch between the system prompt template and config.
- If a plan's frontmatter says "status: pending" but the work is committed,
  the root cause is a missing plan-closeout step.

## Findings from 2026-06-23 audit

| Claim | Memory said | Reality | Severity |
|-------|------------|--------|----------|
| OBn docs/pods | 39,421 / 11 | 55,324 / 12 | STALE |
| OBn failing pods | 5 failing | 1 empty (gardening) | CRITICAL |
| obn_healthcheck.py path | ~/.local/bin/ | ~/Documents/=notes/claude/scheduled-tasks/vault-ingest/ | WRONG PATH |
| MEMORY.md capacity | 59% (10,000 limit) | 99% (6,000 limit) | CRITICAL |
| Hindsight freshness | not checked | last_document 3 days stale | CRITICAL |
| Ankit plan status | pending | completed (committed) | STALE |
| Graph nodes | 873 | 873 (correct) | OK |
| VoltAgent console | running on 3141 | running, HTTP 200 | OK |
| launchd interval | 30min | 30min (1800s, correct) | OK |