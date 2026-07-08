# Known Collisions — pilot-sandbox plugins vs default tree

As of 2026-05-31, these collisions exist between the default skill tree and `pilot-sandbox/plugins/skill-enhancers`:

## grill-each-other/skills vs software-development

| Skill | Default Path | Plugin Path | Recommendation |
|-------|-------------|-------------|----------------|
| `grill-me` | `~/.hermes/skills/software-development/grill-me` | `~/.hermes/skills/grill-me` (symlink to grill-each-other) | Keep plugin — evolved dialectical protocol |
| `grill-me-agents` | `~/.hermes/skills/software-development/grill-me-agents` | `~/.hermes/skills/grill-me-agents` | Keep plugin |
| `grill-me-with-agents` | `~/.hermes/skills/software-development/grill-me-with-agents` | `~/.hermes/skills/grill-me-with-agents` | Keep plugin |
| `grill-with-docs` | `~/.hermes/skills/software-development/grill-with-docs` | `~/.hermes/skills/grill-with-docs` | Keep plugin |
| `peer-grill` | `~/.hermes/skills/software-development/peer-grill` | `~/.hermes/skills/peer-grill` | Keep plugin |
| `peer-grill-with-agents` | `~/.hermes/skills/software-development/peer-grill-with-agents` | `~/.hermes/skills/peer-grill-with-agents` | Keep plugin |

## fleet-ratify

| Skill | Default Path | Plugin Path | Recommendation |
|-------|-------------|-------------|----------------|
| `fleet-ratify` | `~/.hermes/skills/autonomous-ai-agents/fleet-ratify` | `~/.hermes/skills/fleet-ratify` (symlink to grill-each-other) | **Compare before dedup** — default is general fleet ratification; plugin may be peer-grill-specific |

## Verification Notes

- Plugin versions were symlinked on 2026-05-31
- Default versions are built into the Hermes skill tree
- Both versions load into the same session context, causing:
  - Duplicate trigger phrases in system prompt
  - Conflicting instructions if content diverged
  - Wasted context window tokens

## Safe Resolution Steps

1. For each collision above, run:
   ```bash
   diff -u ~/.hermes/skills/software-development/<skill>/SKILL.md ~/.hermes/skills/<skill>/SKILL.md | head -100
   ```

2. If plugin version is strictly superior (more content, more recent, no missing sections):
   ```bash
   # Archive the default version
   mv ~/.hermes/skills/software-development/<skill> ~/.hermes/skills/.archived/<skill>-default-$(date +%Y%m%d)
   ```

3. If versions have diverged in incompatible ways (different scope, different triggers):
   ```bash
   # Rename one to disambiguate
   mv ~/.hermes/skills/software-development/<skill> ~/.hermes/skills/software-development/<skill>-default
   # Edit its SKILL.md name: field to match
   ```

4. Verify: `hermes skills list | grep <skill>` should show exactly one entry.
