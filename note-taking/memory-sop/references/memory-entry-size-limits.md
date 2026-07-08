# MEMORY.md Entry Size Limits

## Context

`MEMORY.md` entries are injected into every turn of the conversation. Large entries:
- Risk **context degradation** in long-running sessions.
- May be **silently truncated** during L1 injection.
- Reduce **retrieval accuracy** due to noise.

## Limits

| Layer | Hard Limit | Soft Limit (Prune At) | Rationale |
|-------|------------|-----------------------|-----------|
| MEMORY.md | **6,000 chars** (config-driven) | 4,800 chars (80%) | Injected every turn. Limit is `memory.memory_char_limit` in `~/.hermes/config.yaml`. |
| USER.md | **1,375 chars** (config-driven) | 1,100 chars (80%) | User preferences; smaller budget. Limit is `memory.user_char_limit` in config. |

> **Critical**: The limits above are read from config at runtime, not hardcoded.
> Always verify with:
> ```bash
> python3 -c "import yaml; c=yaml.safe_load(open('$HOME/.hermes/config.yaml')); print('MEMORY:', c.get('memory',{}).get('memory_char_limit','MISSING'), 'USER:', c.get('memory',{}).get('user_char_limit','MISSING'))"
> ```
> The system prompt may report a different denominator (e.g. "10,000 chars")
> which is WRONG — trust the config file, not the system prompt percentage.
> As of 2026-06-23, the actual file is 5,939/6,000 = 99% full, but the system
> prompt showed "59% — 5,939/10,000" which is dangerously misleading.

> **Historical note**: Before 2026-06-18, the limit was hardcoded at 2,200 chars
> in the prune script. The script was fixed to read from config, but some
> reference files and the SKILL.md still carry the old 2,200 number. Always
> use the config value as source of truth.

## Auxiliary copies

On the default Hermes profile, auxiliary copies exist at `~/MEMORY.md` and
`~/USER.md`. These are NOT subject to the same budget enforcement — the
runtime canonical is `~/.hermes/memories/MEMORY.md`. The auxiliary copy
can be over budget (one audit found it at 8,213/6,000 = 137%) without
the runtime blocking writes. Still, prune it periodically to avoid drift.

## Best Practices

1. **Keep entries under 200 characters** where possible.
2. **Split large entries** into smaller, focused facts.
3. **Move durable knowledge** to L2 (Hindsight) or L3 (fact_store).
4. **Prune proactively** when approaching 80% capacity.
5. **Target 1,500–1,750 chars** (70–80% of budget) after pruning — below
   50% means you over-pruned and lost identity; above 80% triggers warnings.

## Example

```markdown
# Bad (500+ chars)
§ User prefers concise responses for single tasks, especially when using print mode (-p). Dialog mode should be reserved for multi-turn workflows or tasks requiring user input. Context efficiency is critical for long-running sessions.

# Good (split into smaller entries)
§ User prefers concise responses for single tasks.
§ Use print mode (-p) for single tasks to avoid context bloat.
§ Reserve dialog mode for multi-turn workflows or user input.
```