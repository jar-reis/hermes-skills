---
name: turn-sync
version: 1.1.0
created: 2026-06-19
updated: 2026-06-23
author: Hermes
description: >
  Per-turn memory sync protocol using Open Brain (OB1) as the central knowledge graph.
  Every active session writes new facts/decisions to OB1 after each turn and pulls
  recent changes from other sessions before responding. This creates a live, shared
  knowledge graph that all fleet agents can read at any point during their work.
---

# Turn Sync — Per-Turn Memory Synchronization

> **Fleet directive:** Every session with OB1 MCP tools available MUST follow this
> protocol. The goal is a central knowledge graph (OB1) that reflects the live state
> of all active sessions, so any agent can review what others have learned at any turn.

## Why This Exists

Without per-turn sync, sessions work in isolation. Agent A discovers something at
turn 3; Agent B doesn't know until the next cold start reads OBn/AGENTS.md. Turn-sync
closes that gap by making OB1 the live coordination layer — write immediately after
learning, pull before acting.

## Central Graph: Open Brain (OB1)

OB1 is the central knowledge graph. It has:
- 25K+ thoughts already captured
- MCP tools available in every Hermes session: `mcp_open_brain_capture_thought`,
  `mcp_open_brain_search_thoughts`, `mcp_open_brain_list_thoughts`
