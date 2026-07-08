---
name: session-close-ritual
description: Run at session end to reconcile tasks, update skills, and write to brain. Enforces closure discipline across the fleet.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [session, closure, reconciliation, brain]
    related_skills: [verification-before-completion, memory-sop-drain]
---

# Session Close Ritual

## Overview

Enforce **per-session closure discipline** to prevent stale context from leaking into the next session. **Run after every 10 turns or context exhaustion** (not daily).

**Ant’s Guidance (2026-06-09)**:
> "Session close is meant to be per session to align state, tasks, OB1, and Claude files after 10 turns or context exhaustion. Waiting until the end of the day to tidy up behind 3 sessions means those 3 sessions may already have experienced the problem that session close was trying to solve."

**Context Exhaustion Triggers**:
- **Turn Count**: ≥10 turns (configurable via `agent.max_turns`).
- **Token Count**: ≥80% of `model.context_length` (e.g., 102,400/128,000 for kimi-k2.6).
- **Compression Ratio**: ≥0.5 (see `compression.threshold` in config).
- **Manual Override**: `/compress` or `/close`.

## Structured Shutdown Sequence

**Rule**: Follow this sequence for **session wrap-up** (cold restart or context exhaustion):

1. **Update Lifecycle Ledger**:
   - Append session work to `=notes/claude/coordination/LEDGER.md`.
   - Include **session ID**, **owner**, **status**, and **files updated**.
   - If the repo already has unrelated dirty state from another agent/session, do **not** use broad `git add -A` during wrap. Stage only files owned by this session, verify `git diff --cached --name-only`, and explicitly leave unrelated drift for its owner.

2. **Update Daily Note**:
   - Log session details in `memory/<date>.md`.
   - Include **next steps** and **caveats**.

3. **Write Handoff Document**:
   - Create `=notes/claude/mcp-coordination/state/session-handoffs/<session-id>.md`.
   - Include **context**, **files updated**, **next steps**, and **verification**.

4. **Notify Fleet**:
   - Post a summary to the **fleet inbox** (`=notes/claude/coordination/inbox-fleet.md`).
   - Send a **Telegram notification** (if applicable).

**Example**:
```markdown
## Session: 20260610_120000_hermes_fleet_review
**Owner**: Hermes
**Status**: Completed

### Work Completed
- Unblocked Codex lane via OpenAI API bypass.
- Updated `fleet-orchestration` skill.

### Files Updated
| File | Purpose |
|------|---------|
| `inbox-fleet.md` | Fleet updates |
| `fleet-orchestration/SKILL.md` | Updated skill |

### Next Steps
1. Monitor OpenAI API usage.
2. Regenerate Home Assistant token.
```

**Anti-patterns**:
- Skipping the ledger (loses session history).
- Omitting the handoff (breaks continuity).
- Not notifying the fleet (silent work).
- **Assuming Telegram will always work.** `python-telegram-bot` may not be installed in the session runtime. If `send_message` fails with "python-telegram-bot not installed", the file-based notification (fleet inbox append) is sufficient — do not loop retrying Telegram. The inbox entry serves the same fleet-awareness purpose.
- **Assuming `memory` tool will always accept writes.** The tool's round-trip guard rejects writes when MEMORY.md contains non-§-delimited content (tables, nested bullets). If `memory(action='add')` fails repeatedly with "content that wouldn't round-trip", fall back to direct `write_file` on MEMORY.md (rewrite to clean §-delimited format, then append new facts). The handoff, inbox, ledger, and daily note already carry the durable record — memory drain is a convenience, not a hard requirement that should block closeout.
- **Memory char limit on batch add.** The `memory` tool has a char limit (default 6000). When adding multiple facts via `operations`, the batch may exceed the limit even if individual entries are small. Always include `remove` operations in the same batch to free space — the limit is checked on the FINAL result, so a single batch can remove stale entries AND add new ones. If a batch is rejected for exceeding the limit, shorten the new entries or remove more stale ones and retry as a single atomic batch.
- **Leaving conflict markers in wrap surfaces.** Concurrent vault sessions can leave daily notes, fleet inboxes, or handoff pointers in conflict. After appending to any daily note, ledger, inbox, or handoff during wrap, scan touched markdown for `<<<<<<<`, `=======`, and `>>>>>>>`; preserve both meaningful sides and remove markers before claiming wrap complete. If a path was conflicted, also check `git ls-files -u -- <path>` because the worktree can look clean while the index still needs reconciliation. See `references/update-pickup-wrap-conflict-and-live-fanout-20260614.md`.
- **Overwriting append-style files with `write_file`.** Daily notes (`memory/YYYY-MM-DD.md`), fleet inboxes, and ledgers are append-only surfaces — they accumulate entries across sessions. Using `write_file` on them replaces the entire file, destroying all prior entries. **Always use `patch` with `mode='replace'` to append to these files**, or `read_file` first to get the full content, prepend/append your entry, then `write_file` the combined result. If you do overwrite, recover from git: `git show HEAD:<path> > /tmp/restore.md`, then combine and rewrite. See `references/daily-note-overwrite-recovery-20260617.md`.
- **Failing to reconcile late side effects.** If PDF export, live fanout, memory mirrors, or `LATEST_HANDOFF.md` rotation happen after the first handoff/snapshot write, patch every already-written surface with the final evidence (message ID, PDF path, pointer target) before the final response.

