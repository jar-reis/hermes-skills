---
name: memory-sop-feedback-loop
version: 1.1.0
created: 2026-06-03
updated: 2026-06-03
author: Hermes
description: >
  How and when to call fact_feedback on L3 facts. Without feedback
  the trust_score stays at the 0.5 default and `reason` / `contradict`
  queries have no signal. Skill exists to enforce the loop.
---

# Memory SOP — L3 Feedback Loop

## The problem (found in audit 2026-06-03)

L3 fact_store has 56 active facts at trust_score=0.5, 0 of which
have ever been retrieved. The trust score default is 0.5; it only
moves when `fact_feedback(action='helpful'|'unhelpful', fact_id=N)`
is called. Without feedback, `fact_store(action='reason')` returns
uniform-prior results and `action='contradict'` has no signal.

This is **silent corruption**: the store looks healthy (N facts,
K categories) but every fact has the same prior, so signal-driven
queries are useless. The fix is procedural, not technical.

## When to call fact_feedback

For EVERY fact retrieved from L3 during a session:

  - Was the fact correct AND useful for the task?  → `helpful`
  - Was the fact wrong, stale, or not applicable?   → `unhelpful`
  - Was the fact returned but the agent didn't use it? → `unhelpful`
    (a non-use is still a signal — the retrieval was wasted)

## How to call

The actual MCP tool is `fact_feedback` (action='helpful' or
'unhelpful', fact_id=N). The Hermes platform wires this up; this
skill is about the procedure, not the API.

For batch rating (e.g. after a research session), iterate retrieved
facts and call once per fact. Don't aggregate — the trust score
must update per fact to give the scoreboard meaning.

## Integration points

There are three places the loop should be wired:

1. **Session end (AGENTS.md §Session Shutdown)** — for each fact
   that was used during the session, call fact_feedback before
   the daily note write. This is the most important wiring;
   without it, every session makes the problem worse.

2. **In-script usage** — if a fact_store probe is the basis for a
   decision, rate the probe results before the decision is logged.
   This makes the trust score reflect actual usage patterns.

3. **Cron** — a daily job can run a "trust decay" pass: any fact
   not retrieved in 30 days gets `unhelpful` (deprecates with grace).
   This keeps the L3 store from being write-only long-term.

   Candidate cron spec (not yet scheduled):
   `0 23 * * *` daily at 11 PM, with a Python script that selects
   facts where `retrieval_count = 0 AND created_at < now - 30 days`
   and calls `fact_feedback('unhelpful', fact_id=N)`.

## How to verify it's working

```
~/.hermes/bin/memory-prune.sh
```

The audit reports avg trust per category. If all categories are
still at 0.5, the feedback loop is not being called and the store
is degraded. Expected steady state: 0.3–0.7 average with at least
30% of facts having retrieval_count > 0.

## Anti-patterns

- ❌ Never hard-delete a fact in response to "unhelpful" feedback.
  The audit trail matters — `deleted_at` is for duplicates and
  superseded facts, not for subjective dislike.
- ❌ Never call `helpful` defensively because the fact was retrieved.
  Retrieval without usefulness is still a waste — rate `unhelpful`.
- ❌ Never skip feedback "to save time." The 3-second cost of a
  rating is dwarfed by the cost of operating on a degraded store.
- ❌ Never fabricate fact_feedback calls. If you didn't actually
  retrieve the fact, don't rate it. Per the `no-fabricated-deployments`
  skill, only call the tool when you have a real retrieval to
  evaluate.

## When this skill can't help

If the `fact_feedback` MCP tool isn't exposed in your session's
toolset, you can't run the loop from inside the agent. The
mitigations are:

  1. Document the gap explicitly (don't fabricate ratings).
  2. Wire the tool into the platform's session-end ritual so
     the next session can run it.
  3. Schedule a Python wrapper that calls the fact_feedback
     equivalent directly via the fact_store SQLite schema.

Until the wiring is in place, the L3 store will remain degraded
by design — the audit will report "0 of N facts retrieved" and
that is an accurate signal, not a bug to fix in the moment.

## Files

- (no script — this is a procedure skill, paired with the
  `fact_feedback` MCP tool and the AGENTS.md session-end ritual)
- `~/.hermes/skills/note-taking/memory-sop/` — the parent SOP

## Changelog

- v1.1.0 (2026-06-03): added "When this skill can't help" section
  for sessions without `fact_feedback` in the toolset; added
  candidate cron spec for trust decay; added changelog.
- v1.0.0 (2026-06-03): initial release.
