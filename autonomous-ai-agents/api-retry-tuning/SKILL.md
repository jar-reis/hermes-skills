---
name: api-retry-tuning
description: "Tune agent.api_max_retries for fast fallback or resilience."
version: 0.2.0
author: Hermes
metadata:
  hermes:
    tags: [Hermes, Configuration, Reliability, Fallback, Retry]
---

# API Retry Tuning

Control how many times Hermes retries a failed LLM API call before surfacing the error or falling back to the next provider. The `agent.api_max_retries` config key (default **3**) wraps each model API call in the conversation loop. Lowering it makes fallback chains activate faster on flaky primaries; raising it tolerates longer provider hiccups on a single-provider setup.

This is a **config-level** tuning knob — no code changes, no env vars, just `config.yaml`.

## When to Use

- "Lower it for fast fallback" — you have a fallback chain and the primary provider is flaky.
- Provider frequently returns 429/timeout and you want to switch to fallback sooner.
- Single-provider setup hitting transient errors — raise the value for more tolerance.
- Debugging retry behavior — set to 1 to see raw errors without retry noise.

## Prerequisites

- Hermes Agent installed and running (`hermes --version`).
- Config file at `~/.hermes/config.yaml` (or profile-specific `~/.hermes/profiles/<name>/config.yaml`).

## How to Run

Invoke through the `terminal` tool:

```bash
hermes config set agent.api_max_retries <value>
```

Then start a new session (`/reset` in chat, or relaunch the CLI/gateway).

## Quick Reference

| Key | Section | Default | Clamp | Config path |
|-----|---------|---------|-------|-------------|
| `api_max_retries` | `agent` | 3 | min 1 | `config.yaml` |

```
hermes config set agent.api_max_retries 1   # no retry, single attempt
hermes config set agent.api_max_retries 2   # one retry (Aegis default-profile uses this)
hermes config set agent.api_max_retries 3   # default
hermes config set agent.api_max_retries 5   # high tolerance
```

## Procedure

1. **Check current value** — invoke through the `terminal` tool:
   ```bash
   hermes config | grep api_max_retries
   ```
   Or use `read_file` on your config.yaml and look for the `agent:` → `api_max_retries:` key.

2. **Set the desired value:**
   ```bash
   hermes config set agent.api_max_retries <N>
   ```

3. **Restart the session** — the value is read at agent init time (`agent_init.py`), not hot-reloadable:
   - CLI: exit and relaunch `hermes`.
   - Gateway: `/restart` or `hermes gateway restart`.

4. **Verify** — in a new session, the agent's `_api_max_retries` attribute reflects the new value.

## Fallback Chain Design

`api_max_retries` controls retry *within* a single provider. The `fallback_providers` list in `config.yaml` controls what happens when all retries are exhausted. Good chain design matters as much as the retry count.

### Failure domain awareness

The most important principle: **providers sharing infrastructure share a failure domain.** A local Ollama instance serving both the primary (via proxy) and a fallback model is ONE failure domain — when Ollama locks (VRAM contention, daemon crash), both rungs die simultaneously.

Rules:
- Each fallback rung should be on **different infrastructure** from all prior rungs.
- A small local model (e.g. `qwen2.5:7b`) behind the **same Ollama port** as a large local model is NOT a real fallback — the failure mode is "API unreachable," not "model too big."
- Cloud providers on different platforms (Ollama Cloud, OpenAI, Mistral, OpenRouter, Groq) are genuinely independent failure domains.
- A local model on a **separate runtime** (llama-server on a different port, MLX server) IS a real fallback — different process, different failure mode.

### Chain ordering

1. Primary (your preferred model/provider).
2. Cloud fallbacks on distinct providers (different companies, different infra).
3. Local heavy model (free, but shared failure domain with primary if same Ollama).
4. Cloud last-resort on a provider not yet in the chain (e.g. OpenRouter, Groq free tier, Mistral free tier with a different model).
5. (Optional) Local lightweight model on a **separate runtime** — only if offline survival matters.

### Post-local cloud last-resort options

| Option | Pros | Cons |
|--------|------|------|
| OpenRouter | Widest model selection, pennies per call, OpenAI-compatible API | Needs credits + API key |
| Groq | Fastest TTFT, free tier, OpenAI-compatible | Limited model selection |
| Mistral free tier | Already have key in many setups, different model avoids rate-limit sharing | Smaller model selection |
| HuggingFace Endpoints | Flexible | Cold-start delay (10s–min), or always-on hourly bill — wrong for rarely-used last resort |
| Small local model (separate runtime) | Works offline | Operational overhead, another daemon to maintain |

See `references/fallback-chain-design.md` for the full Fable 5 analysis and Aegis-specific chain configuration.

## Pitfalls

- **Not hot-reloadable.** The value is snapshotted at `AIAgent.__init__` time. Changing config mid-session has no effect — always restart.
- **Clamped to minimum 1.** Setting `0` or negative values clamps to `1` (single attempt, no retry). The `while retry_count < max_retries` loop guard requires at least 1.
- **Invalid values fall back to 3.** Non-integer values (e.g. `"not-a-number"`) silently fall back to the default of 3, not an error.
- **This is app-level retry, not SDK-level.** The OpenAI SDK has its own internal retry (default `max_retries=2`) for transient network errors. `api_max_retries` is the Hermes-level loop that wraps the *entire* call including SDK retries. Total attempts on a flaky call ≈ `api_max_retries × (SDK max_retries + 1)`.
- **Lowering burns fewer tokens on deterministic refusals.** Content-policy blocks (HTTP 400) are deterministic — retrying just wastes paid calls. A lower value avoids burning `api_max_retries` attempts on a refusal that will never succeed.
- **HTTP 402 is not retried.** Payment-required responses skip the retry loop and fall back immediately.
- **Local Ollama VRAM locks hang rather than refuse.** A VRAM-locked Ollama instance (e.g. gemma4:31b competing with other GPU processes on 64GB unified memory) often hangs the connection rather than returning an error. Set aggressive timeouts on local fallback rungs (1–2s connect) so the chain doesn't stall 60s on a dead rung before reaching the next cloud provider.
- **Same-port local models are not real fallbacks.** Adding `qwen2.5:7b` as a fallback behind the same `127.0.0.1:11434` as `gemma4:31b` provides zero protection — when Ollama is unreachable, both models are unreachable. Use a separate runtime (llama-server on a different port) or a cloud provider instead.

## Verification

```bash
hermes config | grep api_max_retries
```

Should show your configured value. For runtime confirmation, start a new session and check the agent attribute is set — the value is logged at debug level during agent initialization.