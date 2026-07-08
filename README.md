# Hermes Agent Skills

Custom and agent-created skills for [Hermes Agent](https://hermes-agent.nousresearch.com).

## Structure

Skills are organized by category, mirroring the on-disk layout under
`~/.hermes/profiles/worker/skills/` and `~/.hermes/skills/`:

```
autonomous-ai-agents/   # Agent delegation, MCP, retry tuning
apple/                  # macOS-specific (Apple Notes, Reminders, etc.)
devops/                 # Infrastructure, messaging platforms, memory systems
note-taking/            # Memory SOPs, session rituals, turn sync
productivity/           # Display density, email, open engine
software-development/   # Code review, dedup, skill authoring
```

Each skill has a `SKILL.md` with YAML frontmatter (`name`, `description`,
`version`, `author`) and a markdown body.

## Sync

These skills are synced from Aegis (Jack Reis's Mac Mini) via
`~/agent-configs/sync.sh`. The sync script copies agent-created skills
(`author: Hermes`) from both the worker and default Hermes profiles.

## Provenance

All skills here have `author: Hermes` in their frontmatter — they were
authored by the Hermes agent itself, not bundled with the framework or
installed from the skills hub.
