# Deferred Memory-Plane Verification Manifest

## Context

When a memory plane (e.g., ContextForge) is quota-exhausted, post-write verification cannot run. The verification is *deferred* until the quota resets. This reference documents the manifest pattern for tracking deferred verifications and automatically closing them after quota reset.

## Problem

- **ContextForge quota exhaustion** (500/500 queries/month) blocks all L4 operations.
- Verification queries that should have run are skipped.
- Without a tracking mechanism, deferred verifications are forgotten — the gap is never closed.
- A separate reconciliation job is overkill — the daily cron is already the natural checkpoint.

## Solution: Deferred-Planes Manifest

Maintain a JSON manifest at `~/.hermes/deferred-planes.json` that lists planes with deferred verification, their reset dates, and the queries that need to run.

### Manifest Schema

```json
{
  "description": "Manifest of memory planes with deferred verification due to quota exhaustion.",
  "entries": [
    {
      "plane": "ContextForge",
      "deferred_date": "2026-06-19",
      "reset_date": "2026-07-01",
      "reason": "quota_exceeded_queries (500/500)",
      "deferred_verification_queries": [
        "memory_query --query 'Daily Best Practices Extension findings'",
        "memory_list_items --limit 50"
      ],
      "status": "deferred"
    }
  ]
}
```

### Workflow

1. **At deferral time**: When a plane is quota-exhausted, add an entry to the manifest with:
   - Plane name
   - Date the deferral was recorded
   - Quota reset date
   - List of verification queries that would have run
   - Status: `"deferred"`

2. **At the start of each daily run**: Check if any deferred plane's reset date has passed:
   ```python
   import json, datetime
   manifest = json.load(open("~/.hermes/deferred-planes.json"))
   today = datetime.date.today()
   for entry in manifest["entries"]:
       if entry["status"] == "deferred":
           reset = datetime.date.fromisoformat(entry["reset_date"])
           if today >= reset:
               # Run deferred verification queries
               # On success: remove entry or set status to "resolved"
               # On failure (still exhausted): leave entry, try next run
               pass
   ```

3. **After successful reverification**: Remove the entry from the manifest (or set `status: "resolved"` with the verification result).

### Rules

- **Cap catch-up queries at 10 per run** to avoid burning the entire fresh quota on catch-up.
- **Prioritize most recent deferred entries first**.
- **Handle failure gracefully**: If the plane is still quota-exhausted after the reset date (e.g., quota rolls over on a different schedule), leave the entry and try again next run.
- **Record the verification result** in the handoff or plan outcome to close the gap.

## When NOT to Use

- **Temporary outages** (network blips, daemon restarts): These resolve within minutes. Just retry — don't add a manifest entry.
- **Permanent deprecation**: If a plane is permanently removed, delete the entry — there's nothing to reverify.

## Integration with Daily Best-Practices Cron

The daily best-practices extension cron is the natural checkpoint for this check. Add a pre-flight step at the top of the daily run:

```python
# Pre-flight: check deferred planes
manifest = json.load(open("~/.hermes/deferred-planes.json"))
today = datetime.date.today()
for entry in manifest["entries"]:
    if entry["status"] == "deferred":
        reset = datetime.date.fromisoformat(entry["reset_date"])
        if today >= reset:
            print(f"REVERIFY: {entry['plane']} quota reset on {entry['reset_date']}")
            # Run deferred queries, cap at 10
```

## Current State (2026-06-24)

- ContextForge: deferred (500/500, reset 2026-07-01)
- First run on or after 2026-07-01 should reverify using this manifest.