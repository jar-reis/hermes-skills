---
name: memory-sop-audit
version: 1.1.0
created: 2026-06-03
updated: 2026-06-03
author: Hermes
description: >
  Re-runnable audit of the triple-layer memory system (L1 MEMORY.md/USER.md,
  L2 Hindsight :9177, L3 fact_store SQLite). Use when the user says
  "audit memory", "config memory", "memory-prune", or when MEMORY.md
  is near/exceeding budget. Bundles a one-shot script plus the
  procedure for what to do with the findings.
---

# Memory SOP Audit

## When to use this skill

- User says "config", "audit", "prune", "memory-sop", or "check memory"
- MEMORY.md / USER.md are near or over the char budgets (config-driven:
  `memory.memory_char_limit` and `memory.user_char_limit` in
  `~/.hermes/config.yaml`; currently 6000 / 1375 respectively)
- L3 (fact_store) shows duplicate content
- Hindsight daemon is suspected down or stale
- Fleet directive asks for evidence of memory hygiene
- Weekly cron `memory-audit-weekly` fires (silent on clean, alerts on issues)

## One-shot procedure

### 1. Run the audit script

```
~/.hermes/bin/memory-prune.sh            # read-only, exits 0/1/2
~/.hermes/bin/memory-prune.sh --fix      # soft-delete L3 duplicates
~/.hermes/bin/memory-prune.sh --json     # machine-readable
~/.hermes/bin/memory-prune.sh --no-aux   # skip ~/ copies, only check memories/
```

The script:
  - Reads `~/.hermes/memories/MEMORY.md` and `USER.md` (injected L1),
    computes char count vs budget
  - Also reads `~/MEMORY.md` and `~/USER.md` (auxiliary copies) — use
    `--no-aux` to skip
  - Detects L1 anti-patterns (commit SHAs, PR URLs, audit-delta arrows)
  - Pings `${L2_URL:-http://localhost:9177}/health` and computes ingest age
  - Walks `~/.hermes/memory_store.db` for category distribution,
    trust floor, retrieval counts, and content-fingerprint duplicates
  - With `--fix`, soft-deletes L3 duplicates (keeps oldest fact_id)

Exit codes: 0 clean, 1 warnings, 2 critical.

### 2. Triage findings

For each layer, decide whether the warning is real:

L1:
  - "82% / 71% / over 100%" — if your curated memory is over budget,
    edit MEMORY.md manually (the script never auto-edits L1).
  - Anti-pattern hits — move those lines to a daily note or handoff
    file. They are operational state, not durable identity.

L2:
  - "Hindsight UP" with `last_document_at` older than 7 days — schedule
    a periodic `hindsight_retain` from the session-end drain, or
    weekly via cron.
  - "Hindsight unreachable" — restart with
    `~/.hermes/hermes-agent/venv/bin/hindsight-embed daemon start`.

L3:
  - "0 of N facts retrieved" — L3 is write-only. Add `fact_feedback`
    to the session-end drain. Without feedback, trust scores stay
    pinned at the 0.5 default and `reason` / `contradict` queries
    have no signal. See `note-taking/memory-sop-feedback-loop`.
  - Duplicate content-fingerprint groups — `--fix` handles them.

### 3. Apply L1 prunes (manual)

When trimming MEMORY.md, the right move is usually to **remove**, not
**shrink**, the offending section. Categories of content to delete:

  - JAC ticket completion logs (line-by-line, even if duplicated)
  - Cold Restart checklists (point at AGENTS.md §Session Startup)
  - Commit SHAs and PR URLs (they live in git, not memory)
  - Run-state numbers (PIDs, ports, "84% → 84%" audit deltas)
  - Skill-count trivia (move to a skill file)
  - Hindsight-status blocks that contradict current daemon state
    (re-verify with the script before writing)

Aim for 1,500–1,750 chars (70–80% of budget). Below 50% means you
over-pruned and probably lost identity; above 80% triggers the
proactive-prune warning.

### 4. Apply L3 hygiene (`--fix`)

