---
name: stream-retry-tuning
description: "Tune HERMES_STREAM_RETRIES for mid-stream reconnect resilience."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Hermes, Streaming, Retry, Network, Reliability]
---

# Stream Retry Tuning

Control how many times Hermes silently reconnects when an LLM streaming response drops mid-flight due to a transient network error. `HERMES_STREAM_RETRIES` is an environment variable (read once per API call via `env_int`) that governs mid-stream reconnect attempts independently of the app-level `agent.api_max_retries` config key. The two operate at different layers: stream retries handle *connection drops during streaming*; api_max_retries handles *entire API call failures*.

## When to Use

- "Streaming responses keep dropping on flaky providers" — raise the retry count.
- "Slow provider stalls for minutes after /stop" — lower it to make interrupt faster.
- "OpenRouter sends 'Network connection lost' SSE errors" — this is the retry layer that catches them.
- "Tool call vanished when stream died mid-tool-use" — understand the mid-tool-call silent retry gate.
- Diagnosing whether a stream failure was retried or propagated immediately.

## Prerequisites

- Hermes Agent installed and running.
- Environment file at `~/.hermes/.env` (or profile-specific `~/.hermes/profiles/<name>/.env`).

## How to Run

Set the environment variable, then restart the session. Invoke through the `terminal` tool:

```bash
# Add to .env
echo 'HERMES_STREAM_RETRIES=5' >> ~/.hermes/.env

# Or export for a single CLI session
HERMES_STREAM_RETRIES=5 hermes
```

Then start a new session (`/reset` or relaunch). The value is read inside `_call()` at the start of each streaming API call via `env_int("HERMES_STREAM_RETRIES", 2)`.

## Quick Reference

| Env var | Code default | Docs default | Total attempts | Scope |
|---------|-------------|-------------|----------------|-------|
| `HERMES_STREAM_RETRIES` | 2 | 3 | value + 1 | Per streaming API call |

```
HERMES_STREAM_RETRIES=0   # no retry, single attempt
HERMES_STREAM_RETRIES=1   # 1 retry → 2 total attempts
HERMES_STREAM_RETRIES=2   # code default → 3 total attempts
HERMES_STREAM_RETRIES=5   # high tolerance → 6 total attempts
```

## Procedure

1. **Check current value** — invoke through the `terminal` tool:
   ```bash
   grep HERMES_STREAM_RETRIES ~/.hermes/.env 2>/dev/null || echo "not set (code default: 2)"
   ```

2. **Set the desired value** in `.env`:
   ```bash
   echo 'HERMES_STREAM_RETRIES=5' >> ~/.hermes/.env
   ```

3. **Restart the session** — the env var is read at call time, but `.env` is loaded at process start:
   - CLI: exit and relaunch `hermes`.
   - Gateway: `/restart` or `hermes gateway restart`.

4. **Verify** — in a new session, confirm the env var loaded:
   ```bash
   hermes config env-path  # confirm .env location
   grep HERMES_STREAM_RETRIES "$(hermes config env-path)"
   ```

## What Gets Retried

The retry loop (`for _stream_attempt in range(_max_stream_retries + 1)`) catches these transient errors:

- **httpx timeouts**: `ReadTimeout`, `ConnectTimeout`, `PoolTimeout`
- **httpx connection errors**: `ConnectError`, `RemoteProtocolError`, `ConnectionError`
- **SSE connection-loss errors**: `openai.APIError` with no `status_code` whose message contains phrases like "connection lost", "network error", "broken pipe", "upstream connect error", "peer closed", "connection reset", "connection terminated"
- **Provider stream parse errors**: detected via `agent._is_provider_stream_parse_error(e)`

### Two retry paths

1. **No tokens delivered yet** (`deltas_were_sent["yes"] == False`): silent retry with fresh connection. The stale httpx client is closed and rebuilt before each retry. A `_emit_stream_drop` diagnostic is logged.

2. **Tokens already delivered + tool call in-flight**: silent retry ONLY if the error is transient AND retries remain. The user sees a `⚠ Connection dropped mid tool-call; reconnecting…` marker, stream delivery tracking is reset, and the preamble is re-streamed. This prevents losing a tool call to a network blip.

3. **Tokens delivered, no tool call in-flight**: NO retry. The partial text is kept as the response stub (retrying would duplicate visible text). The error is logged and the call returns.

### What is NOT retried

- Non-transient errors (HTTP 4xx/5xx with status codes) propagate immediately.
- Errors after request cancellation (`_request_cancelled`) exit without retry — these are self-inflicted from `/stop`.
- Bedrock streaming-permission denied errors trigger a permanent flip to non-streaming mode.
- "stream not supported" errors trigger a permanent flip to non-streaming mode.

## Pitfalls

- **Docs say default 3, code says 2.** The docs/tips count *total attempts* (3 = 1 initial + 2 retries). The code default is `env_int("HERMES_STREAM_RETRIES", 2)` — 2 retries, 3 total attempts. Both are correct from their perspective; don't be confused by the mismatch.
- **Env var, not config.yaml.** Unlike `agent.api_max_retries` (config-level), this is an env var read via `os.getenv`/`env_int`. Set it in `.env`, not `config.yaml`.
- **Separate from SDK-level retries.** The OpenAI SDK has its own internal retry (default `max_retries=2`). `HERMES_STREAM_RETRIES` wraps the streaming call including SDK retries.
- **Separate from `agent.api_max_retries`.** That config key retries the *entire* API call (including non-streaming). `HERMES_STREAM_RETRIES` retries only *mid-stream connection drops* during a single streaming response.
- **High values stall `/stop`.** Each retry on a slow provider (e.g. Ollama Cloud) can block for the full stream-read timeout (120s+). Setting `HERMES_STREAM_RETRIES=5` means `/stop` could wait up to 6×120s = 12 minutes before the interrupt takes effect. The code checks `_interrupt_requested` before each retry attempt, but the current attempt must still time out.
- **Invalid values silently fall back to 2.** `env_int` catches `ValueError`/`TypeError` and returns the default (2). A typo like `HERMES_STREAM_RETRIES=high` silently means 2 retries, not an error.
- **`HERMES_STREAM_RETRIES=0` disables all stream retry.** Used in tests to force immediate propagation. The initial attempt still runs, but no retries on failure.

## Verification

```bash
grep HERMES_STREAM_RETRIES ~/.hermes/.env
```

Should show your configured value. For runtime confirmation, check logs after a stream drop — the `_emit_stream_drop` diagnostic logs the attempt number and max attempts (e.g. "attempt 2/3").