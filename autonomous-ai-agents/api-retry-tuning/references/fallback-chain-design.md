# Fallback Chain Design — Analysis & Aegis Configuration

## Fable 5 Analysis (2026-07-08)

Consulted via Claude Code CLI (`claude -p --model claude-fable-5`) on designing
a post-Gemma last-resort fallback for a Mac Mini M4 Pro / 64GB RAM fleet worker.

### The core problem

Aegis worker profile chain (as of 2026-07-08):

| Rung | Provider | Model | Endpoint |
|------|----------|-------|----------|
| Primary | ollama-cloud (custom proxy) | glm-5.2 | `127.0.0.1:11434/v1` |
| Fallback 1 | openai-codex | codex-5.3-spark | ChatGPT backend |
| Fallback 2 | mistral | mistral-large-latest | `api.mistral.ai/v1` |
| Fallback 3 | custom:www.ollama.com | glm-5.2 | `www.ollama.com/v1` |
| Fallback 4 | ollama-launch | gemma4:31b | `127.0.0.1:11434/v1` |

**Failure mode:** gemma4:31b is 31GB and competes with other GPU processes.
During VRAM locks the Ollama API becomes unreachable — hanging connections
rather than refusing them. When this happens, both the primary (local proxy)
and fallback 4 die simultaneously since they share `127.0.0.1:11434`.

### Fable 5's key insight

> Your failure mode is "the Ollama **API becomes unreachable**" during VRAM
> locks — that's a server/process-level failure, not a model-size failure.
> `qwen2.5:7b` behind the same `127.0.0.1:11434` dies with it. Same failure
> domain = not a fallback.

### Recommended additions

**Fallback 5: Diverse cloud provider (Groq or OpenRouter)**

- Different infra from everything already in the chain.
- OpenAI-compatible `/v1` endpoint — drop-in for Hermes' adapter.
- Groq: fastest first-token latency, free tier, 128k+ context on Llama 3.3 70B.
- OpenRouter: widest model selection, pennies per call, can route to anything.
- DeepSeek is a fine alternative on cost but has had more availability wobbles.
- HF Inference Endpoints are the WORST fit: cold starts (10s–min) or always-on
  hourly bill — wrong trade for a rarely-used last resort.

**Fallback 6 (optional, offline survival only): Small local model on SEPARATE runtime**

- Must be a separate process on a separate port: `llama-server` (llama.cpp)
  or an MLX server, NOT Ollama.
- ~7B Q4 model (~4.5GB) loads even under memory pressure on 64GB unified memory.
- `qwen2.5:7b` is a reasonable choice of weights.
- Skip entirely if "no internet" isn't a scenario you care about.

### Config note

Set aggressive connect timeout (1–2s) on the Gemma rung. VRAM-locked Ollama
hangs rather than refusing connections — without a tight timeout the chain
stalls 60s on a dead rung before reaching the next provider.

## Aegis Current Config (Worker Profile)

- `api_max_retries`: 3 (default)
- Mistral API key: present in `.env`
- OpenRouter: config block exists but `api_key: ''` — no `OPENROUTER_API_KEY` env var
- OpenRouter is already used for `AUXILIARY_VISION_PROVIDER` in the default profile

## Decision (pending user action)

Two options discussed with Jack:

1. **OpenRouter** — add credits + API key, route to a cheap fast model as FB 5.
2. **Mistral free tier** — add a second Mistral model (e.g. `open-mistral-7b`)
   as FB 5/6. Already have the key. Different model avoids rate-limit sharing
   with fallback 2.

Jack's response: "Could fall back to hugging face or a small qwen or something"
→ then asked for Fable 5's recommendation → then suggested OpenRouter credits
or Mistral free plan as alternatives.

**Outcome:** Awaiting user decision on which provider(s) to add. The config
edits are ready to implement once a choice is made and credentials are provided.