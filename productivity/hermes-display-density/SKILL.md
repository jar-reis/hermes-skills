---
name: hermes-display-density
description: "Tune Hermes output density via display.compact and related settings."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Hermes, Display, Configuration, Density]
---

# Hermes Display Density

Control how much whitespace and visual chrome Hermes puts in CLI/TUI output. The primary lever is `display.compact: true`, which collapses the startup banner to a minimal bordered box and suppresses decorative spacing. Related settings in the `display` config section further tune output density.

## When to Use

- User says "reduce whitespace" or "denser output" or "more compact display"
- Output feels too verbose / too many blank lines in the CLI
- Running in a narrow terminal pane and the full banner wraps
- User saw the startup tip "Set display.compact: true to reduce whitespace"

## Prerequisites

- Hermes installed and at least one profile configured
- Edit access to `config.yaml` (find it with `hermes config path`)

## How to Run

Set the config value through the `terminal` tool:

```
hermes config set display.compact true
```

Then start a new session (`/reset` in an existing session, or relaunch the CLI). Display settings are read at startup — they do NOT apply mid-conversation (this preserves prompt caching).

## Quick Reference

| Setting | Default | Effect |
|---|---|---|
| `display.compact` | `false` | Compact banner, reduced whitespace |
| `display.resume_display` | `full` | `minimal` = one-liner recap on session resume |
| `display.tool_progress` | `all` | `off` = hide tool call progress entirely |
| `display.streaming` | `true` | Token-by-token streaming output |
| `display.show_reasoning` | `false` | Show model chain-of-thought |
| `display.timestamps` | `false` | Timestamps on messages |
| `display.interim_assistant_messages` | `true` | Show interim assistant text during tool calls |

## Procedure

1. **Enable compact mode:**
   ```
   hermes config set display.compact true
   ```

2. **(Optional) Reduce resume recap noise:**
   ```
   hermes config set display.resume_display minimal
   ```

3. **(Optional) Hide tool progress output entirely:**
   ```
   hermes config set display.tool_progress off
   ```

4. **Start a new session** — display settings snapshot at startup:
   - CLI: relaunch `hermes`
   - In-session: `/reset`
   - Gateway: `/restart`

5. **Verify** the compact banner appears (a small bordered box with model name + tool count, no ASCII caduceus art).

## Pitfalls

- **No mid-session effect.** `display.compact` is read once at startup. Toggling it in config does not change the current session — start a new one.
- **Auto-compact on narrow terminals.** Terminal width < 80 columns triggers compact mode automatically regardless of config. This is by design (the full banner needs ~80 cols).
- **`/compact` is NOT this feature.** The `/compact` slash command is an alias for `/compress` (context compression). It has nothing to do with `display.compact`.
- **No `--compact` CLI flag.** Compact mode is set via config or auto-detected from terminal width. There is no command-line argument for it.
- **Termux auto-compact.** On Termux (Android), compact mode is forced on at startup via `HERMES_DEFER_AGENT_STARTUP=1` and `HERMES_FAST_STARTUP_BANNER=1`.

## Verification

```
hermes config show | grep compact
```

Expected output shows `compact: true` under the Display section. On next session start, the banner is a minimal bordered box instead of the full caduceus art.