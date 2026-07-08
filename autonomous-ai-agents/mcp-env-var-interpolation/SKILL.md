---
name: mcp-env-var-interpolation
description: "Configure MCP servers with env-var placeholders from .env."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [MCP, Configuration, Env-Vars, Hermes]
---

# MCP Env-Var Interpolation in Hermes Config

Hermes resolves `${VAR_NAME}` placeholders in `mcp_servers` config at server spawn time, drawing values from `~/.hermes/.env` (or the active profile's `.env`). This lets you keep secrets out of `config.yaml` while wiring them into MCP server `env`, `headers`, `url`, `args`, and `command` fields.

## When to Use

- Adding an MCP server that needs an API key from `.env` without hardcoding it
- Seeing a literal `${SOME_VAR}` in an MCP server's spawned environment or headers
- Migrating a Cursor/Claude MCP config that uses `${env:VAR}` syntax
- Debugging why an MCP server gets an empty value where a key was expected

## Prerequisites

- `mcp` Python package installed (`pip install mcp`)
- `~/.hermes/.env` (or `~/.hermes/profiles/<name>/.env`) containing the referenced vars
- MCP servers configured under `mcp_servers` in `config.yaml`

## How It Works

### Placeholder Syntax

Two forms are accepted — both resolve identically:

| Syntax | Source |
|--------|--------|
| `${VAR_NAME}` | Standard form |
| `${env:VAR_NAME}` | Cursor-style (prefix stripped) |

Variable names accept hyphens, dots, and other non-`}` characters.

### Resolution Chain

1. Hermes starts → `load_hermes_dotenv()` loads `~/.hermes/.env` into `os.environ`
2. `_load_mcp_config()` reads `mcp_servers` from `config.yaml`
3. Suspicious configs are filtered (exfiltration-shaped entries dropped)
4. `_interpolate_env_vars()` recursively walks each server's config dict
5. For every string value, `${VAR}` placeholders are replaced via `get_secret(name)`
6. Resolved configs are passed to the server spawn path

### Value Source by Mode

| Mode | Lookup source |
|------|--------------|
| Single-profile (default) | `os.environ` (includes `.env` loaded at startup) |
| Multiplexed gateway | Active profile's secret scope (contextvar), NOT global `os.environ` |
| Unset variable | Literal `${VAR}` placeholder preserved (no error) |

### Resolution Scope

Interpolation is **recursive** — it walks dicts, lists, and nested structures. Placeholders work in:

- `env:` values (most common — passed to stdio subprocess)
- `headers:` values (HTTP transport auth)
- `url:` strings (HTTP transport endpoint)
- `args:` elements (command arguments)
- `command:` strings

## Quick Reference

```yaml
# config.yaml — placeholder references .env vars
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"   # resolved from .env

  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ${MCP_AUTH_TOKEN}"          # resolved from .env
```

```bash
# .env — actual values live here
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
MCP_AUTH_TOKEN=sk-xxxxxxxxxxxxxxxxxxxx
```

## Procedure

1. Add the env var to `~/.hermes/.env` (or `~/.hermes/profiles/<name>/.env`):
   ```
   MY_API_KEY=sk_abc123
   ```
2. Reference it in `config.yaml` under the server's config using `${MY_API_KEY}`:
   ```yaml
   mcp_servers:
     my_server:
       command: "npx"
       args: ["-y", "my-mcp-server"]
       env:
         API_KEY: "${MY_API_KEY}"
   ```
3. Restart Hermes (new session or `/restart` in gateway). MCP config is read at startup — no hot-reload.
4. Verify with `hermes mcp list` — the server should show `✓ enabled`.

## Pitfalls

- **No hot-reload.** Adding vars to `.env` or changing `mcp_servers` config requires a restart (`/reset` or `/restart`). The `/reload` slash command reloads `.env` into the running session but does NOT re-spawn MCP servers.
- **Unset vars are silently preserved as literals.** If `${MY_KEY}` is not in `.env`, the spawned server receives the literal string `${MY_KEY}` — not an empty string, not an error. Check `.env` spelling and profile path.
- **Profile-specific `.env` path.** With profiles, the `.env` is at `~/.hermes/profiles/<name>/.env`, not `~/.hermes/.env`. `hermes config env-path` prints the active path.
- **Multiplexed gateway uses secret scope, not `os.environ`.** In a multiplexed gateway, `get_secret()` reads from the active profile's contextvar scope. A var present in global `os.environ` but not in the profile scope will NOT resolve. This prevents cross-profile key leakage.
- **Safe mode skips MCP.** `HERMES_SAFE_MODE=1` (or `--safe-mode`) returns an empty server dict — no MCP servers connect, so no interpolation runs.
- **Env filtering for stdio subprocesses.** Even after interpolation, stdio subprocesses receive only a filtered environment (PATH, HOME, USER, LANG, etc. + explicitly specified `env:` vars). `${VAR}` in an `env:` entry is resolved and passed; vars in `os.environ` that are NOT in `env:` are NOT inherited by the subprocess.
- **Suspicious config filter.** Configs that look like data exfiltration (e.g., sending env contents to an external URL) are silently dropped before interpolation. Check startup logs for "Skipping suspicious MCP server" warnings.

## Verification

```bash
# Confirm the server connected and tools are registered
hermes mcp list
# Should show the server with ✓ enabled and a tool count > 0

# Confirm the .env var is loadable at the expected path
hermes config env-path    # prints the active .env path
```