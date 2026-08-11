---
name: profile-instruction-centralization
description: "Use when auditing/centralizing Hermes profile instructions."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [profiles, audit, consolidation, doctrine, fleet, hfs]
    category: devops
    related_skills: [hierarchical-folder-structure, hermes-agent, memory-sop-audit]
---

# Profile Instruction Centralization

## Overview

Hermes profiles drift: the same "fleet doctrine" block gets copied into several
profiles' `AGENTS.md`, memory files get near-duplicated, and per-profile identity
files degrade to stock boilerplate. The fix is not to merge/delete per-profile
runtime data — it is to **centralize shared knowledge into one doctrine source and
replace duplicated instruction blocks with thin pointers**, while leaving runtime
stores and machine-specific content strictly local.

This skill encodes the working pattern from the 2026-08-10 profile audit (default
profile). It applies the HFS lens: routing pointers belong in the L1 routing layer
(`AGENTS.md`), not in character-limited L3 content stores (`MEMORY.md`/`USER.md`).

## When to Use

- "Audit all Hermes profiles except yourself."
- "Find stale / duplicated / conflicting instructions across profiles."
- "Centralize shared profile guidance into one source."
- "Why is this profile telling itself it runs a model it doesn't run?"

**Don't use for:** merging per-profile memory stores, editing config.yaml, or any
per-profile behavior that is legitimately distinct.

## Core Principles

1. **Read-only audit first.** Inventory every non-default profile's instruction
   files (`AGENTS.md`, `SOUL.md`, `profile.yaml`, `memories/MEMORY.md`,
   `memories/USER.md`) and diff them. Identify byte-identical blocks before
   proposing anything.
2. **Model-less roster.** Do NOT tell a profile which model it runs. The roster
   column is Role · Profile · Responsibility. Telling a profile its model is the
   single fastest way to make instructions stale the moment config changes.
   (Confirmed by Jack: "I see no reason to tell it which model it is running.")
3. **HFS layer discipline.** Routing pointers belong in the L1 routing layer
   (`AGENTS.md`), NOT in `MEMORY.md`/`USER.md`. The latter are character-limited
   (2200 memory / 1375 user), runtime-managed stores — hand-adding content there
   can push them over the limit and break future writes.
4. **Runtime stores are live files, not docs.** `tools/memory_tool.py` loads
   `MEMORY.md`/`USER.md` into the system prompt as a frozen snapshot, with file
   locks, drift detection, dedup, and char limits. Editing them directly bypasses
   the store. Merge/delete only via the memory tool with gateways stopped — or
   better, don't merge at all.
5. **Machine-specific + sensitive stays local.** Anything with Aegis/Talaris
   paths, ports, PIDs, or an explicit "never copy off-box" / "never print the
   token" boundary is per-profile runtime/skill content, never fleet doctrine.
6. **Back up before mutating.** Snapshot all profiles' instruction + memory
   files into `~/.hermes/backups/<name>-<timestamp>/` before any edit.

## Procedure

### Phase 1 — Read-only audit
1. `hermes profile list` — get live model/gateway/alias for every profile.
2. `ls ~/.hermes/profiles/` — inventory the non-default profiles.
3. For each profile, list instruction files:
   `ls <profile>/AGENTS.md <profile>/SOUL.md <profile>/profile.yaml <profile>/memories/*.md`
4. **Diff the same-named files across profiles** to find byte-identical blocks:
   `md5 -q <profiles>/*/AGENTS.md` then `diff` the matches.
5. Record: exact md5s, which profiles share the block, whether the content is
   stale (contradicts `hermes profile list`), and whether the content embeds
   machine-specific or sensitive data.

**Completion:** you have a file-by-file matrix of duplicates, staleness, and
conflicts, with no files modified.

### Phase 2 — Identify the canonical authority (before deleting copies)
- The vault already owns topology: `~/Documents/=notes/docs/architecture/
  fleet-topology-canonical.md` and `~/Documents/=notes/fleet/manifest.md`.
- Author the centralized doctrine at `~/Documents/=notes/fleet/doctrine.md`
  (vault is the canonical origin) with: fleet topology + three-layer work model,
  **model-less roster**, coordination mechanics (wakeup, delegation, memory
  layers), operational directives. Cross-link to the topology/manifest SSOTs.

**Completion:** the doctrine file exists and is the single source of truth.

