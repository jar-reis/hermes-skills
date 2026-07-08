# L1 vs OBn — Cold-Restart Surface Mismatch (2026-06-04)

## The pattern

The Hermes `memory` tool writes to L1 (`~/.hermes/memories/MEMORY.md`,
runtime-injected every turn, ≤2200 chars). The AGENTS.md auto-brief at
session start reads a *different* file first as step 1:
`~/Documents/=notes/claude/memory/HERMES-MEMORY.md` (OBn, vault-local,
unlimited, survives fleet agent handoffs).

L1 and OBn are NOT the same file. Writing only to L1 means the next
session's auto-brief is empty for the project, even though this
session's reasoning context was full of it.

## Real session: red-team project, 2026-06-04

Built a 30-probe red-team canary harness + 2 baselines + 70B OOM
post-mortem. Wrote a comprehensive L1 entry summarizing the project
location, baseline numbers, and the OOM-not-slow lesson. The L1
entry was 666 chars, well within budget.

User asked "ready for cold restart?" Ran the verifier:
- All 4 verifier commands pass
- Handoff file exists, 143 lines
- Git log shows recent commit
- BUT: HERMES-MEMORY.md has zero "red-team" mentions

A cold-restart session reading the auto-brief would only have found
the red-team work via the handoff file, and only if they were doing
work that cross-references it. The auto-brief would have surfaced
nothing.

## The fix

Dual-write. When writing a project-level fact (location, baseline,
lesson, next-action) that should survive to the next session's
auto-brief:

1. Write to L1 with the `memory` tool (or skip if budget-constrained
   and the fact is project-level, not session-internal)
2. ALSO append to OBn with `write_file` to
   `~/Documents/=notes/claude/memory/HERMES-MEMORY.md`

OBn is plain markdown, no size budget, no tokenization rules.
Append at the end of the file; preserve the `## YYYY-MM-DD — Topic`
section header pattern that OBn already uses. Surgical append only,
never overwrite the whole file.

## When to skip the dual write

- L1-only facts (user preferences, agent identity, project-of-the-
  day pointers) → L1 only, OBn would be noise
- Ephemeral state (current PID, current task list) → L1 only, OBn
  would be stale by next session
- Facts already in L2 (Hindsight) and the L1 entry references them
  with a pointer → L1 only, OBn would be duplicate

## When dual-write is mandatory

- New project location + first baseline numbers
- New skill the user will want future sessions to consult
- A new failure mode the next session is likely to hit
  (e.g. "70B OOMs on this hardware")
- A new convention or workflow that changes how the next session
  should behave

## The verifier

After session end, before claiming "ready for cold restart":

```bash
# Check the auto-brief surface has the new fact
grep -c "<key term>" ~/Documents/=notes/claude/memory/HERMES-MEMORY.md
# expected: ≥ 1

# Check the L1 surface has the new fact
grep -c "<key term>" ~/.hermes/memories/MEMORY.md
# expected: ≥ 1 (or zero if deliberately L1-skipped)

# Check the handoff file mentions it
grep -c "<key term>" ~/Documents/=notes/claude/mcp-coordination/state/session-handoffs/session-*.md
# expected: ≥ 1 in at least one recent handoff
```

If any of the three is empty for a project-level fact, you have a
cold-restart surface gap. Fix before claiming "ready."

## Companion

The `note-taking/session-briefing` skill lists the direct-read
authoritative context files but does NOT include HERMES-MEMORY.md
(OBn). That's the auto-brief surface gap from the other side — the
briefing skill doesn't tell the agent to read the file the
AGENTS.md auto-brief reads. See the patch to `session-briefing` for
the fix.
