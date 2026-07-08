# Session Log Format

## On-Disk Location

Session logs live at `~/session-logs/` (85+ files as of 2026-06-19).

## Filename Schema

```
YYYYMMDD_HHMMSS.<HARNESS>.<worker_thread_pane>.<SESSION-UUID>.<PID>.<size_bytes>.log
```

### Field Breakdown

| Field | Example | Description |
|-------|---------|-------------|
| `YYYYMMDD_HHMMSS` | `20260603_143801` | Session start timestamp |
| `<HARNESS>` | `Claw` | Harness/app that produced the log (Claude Code = `Claw`) |
| `<worker_thread_pane>` | `w0t0p0` | Worker N, thread N, pane N (zero-indexed) |
| `<SESSION-UUID>` | `615C605D-B7E6-40AE-AD46-D96F5E3896AD` | Unique session identifier |
| `<PID>` | `90374` | Process ID of the harness |
| `<size_bytes>` | `3748711420` | Log file size in bytes |

### Known Harnesses

| Harness value | Agent |
|---------------|-------|
| `Claw` | Claude Code |
| (TBD) | Hermes |
| (TBD) | OpenClaw / Pi |
| (TBD) | Codex |
| (TBD) | Kimi |

## What's Missing (and why it didn't matter)

The filename schema captures **harness + session UUID + timestamp** but does
NOT include model, host, or agent identity. The original plan proposed
enriching session log filenames to add these fields.

**Resolution (2026-06-23):** Session log enrichment was bypassed entirely. The
chronological brief builder (`~/.hermes/scripts/chronological_brief.py`)
queries `[TURN]` entries from the Holographic fact_store instead, which already
carry agent, model, session, cwd, and snippet metadata (captured by the
turn-end hook). This was simpler and avoided changing the session log naming
convention. Session logs remain as raw transcripts — the `[TURN]` fact_store
is the structured layer.

## Related

- Turn-sync skill: `note-taking/turn-sync/SKILL.md` → "Chronological Federation Format" section
- Knowledge graph entry: `=notes/knowledge-graph/Users-jack-reis--session-logs.md`
- Session log design plan: `=notes/docs/plans/2026-03-15-session-log-skill-design.md`
- Session log hook repair: `=notes/docs/plans/2026-04-11-session-log-hook-repair.md`