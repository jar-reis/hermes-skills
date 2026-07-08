# Skill Drift Detection Case Study (2026-06-23)

## Context

During the daily best practices extension run on 2026-06-23, the `writing-plans` skill was loaded and found to have severe within-skill content drift from repeated `skill_manage(action='patch')` calls across cron reruns.

## Symptoms

- **4+ duplicated "Concise Responses" user-preference blocks** — each rerun patched in the same preference section without checking if one already existed.
- **3+ duplicated "ACTIVE Update Discipline" blocks** — same pattern.
- **Version field**: `1.1.0` — not bumped despite visible content accumulation.
- **Accumulated rerun caveats**: Multiple `[date] Rerun Refresh` sections in the plan file, but the SKILL.md itself had the preference drift.

## Root Cause

The `skill_manage(action='patch')` tool does targeted find-and-replace. When a daily cron job patches a user-preference or pitfall into a skill, it appends a new block if the `old_string` matches a unique location — but if the same preference was already patched in a previous rerun, the `old_string` may match a different unique context, resulting in a second copy of the block being inserted elsewhere in the file.

Over 5+ reruns (2026-06-07 through 2026-06-23), this compounded into 4+ copies of the same "Concise Responses" block scattered through the file.

## Detection Method

```bash
# Count occurrences of a known preference heading
grep -c '## User Preferences' ~/.hermes/skills/software-development/writing-plans/SKILL.md
# Result: 5 (should be 1)

# Count occurrences of the "Concise Responses" sub-heading
grep -c '#### Concise Responses' ~/.hermes/skills/software-development/writing-plans/SKILL.md
# Result: 4+ (should be 1)
```

## Remediation

1. Subagent `deleg_49dd3707` dispatched to perform `skill_manage(action='edit')` with a full consolidated rewrite.
2. Version bumped from 1.1.0 to 1.2.0.
3. Historical rerun caveats to be moved to `references/changelog.md`.

## General Pattern

Skills maintained by recurring cron jobs are especially prone to this drift because:
- No human reviews the full file between reruns.
- `skill_manage(action='patch')` inserts rather than deduplicates when context differs slightly.
- The `version:` field is not always bumped in the same operation.

**Recommendation**: Audit cron-maintained skills for duplicated sections at least weekly using `grep -c` on key headings.