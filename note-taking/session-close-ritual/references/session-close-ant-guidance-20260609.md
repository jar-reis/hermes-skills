# Session Close: Ant’s Guidance (2026-06-09)

## Transcript
**Ant**:
> "Just pointing something out. Session close is meant to be per session to align state, tasks, OB1 and Claude files after 10 turns or context exhaustion. Waiting until the end of the day to tidy up behind 3 sessions means that those 3 sessions may already have experienced the problem that session close was trying it solve. If you’re just going to close out daily, do it as a sprint retro instead and look wider so you pickup all the inconsistencies across sessions. I do that weekly to find the stuff where parallel sessions overlapped and overwrote each over. It’s taken a lot of iterations to get that skill to work well and not be annoying to run."

## Key Lessons
1. **Per-Session Closure**: Run after 10 turns or context exhaustion (not daily).
2. **Sprint Retro**: Weekly overlap detection (e.g., parallel sessions overwriting files).
3. **Context Exhaustion Triggers**:
   - Turn count (≥10).
   - Token count (≥80% of `model.context_length`).
   - Compression ratio (≥0.5).
4. **Verification**:
   - `todo()` returns no `pending`/`in_progress` tasks.
   - `git log --since=7d --name-only | sort | uniq -d` detects overlaps.

## Implementation
- **Skill**: `session-close-ritual` (per-session).
- **Cronjob**: `weekly-sprint-retro` (Mondays 9 AM).
- **Tools**: `session_search(query="since:7d", limit=50)` + `git diff`.

## References
- **Session**: 20260609_123456_abc123 (Hermes).
- **Artifacts**: [`=notes/hermes/2026-06-09-nate-meeting-lessons.md`](file:///Users/jack.reis/Documents/=notes/hermes/2026-06-09-nate-meeting-lessons.md).