---
name: memory-sop-drain
version: 1.1.0
created: 2026-06-03
updated: 2026-06-03
author: Hermes
description: >
  Session-end ritual for the L2 Hindsight layer. Drains durable
  session facts into the Hermes bank so they survive the L1 budget
  cull and become semantically searchable. Pairs with memory-sop-audit
  and the standard session-end ritual in AGENTS.md.
---

# Memory SOP — L2 Session-End Drain

## When to use

- End of any non-trivial session (per AGENTS.md §Session Shutdown,
  between commit/push/ledger/daily-note and stop).
- Whenever a durable fact emerged that L1 shouldn't carry (commit
  SHA, file path, run-state, JAC completion summary) but L2 should.
- After the agent learns something about the user, environment, or
  fleet that's worth keeping for 7+ days.

## Hard requirement: Hindsight retain is ALWAYS async

Hindsight runs LLM extraction on every retained item, which takes
**10-30 seconds per fact**. The HTTP request has a 30-second timeout.

  - **Always POST with `async: true`.** Sync mode (`async: false`)
    will time out and silently lose the fact.
  - The POST returns HTTP 200 immediately. The actual extraction
    and embedding happen in the background.
  - Verify a fact landed by waiting 3-5 seconds after the POST,
    then running a `recall` against a unique marker from the
    fact's `document_id`.

`memory-drain.sh` enforces this — it builds the JSON with
`async: true` and tags items as `["drain", "session-end"]` for
visibility scoping. Do not bypass the script with a raw curl unless
you know the API contract.

### Quick command

```
L2_URL=http://localhost:9177 ~/.hermes/bin/memory-drain.sh hermes "Fact 1" "Fact 2" ...
echo "Long fact" | L2_URL=http://localhost:9177 ~/.hermes/bin/memory-drain.sh hermes -
```

**Port note (updated 2026-07-05):** The `hindsight` daemon on Aegis runs on port **8888** (verified live 2026-07-05). The previous note referencing port 9177 was stale — 9177 is down, 8888 returns `{"status":"healthy","database":"connected"}`. All drain scripts and health checks should target 8888. Always verify with `curl -s http://localhost:8888/health` before draining. If 8888 is down, check 9177 as a fallback (the daemon may have been rebuilt on a different port).

**Doc-ID note (2026-06-19):** The local script should pipe facts into Python as `... | DRAIN_DOC_ID="$doc_id" python3 -c ...`. If raw recall shows only `document_id: drain-0` / `drain-1` despite the script printing a timestamped `doc_id prefix`, patch the script to export `DRAIN_DOC_ID` into the Python process before relying on the printed IDs.

**Doc-ID note (2026-06-19):** The local script should pipe facts into Python as `... | DRAIN_DOC_ID="$doc_id" python3 -c ...`. If raw recall shows only `document_id: drain-0` / `drain-1` despite the script printing a timestamped `doc_id prefix`, patch the script to export `DRAIN_DOC_ID` into the Python process before relying on the printed IDs.

## What the script does

1. Pre-flights `Hindsight /health` — aborts with exit 2 if daemon is down.
2. Builds a `RetainRequest` JSON body with one `MemoryItem` per fact,
   tagged `["drain", "session-end"]` for visibility scoping.
3. POSTs to `${L2}/v1/default/banks/${BANK}/memories` with
   `async: true` — returns immediately, ingest happens in background.
4. Reports HTTP status and a `drain-YYYYMMDDTHHMMSSZ-$$` doc_id
   prefix so the items are findable later.

## When NOT to use

- For ephemeral operational state (PIDs, ports, current time).
  Belongs in a daily note.
- For facts that belong in L1 because every turn needs them.
  Edit `~/.hermes/memories/MEMORY.md` directly.
- For things that have an L3 fact (entity-attributed). Use
  `fact_store(action='add', ...)` instead.

## Verify the drain landed

```
~/.hermes/bin/memory-demo.sh recall "your marker"
```

**Pitfall**: If the script fails with `(parse error) Expecting value: line 1 column 1 (char 0)`, it means the Hindsight daemon returned non-JSON text (e.g., HTTP 500 or network errors). The script uses Python's `json.loads()` on raw daemon output, which is fragile. **Workaround**: Use direct `curl` + `jq` for verification:

```bash
curl -s http://localhost:9177/v1/default/banks/hermes/memories/recall \
  -H 'content-type: application/json' \
  -d '{"query":"drain-20260620T0044", "budget":"low"}' | jq .
```

See `references/hindsight-async-drain-verification-20260620.md` for details.

