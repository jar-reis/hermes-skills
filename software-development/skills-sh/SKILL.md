---
name: skills-sh
description: Discover, install, and manage agent skills from skills.sh.
version: 0.1.0
author: Hermes
metadata:
  hermes.tags:
    - Skills
    - CLI
    - Discovery
    - Agents
---

# skills.sh — Open Agent Skills Ecosystem

skills.sh (by Vercel) is a directory and leaderboard for reusable AI agent skills. The `npx skills` CLI installs skills from GitHub repos into agent-specific directories, and the REST API at `https://skills.sh/api/v1/` provides programmatic access to the catalog, search, and security audits. Hermes Agent is a supported target (`--agent hermes-agent`), so skills installed via this CLI land in `.hermes/skills/` (project) or `~/.hermes/skills/` (global).

## When to Use

- "Find a skill for React best practices" or "search skills.sh for X"
- "Install a skill from vercel-labs/agent-skills"
- "Browse trending agent skills"
- "Check the security audit for a skill before installing"
- "Use a skill without installing it permanently"
- "Create a new SKILL.md scaffold"
- "List / update / remove skills I've installed"

## Prerequisites

- Node.js installed (npx comes with npm)
- No account needed for CLI usage; API requires Vercel OIDC token (see API section)
- Optional: `DISABLE_TELEMETRY=1` env var to opt out of anonymous telemetry

## How to Run

Invoke through the `terminal` tool. All commands use `npx skills` — no global install required.

## Quick Reference

| Command | Purpose |
|---|---|
| `npx skills add <owner/repo>` | Install skills from a GitHub repo |
| `npx skills use <source>` | Use a skill without installing (prints prompt to stdout) |
| `npx skills list` | List installed skills (alias: `ls`) |
| `npx skills find [query]` | Search for skills interactively or by keyword |
| `npx skills remove [skills]` | Remove installed skills (alias: `rm`) |
| `npx skills update [skills]` | Update installed skills to latest |
| `npx skills init [name]` | Create a new SKILL.md template |

**API base:** `https://skills.sh/api/v1/` — all JSON, requires `Authorization: Bearer <vercel-oidc-token>`.

## Procedure

### 1. Discover skills

Browse the leaderboard at `https://www.skills.sh` or search via CLI:

```
npx skills find react
npx skills find react --owner vercel
```

Or query the API (requires Vercel OIDC token):

```
curl "https://skills.sh/api/v1/skills/search?q=react&limit=10" \
  -H "Authorization: Bearer $VERCEL_OIDC_TOKEN"
```

API search: single-word queries use fuzzy matching; multi-word queries use semantic search. The `searchType` field in the response indicates which was used.

### 2. List skills in a repo without installing

```
npx skills add vercel-labs/agent-skills --list
```

### 3. Install skills

```bash
# Install all skills interactively (prompts for agent + scope)
npx skills add vercel-labs/agent-skills

# Install specific skills to Hermes Agent, global scope, no prompts
npx skills add vercel-labs/agent-skills --skill frontend-design -a hermes-agent -g -y

# Install all skills from a repo to all agents
npx skills add vercel-labs/agent-skills --all
```

**Key flags:**

| Flag | Description |
|---|---|
| `-g, --global` | Install to `~/.hermes/skills/` instead of `.hermes/skills/` |
| `-a, --agent <agents...>` | Target specific agents (e.g., `hermes-agent`, `claude-code`) |
| `-s, --skill <skills...>` | Install specific skills by name (`*` for all) |
| `-l, --list` | List available skills without installing |
| `--copy` | Copy files instead of symlinking |
| `-y, --yes` | Skip confirmation prompts |
| `--all` | Install all skills to all agents |

**Source formats accepted:** `owner/repo`, full GitHub URL, GitLab URL, any git URL, local path (`./my-skills`).

### 4. Use a skill without installing

```bash
# Generate a prompt and pipe to an agent
npx skills use vercel-labs/agent-skills@web-design-guidelines | claude

# Start an agent interactively with the generated prompt
npx skills use vercel-labs/agent-skills --skill web-design-guidelines --agent claude-code
```

