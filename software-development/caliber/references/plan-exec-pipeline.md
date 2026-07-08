# Plan-Execution Pipeline

How a superpowers plan flows through caliber → model → verify → track → learn.

## Overview

```
Plan (superpowers)
  → Caliber routing (demand-surface vector → cheapest viable model)
    → Model execution (Hermes delegate / Claude Code CLI / Antigravity CLI / direct API)
      → Defender verification (surface-specific verifier)
        → Open Engine tracking (beads receipt + state transition)
          → Skill learning (pattern extraction from successful closures)
```

---

## 1. Plan → Caliber Routing

A **superpowers plan** (from the `plan` skill or `superpowers:writing-plans`)
produces a structured markdown plan with numbered steps, each step having a
clear input → output transformation.

For each step in the plan:

1. **Normalize the step** into input → output with constraints, error tolerance,
   and side effects.

2. **Gate the pool.** Check for:
   - Regulated/private data → local-only models (qwen2.5:7b, gemma4:31b)
   - Secrets/credentials → local-only or secure references
   - Production writes → human gate + defender required
   - External sends → approval required

3. **Build the task surface vector.** Assign a required demand level (-1 to 6)
   for every material surface:
   - `reasoning` — cognitive demand
   - `coding` — code generation / software engineering
   - `long_context` — context window requirement
   - `tool_use` — agentic tool calling
   - `media` — vision / video / multimodal
   - `structured_output` — schema-constrained output

4. **Consult `fleet-model-routing.yaml`.** For each surface, find the cheapest
   model that clears the required demand level. The **binding constraint** is
   the surface with the highest demand that eliminates cheaper models.

5. **Pick the cheapest viable constructor:**
   - `model` from the routing table
   - `deployment_path` from the model's deployment paths
   - `defender` from the defender registry (caliber SKILL.md)
   - `human_gate` if production write or high-stakes

**Example:**
- Step: "Refactor auth module, add tests, verify CI passes"
- Surfaces: coding=3, tool_use=3, reasoning=2
- Gates: none (non-regulated, dev environment)
- Routing: coding@3 → codex-5.3, tool_use@3 → codex-5.3, reasoning@2 → glm-5.2
- Binding: coding@3 → **codex-5.3** via Hermes delegate (codex skill)

---

## 2. Model Execution

The chosen constructor's `deployment_path` determines how the step is executed:

| Deployment path | How it runs | When to use |
|---|---|---|
| Hermes delegate | Direct in Hermes session with that model as active | Default for glm-5.2, local Ollama models |
| Claude Code CLI | `hermes` delegates to `claude` CLI via claude-code skill | When claude-fable-5 is selected for coding/agentic tasks |
| Antigravity CLI | `hermes` delegates to `agy` CLI via antigravity skill | When gemini-3.1-pro is selected, especially long-context or multimodal |
| Codex CLI | `hermes` delegates to `codex` CLI via codex skill | When codex-5.3 is selected for repo-scale coding |
| Direct API | Hermes makes API calls directly | Fallback when no CLI delegate is available |

The executor receives:
- The plan step (input → output + constraints)
- The chosen model + deployment path
- The defender specification (what must pass)
- The beads issue ID (for tracking)

---

## 3. Defender Verification

After the model produces output, the **defender layer** verifies it before
the result is accepted. Defenders are surface-specific (from caliber SKILL.md):

| Surface | Defender |
|---|---|
| software_engineering | unit tests, typecheck, lint, integration tests, code review |
| agentic_coding | plan review, test suite, diff review, behavior smoke test, rollback note |
| tool_calling | schema validation, dry-run, idempotency key, audit log |
| data_analysis | executable notebook/script, row counts, reconciliation totals |
| math_formal | deterministic calculator/Python/SymPy or proof checker |
| external_send_or_write | approval receipt, dry-run, audit log, rollback plan |

**Defender escalation protocol:**
1. Run the defender.
2. If it **passes** → accept result, proceed to tracking.
3. If it **fails** → escalate one model tier (e.g., glm-5.2 → codex-5.3 →
   claude-fable-5) and re-execute. Log the misroute.
4. If escalated model also fails → block for human review. File a comment
   on the beads issue: `AGENT BLOCKED: defender <X> failed at tier <Y>`.

**Misroute logging:** Cheap-tier failures and frontier-overuse are signals to
tune the routing table. The skill-learner.py script (below) extracts these
patterns from closed beads.

