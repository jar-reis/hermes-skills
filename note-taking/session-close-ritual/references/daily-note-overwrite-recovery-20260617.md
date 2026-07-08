# Daily Note Overwrite Recovery

**Pitfall**: Using `write_file` on an append-only surface like `memory/YYYY-MM-DD.md` replaces the entire file, destroying all prior session entries. This happened 2026-06-17 when appending a pickup session entry — the file went from 188 lines (multiple sessions) to 40 lines (only the new entry).

## Recovery procedure

1. **Restore from git**:
   ```bash
   cd ~/Documents/=notes
   git show HEAD:memory/YYYY-MM-DD.md > /tmp/daily-restore.md
   ```

2. **Combine with your new entry**:
   ```bash
   cat /tmp/daily-restore.md > memory/YYYY-MM-DD.md
   # Then append your new entry via patch or write_file with full content
   ```

3. **Verify**:
   ```bash
   wc -l memory/YYYY-MM-DD.md  # Should be >= original line count
   ```

## Prevention

- **Use `patch` with `mode='replace'`** to append to daily notes, inboxes, and ledgers. Find a unique anchor string near the end and replace it with itself + your new entry.
- **Or read first, then write**: `read_file` the full content, prepend/append your entry in memory, then `write_file` the combined result.
- **Never `write_file` on append-only surfaces without reading first.**

## Affected surfaces

- `memory/YYYY-MM-DD.md` — daily notes
- `claude/coordination/inbox-fleet.md` — fleet inbox
- `claude/coordination/LEDGER.md` — lifecycle ledger
- Any file described as "append-only" or "accumulates entries across sessions"

## Discovered

2026-06-17 — Hermes session `20260617_telegram_main (pickup)`. Overwrote `memory/2026-06-17.md` from 188 lines to 40 lines. Recovered from git HEAD.
