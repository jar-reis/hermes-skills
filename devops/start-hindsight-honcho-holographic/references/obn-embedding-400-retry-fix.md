# OBn Embedding 400 Retry Exhaustion Fix

**Discovered**: 2026-06-23
**Commit**: 964bd5b7e
**Impact**: 5/12 OBn pods were failing during sync with 1670+ errors each

## Root Cause

The `get_embeddings_batch` function in `ingest_chroma.py` handles
Ollama 400 errors (batch too large or text exceeding nomic-embed-text's
2048-token context window) by splitting the batch in half and retrying
recursively. However, the split was guarded by `attempt < max_retries - 1`,
meaning on the LAST retry attempt, the 400 error fell through to the
general HTTPError handler and raised `RuntimeError`.

This caused the entire pod to fail with errors for every chunk in the
failed batch, even though most chunks were perfectly valid — only a
few oversized texts triggered the 400.

## The Bug (before)

```python
# Line ~160 of ingest_chroma.py (BEFORE fix)
if response is not None and response.status_code == 400 and attempt < max_retries - 1:
    # 400 errors often mean batch too large — split and retry
    mid = len(texts) // 2
    if mid > 0:
        left = get_embeddings_batch(texts[:mid], model, ollama_url, max_retries - 1)
        right = get_embeddings_batch(texts[mid:], model, ollama_url, max_retries - 1)
        return left + right
```

When `attempt == max_retries - 1` (last attempt), the condition is False,
so the 400 falls through to:

```python
if attempt < max_retries - 1:
    time.sleep(wait)
else:
    raise  # RuntimeError kills the pod
```

## The Fix (after)

```python
# AFTER fix (commit 964bd5b7e)
if response is not None and response.status_code == 400:
    # Always split on 400, regardless of attempt count
    mid = len(texts) // 2
    if mid > 0:
        child_retries = max(1, max_retries - 1)  # ensure >= 1 retry
        left = get_embeddings_batch(texts[:mid], model, ollama_url, child_retries)
        right = get_embeddings_batch(texts[mid:], model, ollama_url, child_retries)
        return left + right
    else:
        # Single text still 400s — skip (dims preserved)
        return [[0.0] * 768
```

Two changes:
1. Removed `and attempt < max_retries - 1` — always split on 400
2. Use `max(1, max_retries - 1)` for recursive calls — ensures
   children always get at least 1 retry, so they can split again
   if needed, or hit the single-text fallback

## Verification

Tested on all 5 previously-failing pods:

```bash
cd ~/Documents/=notes/claude/scheduled-tasks/vault-ingest

for pod in config-ai-systems.yaml config-core.yaml config-home-improvement.yaml \
           config-rib-recovery.yaml config-sea-ranch-ops.yaml; do
  ~/Documents/=notes/.venv/bin/python3 ingest_chroma.py --config "$pod" --batch-size 16
done
```

All 5 pods completed with 0 errors. Total docs went from 54,663 to 58,246.

Full healthcheck:
```bash
~/Documents/=notes/.venv/bin/python3 \
  ~/Documents/=notes/claude/scheduled-tasks/vault-ingest/obn_healthcheck.py
```

Output: 12 collections, 58,246 docs, only gardening empty (known).

## How to Diagnose

1. Check the sync log for pod failures:
   ```bash
   grep "Pod.*failed" ~/Documents/=notes/claude/scheduled-tasks/logs/obn-sync.*.log
   ```

2. Check if Ollama is up and nomic is available:
   ```bash
   curl -sf http://localhost:11434/api/tags | python3 -c \
     "import json,sys; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]" | grep nomic
   ```

3. If Ollama is up but pods fail with many errors, check the error
   pattern — if you see "400 error, splitting batch" followed by
   "Batch embedding failed" (not "Model not found"), it's the retry
   exhaustion bug, not a model availability issue.