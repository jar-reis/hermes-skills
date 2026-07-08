# Hermes Agent Skills

Unified, tag-filterable registry of skills across Jack's fleet — Hermes Agent, Claude Code, Codex, and shared agent dirs.

## What's Here

- **`registry.json`** — Machine-generated index of all skills across 5 source directories, with runtime tags, capability requirements, and lane assignments.
- **Skill directories** — Agent-authored skills (`author: Hermes`) synced from `~/.hermes/profiles/worker/skills/` and `~/.hermes/skills/`.

## Registry Schema

Each skill entry in `registry.json`:

```json
{
  "id": "skill-name",
  "name": "skill-name",
  "description": "One-sentence description.",
  "author": "Hermes",
  "version": "0.1.0",
  "category": "autonomous-ai-agents",
  "runtimes": ["hermes", "claude"],
  "requires": ["mcp-server", "terminal"],
  "lane": "Shape",
  "available_in": ["worker", "default", "claude"],
  "tags": ["MCP", "Configuration"]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `runtimes` | `string[]` | Which agent systems have this skill: `hermes`, `claude`, `codex`, `agents` |
| `requires` | `string[]` | Capabilities needed: `mcp-server`, `browser`, `terminal`, `vision`, `claude-artifacts`, `skills-system`, `api-key` |
| `lane` | `string` | Skill Railway lane: `Sense`, `Shape`, `Spec`, `Execute`, `Transfer` |
| `available_in` | `string[]` | Source dirs: `worker`, `default`, `claude`, `codex`, `agents` |
| `tags` | `string[]` | Frontmatter `metadata.hermes.tags` |
| `category` | `string` | Top-level directory grouping |

### Querying

Filter by runtime:
```bash
jq '.skills[] | select(.runtimes | index("claude")) | .name' registry.json
```

Filter by capability requirement:
```bash
jq '.skills[] | select(.requires | index("mcp-server")) | .name' registry.json
```

Find skills available in both Hermes and Claude:
```bash
jq '.skills[] | select(.runtimes | index("hermes") and .runtimes | index("claude")) | .name' registry.json
```

Filter by lane:
```bash
jq '.skills[] | select(.lane == "Sense") | .name' registry.json
```

## Stats (2026-07-08)

- **490 skills** across 5 source directories
- **428** available in Hermes, **70** in Claude, **16** in Codex, **13** in shared agents
- **23** agent-authored (`author: Hermes`)

## Sync

Run `~/agent-configs/sync.sh --sync-skills` to regenerate. The script:
1. Scans all 5 skill directories for `SKILL.md` files
2. Parses frontmatter for metadata
3. Infers `runtimes`, `requires`, and `lane`
4. Writes `registry.json` and syncs agent-created skills to this repo
5. Commits and pushes

The registry generator is a Python script at `scripts/generate_registry.py`.