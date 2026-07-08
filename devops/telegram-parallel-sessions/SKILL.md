---
name: telegram-parallel-sessions
description: "Manage parallel Hermes sessions in Telegram topics."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Telegram, Sessions, Topics, Parallel, Hermes]
---

# Telegram Parallel Sessions

Hermes supports multiple isolated conversation sessions within a single Telegram bot DM using forum-style topics. Each topic gets its own session ID, conversation history, context window, and model state — completely independent from other topics. This skill covers when to use `/new` (which replaces a topic's session) versus creating a new topic (which adds a parallel session), and how to operate the multi-session model effectively.

## When to Use

- User ran `/new` in a Telegram topic and wants to understand what happened
- User needs to run multiple parallel workstreams in the same bot DM
- Agent needs to explain why `/new` is the wrong choice for parallel work
- User asks how to create a separate conversation without losing the current one
- Agent is coordinating fleet work across multiple Telegram topics

## Prerequisites

- Hermes gateway running with Telegram platform configured
- BotFather Threads Settings enabled: **Threaded Mode** ON, **users creating topics** ON
- User has enabled **Topics** toggle in their DM with the bot (tap bot name → chat info → Topics)
- Multi-session mode activated via `/topic` command in root DM

## How to Run

All actions are performed through Telegram chat commands. The agent frames guidance to the user; no `terminal` or `write_file` calls are needed for the core workflow.

## Quick Reference

| Action | How | Effect |
|--------|-----|--------|
| Start fresh session in current topic | `/new` or `/reset` | Replaces the topic's session with a new ID — old history is gone from this topic |
| Create a parallel session | Tap **All Messages** → send any message | Telegram creates a new topic; Hermes assigns it a fresh isolated session |
| Enable multi-session mode | `/topic` in root DM | Activates user-driven topic mode; root DM becomes a system lobby |
| Check current topic binding | `/topic` inside a topic | Shows session title, ID, and binding status |
| Restore a previous session | `/topic <session-id>` inside a topic | Binds that topic to an existing Hermes session |
| Disable multi-session mode | `/topic off` in root DM | Clears all topic bindings; root DM reverts to normal chat |
| Skip confirmation on `/new` | `/new now` or `/new --yes` | Bypasses the destructive-command modal |

## Procedure

1. **Understand the isolation model.** Each Telegram topic maps to a session key: `agent:main:telegram:dm:{chat_id}:{thread_id}`. Messages in each topic have their own conversation history, memory flush, and context window. Topics are fully isolated — context does not leak between them.

2. **When the user runs `/new` inside a topic:**
   - Hermes creates a fresh session (new session ID, empty history) and rewrites the topic's binding row in `telegram_dm_topic_bindings` to point at the new session.
   - The **old session is not deleted** — it remains in the session store and can be restored later via `/topic <old-session-id>`.
   - The topic itself is **not renamed** (unless auto-rename is enabled and a new title is generated after the first exchange).
   - This is a **replacement**, not a parallel addition. The topic now has a different session, but there is still only one session in this topic.

3. **When the user wants parallel work (the correct approach):**
   - Instruct them to tap **All Messages** at the top of the bot DM interface in Telegram.
   - Send any message there — Telegram creates a new topic automatically.
   - Hermes responds inside that topic, which is now a standalone session.
   - Repeat for each parallel workstream. Each topic is an independent Hermes session.

4. **When the user should NOT use `/new`:**
   - If they want to keep the current session's context and start a *different* task → create a new topic instead.
   - If they want to run two things at once → `/new` will destroy the current topic's session binding and replace it; use "All Messages" to create separate topics.

5. **Restoring a previous session:**
   - Send `/topic` (no argument) in the root DM to list unlinked sessions.
   - Inside a topic, send `/topic <session-id>` to bind that topic to the old session.
   - Hermes replays the last assistant message for context.

## Pitfalls

- **`/new` is not parallel.** It replaces the session attached to the current topic. The old session still exists in the store but is no longer bound to this topic. If the user wanted parallel work, they should create a new topic via "All Messages" instead.
- **Root DM becomes a lobby.** After `/topic` is enabled, normal messages in the root DM are rejected with guidance to use "All Messages." System commands (`/status`, `/help`, `/sessions`, etc.) still work in the root.
- **BotFather prerequisites must be met.** If Threaded Mode or user-topic-creation is off, `/topic` will refuse activation and send a BotFather settings screenshot. These screenshots are rate-limited to one per 5 minutes.
- **`/new` confirmation modal.** In the CLI, `/new` triggers a destructive-command confirmation. In messaging, append `now`, `--yes`, or `-y` to skip (e.g., `/new --yes my-experiment`). Set `approvals.destructive_slash_confirm: false` in config.yaml to disable globally.
- **Topics created outside config are discovered automatically.** If a user creates a topic via Telegram directly (not through `extra.dm_topics` config), Hermes picks it up when a `forum_topic_created` service message arrives or on the next cache miss.
- **`extra.dm_topics` (config-driven) vs `/topic` (user-driven) can coexist.** Config-driven topics are operator-curated with fixed names and optional skill binding. User-driven topics are ad-hoc. Both use the same isolation key pattern.
- **Auto-rename may change topic names.** After the first exchange, Hermes renames the Telegram topic to match the generated session title. Set `extra.disable_topic_auto_rename: true` to preserve manual topic names.
- **Cron deliveries in topic mode.** Set `TELEGRAM_CRON_THREAD_ID=<topic_id>` to route cron results to a dedicated topic. Without this, cron messages land in the system lobby.

## Verification

Send `/topic` inside any Telegram topic in the bot DM. Hermes replies with the current topic's session title, session ID, and binding status — confirming the multi-session model is active and the topic has its own isolated session.