---

## 4. Open Engine Tracking (Beads)

Every step in the pipeline is tracked in **Beads** (Open Engine protocol):

| Pipeline stage | Beads receipt | Command |
|---|---|---|
| Start execution | claim | `bd update <id> --claim && bd comment <id> "AGENT CLAIMED <session>"` |
| Defender fails | block | `bd update <id> -s blocked && bd comment <id> "AGENT BLOCKED: <defender> <reason>"` |
| Human approval needed | hold | `bd update <id> -s blocked && bd comment <id> "AGENT HUMAN HOLD: <what>"` |
| Step complete, next step | resume | `bd update <id> -s in_progress && bd comment <id> "AGENT RESUMED"` |
| All steps done, needs review | review | `bd label add <id> review && bd comment <id> "AGENT DONE (needs-human: <items>)"` |
| Fully verified + done | done | `bd close <id> --reason "AGENT DONE: <artifact+path+verification>"` |
| Failed, cannot proceed | fail | `bd update <id> -s blocked && bd comment <id> "AGENT FAILED: last safe step <x>"` |

The close reason MUST include:
- **Artifact**: what was produced (file path, commit, deployed service)
- **Path**: where to find it
- **Verification**: which defender passed
- **Model used**: which fleet model executed the work
- **Caveats**: known limitations or follow-ups

This metadata is what `skill-learner.py` extracts to learn patterns.

---

## 5. Skill Learning & Persistence

After a bead is closed successfully, the **skill-learning loop** fires:

### 5a. Pattern Extraction (`skill-learner.py`)

The script at `~/.hermes/scripts/skill-learner.py`:
1. Scans recently closed beads (`bd list --status closed --json`, last 7 days)
2. Extracts from each closure:
   - **Skill used** — inferred from issue labels and title keywords
   - **Model used** — parsed from close_reason (model name pattern match)
   - **Task type** — inferred from issue_type + labels
   - **Success** — bead is closed (vs blocked/reopened)
   - **Time to close** — closed_at - started_at
   - **Defender** — parsed from close_reason if present
3. Aggregates patterns:
   - Which models succeed most for which task types
   - Which skill + model combinations are most efficient
   - Misroute signals (beads that were blocked then re-executed at higher tier)
4. Outputs summary to `~/.fleet-dashboard/skill-learning-report.json`

### 5b. Skill Persistence

When a successful execution reveals a reusable workflow (5+ tool calls,
non-trivial procedure, user-corrected approach), Hermes offers to save it
as a skill via `skill_manage(action='create')`:

- **Trigger**: complex task succeeded, errors overcome, non-trivial workflow
- **Content**: trigger conditions, numbered steps with exact commands, pitfalls,
  verification steps
- **Location**: `~/.hermes/profiles/worker/skills/<category>/<name>/SKILL.md`
- **Linking**: the skill references `fleet-model-routing.yaml` for model
  selection guidance

When a skill is used and found outdated/wrong, it is patched immediately via
`skill_manage(action='patch')` — not deferred.

### 5c. Routing Table Feedback

The skill-learning report feeds back into caliber routing:
- If a model consistently fails at a demand level → lower its confidence for
  that surface in `fleet-model-routing.yaml`
- If a cheaper model consistently succeeds above its assigned tier → promote it
- If a surface is frequently misrouted → adjust the routing table thresholds

This creates a **closed feedback loop**:
```
execution → defender → beads closure → skill-learner → routing table update → better routing
```

---

## Quick Reference: Full Pipeline for a Plan Step

```bash
# 1. Read the plan step
# 2. Route via caliber (consult fleet-model-routing.yaml)
# 3. Execute via chosen deployment path
#    - Hermes delegate: direct session work
#    - Claude Code CLI: hermes → claude skill delegate
#    - Antigravity CLI: hermes → agy skill delegate
#    - Codex CLI: hermes → codex skill delegate
# 4. Run defender (surface-specific)
# 5. Track in beads:
bd comment <id> "Step N done: model=<model>, defender=<verifier>, result=pass"
# 6. On full completion:
bd close <id> --reason "AGENT DONE: <artifact> at <path>, verified by <defender>, model=<model>"
# 7. Skill-learner picks up the closure pattern (runs on schedule or manually)
python3 ~/.hermes/scripts/skill-learner.py --dry-run
```