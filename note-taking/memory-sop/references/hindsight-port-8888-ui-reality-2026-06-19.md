# Hindsight Port — UI Reality and Port History

## Current Canonical (2026-06-24)

- **Port**: `9876` (canonical as of 2026-06-24)
- **Health check**: `http://localhost:9876/health` → `{"status":"healthy","database":"connected"}`
- **Root path**: `http://localhost:9876/` → `{"detail":"Not Found"}` (no web dashboard)
- **Swagger UI**: `http://localhost:9876/docs`
- **OpenAPI spec**: `http://localhost:9876/openapi.json`
- **API base**: `http://localhost:9876/v1/default/banks/{bank_id}/...`
- **Fallback port**: `8888` (if 9876 is down, try 8888 before declaring Hindsight unreachable)

## Port History

| Date | Port | Notes |
|------|------|-------|
| 2026-06-18 to 2026-06-23 | 8888 | Daemon moved to 8888 during fleet reconfig |
| 2026-06-24 onwards | 9876 | Daemon moved back to 9876 after launchd restart cycle |

The port has changed more than once. **Always check both ports** if Hindsight
seems unreachable. The daemon process is `hindsight-api --daemon --port <PORT>`
launched by launchd `com.jackreis.hindsight-embed`.

## Verification Commands

```bash
# Check which port is active
curl -s http://localhost:9876/health
curl -s http://localhost:8888/health

# Check the process directly
ps aux | grep hindsight-api | grep -v grep

# Check launchd status
launchctl list com.jackreis.hindsight-embed
```

## Provider Quirk

- Hindsight **has no root-path web dashboard**. The daemon returns
  `{"detail":"Not Found"}` at `/`.
- Use `/docs` for Swagger UI, `/health` for health checks,
  `/openapi.json` for the full API schema.
- All data operations are under `/v1/default/banks/{bank_id}/...`.
- The retain endpoint is `POST /v1/default/banks/{bank_id}/memories`
  (NOT `/memories/retain`). Requires `{"items": [...], "async": true}` format.

## Related Skills

- `memory-sop` — Updated to reflect port 9876 as canonical (2026-06-24).
- `memory-sop-drain` — Should default to port 9876.