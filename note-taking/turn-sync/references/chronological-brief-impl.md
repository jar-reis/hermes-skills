# Chronological Brief Implementation (2026-06-23)

## Architecture

The chronological brief replaced the old semantic grab-bag brief. Instead of
random Holographic facts, it shows a table of recent fleet activity per agent.

```
┌─────────────────────────────────────────────────┐
│  local_turn_sync_hook.py                         │
│    (UserPromptSubmit hook — turn-start)          │
│                                                   │
│  ┌─────────────────────────────────────────┐     │
│  │  chronological_brief.py                  │     │  PRIMARY
│  │  ~/.hermes/scripts/                     │     │
│  │                                          │     │
│  │  1. Query [TURN] entries from            │     │
│  │     Holographic fact_store SQLite        │     │
│  │  2. Parse agent/session/model/snippet    │     │
│  │  3. Dedupe by agent (most recent)       │     │
│  │  4. Emit markdown table                  │     │
│  └─────────────────────────────────────────┘     │
│                                                   │
│  ┌─────────────────────────────────────────┐     │
│  │  brief() — semantic search              │     │  SUPPLEMENT
│  │  (Holographic + Hindsight + OBn)         │     │
│  │  demoted to supplement section          │     │
│  └─────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  turn-sync-surface.py                            │
│  (cron, every 5 min)                             │
│                                                   │
│  Writes chronological brief to:                  │
│    ~/.hermes/state/turn-sync-chronological.md    │
│                                                   │
│  Also writes OB1-only surface:                   │
│    ~/.hermes/state/turn-sync-recent.md            │
└─────────────────────────────────────────────────┘
```

## Key Files

| File | Role |
|------|------|
| `~/.hermes/scripts/chronological_brief.py` | Main builder script (380 lines) |
| `=notes/scripts/fleet_memory/local_turn_sync_hook.py` | Turn-start hook, imports builder (line 213-216) |
| `~/.hermes/scripts/turn-sync-surface.py` | Cron job, writes state file (lines 317-324) |
| `~/.hermes/state/turn-sync-chronological.md` | Cached brief output |
| `~/.hermes/memory_store.db` | Holographic SQLite DB, source of `[TURN]` entries |

## Verification Commands

```bash
# Full brief (default)
python3 ~/.hermes/scripts/chronological_brief.py

# Table only (no header, no supplement)
python3 ~/.hermes/scripts/chronological_brief.py --table-only

# JSON output (structured)
python3 ~/.hermes/scripts/chronological_brief.py --json

# Check cron state file is being written
cat ~/.hermes/state/turn-sync-chronological.md

# Verify hook integration (should show import on lines 213-216)
grep -n 'chronological_brief' ~/Documents/=notes/scripts/fleet_memory/local_turn_sync_hook.py
```

## Design Rationale

### Why [TURN] fact_store, not session logs?

The original plan (2026-06-23-turn-sync-chronological-brief.md) proposed
enriching session log filenames with host/agent/model metadata, then scanning
those logs. The subagent that built the script correctly bypassed this:

1. **[TURN] entries already carry the metadata** — agent, session, cwd, model,
   platform, and user snippet are captured by the turn-end hook into the
   Holographic fact_store. No enrichment needed.
2. **Session logs are raw transcripts** — they don't have structured metadata
   and would require content parsing to infer agent/model.
3. **Simpler integration** — one SQLite query vs. scanning 85+ log files,
   parsing filenames, and reading first/last lines.
4. **Already deduped by the hook** — the turn-end hook writes one `[TURN]`
   entry per turn, so the fact_store is already structured.

### Why Holographic fact_store, not Hindsight?

The investigation report (2026-06-23) confirmed Hindsight's `/recent` endpoint
returns 404 — it doesn't exist. The fact_store SQLite DB is directly queryable
and carries the `[TURN]` entries the hook writes. Hindsight is used for
semantic search (the supplement section), not chronological queries.

## Known Limitations

1. **Host is always `hostname`** — the script uses `platform.node()` which
   returns the machine's hostname, not a fleet-friendly name like "MBP" or
   "Aegis". All entries show the same host.

2. **Only agents that write [TURN] entries appear** — agents without the
   turn-end hook (e.g., raw CLI sessions not wired to the hook) won't show up.
   The OB1 supplement partially covers this.

3. **Snippet is the user's prompt, not the assistant's output** — the `[TURN]`
   entry captures the user's message, not what the agent did about it. This
   shows "what was asked" not "what was accomplished."

4. **Hindsight is NOT queried for chronological data** — the script only
   queries the Holographic fact_store. Hindsight's `/recent` endpoint doesn't
   exist (returns 404). This is by design — the fact_store has what we need.

## Pitfalls

- **If memory_store.db is missing or empty**, the table will be empty and
  only the semantic supplement will show. The script handles this gracefully
  (returns empty list, `build_chronological_table` returns "No recent fleet
  activity found").

- **If the script is missing**, the hook fails open — semantic search only.
  No error is raised. Check for the file at
  `~/.hermes/scripts/chronological_brief.py` if the chronological table
  disappears from the brief.

- **Stale entries** — [TURN] entries persist forever in the fact_store. The
  `LIMIT 50` in the query means very old entries could appear if no recent
  turns have been captured. Consider adding a time filter (e.g.,
  `created_at > datetime('now', '-24 hours')`) if this becomes a problem.