---
name: messaging-platform-integration
description: Integrate messaging platforms (Mattermost, Discord, Telegram, Slack, Matrix, SMS, email) with Hermes for bidirectional message delivery, media attachments, thread support, and fleet coordination.
category: devops
trigger_phrases:
  - "Integrate Mattermost"
  - "Integrate Discord"
  - "Integrate Telegram"
  - "Integrate Slack"
  - "Integrate Matrix"
  - "Integrate SMS"
  - "Integrate email"
  - "Set up Hermes bot on"
  - "Send messages from Hermes to"
  - "Receive messages in Hermes from"
  - "Debug <platform> integration"
author: Hermes
created: 2026-06-05
updated: 2026-06-05
---

# Messaging Platform Integration

## Workflow

### 1. Platform Setup
- Verify platform is running (e.g., `curl http://localhost:8065/api/v4/system/ping` for Mattermost)
- Create bot account (manual UI or API)
- Generate bot token and store securely in `.env`
- Set permissions (read/post channels, manage webhooks, upload media)

### 2. Hermes Configuration
Add platform to `~/.hermes/config.yaml` under `messaging.platforms`:
```yaml
mattermost:
  enabled: true
  home_channel: "town-square"
  api_url: "http://localhost:8065/api/v4"
  bot_token: "${MATTERMOST_BOT_TOKEN}"
  message_mode: "post"  # or "webhook"
```

### 3. Gateway Plugin
- Scaffold plugin in `~/.hermes/gateway/plugins/<platform>.py`
- Implement:
  - WebSocket listener (real-time receive)
  - REST API wrapper (send)
  - Thread resolution
  - Media upload

### 4. Fleet Routing
Update `fleet-routing.yaml`:
```yaml
channels:
  - name: "mattermost:town-square"
    audience: "home"
    platform: "mattermost"
    chat_id: "town-square"
    thread_id: null
```

### 5. Verification
- Send test message: `hermes send_message --target "<platform>" --message "Integration test"`
- Receive test message: Post in platform → Hermes logs it
- Media upload: `hermes send_message --target "<platform>" --message "MEDIA:/tmp/test.png"`
- Heartbeat: `hermes heartbeat --deliver "<platform>"`
- Cron delivery: Update a cron job to deliver to `<platform>`

### 6. Cold Restart Resilience
Add to `~/.hermes/bin/cold-restart-checklist.sh`:
```bash
check_<platform>() {
  curl -s -H "Authorization: Bearer *** ${API_URL}/system/ping | grep -q '"status":"OK"'
  echo "<Platform>: $?"
}
```

## Decommissioned Platforms

### Mattermost (removed 2026-07-02)
Mattermost was fully ripped out of the Aegis fleet on 2026-07-02. All components deleted:
- Docker containers, volumes, images
- Hermes config.yaml messaging block
- `.env` `MATTERMOST_URL` entry
- Gateway plugin, skill references, vault dirs, kimi_openclaw dirs
- 2 superseded LaunchAgents (`ai.hermes.gateway-family` crash-loop, `com.jackreis.obn-sync` AGENTS.md violation)
- iCloud container (0 bytes, self-cleans via iCloud)
- All beads queue items related to Mattermost closed

Do NOT re-add Mattermost unless the user explicitly requests it. The Mattermost config template and references below are kept for historical reference only.

## Pitfalls
- **Token not found**: Check `.env` and `=notes/claude/orchestration/rbitr/.env`
- **WebSocket disconnects**: Add exponential backoff
- **Media upload failures**: Verify bot permissions
- **Thread resolution**: Use `root_id` for replies, `id` for new messages
- **Browser tool failures**: Prefer terminal/curl for setup, use browser tools only for UI navigation
- **Rip-out completeness**: When decommissioning a messaging platform, remove ALL artifacts — config block, .env entries, LaunchAgents, Docker volumes, skills, vault dirs, iCloud containers. Check `grep -ri '<platform>' ~/.hermes/` to catch stragglers. iCloud-managed containers (e.g. `~/Library/Mobile Documents/iCloud~com~mattermost~rn/`) cannot be `rm`'d directly — they self-clean via iCloud.

## Verification Scripts
- [`scripts/verify-<platform>-token.sh`](scripts/verify-<platform>-token.sh): Validate bot token
- [`scripts/test-<platform>-send-receive.sh`](scripts/test-<platform>-send-receive.sh): End-to-end test

## References
- [Mattermost Setup](references/mattermost-setup.md): Session transcript + pitfalls

## Templates
- [`templates/mattermost-config.yaml`](templates/mattermost-config.yaml): Known-good config