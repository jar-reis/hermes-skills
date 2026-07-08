---
name: caliber
description: "Route prompts by task-demand surface before spending tokens."
version: 0.1.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [Routing, Model-Selection, Cost-Optimization, Verification]
---

# CALIBER — Demand-Surface Model Routing

Turns a request into a **task-surface demand vector**, compares it against a **model capability matrix**, and returns the cheapest constructor that clears the task with the right defender. A constructor is: `model + deployment path + context + retrieval + tools + verifier + human gate`.

Does NOT pick "the best model." It picks the cheapest allowed constructor whose proven capabilities clear the task's required surfaces and whose defender can verify the result.

## When to Use

- Deciding which model, tool lane, verifier, or human gate a task needs.
- A task involves local/private models, small/cheap models, coding, agents, long context, media, compliance, or high-stakes verification.
- You are about to default to a frontier model and want to check if a cheaper lane clears the defender.
- Designing an automation pipeline and need to assign models per stage.

## Prerequisites

- Access to `references/model-capability-matrix.yaml` (bundled with this skill).
- Understanding of the deployment pool available in your environment (local Ollama, cloud APIs, private endpoints).

## How to Run

1. Load the surface taxonomy and capability matrix from this skill's `references/` directory via `skill_view`.
2. Gate the deployment pool — check for regulated/private data, local-only requirements, secrets, production writes, or external sends.
3. Break the task into surfaces (reasoning, coding, long context, tool use, media, structured output, local/private, compliance).
4. Assign a required demand level (-1 to 6) per surface.
5. Filter candidate models from the capability matrix.
6. Attach defenders from the defender registry.
7. Pick the cheapest viable constructor.
8. If the defender fails, escalate one tier or switch specialist lane.

## Quick Reference

### Demand Levels

| Level | Name | Meaning |
|---:|---|---|
| -1 | deterministic | No model; SQL/rules/regex/script/API directly |
| 0 | tiny | Simple classify/extract/rewrite/routing |
| 1 | small | Simple reasoning, short summaries, low-stakes drafts |
| 2 | workhorse | Normal professional work, routine code/specs, common RAG |
| 3 | strong specialist | Harder domain work, repo work, complex synthesis, multimodal |
| 4 | frontier | Expensive-to-fail planning, novel architecture, high-reliability synthesis |
| 5 | orchestrated frontier | Decomposition + tools + defenders + human gates |
| 6 | reserved future | Super-frontier/research-grade |

### Pool Gates

| Gate | Restriction |
|---|---|
| Regulated/private data | Approved compliant/private deployment only |
| Secrets/credentials | Do not send raw secrets; use secure references or local tools |
| Local/private-only | Local/open-weight/private endpoint candidates only |
| External send/write | Human approval unless explicitly authorized |
| CRM/EHR/finance write | Dry-run + audit log + rollback + approval |
| Public upload | Explicit approval required |
| Human-impacting labels | Human gate unless pre-approved policy exists |

### Surface Clusters

| Cluster | Key surfaces |
|---|---|
| Language & cognition | `text_transform`, `instruction_following`, `general_reasoning`, `math_formal`, `science_expert`, `world_knowledge_current`, `creative_writing_worldbuilding`, `strategy_architecture` |
| Reading & memory | `long_context_retrieval`, `long_context_synthesis`, `rag_grounding`, `memory_personalization` |
| Code & tools | `code_generation`, `software_engineering`, `agentic_coding`, `tool_calling`, `computer_use`, `workflow_automation`, `structured_output` |
| Data & docs | `data_analysis`, `chart_diagram_understanding`, `document_ocr_extraction`, `financial_legal_admin` |
| Multimodal | `vision_static`, `image_generation`, `video_understanding`, `video_generation`, `audio_asr`, `audio_tts_voice`, `music_audio_generation`, `multimodal_composition` |

### Defenders by Surface

| Surface | Defender |
|---|---|
| `software_engineering` | unit tests, typecheck, lint, integration tests, code review |
| `agentic_coding` | plan review, test suite, diff review, behavior smoke test, rollback note |
| `tool_calling` | schema validation, dry-run, idempotency key, audit log |
| `workflow_automation` | replay harness, canary, queue dashboard, kill switch |
| `world_knowledge_current` | citation audit, source freshness check, source diversity check |
| `rag_grounding` | quote verifier, retrieval trace, contradiction check |
| `math_formal` | deterministic calculator/Python/SymPy or independent proof check |
| `data_analysis` | executable notebook/script, row counts, reconciliation totals |
| `external_send_or_write` | approval receipt, dry-run, audit log, rollback/undo plan |
| `real_world_safety` | formal safety case, canary, kill switch, human gate |

## Procedure

1. **Normalize the request.** Rewrite it as input → output transformation with constraints, tolerance for error, and side effects.
2. **Gate the pool.** Apply compliance, privacy, data residency, local-only, external-send, production-write, and human-impacting gates before scoring.
3. **Build task surface vector.** Assign required levels (-1 to 6) for every material surface.
4. **Filter candidates.** Use the capability matrix to keep only models and deployments that meet required surfaces and gates.
5. **Construct route.** A route is model + deployment + context + retrieval + tools + defender + human gate.
6. **Choose cheapest viable.** Prefer the lowest-cost candidate expected to pass the defender. Do not pre-pay frontier by default.
7. **Defend.** Run or name the required verifier. High-stakes routes require a defender even if the model is frontier.
8. **Escalate on failure.** If defender fails: escalate one model tier, switch specialist lane, add retrieval/tools, or block for missing context/human review.
9. **Log misroutes.** Cheap-tier failures and frontier-overuse are signals to tune the matrix.

## Output Shape

```text
Task surfaces:
- <surface>: required level <n> — <why>

Gate pool:
- allowed deployments:
- excluded deployments:

Candidate comparison:
- cheapest viable:
- strongest reliable:
- local/private option:
- specialist option:

Defenders:
- required verifier(s):
- human gate:

Recommendation:
- primary constructor:
- fallback constructor:
- escalation rule:
- evidence confidence:
```

## Pitfalls

1. **Pre-paying frontier by default.** The core trap. Always check if a workhorse or small model clears the defender first.
2. **Flattening all evidence into a single leaderboard.** Each surface has its own benchmark family. MMLU is saturated at frontier; HumanEval is saturated for coding. Use surface-specific evidence.
3. **Context size ≠ effective recall.** A model's advertised context window does not guarantee retrieval quality. Validate with RULER/Needle/MRCR evals for long-context tasks.
4. **Ignoring deployment path.** A model's raw capability score is separate from its deployment permissions. Regulated/private data requires an approved deployment even if a first-party API version is more capable.
5. **Running the full demand-card on trivial traffic.** The 12-signal deep demand card is for ambiguous or auditable cases. For everyday routing, the gate + 3-read fast-path is sufficient.
6. **Gate failure ≠ bigger model.** Gate signals (specification load, evidence availability, tool burden, verification burden) force a *capability* (clarify, retrieve, tools, verifier), not a more expensive model.

## Verification

Invoke through `terminal`:

```bash
# Verify the capability matrix is valid YAML
python3 -c "import yaml; yaml.safe_load(open('references/model-capability-matrix.yaml')); print('OK')"
```

Then check that your routing output names a primary constructor, a fallback, an escalation rule, and a defender — if any are missing, the route is incomplete.