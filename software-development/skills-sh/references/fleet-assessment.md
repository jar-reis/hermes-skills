# Fleet Agent Assessment — skills.sh

Findings from hands-on testing of skills.sh CLI and API for a multi-agent fleet
(Hermes Agent, Claude Code, Codex) running on a Mac Mini.

## CLI Testing (npx skills@1.5.15)

### Confirmed Working
- `npx skills find <query>` — discovery without auth, returns ranked results with install counts
- `npx skills add <owner/repo> --agent hermes-agent --skill <name> -g -y` — installs to correct Hermes directory
- `npx skills list --agent hermes-agent` — lists installed skills
- `npx skills remove --agent hermes-agent --skill <name> -y -g` — clean removal
- `npx skills add <owner/repo> --list` — lists available skills without installing
- Security audit shown during install (Gen, Socket, Snyk verdicts displayed inline)

### Agent Support
72 agents supported (verified from source at github.com/vercel-labs/skills/src/agents.ts).
Hermes Agent entry:
```typescript
'hermes-agent': {
  name: 'hermes-agent',
  displayName: 'Hermes Agent',
  skillsDir: '.hermes/skills',
  globalSkillsDir: join(hermesHome, 'skills'),  // hermesHome = HERMES_HOME || ~/.hermes
  detectInstalled: async () => existsSync(hermesHome),
}
```

## API Testing

### Endpoint Status (without auth)

| Endpoint | HTTP Status | Notes |
|---|---|---|
| `GET /api/v1/skills` | 401 | Auth required |
| `GET /api/v1/skills/search?q=react` | 401 | Auth required |
| `GET /api/v1/skills/curated` | 401 | Auth required |
| `GET /api/v1/skills/{source}/{skill}` | 401 | Auth required |
| `GET /api/v1/skills/audit/{source}/{skill}` | **200** | **No auth needed** |

### Wrong Endpoints (return 404, not 401)
These paths were referenced in some docs but do NOT exist:
- `/api/v1/leaderboard` → 404
- `/api/v1/agents` → 404
- `/api/v1/search` → 404
- `/api/v1/picks` → 404
- `/api/v1/sets` → 404
- `/api/v1/audits` → 404

The correct paths all start with `/api/v1/skills/...`.

### Audit Endpoint Example Response

```json
{
  "id": "vercel-labs/agent-skills/deploy-to-vercel",
  "source": "vercel-labs/agent-skills",
  "slug": "deploy-to-vercel",
  "audits": [
    {
      "provider": "Gen Agent Trust Hub",
      "slug": "agent-trust-hub",
      "status": "pass",
      "summary": "This skill provides a standard and well-structured workflow...",
      "auditedAt": "2026-03-06T14:34:50.948Z",
      "riskLevel": "SAFE"
    },
    {
      "provider": "Socket",
      "slug": "socket",
      "status": "pass",
      "summary": "No alerts",
      "auditedAt": "2026-03-18T16:47:58.222Z"
    },
    {
      "provider": "Snyk",
      "slug": "snyk",
      "status": "pass",
      "summary": "Risk: LOW · No issues",
      "auditedAt": "2026-03-06T14:34:51.391606+00:00",
      "riskLevel": "LOW"
    },
    {
      "provider": "Runlayer",
      "slug": "runlayer",
      "status": "warn",
      "summary": "3/3 files flagged",
      "auditedAt": "2026-03-06T14:34:33.006Z",
      "riskLevel": "MEDIUM"
    },
    {
      "provider": "ZeroLeaks",
      "slug": "zeroleaks",
      "status": "pass",
      "summary": "Score: 93/100 · 2 sections analyzed",
      "auditedAt": "2026-04-16T15:34:11.288Z",
      "riskLevel": "NONE"
    }
  ]
}
```

## Auth Architecture

- **Vercel OIDC only.** No API keys, no service accounts, no OAuth.
- Token is a short-lived JWT (~12h rotation), scoped to (team, project).
- To get a token without a Vercel deployment: create a throwaway Vercel project,
  enable OIDC, `vercel link` locally, `vercel env pull` to get token in `.env.local`.
- This is impractical for non-Vercel fleets — use CLI instead.

## Fleet Recommendations

1. **Use CLI, not API** — `find`, `add`, `list`, `remove` all work without Vercel account
2. **Use `--copy` not symlinks** — fleet resilience against cache deletion
3. **Pre-screen with audit endpoint** — only unauth API endpoint, check before installing
4. **Cross-agent install** — `--agent hermes-agent claude-code codex` in one command
5. **Keep custom skills manual** — skills.sh is for generic/vendor skills, not proprietary workflows
6. **Set `DISABLE_TELEMETRY=1`** if install tracking is a concern
7. **Don't invest in API automation** — OIDC-only auth is a dealbreaker for non-Vercel infra

## Ecosystem Stats (as of testing)

- 72 agents supported
- 8,420+ skills on the leaderboard (per API docs example response)
- Top skill: vercel-labs/agent-skills@vercel-react-best-practices (534.3K installs)
- Security audit partners: Gen Agent Trust Hub, Socket, Snyk, Runlayer, ZeroLeaks