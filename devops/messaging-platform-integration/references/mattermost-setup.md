---
created: 2026-06-05
updated: 2026-06-05
session: 2026-06-05-mattermost-integration
---

# Mattermost Integration Session

## Context
- **Goal**: Integrate Mattermost with Hermes for bidirectional messaging, media, threads, and fleet coordination.
- **Platform**: Mattermost Team Edition (Docker, `localhost:8065`)
- **Bot Account**: `hermes`

## Steps Taken

### 1. Platform Verification
```bash
curl -s http://localhost:8065/api/v4/system/ping
```
**Output**: `{"status":"OK"}` ✅

### 2. Bot Token Issue
- **Problem**: `MATTERMOST_BOT_TOKEN` not found in `~/.hermes/.env` or vault.
- **Solution**: Manual bot account creation via Mattermost UI.

### 3. Browser Tool Failure
- **Problem**: Mattermost UI did not load in `browser_navigate`.
- **Root Cause**: Browser tool stack (Browserbase) may not support local `localhost` URLs.
- **Workaround**: Use terminal/curl for setup, browser tools only for UI navigation.

### 4. Manual UI Steps
1. Open [http://localhost:8065](http://localhost:8065)
2. Log in as admin (credentials in `=notes/claude/orchestration/rbitr/.env`)
3. Navigate to **System Console > Integrations > Bot Accounts**
4. Click **Add Bot Account**
   - Username: `hermes`
   - Display Name: `Hermes`
   - Description: `Hermes Agent Bot`
5. Click **Generate Token** and save to `~/.hermes/.env`:
   ```
   MATTERMOST_BOT_TOKEN=abc123...
   ```

## Pitfalls
- **Token Storage**: `.env` is the canonical source, not vault files.
- **Browser Tools**: Avoid for `localhost` URLs; use terminal/curl instead.
- **Permissions**: Bot needs `read_channel`, `post_channel`, `manage_webhooks`.

## Verification
```bash
curl -s -H "Authorization: Bearer $MATTERMOST_BOT_TOKEN" http://localhost:8065/api/v4/users/me
```
**Expected Output**: `{"username":"hermes"}`