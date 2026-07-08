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

All under `https://skills.sh/api/v1/`, require Vercel OIDC auth, JSON responses.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/skills` | Paginated leaderboard (`view=all-time\|trending\|hot`, `page`, `per_page=1-500`) |
| GET | `/skills/search` | Search by name/description (`q` required, `limit=1-200`, `owner`) |
| GET | `/skills/curated` | Official first-party skills set |
| GET | `/skills/{source}/{skill}` | Skill detail with full file tree (SKILL.md + supporting files) |
| GET | `/skills/audit/{source}/{skill}` | Security audit results |

**Rate limit:** 600 req/min per (team, project). Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. 429 returns `Retry-After`.

**Auth setup (Vercel OIDC):**
1. Enable OIDC Federation in Vercel dashboard → Settings → OIDC Federation
2. `npm install @vercel/oidc` (recommended) or read `process.env.VERCEL_OIDC_TOKEN` directly
3. Call `getVercelOidcToken()` inside request handlers (rotates ~12h, do not cache at module scope)
4. Header form: `Authorization: Bearer <token>` or `x-vercel-oidc-token: <token>`

## Hermes Agent Integration

Hermes Agent is a first-class supported agent:

| Scope | Flag | Path |
|---|---|---|
| Project | (default) | `.hermes/skills/` |
| Global | `-g` | `~/.hermes/skills/` |

Install directly: `npx skills add <owner/repo> -a hermes-agent -g -y`

Skills installed this way are discoverable by `skills_list` and loadable via `skill_view`.

## Pitfalls

- **Telemetry is on by default.** Set `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` to opt out. Auto-disabled in CI.
- **Symlink vs copy.** Default is symlink (single source of truth, easy updates). Use `--copy` when symlinks aren't supported (e.g., some Windows setups).
- **Skill not loading.** Verify SKILL.md has valid YAML frontmatter with both `name` and `description` fields. Check the install path matches the agent's expected directory.
- **API auth is Vercel-only.** The REST API requires a Vercel OIDC token — there is no API key alternative. Without Vercel, use the CLI instead.
- **Security audits may not exist yet.** The audit endpoint returns 404 for skills that haven't been installed/audited. Audits auto-generate after first install with a few minutes delay.
- **`isDuplicate` flag.** Some skills are forks. Listing/search responses include `isDuplicate: true` — filter these if you only want originals.
- **Internal skills hidden by default.** Skills with `metadata.internal: true` are only visible when `INSTALL_INTERNAL_SKILLS=1` env var is set.

## Verification

```bash
npx skills list -a hermes-agent
```

This shows all skills installed for Hermes Agent. If a newly installed skill appears here, the install succeeded.