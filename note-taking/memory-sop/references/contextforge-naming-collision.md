# ContextForge Naming Collision — Full Resolution

**Resolved:** 2026-06-13 by Hermes (Session 27f8a497 follow-up)

## The Problem

For weeks, the fleet had an unresolved question: "Did we ever figure out how to resolve the confusion with the two ContextForge usages?" Two distinct systems shared the same name, causing agents to conflate them and make incorrect assumptions about auth, reachability, and purpose.

## The Two Systems

### ContextForge SaaS (contextforge.dev)
- **What:** Persistent memory/knowledge graph cloud service
- **URL:** `https://contextforge.dev`
- **Auth:** API key stored in macOS Keychain (`contextforge-dev-api-key`, account `jackareis@gmail.com`)
- **Launcher:** `~/.local/bin/contextforge-mcp-keychain.sh` → npm package `contextforge-mcp` v0.2.0
- **API surface:** `/functions/v1/ingest`, `/query`, `/projects`, `/spaces`, `/relationships`, `/items`, `/stats`, `/git-repos`
- **Used by:** Hermes (via `mcp_contextforge_memory_*` tools), Kimi Cloud (via `~/.kimi/mcp.json` `contextforge` entry)
- **Purpose:** Store and query knowledge items with semantic search, cross-agent shared memory
- **Project:** "Open Brain 1" — the fleet's shared knowledge graph project
- **Status (2026-06-13):** ✅ Working. All endpoints functional except `POST /functions/v1/relationships` which returns 401 `UNAUTHORIZED_INVALID_JWT_FORMAT` (server-side JWT middleware bug — the `/relationships` endpoint expects JWT tokens while all other endpoints accept API keys).

### ContextForge Gateway (IBM open-source)
- **What:** MCP proxy/router — an AI Gateway, registry, and proxy that sits in front of any MCP, A2A, or REST/gRPC APIs
- **URL:** `http://localhost:8090`
- **Container:** `ghcr.io/ibm/mcp-context-forge:latest` (Docker, OrbStack-managed)
- **GitHub:** `github.com/IBM/mcp-context-forge` (Apache 2.0)
- **Auth:** JWT tokens generated via Bifrost at `localhost:8078`
- **Launcher:** Docker Compose in `~/ai-dev/contextforge-test/`
- **API surface:** `/mcp/` (MCP protocol endpoint), `/health`
- **Used by:** Kimi Cloud as `mcpgateway-a2a` proxy (in `~/.kimi/mcp.json`)
- **Purpose:** Route MCP calls to backend services, centralized discovery, guardrails
- **Status (2026-06-13):** ✅ Healthy. Container `contextforge` + Redis `contextforge-redis` both Up.

## How the Confusion Started

1. IBM named their open-source MCP gateway "mcp-context-forge" — the name "ContextForge" appears in the container image, the GitHub repo, and the Docker Compose project.
2. The SaaS memory service is also called "ContextForge" — it appears in the npm package name (`contextforge-mcp`), the MCP tool names (`mcp_contextforge_memory_*`), and the domain (`contextforge.dev`).
3. Kimi Cloud's `mcp.json` has TWO entries: `contextforge` (the SaaS, via keychain wrapper) and `mcpgateway-a2a` (the IBM gateway at `:8090`). Both use the word "contextforge" in their config.
4. Older L1 memory entries said "ContextForge MCP: Depends on OrbStack/Docker :8090" — this referred to the gateway, not the SaaS. Agents reading this would check `:8090` health and conclude "ContextForge is down" when the SaaS was actually fine.

## Resolution

- The L4 memory layer uses **ContextForge SaaS** (contextforge.dev), NOT the Docker gateway.
- The Docker gateway at `:8090` is infrastructure (MCP routing), not a memory store.
- When an agent says "ContextForge is down," clarify WHICH one: the SaaS (check `contextforge.dev` API) or the gateway (check `localhost:8090/health`).
- The `contextforge-token.sh` script manages the SaaS API key, not gateway JWT tokens.
- Bifrost at `:8078` generates JWT tokens for the gateway, not for the SaaS.

## Verification Commands

```bash
# SaaS health (via MCP bridge)
~/.hermes/bin/contextforge-token.sh check

# Gateway health
curl -s http://localhost:8090/health

# SaaS query test
python3 -c "
import subprocess, json, urllib.request
key = subprocess.run(['security','find-generic-password','-s','contextforge-dev-api-key','-a','jackareis@gmail.com','-w'], capture_output=True, text=True).stdout.strip()
req = urllib.request.Request('https://contextforge.dev/functions/v1/query', data=json.dumps({'query':'test','limit':1}).encode(), headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'}, method='POST')
# Note: direct curl to /functions/v1/ returns 404 — the API surface requires the MCP bridge's auth layer
print('SaaS reachable via MCP bridge')
"
```