### Phase 3 — Back up
```
BK=~/.hermes/backups/<name>-$(date +%Y%m%d-%H%M%S)
mkdir -p "$BK"; for p in <profile-dirs>; do
  mkdir -p "$BK/$p"
  cp -p ~/.hermes/profiles/$p/AGENTS.md "$BK/$p/" 2>/dev/null
  cp -p ~/.hermes/profiles/$p/SOUL.md "$BK/$p/" 2>/dev/null
  cp -p ~/.hermes/profiles/$p/profile.yaml "$BK/$p/" 2>/dev/null
  cp -p ~/.hermes/profiles/$p/config.yaml "$BK/$p/" 2>/dev/null
  for m in MEMORY.md USER.md; do
    cp -p ~/.hermes/profiles/$p/memories/$m "$BK/$p/" 2>/dev/null
  done
done
```
Verify one md5 matches the original before trusting the backup.

**Completion:** every file you will mutate exists in the backup; spot-check md5.

### Phase 4 — Collapse duplicated AGENTS.md to pointers
Replace each duplicated `AGENTS.md` with a thin pointer:
```markdown
# ⚓ <Profile Name>

Role: **<Role>** — <one-line responsibility>.

Fleet topology, roster, coordination mechanics, memory layers, and operational
directives are defined in the single shared source:

**`~/Documents/=notes/fleet/doctrine.md`** — read it before acting on fleet work.

Profile-specific mission, do/don't, and closeout verifier live in `SOUL.md`.
```
Keep the profile's distinct `SOUL.md` untouched (it carries the real per-role
identity).

**Completion:** each collapsed AGENTS.md is < 500 bytes and points to doctrine.

### Phase 5 — Dedupe stock boilerplate SOUL.md (only when identical)
Only delete a `SOUL.md` if it is byte-identical to the stock Nous persona
("You are Hermes Agent, created by Nous Research…") and has no profile identity.
Hermes loads the default persona when SOUL.md is absent.
Confirm all copies share one md5 before deleting.

**Completion:** deleted only byte-identical stock persona files; distinct role
SOUL.md files are all still present.

### Phase 6 — Leave runtime stores alone
- Do NOT hand-edit `MEMORY.md`/`USER.md` under live gateways.
- Do NOT merge near-identical memory stores — the shared knowledge is already
  centralized in doctrine.md, so the per-profile copies are harmless residue.
- A pointer prepended to `MEMORY.md` will push it over the 2200-char limit and
  break future `memory add` calls (verify with `wc -c`; `memory_char_limit=2200`).
  Revert it if it overflows.
- Keep machine-specific + "never copy off-box" content (e.g. worker's
  `aegis-fleet-ops`, `contextforge-aegis-ops` skills) untouched.

**Completion:** every memory file that is machine-specific or at/near its char
limit is byte-identical to the backup; no memory store was hand-merged.

### Phase 7 — Verify
1. `hermes profile list` — profiles still resolve, gateways unaffected.
2. `wc -c` the collapsed AGENTS.md — small pointer stubs.
3. `md5` the protected memory files vs backup — must match (untouched).
4. `grep -c "Model" doctrine.md` — 0 (model-less roster).
5. Confirm protected Aegis skill dirs still exist.

**Completion:** every check above passes; report the file-by-file change list.

## Common Pitfalls

1. **Telling a profile its model.** Roster must be model-less. Config drifts;
   instructions telling a profile its model become stale the moment config changes.
2. **Putting the doctrine pointer in MEMORY.md.** It belongs in AGENTS.md (L1
   routing). Adding it to MEMORY.md overflows the char limit and breaks future
   memory writes — and is redundant since AGENTS.md already routes at session start.
3. **Merging runtime memory stores.** They're frozen-snapshot, file-locked,
   character-limited stores. Hand-merging under a live gateway risks drift errors,
   truncation, or a running session writing back stale state. Leave them alone.
4. **Centralizing machine-specific content.** Anything with host paths, ports,
   PIDs, or an explicit "never copy off-box"/"never print token" boundary stays
   local. It is not doctrine.
5. **Editing config.yaml during the migration.** Config divergence (cwd, personality,
   voice, ports, allowlists) is legitimate per-profile behavior. Never touch it.
6. **Truncated shell output looks like failure.** After mutations, verify with a
   clean `ls`/`wc -c`/`md5` pass — the files are usually fine even when a prior
   command's output was cut off.

## Verification Checklist

- [ ] Audit was read-only; nothing modified before approval
- [ ] Doctrine exists at `~/Documents/=notes/fleet/doctrine.md`
- [ ] Doctrine roster is model-less (`grep -c "Model"` == 0)
- [ ] Backup dir contains every file that will be mutated (md5 spot-checked)
- [ ] Duplicated AGENTS.md files collapsed to < 500-byte pointers
- [ ] Distinct per-role SOUL.md files preserved
- [ ] Only byte-identical stock persona SOUL.md deleted
- [ ] No memory store hand-merged or overflowed
- [ ] Machine-specific / "never copy off-box" content untouched
- [ ] `hermes profile list` still resolves; gateways unaffected
- [ ] Protected memory files byte-identical to backup
