---
name: ephemeral-system-prompt
description: "Inject non-persisting system prompts via environment variables."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Configuration, Runtime, SystemPrompt]
---

# Ephemeral System Prompt

Use the `HERMES_EPHEMERAL_SYSTEM_PROMPT` environment variable to inject instructions into the agent's system prompt that are not persisted to conversation history. This is used for transient constraints, temporary personas, or runtime-specific overrides that should not pollute long-term memory or session logs.

## When to Use

- "Set a temporary persona for this specific run"
- "Inject transient operational constraints without modifying history"
- "Apply one-time behavior flags that shouldn't be recalled in future sessions"

## Prerequisites

- Access to the shell or environment configuration where the `hermes` binary is executed.

## How to Run

Set the environment variable before invoking the agent through the `terminal` tool.

## Quick Reference

- **Variable**: `HERMES_EPHEMERAL_SYSTEM_PROMPT`
- **Scope**: Process-level (ephemeral)

## Procedure

1. Define the transient instructions you wish to inject.
2. Export the variable in your current shell session:
   ```bash
   export HERMES_EPHEMERAL_SYSTEM_PROMPT="You are currently operating in [MODE]. Prioritize X over Y for this session."
   ```
3. Launch the Hermes agent as usual:
   ```bash
   hermes
   ```

## Pitfalls

- **Lack of Persistence**: Because these instructions never enter the history, they cannot be retrieved via `session_search` or memory tools after the process exits.
- **Process Bound**: The prompt is only active for the lifetime of the process started with that environment variable.

## Verification

Verify the behaviorally injected constraint by asking the agent to perform a task that conflicts with its default state but aligns with the ephemeral prompt.