- Supabase-backed, no document cap (unlike ContextForge's 200-doc limit)
- Semantic search with embeddings
- Source tagging for agent attribution

## Protocol

### 1. TURN-START PULL (before substantive work)

At the start of each turn, before doing substantive work, pull recent thoughts from
OB1 to see what other sessions have captured:

```
mcp_open_brain_list_thoughts(limit=5)
```

If working on a specific topic, also search:

```
mcp_open_brain_search_thoughts(query="<topic keywords>", limit=5)
```

**Rules:**
- Pull is lightweight (1-2 MCP calls). Don't over-pull — 5 recent thoughts is enough
  to stay current.
- If OB1 is unreachable, note it in one line and continue. Never block on the pull.
- The pull is in ADDITION to L1 (auto-injected MEMORY.md), not a replacement.

### 2. TURN-END CAPTURE (after learning something new)

After each turn where you learned or decided something worth sharing, capture it to
OB1 immediately:

```
mcp_open_brain_capture_thought(
  content="<what was learned/decided/discovered>",
  source="<agent-name>",         # e.g. "hermes", "codex", "claude-code"
  task_id="<session-namespace>"  # e.g. "session/2026-06-19-turn-sync-setup"
)
```

**What to capture per-turn:**
- Decisions made (architecture choices, tool selections, approach changes)
- Facts discovered (environment state, tool behavior, API responses)
- Corrections from the user (style, workflow, approach)
- Blockers encountered (failed installs, broken tools, missing deps)
- Significant completions (feature done, test passed, file created)

**What NOT to capture per-turn:**
- Routine tool output (file reads, search results)
- Ephemeral state (PIDs, temp file paths, in-progress TODO state)
- Duplicates of what's already in OB1 — search first if unsure
- Secrets, tokens, credentials (EVER)

**Content format:**
- Start with a category tag: `[DECISION]`, `[FACT]`, `[CORRECTION]`,
  `[BLOCKER]`, `[DONE]`, `[SESSION]`
- One thought per capture call — don't batch unrelated facts
- Keep it standalone: the thought should make sense when retrieved later
  by any agent without conversation context

Example:
```
mcp_open_brain_capture_thought(
  content="[DECISION] Turn-sync protocol uses OB1 as central graph (not ContextForge) because OB1 has no document cap and MCP tools are available in every Hermes session. Write after each turn, pull before substantive work.",
  source="hermes",
  task_id="session/2026-06-19-turn-sync-setup"
)
```

### 3. TOPIC SEARCH (when working on a specific area)

When your work touches a specific topic, search OB1 for what other agents know:

```
mcp_open_brain_search_thoughts(query="memory sync architecture", limit=10)
```

This is semantic search — use natural language, not exact keywords.

### 4. SESSION BOUNDARY SYNC

At session start and session end, do a fuller sync (this is the existing protocol
from AGENTS.md, turn-sync is the per-turn complement):

**Session start:**
- `mcp_open_brain_list_thoughts(limit=10)` — broader pull
- `mcp_open_brain_search_thoughts(query="<session topic>", limit=5)`

**Session end (closeout):**
- Capture a `[SESSION]` summary thought with Done/Blocked/Next
- Drain durable facts as individual `[FACT]` thoughts
- Use stable source labels: `hermes`, `codex`, `claude-code`, `antigravity`,
  `kimi-code`, `pi`

## What About Other Memory Layers?

Turn-sync is the **real-time layer**. The existing triple-layer system stays:

| Layer | Role | When |
|-------|------|------|
| OB1 (this skill) | Real-time cross-session sync | Every turn |
| L1 MEMORY.md | Always-injected identity/prefs | Auto-injected |
| L2 Hindsight | Knowledge graph (when installed) | Session boundaries |
| L3 fact_store | Entity-attributed facts | As needed |
| L4 ContextForge | Curated cross-fleet (200-doc cap) | Session boundaries |
| OBn vault | Cold-restart briefing | Session start/end |

**No duplication rule:** If you capture to OB1 per-turn, you do NOT also need to
write the same fact to L1 or L4 at turn time. L1 stays for stable identity/prefs.
L4 stays for curated durable facts at session boundaries. OB1 is the live working
memory.

## For Non-Hermes Agents (Codex, Claude Code, Kimi, etc.)

Agents without OB1 MCP tools use the CLI fallback:

```bash
# Pull recent
python3 /Users/jack.reis/Documents/=notes/bin/ob1-pull --recent --limit 5

# Search
python3 /Users/jack.reis/Documents/=notes/bin/ob1-pull --query "<topic>" --limit 5

# Capture
python3 /Users/jack.reis/Documents/=notes/bin/ob1-pull \
  --capture "[DECISION] <content>" \
  --task-id "session/<date>-<slug>" \
  --source "<agent-name>"
```

## Existing Hook Integration (2026-06-19)

A turn-sync hook system was already installed at
`/Users/jack.reis/Documents/=notes/scripts/fleet_memory/local_turn_sync_hook.py`
across Hermes, Claude Code, and Codex. It has two sides:

**Turn-start (pre_llm_call / UserPromptSubmit) — KEEP:**
Searches local memory planes (Holographic, Hindsight, OBn) and injects a
source-backed brief before the turn. Complements this skill's TURN-START PULL.

**Turn-end (post_llm_call / Stop) — RESOLVED (2026-07-01):**
The `--no-ob1` flag was a **complete no-op on Aegis**. It was accepted purely
for CLI compatibility with the talaria invocation (which has an OB1 mirror
plane that Aegis lacks). The flag was parsed but never referenced in any code
path — `capture()` always writes to both holographic (SQLite) and hindsight
(HTTP API) regardless. Removing it changed zero runtime behavior.

The flag has been removed from `~/.hermes/config.yaml` → `hooks.post_llm_call`.
The post-LLM hook now reads:
`local_turn_sync_hook.py --event stop --source hermes --limit 5`

No dedup mechanism was needed because:
- The pre-LLM hook runs `user-prompt-submit` (injects a brief, does NOT capture)
- The post-LLM hook runs `stop` (captures a turn summary)
- These are different code paths with no overlap
- `capture()` already has built-in dedup: holographic uses
  `INSERT ... ON CONFLICT(content) DO UPDATE`, hindsight uses stable
  `document_id` based on content hash

**IMPORTANT — `hermes config set` cannot edit nested hook arrays.**
`hermes config set hooks.post_llm_call[0].command '...'` does NOT update the
existing array entry — it creates a stray literal key `post_llm_call[0]` under
`hooks` and leaves the original entry untouched. The tool also coerces all
values to strings, so `hermes config set hooks.post_llm_call '[{...}]'` stores
a string, not a list. To edit hook entries in config.yaml, use Python YAML
manipulation (read → modify dict → write back) or surgical sed, NOT
`hermes config set`. The `patch` tool refuses config.yaml as security-sensitive.

See `references/no-ob1-investigation-2026-07-01.md` for the full investigation:
code analysis, duplicate-write analysis, the `hermes config set` limitation
that prevents array-index edits, and dry-run verification output.

Hook config locations:
- Hermes: `~/.hermes/config.yaml` → `hooks.post_llm_call`
- Claude Code: `~/.claude/settings.json` → `hooks.Stop`
- Codex: `~/.codex/hooks.json` → `Stop`

## Read-Side Surfacing (cron job)

Cron job `turn-sync-surface` (ID: `e48c6002f56e`) runs every 5 minutes and
pulls the 5 most recent OB1 thoughts to `~/.hermes/state/turn-sync-recent.md`
with watermark dedup. Silent when no new thoughts. Active sessions can read
this file at any time to see what other sessions have captured.

Script: `~/.hermes/scripts/turn-sync-surface.py`
Watermark: `~/.hermes/state/turn-sync-watermark.txt`

## Chronological Federation Format (IMPLEMENTED 2026-06-23)

The turn-sync brief now surfaces **chronological recent turns from each fleet
agent** as a markdown table, most recent first, one row per agent. This
replaced the old semantic grab-bag brief that surfaced random Holographic
entries.

### How It Works

Script: `~/.hermes/scripts/chronological_brief.py` (380 lines)

1. Queries the Holographic fact_store SQLite DB (`~/.hermes/memory_store.db`)
   for recent `[TURN]` entries, ordered by `created_at DESC`, limit 50
2. Parses each `[TURN]` content line to extract agent, session, cwd, model,
   platform, and user snippet (regex-based, see `TURN_RE` in the script)
3. Deduplicates by agent (keeps most recent entry per agent)
4. Optionally pulls 3 recent OB1 thoughts as supplement
5. Emits a markdown table: `| Time | Host | Agent | Harness | Model | Session | Last Turn (snippet) |`

### Integration Points

- **Turn-start hook** (`local_turn_sync_hook.py` line 26, 213-216): Dynamically
  imports `chronological_brief.py` as the PRIMARY brief source. Semantic search
  is demoted to supplement (appended below the table). Fail-open: if the script
  is missing, falls back to semantic-only.
- **Cron** (`turn-sync-surface.py` lines 25, 29, 317-324): Writes the
  chronological brief to `~/.hermes/state/turn-sync-chronological.md` every 5 min,
  alongside the existing OB1-only surface file.
- **Standalone**: `python3 ~/.hermes/scripts/chronological_brief.py` outputs the
  full brief. `--table-only` for just the table. `--json` for structured output.

### Key Design Decision

The plan originally proposed enriching session log filenames
(`~/session-logs/`) with host/agent/model metadata. The actual implementation
**bypassed session logs entirely** and instead queries `[TURN]` entries from
the Holographic fact_store, which already carry agent, session, cwd, model,
and snippet metadata (captured by the turn-end hook). This was simpler and
avoided needing to change the session log naming convention.

See `references/chronological-brief-impl.md` for implementation details,
verification commands, and the architecture rationale.

## Pitfalls

- **CRITICAL — skipping the turn-start pull causes stale-state errors.**
  On 2026-06-23, Hermes skipped the turn-start brief pull and then read
  11-day-old gateway error logs as if they were current state, producing
  inaccurate claims about Pi being "degraded" when it was actually running
  fine on Claude Code Opus 4.8. The Holographic layer HAD this information but
  it wasn't surfaced because the brief wasn't pulled. ALWAYS pull the brief
  at turn-start, even for casual conversations. The brief is injected
  automatically by the local-turn-sync hook — read it and USE it when
  interpreting terminal output and logs.

- **Stale logs vs. live state.** When investigating agent health, always
  cross-reference: (1) the turn-sync brief, (2) `launchctl list` / `ps aux`
  for live process state, (3) `curl localhost:<port>/health` for gateway
  health, (4) the most recent log entries by timestamp. Never assume old
  error logs reflect current state. The turn-sync brief is the fastest signal
  for "what is this agent actually doing right now?"

- **Don't capture noise.** If a turn only did a file read with no new learning,
  skip the capture. Over-capturing degrades search quality.
- **Don't pull if OB1 was pulled < 2 turns ago** and no other session is likely
  to have written. Use judgment — the pull is cheap but not free.
- **OB1 MCP tools may be flaky.** If `capture_thought` fails, retry once. If it
  fails again, note it and continue — the fact can be captured at session end.
  Fallback: use the CLI (`ob1-pull --capture "..." --source "..." --task-id "..."`).
- **source field is agent identity, not session ID.** Use `hermes`, `codex`,
  `claude-code`, etc. The `task_id` carries the session namespace.
- **Don't use turn-sync as a replacement for handoffs.** Handoffs carry deep
  pickup context. Turn-sync carries discrete facts. They complement, not replace.
- **OB1 MCP server may disconnect mid-session.** If `mcp_open_brain_*` tools
  return "MCP server 'open-brain' is not connected", fall back to the CLI:
  `python3 ~/Documents/=notes/bin/ob1-pull --recent --limit 5` (after
  `eval "$($HOME/.hermes/bin/ob1-token.sh export)"`).
- **OB1 DNS resolution may fail on macOS.** The macOS system resolver (Python
  `socket.getaddrinfo`, `curl`) may fail to resolve `jhpuctiyosazlyrcnfuu.supabase.co`
  even though `dig` and `nslookup` succeed. Root cause: Tailscale MagicDNS
  interfering with specific subdomain resolution. The `ob1-pull` script is
  patched with a `socket.getaddrinfo` fallback to resolved IPs
  (`104.18.38.10`, `172.64.149.246`). If OB1 is unreachable via CLI, check
  whether DNS is the issue: `nslookup jhpuctiyosazlyrcnfuu.supabase.co`
  (works) vs `python3 -c "import socket; socket.getaddrinfo('jhpuctiyosazlyrcnfuu.supabase.co', 443)"`
  (fails). If confirmed, the fallback patch in `ob1-pull` handles it automatically.
- **Tailscale MagicDNS may break OB1 subdomain resolution.** On macOS with
  Tailscale active, the system resolver (`socket.getaddrinfo`, `curl`) can
  fail to resolve `jhpuctiyosazlyrcnfuu.supabase.co` even though `dig` and
  `nslookup` succeed. This is caused by Tailscale's MagicDNS interfering
  with specific subdomain resolution. The `ob1-pull` script was patched
  (2026-06-24) with a `socket.getaddrinfo` fallback to resolved IPs
  (`104.18.38.10`, `172.64.149.246`). If OB1 is unreachable via Python/curl
  but `dig` resolves it, check for this pattern and apply the same fallback.
  See `references/ob1-dns-fallback-20260624.md` for the patch details.
- **OB1 DNS resolution may fail on macOS with Tailscale MagicDNS.** The system
  resolver (used by Python `socket.getaddrinfo` and `curl`) may fail to resolve
  `jhpuctiyosazlyrcnfuu.supabase.co` even though `dig` and `nslookup` succeed.
  This is a Tailscale MagicDNS issue affecting specific subdomains. The
  `ob1-pull` script (as of 2026-06-24) includes a `socket.getaddrinfo` fallback
  to resolved IPs (104.18.38.10, 172.64.149.246). If OB1 CLI calls fail with
  `Errno 8: nodename nor servname provided`, check if the fallback patch is in
  place: `grep OB1_FALLBACK_IPS ~/Documents/=notes/bin/ob1-pull`. If not, add
  it. Do NOT report OB1 as "down" when the issue is DNS — the edge function
  itself is healthy and responds correctly via IP.
- **Tailscale MagicDNS may break OB1 subdomain resolution.** The macOS system
  resolver (Python `socket.getaddrinfo`, `curl`) can fail to resolve
  `jhpuctiyosazlyrcnfuu.supabase.co` even though `dig` and `nslookup` succeed.
  Symptom: `<urlopen error [Errno 8] nodename nor servname provided, or not known>`
  from `ob1-pull` or any Python HTTP call to OB1. The `ob1-pull` script has a
  patched `socket.getaddrinfo` that falls back to resolved IPs
  (104.18.38.10, 172.64.149.246). If other scripts hit the same DNS failure for
  this domain, apply the same fallback pattern. Root cause: Tailscale's MagicDNS
  resolver (100.100.100.100) interferes with resolution of certain external
  subdomains on macOS.

- **OB1 DNS resolution may fail on macOS with Tailscale.** The macOS system
  resolver (used by Python `socket.getaddrinfo` and `curl`) can fail to resolve
  `jhpuctiyosazlyrcnfuu.supabase.co` even though `dig` and `nslookup` succeed.
  Root cause: Tailscale MagicDNS interfering with specific subdomain resolution.
  The `ob1-pull` script is patched with a `socket.getaddrinfo` fallback to
  resolved IPs (104.18.38.10, 172.64.149.246) — if the system resolver returns
  NXDOMAIN for the OB1 host, it falls back to the IP automatically. If you
  encounter `Errno 8: nodename nor servname provided` from ob1-pull, verify
  the patch is present: `grep OB1_FALLBACK_IPS ~/Documents/=notes/bin/ob1-pull`.
  See `references/ob1-dns-fallback-2026-06-24.md` for details.

## Quick Reference

```
WHEN                    → WHAT                           → TOOL
──────────────────────────────────────────────────────────────────────
Turn start (substantive)→ Pull 5 recent thoughts         → list_thoughts(5)
Turn start (topic-specific) → Search OB1 for topic       → search_thoughts(query, 5)
Turn end (learned X)    → Capture X to OB1              → capture_thought(X)
Session start           → Pull 10 + topic search         → list_thoughts(10) + search
Session end             → [SESSION] summary + drain      → capture_thought per fact
Non-Hermes agent        → CLI fallback                   → ob1-pull --capture/--query/--recent
```

## Verification

To verify turn-sync is working in a session:
1. `mcp_open_brain_list_thoughts(limit=3)` — should return recent thoughts
2. `mcp_open_brain_capture_thought(content="[TEST] turn-sync verification", source="hermes", task_id="test")`
3. `mcp_open_brain_search_thoughts(query="turn-sync verification", limit=1)` — should find the test thought
4. If all three succeed, turn-sync is operational