The script adds a `deleted_at TIMESTAMP` column on first run if
missing, then soft-deletes all-but-oldest fact_id in each content-
fingerprint duplicate group. This preserves the audit trail per
Fleet Directive — hard-deletes are reserved for quarterly hygiene
with operator approval.

### 5. Verify and record

Re-run the script. Expected output:

```
RESULT: all layers within budget. L1/L2/L3 healthy.
---exit: 0---
```

Save the audit as `~/.hermes/plans/YYYY-MM-DD-memory-sop-config-audit.md`
with: pre-state evidence, what was removed, post-state numbers, and
any open items left for next session.

## Common pitfalls

- **L1 lives in two places on this profile.** The runtime canonical
  is `~/.hermes/memories/MEMORY.md` (injected every turn). Auxiliary
  copies at `~/MEMORY.md` and `~/USER.md` are kept as backup. The
  audit script checks both; use `--no-aux` to skip the auxiliary
  set. Other profiles may have a single L1 path — verify with
  your profile config before assuming.

  **Bug-bait:** if the audit script's hardcoded default paths point
  to `~/` instead of `~/.hermes/memories/`, the script will report
  the *auxiliary* copy's char count (which is the smaller, less
  frequently edited file) and miss real bloat at the injected path.
  This produced false "all healthy" reports in the 2026-06-03 audit's
  first pass. Verify the script reads the right file by `wc -c`ing
  it manually on the first run.

- **Cron scripts must live in `~/.hermes/scripts/`, not `bin/`.**
  The Hermes `cronjob` scheduler rejects symlinks (treats them as
  path traversal) and `bin/`-relative paths. If your real
  executable is in `~/.hermes/bin/`, copy or wrap it into
  `~/.hermes/scripts/` for the cron to find it. Use a thin Python
  wrapper if you want the cron to inherit the bin/ version's behavior.

- **Heredoc with single-quoted delimiter hides the fix flag.** If you
  embed Python in a bash script, use unquoted `<<PYEOF` so `$VAR`
  expands. `<<'PYEOF'` makes the inner script see literal strings.
  This bit the first version of `memory-prune.sh` — the `--fix`
  flag was being passed but the inner `if fix == '1':` never saw
  it because the heredoc body wasn't expanded. The symptom is
  "duplicates persist after `--fix` runs." Always run a
  one-iteration test before trusting the script to do its work.

- **String vs bool in the fix check.** Compare `if fix:` (truthy)
  rather than `if fix == '1':` — bash already gives you a string,
  Python `bool('1')` is True, but the reverse depends on the
  comparison. `if fix:` is robust.

- **Don't soft-delete the L1 file.** The script never edits MEMORY.md
  / USER.md. L1 is operator-curated; the script only reports.

- **Don't hard-delete L3 facts.** The Fleet Directive demands
  durable evidence. Soft-delete with a `deleted_at` timestamp.

- **Hindsight status block in MEMORY.md goes stale fast.** Treat it
  as a 7-day TTL: re-verify daemon state via `/health` before
  writing, and update or remove the block each time you prune.

- **Hindsight retain timeout.** `async: true` is mandatory; sync
  mode times out at 30s because LLM extraction is slow. See the
  parent SOP `note-taking/memory-sop` rule #6 under L2.

- **Hardcoded budget in prune script (fixed 2026-06-18).**
  `memory-prune.sh` originally hardcoded `MEM_BUDGET=2200` and
  `USER_BUDGET=1375`. The real budgets are in `~/.hermes/config.yaml`
  under `memory.memory_char_limit` (currently 6000) and
  `memory.user_char_limit` (1375). The script now reads from config
  via a Python one-liner with a fallback to 2200. If the script
  reports "CRITICAL: over budget" but the file looks reasonable,
  check whether the config read is working: run
  `python3 -c "import yaml; print(yaml.safe_load(open('$HOME/.hermes/config.yaml')).get('memory',{}).get('memory_char_limit','MISSING'))"`
  and verify it returns the expected value. The config key is
  `memory_char_limit` (not `char_limit`).