`skills use` writes skill files to a temp directory and prints the prompt to stdout (unless `--agent` is given, which launches the agent interactively).

### 5. List installed skills

```bash
npx skills list              # all installed (project + global)
npx skills ls -g             # global only
npx skills ls -a hermes-agent  # filter by agent
```

### 6. Update skills

```bash
npx skills update              # interactive, all skills
npx skills update my-skill     # specific skill
npx skills update -g -y        # global, non-interactive
```

### 7. Remove skills

```bash
npx skills remove my-skill
npx skills rm frontend-design web-design-guidelines
npx skills remove --global my-skill
npx skills remove --all        # remove everything, no confirmation
```

### 8. Create a new skill scaffold

```bash
npx skills init              # SKILL.md in current directory
npx skills init my-skill     # in a subdirectory
```

### 9. Check security audits via API

```bash
curl "https://skills.sh/api/v1/skills/audit/vercel-labs/skills/find-skills" \
  -H "Authorization: Bearer $VERCEL_OIDC_TOKEN"
```

Returns audit results from partners (Gen Agent Trust Hub, Socket, Snyk, Runlayer, ZeroLeaks). Each entry has `status` ("pass", "warn", "fail"), `summary`, `riskLevel` ("NONE"/"LOW"/"MEDIUM"/"HIGH"/"CRITICAL"), and `auditedAt`. Returns 404 if no audits exist yet — audits are generated automatically after first install, with a few minutes delay.

## API Endpoints