**Companion**: `verification-before-completion` (user-declared validation).

### 1. Reconcile Tasks
- Run `verification-before-completion` to catch stale tasks.
- Mark incomplete tasks as `cancelled` in `todo()`.
- Write handoff for pending work (include **session ID** and **timestamp**).
- **After context compression or active-task replay, reconcile again.** Compression can re-surface an older todo list after the user's active scope has narrowed to wrap/cold restart. Do not resume deferred repair tasks just because the replay says `pending`; mark completed wrap tasks as `completed` and approval-gated/deferred work as `cancelled` with a reason. See `references/context-compression-task-reconciliation-20260615.md`.

### 2. Update Skills

**Guiding principle** (Christopher Alexander, *A Pattern Language*):
> "When you build a thing you cannot merely build that thing in isolation, but must also repair the world around it, and within it, so that the larger world at that one place becomes more coherent, and more whole."

Every closeout is an opportunity to repair the skill library — not just the files you touched, but the skills that governed the work. If something was non-optimal, even slightly, fix it as part of the wrap. Be ACTIVE: most sessions produce at least one skill update. A pass that does nothing is a missed learning opportunity.

- Flag failed skills for iteration (e.g., "Failed: `browser-automation-handoff` — missing `CACHE_VERSION` bump").
- Patch skills with new pitfalls/fixes (e.g., "Added PWA cache trap to `verification-before-completion`").
- If a loaded skill had a wrong step, missing step, or outdated path, patch it NOW — don't leave it for the next session to rediscover.

### 3. Write to Brain

Capture durable session facts using the canonical fleet path (NOT the deprecated `.hermes/brain/` directory):

1. **local-turn-sync capture** (primary local dual-core path):
   ```bash
   /Users/jack.reis/Documents/=notes/bin/local-turn-sync capture "<one durable fact>" --source "<agent>" --session-id "session/YYYY-MM-DD-<slug>" --task-id "session/YYYY-MM-DD-<slug>" --kind "<decision|fact|correction|blocker|done|environment>"
   ```
2. **OB1 drain** (cross-tool mirror):
   ```bash
   eval "$("$HOME/.hermes/bin/ob1-token.sh" export)" && python3 /Users/jack.reis/Documents/=notes/bin/ob1-pull --capture "[SESSION] <summary>" --task-id "session/YYYY-MM-DD-<slug>" --source "<agent>"
   ```
3. **Memory tool** (L1 durable facts, if space allows): `memory(action='add', content='...', target='memory')`

If Hindsight (:9876) is reachable, local-turn-sync will also drain there. If it's down, holographic + OBn captures still succeed — never block on a single memory plane.

### 4. Knowledge Graph Integration
- For sessions involving **collaborative discussions** (e.g., Exec Circle, fleet coordination), update the knowledge graph (KG) to reflect:
  - **New Participants**: Add any new members to the KG nodes.
  - **Topics/Resources**: Include new topics, shared files, or tools.
  - **Decisions/Actions**: Document follow-ups, decisions, or community actions.
  - **Relationships**: Add edges like `mentions`, `shares`, `decides`, or `follows_up`.
- Use the `smart-graph` skill to verify note relationships and avoid orphans.
- For high-impact sessions, export the KG to a shared vault or dashboard (e.g., `index.md`).

See [`references/exec-circle-kg.md`](file:///Users/jack.reis/.hermes/skills/note-taking/session-close-ritual/references/exec-circle-kg.md) for a detailed workflow.

### 5. Sprint Retro (Weekly)
- **Scope**: All sessions since last retro.
- **Goal**: Detect overlaps (e.g., parallel sessions overwriting the same file).
- **Tool**: `session_search(query=

## Example

```bash
# Run the ritual
h Hermes session-close-ritual

# Verify — check local-turn-sync capture + OB1 drain
/Users/jack.reis/Documents/=notes/bin/local-turn-sync brief "session close" --limit 3
```