---
name: hermes-boot-checklist
description: "Run a startup checklist via a gateway:startup hook on every boot."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Hermes, Hooks, Gateway, Startup, Automation]
---

# Hermes Boot Checklist

Run a natural-language checklist every time the Hermes gateway starts by dropping a `~/.hermes/BOOT.md` file and wiring a `gateway:startup` hook that spawns a one-shot agent. This is a documented community pattern, not a built-in feature — you create the hook files yourself so you control exactly what runs.

## When to Use

- You want the agent to check overnight cron failures and ping you on startup
- You want a deploy-log summary posted to a channel every time the gateway restarts
- You want schedule-aware boot tasks (e.g. "if it's Monday, also check the weekly deploy log")
- You need a one-shot agent run that inherits the gateway's resolved model and credentials

## Prerequisites

- Hermes Agent installed and gateway configured (`hermes gateway setup`)
- Gateway running (`hermes gateway start` or `hermes gateway install`)
- `~/.hermes/hooks/` directory exists (created automatically by Hermes)

## How to Run

1. Write your checklist to `~/.hermes/BOOT.md` using `write_file`
2. Create the hook directory and files under `~/.hermes/hooks/boot-md/`
3. Restart the gateway via `terminal` tool: `hermes gateway restart`
4. Verify via `terminal` tool: `hermes logs --follow --level INFO | grep boot-md`

## Quick Reference

```
~/.hermes/BOOT.md                          # Your checklist (plain Markdown)
~/.hermes/hooks/boot-md/HOOK.yaml          # Event subscription: gateway:startup
~/.hermes/hooks/boot-md/handler.py         # Spawns one-shot AIAgent with BOOT.md
hermes gateway restart                     # Triggers the hook
hermes logs --follow --level INFO | grep boot-md  # Verify
```

## Procedure

### 1. Write the checklist

Use `write_file` to create `~/.hermes/BOOT.md`:

```markdown
# Startup Checklist

1. Run `hermes cron list` and check if any scheduled jobs failed overnight.
2. If any failed, summarize them for Discord #ops.
3. Check if `/opt/app/deploy.log` has any ERROR lines from the last 24 hours.
4. If nothing went wrong, reply with only `[SILENT]` so no message is sent.
```

The agent sees this as its prompt, so anything describable in plain language works — tool calls, shell commands, summarizing files.

### 2. Create the hook

Use `write_file` to create two files:

**`~/.hermes/hooks/boot-md/HOOK.yaml`**:

```yaml
name: boot-md
description: Run ~/.hermes/BOOT.md on gateway startup
events:
  - gateway:startup
```

**`~/.hermes/hooks/boot-md/handler.py`**:

```python
"""Run ~/.hermes/BOOT.md on every gateway startup."""

import logging
import threading
from pathlib import Path

logger = logging.getLogger("hooks.boot-md")

BOOT_FILE = Path.home() / ".hermes" / "BOOT.md"


def _build_prompt(content: str) -> str:
    return (
        "You are running a startup boot checklist. Follow the instructions "
        "below exactly.\n\n"
        "---\n"
        f"{content}\n"
        "---\n\n"
        "Execute each instruction. Put any user-facing summary in your "
        "final response — the hook delivers it to the configured channel "
        "(e.g. Discord or Slack); you do not send messages yourself.\n"
        "If nothing needs attention and there is nothing to report, reply "
        "with ONLY: [SILENT]"
    )


def _run_boot_agent(content: str) -> None:
    """Spawn a one-shot agent and execute the checklist."""
    try:
        from gateway.run import _resolve_gateway_model, _resolve_runtime_agent_kwargs
        from run_agent import AIAgent

        agent = AIAgent(
            model=_resolve_gateway_model(),
            **_resolve_runtime_agent_kwargs(),
            platform="gateway",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            max_iterations=20,
        )
        result = agent.run_conversation(_build_prompt(content))
        response = (result.get("final_response", "") or "").strip()
        if response.upper() not in {"[SILENT]", "SILENT", "NO_REPLY", "NO REPLY"}:
            logger.info("boot-md completed: %s", response[:200])
        else:
            logger.info("boot-md completed (nothing to report)")
    except Exception as e:
        logger.error("boot-md agent failed: %s", e)


async def handle(event_type: str, context: dict) -> None:
    if not BOOT_FILE.exists():
        return
    content = BOOT_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return

    logger.info("Running BOOT.md (%d chars)", len(content))

    thread = threading.Thread(
        target=_run_boot_agent,
        args=(content,),
        name="boot-md",
        daemon=True,
    )
    thread.start()
```

### 3. Restart and verify

Invoke through the `terminal` tool:

```bash
hermes gateway restart
hermes logs --follow --level INFO | grep boot-md
```

Expect `Running BOOT.md (N chars)` followed by `boot-md completed: ...` or `boot-md completed (nothing to report)`.

### 4. Disable

Delete `~/.hermes/BOOT.md` — the hook stays loaded but silently skips when the file is absent.

## Pitfalls

- **Not a built-in.** Hermes does not ship a BOOT.md hook. You must create the hook files yourself. An earlier version shipped it as built-in and surprised users with custom endpoints — it was removed in favor of the explicit pattern.
- **Gateway-only.** Gateway hooks only fire in the gateway (Telegram, Discord, Slack, etc.). The CLI does not load gateway hooks. For CLI+gateway coverage, use plugin hooks or shell hooks instead.
- **Custom endpoints require `_resolve_gateway_model()` and `_resolve_runtime_agent_kwargs()`.** Without these, a bare `AIAgent()` falls back to built-in defaults and will 401 against any non-default endpoint.
- **Background thread.** The handler runs the agent in a daemon thread so gateway startup isn't blocked. This means if the gateway process exits quickly, the boot agent may be cut short.
- **`[SILENT]` convention.** The agent must reply with exactly `[SILENT]` (case-insensitive) to suppress output. Other silence tokens accepted: `SILENT`, `NO_REPLY`, `NO REPLY`.
- **Non-TTY consent.** If using shell hooks instead of gateway hooks, non-TTY environments (gateway, cron) need `HERMES_ACCEPT_HOOKS=1` or `hooks_auto_accept: true` in config — otherwise newly-added hooks silently stay unregistered.

## Verification

```bash
hermes gateway restart && sleep 5 && hermes logs --level INFO | grep boot-md
```

You should see `Running BOOT.md` and a completion line within seconds of restart.