All under `https://skills.sh/api/v1/`, JSON responses.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/skills` | ✅ Required | Paginated leaderboard (`view=all-time\|trending\|hot`, `page`, `per_page=1-500`) |
| GET | `/skills/search` | ✅ Required | Search by name/description (`q` required, `limit=1-200`, `owner`) |
| GET | `/skills/curated` | ✅ Required | Official first-party skills set |
| GET | `/skills/{source}/{skill}` | ✅ Required | Skill detail with full file tree (SKILL.md + supporting files) |
| GET | `/skills/audit/{source}/{skill}` | ❌ **None** | Security audit results — works without auth |

**The audit endpoint is the only unauthenticated API endpoint.** All others return HTTP 401 without a Vercel OIDC token. This means you can pre-screen any skill's security posture without any Vercel account — useful for fleet safety checks before installing.

```bash
# No auth needed — works as-is
curl -s "https://skills.sh/api/v1/skills/audit/vercel-labs/agent-skills/deploy-to-vercel"
```

Returns audits from Gen Agent Trust Hub, Socket, Snyk, Runlayer, ZeroLeaks. Each entry has `status` ("pass"/"warn"/"fail"), `summary`, `riskLevel` ("NONE"/"LOW"/"MEDIUM"/"HIGH"/"CRITICAL"), and `auditedAt`. Returns 404 if no audits exist yet.

**Rate limit:** 600 req/min per (team, project). Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. 429 returns `Retry-After`.

**Auth setup (Vercel OIDC):**
1. Enable OIDC Federation in Vercel dashboard → Settings → OIDC Federation
2. `npm install @vercel/oidc` (recommended) or read `process.env.VERCEL_OIDC_TOKEN` directly
3. Call `getVercelOidcToken()` inside request handlers (rotates ~12h, do not cache at module scope)
4. Header form: `Authorization: Bearer <token>` or `x-vercel-oidc-token: <token>`

## Hermes Agent Integration

Hermes Agent is a first-class supported agent (one of 72 total):

| Scope | Flag | Path |
|---|---|---|
| Project | (default) | `.hermes/skills/` |
| Global | `-g` | `~/.hermes/skills/` |

Install directly: `npx skills add <owner/repo> -a hermes-agent -g -y`

Skills installed this way are discoverable by `skills_list` and loadable via `skill_view`.

**HERMES_HOME override:** The CLI respects the `HERMES_HOME` environment variable. If set, global skills install to `$HERMES_HOME/skills/` instead of `~/.hermes/skills/`. On a profile-based Hermes setup, the actual install path may differ from the default — verify with `npx skills list -a hermes-agent` after installing.

## Fleet Deployment Patterns

When running a fleet of multiple agent types (Hermes Agent, Claude Code, Codex, etc.):

**Cross-agent install — one command, multiple agents:**
```bash
npx skills add vercel-labs/agent-skills --agent hermes-agent claude-code codex --copy -y
```

**Use `--copy` instead of symlinks for fleet deployments.** Symlinks (default) create a single point of failure — if the source cache is deleted, all symlinked skills break. `--copy` duplicates files into each agent's directory, making them independent.

**Pre-screen before installing (no auth needed):**
```bash
curl -s "https://skills.sh/api/v1/skills/audit/vercel-labs/agent-skills/deploy-to-vercel" | python3 -m json.tool
```

**CLI over API for non-Vercel fleets.** The REST API requires Vercel OIDC tokens (no API key alternative). For fleets not deployed on Vercel, use the CLI (`find`, `add`, `list`, `remove`) and the unauthenticated audit endpoint — skip the rest of the API entirely.

## Pitfalls

- **API auth is Vercel-only — no API key alternative.** All endpoints except `/skills/audit/{source}/{skill}` return HTTP 401 without a Vercel OIDC token. For non-Vercel fleets, use the CLI and the unauthenticated audit endpoint only. Do not invest in API integration unless you have a Vercel project with OIDC enabled.
- **Audit endpoint is the only unauthenticated API path.** `/api/v1/skills/audit/{source}/{skill}` returns HTTP 200 without auth — everything else returns 401.
- **Wrong endpoint paths in some documentation.** The correct API paths are `/api/v1/skills`, `/api/v1/skills/search`, `/api/v1/skills/curated`, `/api/v1/skills/{source}/{skill}`, `/api/v1/skills/audit/{source}/{skill}`. Paths like `/api/v1/leaderboard`, `/api/v1/agents`, `/api/v1/search` (without the `/skills/` prefix) return 404.
- **Telemetry is on by default.** Set `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` to opt out. Auto-disabled in CI.
- **Symlink vs copy.** Default is symlink (single source of truth, easy updates). Use `--copy` for fleet deployments where a single cache deletion would break all agents.
- **HERMES_HOME path override.** If `HERMES_HOME` is set, global skills install to `$HERMES_HOME/skills/` not `~/.hermes/skills/`. Verify actual install location with `npx skills list -a hermes-agent`.
- **Skill not loading.** Verify SKILL.md has valid YAML frontmatter with both `name` and `description` fields. Check the install path matches the agent's expected directory.
- **Security audits may not exist yet.** The audit endpoint returns 404 for skills that haven't been installed/audited. Audits auto-generate after first install with a few minutes delay.
- **`isDuplicate` flag.** Some skills are forks. Listing/search responses include `isDuplicate: true` — filter these if you only want originals.
- **Internal skills hidden by default.** Skills with `metadata.internal: true` are only visible when `INSTALL_INTERNAL_SKILLS=1` env var is set.
- **`vercel-labs` project — not core Vercel.** skills.sh is a labs project, which carries higher deprecation risk than mainline Vercel products. The repo is open source at github.com/vercel-labs/skills — self-hosting is possible but audit partner integrations wouldn't carry over.
- **OIDC token rotation (~12h).** Any automation using the API needs `@vercel/oidc` helper for auto-refresh, or manual `vercel env pull` cycles. Fragile for long-running fleet automation.

## Verification

```bash
npx skills list -a hermes-agent
```

This shows all skills installed for Hermes Agent. If a newly installed skill appears here, the install succeeded.

## References

- **[Fleet Assessment](references/fleet-assessment.md)** — Detailed findings from hands-on testing of CLI and API for a multi-agent fleet. Includes verified endpoint status codes, audit response example, auth architecture analysis, and fleet deployment recommendations.