Or wait ~5s and run:

```
curl -s http://localhost:9177/v1/default/banks/hermes/memories/recall \
  -H 'content-type: application/json' \
  -d '{"query":"<your marker>","budget":"low"}' | python3 -m json.tool | head -30
```

## Pair with cron (silent background drain)

For unattended long-running processes, drop the `memory-drain.sh`
call into a wrapper. For periodic fleet-wide ingestion, schedule
via `cronjob(action='create')` with `deliver='local'`. The script
exits 2 on daemon-down, which cron can route to alerts.

The standard pattern on this profile is a queue directory:

```
~/.hermes/memory-drain-queue/<ticket-or-session-id>.txt   # one fact per file
```

The `memory-drain-cron.py` wrapper (in `~/.hermes/scripts/`) is
scheduled as `memory-drain-daily` (Daily 6 PM, 365 days). It
consumes the queue, retains each file's content to L2, and moves
the file to `.drained/`. Silent on empty queue.

**Important:** the cron scheduler rejects symlinks and `bin/`
traversal paths. The actual `memory-drain.sh` lives in
`~/.hermes/bin/`, but the cron wrapper must live in
`~/.hermes/scripts/`. See `note-taking/memory-sop-audit` for the
full pattern.

## LLM extraction timing

  - Extraction latency: 10-30s per item, depending on the LLM
    provider's cold-start state. First drain of the day is
    typically the slowest.
  - Provider on this profile: `ollama-cloud` / `kimi-k2.6:cloud`.
    If you see extraction timeouts > 30s, check the provider
    status first; switch to `cerebras` or `openai` as fallback.
  - Recall latency: 1-3s for typical queries, longer for `reflect`
    (synthesizes across memories). Set `budget=low` for sub-second
    response, `budget=mid` for default, `budget=high` for
    comprehensive synthesis.

## Pitfalls

- **Drain cron runs "ok" but Hindsight stays stale — empty queue.** The
  `memory-drain-daily` cron (eb438b36c7be) processes the drain queue directory
  (`~/.hermes/memory-drain-queue/`) and reports `ok` when done. But if
  interactive sessions never run `memory-drain.sh` at session end, the queue
  stays empty and Hindsight receives zero new documents. **Symptom**: cron
  list shows `ok`, `/health` shows `healthy`, but `last_document_at` is >48h
  old. **Diagnosis**: check `ls ~/.hermes/memory-drain-queue/` — if empty,
  interactive sessions are not draining. **Fix**: run `memory-drain.sh`
  manually, or add it to the session-close ritual. This is a root-cause
  issue, not a cron failure — the cron is correctly processing an empty
  queue.

  Observed 2026-06-23: Hindsight `last_document_at` was 2026-06-20T22:51
  (3 days stale) despite drain cron running daily and reporting `ok`. The
  queue was empty because no interactive session had run the drain script.

- **Hindsight port (updated 2026-06-24).** The `hindsight-embed` daemon runs on port **9177** (changed from 9876). All
  drain scripts must default to 9177. The health check endpoint is
  `http://127.0.0.1:9177/health` (returns {"status":"healthy","database":"connected"}).
  If any script still defaults to 9876 or 8888, patch it — the port changed when the daemon was rebuilt.

## Files

- `~/.hermes/bin/memory-drain.sh` — the script
- `~/.hermes/bin/memory-demo.sh` — paired live walkthrough
- `~/.hermes/scripts/memory-drain-cron.py` — cron wrapper
- `~/.hermes/skills/note-taking/memory-sop/` — the parent SOP

## Changelog

- v1.2.2 (2026-06-24): corrected all port references from 9876 to **9177** (daemon auto-selects 9177 when rebuilt).
  Updated drain script examples, verification curl commands, and the port pitfall section.
- v1.2.1 (2026-06-23): corrected all port references to 9876 (verified live daemon).
  The 8888 references in prior versions were wrong — the hindsight-embed daemon has always
  defaulted to 9876. Updated drain script examples, verification curl commands, and the
  port pitfall section. Also added note that drain scripts have been patched to default to 9876.
- v1.2.0 (2026-06-23): added "drain cron runs ok but Hindsight stays stale"
  pitfall (empty queue root cause, 3-day staleness observed); added Hindsight
  port confusion pitfall (8888 vs 9876).
- v1.1.0 (2026-06-03): promoted "Hindsight retain is async" to
  hard requirement at top; added cron queue pattern; added LLM
  extraction timing section; added changelog.
- v1.0.0 (2026-06-03): initial release.
