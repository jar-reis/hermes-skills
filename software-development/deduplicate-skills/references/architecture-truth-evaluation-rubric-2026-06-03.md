# Architecture-Truth Skill Evaluation Rubric (2026-06-03)

When a skills audit has to distinguish "KEEP" from "REVIEW" from "DELETE" at
scale (150+ skills), name-collision detection from the main `SKILL.md` is
necessary but not sufficient. You also need a rubric grounded in the
**current architecture truth** of the fleet, not in the skill's stated
description.

This reference captures the rubric used in the 2026-06-03 skills audit
(156 skills → 154 after −2 confirmed dead) and the architecture ground
truth that informed it.

## Why this rubric is needed

Skills can be:

- **Stale:** Created for a system that no longer exists (e.g.,
  Discord-era coordination skills after a Telegram migration).
- **Orphaned:** Symlink targets that moved or whose source repo
  deleted the skill, leaving a dangling link.
- **Superseded:** A new skill (or new MCP) replaced this one's job.
- **Niche-but-valid:** Used once a quarter, not dead, not active.

The danger in a "dead" sweep is over-pruning the niche-but-valid tier.
A name-collision check would miss this entirely; only an
architecture-truth rubric catches it.

## Architecture ground truth (Fleet Reis, 2026-06-03)

When evaluating any skill, the question is: **does the skill match
the current architecture?** If the architecture has moved on, the
skill is stale regardless of how well-written it is.

| Layer | Active | Retired (do not match) |
|---|---|---|
| Comms | Telegram (since 2026-06-01), Matrix relay | Discord (retired 2026-06-02), Slack, dizzy-relay |
| Memory | OB1 (Supabase), OBn (vault), Hindsight (Postgres) | Khoj (shut down 2026-05-21, DB pool exhausted) |
| Workstate | Linear, Beads, GitHub | — |
| MCP | n8n (Hermes-local stdio), ContextForge (localhost:8090), Linear (OAuth), fleet-memory | nate-promptkit (intentionally disconnected) |
| Fleet agents | Hermes, Claude Code, Codex, Kimi-Code (canonical responders) | OpenClaw-peer lanes (Klaude, Zoe, Maria, Zatara, Blue, Pi, Neo, Kimi-MBP, Olivier-MBP, Wingardia) — present but not canonical |
| Launchd canonical services | `ai.hermes.gateway`, `ai.bifrost.gateway`, `ai.fleet-matrix-relay`, `ai.matrix-mcp-shim-express`, `ai.rbitr.dramatis`, `ai.guest-resources-bot` | Discord-era services, all `*.plist.disabled` and `*.plist.parked` |

## The rubric

For each skill, walk this decision tree:

1. **Symlink?** (check `os.path.islink(skill_dir)`)
   - YES → KEEP. Plugin-managed, do not touch.
2. **Does the skill name or description reference a retired layer?**
   - Discord / dizzy / wings / khoj → DELETE.
   - Slack (when Slack is retired in this fleet) → DELETE.
   - Specific retired bot names (e.g., `zoe-credentials`) → DELETE.
3. **Does the skill reference a layer the fleet has never used?**
   - VS Code-specific when the fleet uses JetBrains, or vice versa
     → REVIEW (likely niche, may be useful for one-off).
4. **Category-based default:**
   - `software-development`, `github`, `note-taking`, `devops`,
     `mcp`, `apple`, `productivity`, `autonomous-ai-agents`,
     `agentic-os`, `data-science` → KEEP (active fleet ops).
   - `creative`, `media`, `gaming` → REVIEW (legitimate utilities,
     not core; audit per-skill in a follow-up).
   - `red-teaming`, `research`, `smart-home`, `social-media`,
     `email` → KEEP (utility, low-frequency, but real).
5. **Cross-reference with active code paths:** grep the skill name in
   `AGENTS.md`, `CLAUDE.md`, `~/.hermes/config.yaml`, the most recent
   handoff, and `ai-control.sh`. If found → KEEP with high
   confidence.

## Verdicts

- **KEEP (n ≈ 80% of skills)** — active or symlinked, no change.
- **REVIEW (n ≈ 15-20%)** — niche-but-valid; deferred for a
  follow-up pass.
- **DELETE (n ≈ 1-5%)** — confirmed dead; safe to remove.

## The 2026-06-03 audit numbers

| Verdict | Count | % |
|---|---|---|
| KEEP | 127 | 81% |
| REVIEW | 27 | 17% |
| DELETE | 2 | 1% |

The 2 confirmed deletions:

- `software-development/discord-credential-routing/`
- `software-development/discord-relay-attribution/`

Both predate the 2026-06-01 Telegram migration and reference
Discord-era patterns (Wings, Dizzy relay, lane attribution). Discord
retired 2026-06-02.

## How to apply this in a future audit

1. Read recent handoffs (last 7 days) to extract the **current**
   architecture truth. Memory is a secondary source.
2. Build the active/retired table from those handoffs.
3. Run the name-collision scan from the main `SKILL.md`.
4. Walk the rubric per skill, recording verdict + confidence +
   rationale.
5. For DELETE verdicts, require HIGH confidence. The cost of
   leaving a stale skill is low; the cost of deleting a
   niche-but-valid skill is "the user reaches for it and it's gone."
6. Export to CSV + JSON + MD. The CSV is for spreadsheet editing;
   the JSON is for downstream automation; the MD is the human
   summary.
7. Do NOT touch symlinks (Rule 1). Do NOT touch REVIEW without
   per-skill review.

## Deliverable shape

The 2026-06-03 audit produced these files (model for future audits):

```
claude/coordination/skills-audit-YYYY-MM-DD.csv   # 156 rows, all fields
claude/coordination/skills-audit-YYYY-MM-DD.json  # machine-readable
claude/coordination/skills-audit-YYYY-MM-DD.md    # human summary
.hermes/plans/YYYY-MM-DD-skills-audit.md          # plan with verifier
claude/mcp-coordination/state/session-handoffs/session-<agent>-skills-audit-YYYYMMDD.md
```

The CSV columns: `category, name, verdict, confidence, action,
rationale, description, is_symlink, referenced_in_active_files,
size_bytes, path`.

## Related

- The main `SKILL.md` covers **name collisions** (the deduplication
  axis).
- This reference covers **architecture-truth-based dead-skill
  detection** (the audit axis). The two are complementary: a
  future audit should apply both.
