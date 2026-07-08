# Cron Memory Fallback and Quota Handling

## Context
Cron jobs (e.g., `fleet-beads-linear-kanban`, nightly memory syncs) must capture lessons, insights, and follow-ups to **persistent memory**. However, memory providers (e.g., ContextForge Hindsight, Open Brain) may be unavailable or quota-limited during execution.

## Problem
- **ContextForge Hindsight Quota:** The `mcp_contextforge_memory_ingest` tool enforces a query limit (e.g., 500/500). When exceeded, the tool rejects new entries with `quota_exceeded_queries`.
- **MCP Unavailability:** If the MCP server (e.g., ContextForge) is unreachable, the `mcp_contextforge_memory_ingest` tool fails silently or returns an error.
- **Durable Lessons:** Cron jobs must capture lessons even when primary memory providers are unavailable.

## Solution
Use **fallback memory providers** and **session transcripts** to ensure lessons are not lost. The fallback hierarchy:

1. **Open Brain** (`mcp_open_brain_capture_thought`)
   - Preferred fallback for structured lessons.
   - Example payload:
     ```json
     {
       "content": "Beads poll and Kanban seeding completed as scheduled cron job. Summary of open issues, review gate status, and follow-ups.",
       "source": "hermes-cron",
       "task_id": "beads-linear-sync-<timestamp>"
     }
     ```

2. **Session Transcript**
   - If Open Brain is unavailable, log the lesson in the session transcript.
   - Example:
     ```markdown
     [CRON LESSON]
     Beads poll and Kanban seeding completed (2026-06-19 20:00 UTC).
     - Open issues: 22 (all blocked).
     - Substack Phase 1: complete (45/45 posts).
     - Hindsight quota exceeded; lesson captured in Open Brain.
     ```

3. **Local File Backup**
   - As a last resort, append lessons to a local file (e.g., `/tmp/beads_linear_kanban_lessons.log`).
   - Example:
     ```bash
     echo "$(date -u) | Beads poll complete. Open issues: 22. Hindsight quota exceeded." >> /tmp/beads_linear_kanban_lessons.log
     ```

## Quota Handling
- **Monitor Reset Dates:** ContextForge Hindsight quota resets on the 1st of each month (e.g., 2026-07-01).
- **Fallback on Quota Exceeded:** If `mcp_contextforge_memory_ingest` returns `quota_exceeded_queries`, immediately fall back to Open Brain or session transcript.
- **Log Quota Status:** Include quota status in the lesson (e.g., "Hindsight quota: 500/500").

## Verification
- **Open Brain:** Confirm lessons are captured by querying `mcp_open_brain_list_thoughts` with `source="hermes-cron"`.
- **Session Transcript:** Search the transcript for `[CRON LESSON]` markers.
- **Local File:** Check `/tmp/beads_linear_kanban_lessons.log` for entries.

## Example Workflow
```bash
# Attempt Hindsight ingest
if ! mcp_contextforge_memory_ingest "$LESSON"; then
  # Fall back to Open Brain
  if ! mcp_open_brain_capture_thought "$LESSON"; then
    # Fall back to session transcript
    echo "[CRON LESSON] $LESSON" >> "$SESSION_TRANSCRIPT"
  fi
fi
```

## References
- **Open Brain:** `mcp_open_brain_capture_thought` tool documentation.
- **Hindsight Quota:** ContextForge dashboard (https://contextforge.dev/dashboard/billing).
- **Session Transcripts:** Hermes session DB (`session_search`).