- **Phantom-artifact trap on ticket/plan references.** When the user
  asks for "the X plan" or "Phase 2 of Y" and no such plan or
  phase exists in `~/.hermes/plans/`, Linear, or the session
  history, do not invent a plan to fill the gap. The 2026-06-04
  "Honcho / Hindsight Phase 2" question is a real example: a
  natural-language reference to a plan that had never been written.
  The correct response is to ground-truth it (search plans, search
  Linear, search session history) and then ask the user which of
  the candidate interpretations they meant. See
  `verification-before-completion/references/phantom-artifact-jac165-20260604.md`
  for the full case study. The general rule: verify the artifact
  exists *as described* before acting on a reference to it.

## Optional follow-ups (skill candidates)

- `memory-sop-feedback-loop` — add `fact_feedback` calls to the
  session-end drain so L3 trust scores move off the 0.5 floor.
- `memory-sop-l2-drain` — periodic `hindsight_retain` from session-
  end, so the bank stays fresh (currently 36h stale at audit time).
- Cron `memory-prune` weekly with `deliver=local` (silent on clean,
  alert on warnings/critical).

## Companion scripts (this profile)

The full triple-layer memory loop has three scripts in `bin/` plus
two cron wrappers in `scripts/` that work together:

  - `~/.hermes/bin/memory-prune.sh`  — one-shot audit (this skill's core)
  - `~/.hermes/bin/memory-drain.sh`  — session-end L2 retain (see
    `note-taking/memory-sop-drain`)
  - `~/.hermes/bin/memory-demo.sh`   — live walkthrough of L1/L2/L3
    with real output; perfect for "show me what the system actually
    looks like right now"
  - `~/.hermes/scripts/memory-audit.py`     — cron-friendly wrapper
    around prune.sh; silent on clean, alerts on issues
  - `~/.hermes/scripts/memory-drain-cron.py` — drains the
    `~/.hermes/memory-drain-queue/` directory; drop a `.txt` file
    with one fact in it and the daily cron will retain it to L2

The scripts are the canonical source of this skill. A copy of
`memory-prune.sh` is mirrored in `scripts/memory-prune.sh` for
explicit cron use; cron must reference `scripts/`, not `bin/`.

## Companion skills

  - `note-taking/memory-sop`           — the parent SOP
  - `note-taking/memory-sop-drain`     — L2 session-end drain procedure
  - `note-taking/memory-sop-feedback-loop` — L3 fact_feedback loop

## Cron jobs (this profile)

  - `memory-audit-weekly`  — Mondays 9 AM, 52 weeks, silent on clean
  - `memory-drain-daily`   — Daily 6 PM, 365 days, silent when queue empty

## Files

- `~/.hermes/bin/memory-prune.sh` — the audit script (canonical)
- `~/.hermes/scripts/memory-prune.sh` — mirror for cron
- `~/.hermes/plans/2026-06-03-memory-sop-config-audit.md` — original
  audit log; future audits use the same template
- `~/.hermes/skills/note-taking/memory-sop/SKILL.md` — the SOP this
  skill audits against

## Cross-verification of memory claims against live state

When auditing memory, don't just check char counts and daemon health —
**cross-verify each durable claim in MEMORY.md against the live system**.
Memory facts go stale silently. The audit should:

1. **List all quantitative claims in MEMORY.md** (doc counts, pod counts,
   port numbers, graph node counts, cron schedules).
2. **Probe each one against the live source**:
   - OBn pods/docs: `mcp_fleet_memory_fleet_memory_status` (not the old
     hardcoded count in memory)
   - Graph nodes: `jq '.nodes | length' knowledge-graph.json`
   - Port services: `lsof -i :PORT` + `curl -s -o /dev/null -w "%{http_code}"`
   - Cron health: `hermes cron list` (check for error states)
   - Script paths: `find ~/.local/bin -name 'script*'` (memory may cite
     a path that was renamed or moved)
3. **Flag every discrepancy** — stale counts, wrong paths, missing pods,
   services that moved ports.
4. **Update both the reference file AND MEMORY.md** — a stale reference
   file under the skill teaches the next agent the wrong numbers.

Pattern observed 2026-06-23: MEMORY.md said "39,421 docs across 11 pods"
but live OBn had 55,324 docs across 12 pods. The skill's reference file
`references/obn-ultra-robust-architecture-20260622.md` also had the old
count. Both needed updating.

## Pitfalls

- **System prompt char limit may be wrong.** The system prompt's
  "MEMORY (your personal notes) [59% — 5,939/10,000 chars]" used a
  10,000-char denominator, but the actual `memory.memory_char_limit`
  in config is 6,000. This means 5,939 chars is **99% full, not 59%**.
  The agent seeing "59%" will not prune; the agent seeing "99%" will
  prune immediately. **Always verify the limit from config, not from
  the system prompt's percentage.** Check with:
  ```
  python3 -c "import yaml; print(yaml.safe_load(open('$HOME/.hermes/config.yaml')).get('memory',{}).get('memory_char_limit','MISSING'))"
  ```
  Then compute `wc -c ~/.hermes/memories/MEMORY.md` and divide by
  the config value, not by 10,000.

- **Hindsight drain cron can run "ok" but produce zero new documents.**
  The `memory-drain-daily` cron (eb438b36c7be) reports `ok` in the cron
  list, but Hindsight's `last_document_at` was 3 days stale (2026-06-20
  vs audit date 2026-06-23). The cron successfully processes the drain
  queue, but the queue was empty — no facts were queued for retention.
  **Symptom**: cron says `ok`, Hindsight `/health` says `healthy`, but
  `last_document_at` is >48h old. **Root cause**: the session-end drain
  script (`memory-drain.sh`) is not being run by interactive sessions,
  so the queue stays empty. **Fix**: check the drain queue directory
  (`~/.hermes/memory-drain-queue/`) for pending `.txt` files; if empty,
  the interactive sessions are not draining — run `memory-drain.sh`
  manually or add it to the session-close ritual.

