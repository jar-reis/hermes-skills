# Update-pickup wrap: conflict-marker cleanup and live fanout finalization (2026-06-14)

## Context
During a Hermes update pickup wrap, the session appended closeout records to a vault that already had broad concurrent dirty state and an existing merge conflict in `daily/2026-06-14.md`. The first patch preserved both sides of the conflict but accidentally left conflict markers. A verifier then caught `<<<<<<<`, `=======`, and `>>>>>>>` markers before final response. The session removed markers, verified no markers remained, rotated `LATEST_HANDOFF.md`, generated a PDF snapshot, sent a Discord fleet notification, and patched previously-written artifacts with the live message ID.

## Reusable pattern
1. Before wrap writes, assume daily notes and fleet inbox may contain concurrent edits or conflict markers.
2. After every append/patch to a daily note, inbox, handoff, or ledger, run a marker check over touched markdown files:
   - `<<<<<<<`
   - `=======`
   - `>>>>>>>`
3. If conflict markers are present, preserve both meaningful content sides, remove only the markers, then re-run the marker check.
4. For files previously in conflict, also check index state with `git ls-files -u -- <path>` or `git status --short -- <path>`. A clean worktree file can still be flagged as unmerged until the index is reconciled later.
5. If late side effects occur after the first artifact write — e.g. PDF export succeeds, live notification sends, `LATEST_HANDOFF.md` rotates — patch all already-written surfaces before final response:
   - handoff
   - snapshot
   - plan/outcome
   - daily note
   - coordination ledger
   - fleet inbox
6. Do not claim wrap complete until the artifact markers and final side effects are represented consistently.

## Example final verifier shape
```bash
cd /Users/jack.reis/Documents/=notes
python3 claude/scripts/validate_handoff_custody.py <handoff.md>
python3 - <<'PY'
from pathlib import Path
for rel in [
    'daily/YYYY-MM-DD.md',
    'claude/coordination/inbox-fleet.md',
    'claude/coordination/LEDGER.md',
    'claude/mcp-coordination/state/session-handoffs/<handoff>.md',
]:
    text = Path(rel).read_text(errors='replace')
    if any(marker in text for marker in ('<<<<<<<', '=======', '>>>>>>>')):
        raise SystemExit(f'CONFLICT_MARKER {rel}')
print('NO_CONFLICT_MARKERS')
PY
git ls-files -u -- daily/YYYY-MM-DD.md claude/mcp-coordination/state/session-handoffs/LATEST_HANDOFF.md
readlink claude/mcp-coordination/state/session-handoffs/LATEST_HANDOFF.md
```

## Lesson
A wrap artifact is not final just because it was written. In a concurrent vault, finalization includes: conflict-marker scan, index awareness, late-side-effect reconciliation, and artifact marker verification.