- **Reference files go stale faster than SKILL.md.** A skill's
  `references/` files carry quantitative snapshots (doc counts, pod
  layouts, port mappings) that change as the system grows. The SKILL.md
  changelog may say "updated to 55K+" but the reference file still has
  the old numbers. **Always update both** when counts change. The
  reference file is what a subagent loads with `skill_view(file_path=...)`
  — it is the authoritative detail, not just a historical note.

## Reference files

- `references/memory-claim-cross-verification-20260623.md` — full technique
  for cross-verifying quantitative memory claims against live system state,
  with the 2026-06-23 audit findings table as a worked example.

## Changelog

- v1.4.0 (2026-06-23): added "Cross-verification of memory claims against
  live state" section — technique for checking quantitative memory facts
  against live sources; added "System prompt char limit may be wrong"
  pitfall (10,000 vs 6,000 denominator causing false 59% vs real 99%);
  added "Hindsight drain cron silent empty-queue" pitfall (cron ok but
  no new documents for days); added "Reference files go stale" pitfall.
- v1.2.0 (2026-06-04): added "Phantom-artifact trap" pitfall with
  reference to JAC-165 case study; sharpened L1 dual-path language
  to call out the false-clean-report bug-bait (script defaulting
  to `~/` instead of `~/.hermes/memories/`); promoted heredoc +
  string/bool pitfalls to first-class trap examples.
- v1.1.0 (2026-06-03): added L1 dual-location pitfall; added
  cron-traversal pitfall (scripts/ vs bin/ + symlink rejection);
  added `--no-aux` flag; added changelog; pointed at the
  `scripts/` mirror for cron.
- v1.1.0 (2026-06-03): initial release.
- v1.3.0 (2026-06-18): updated budget references from hardcoded 2200 to
  config-driven `memory.memory_char_limit` (currently 6000); added
  "Hardcoded budget in prune script" pitfall documenting the config key
  (`memory_char_limit`, not `char_limit`) and the Python one-liner
  verification command.
