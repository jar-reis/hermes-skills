# MEMORY.md Round-Trip Drift Resolution — 2026-06-14

## Trigger
The `memory` tool refused writes with:

```text
Refusing to write MEMORY.md: file on disk has content that wouldn't round-trip through the memory tool
```

The active file was under the configured `memory.memory_char_limit` (6,000 in this profile) after compression work, but still failed the round-trip guard.

## Root cause found
Hermes parses memory entries using the exact delimiter:

```text
\n§\n
```

It then serializes entries with the same delimiter and compares `raw.strip()` to the serialized result. Extra blank lines around delimiters create a byte mismatch even when the visible sections look valid.

Bad shape:

```text
entry text

§
next entry
```

Good shape:

```text
entry text
§
next entry
```

A separate drift signal is any single parsed entry exceeding the configured whole-store char limit. Check the configured limit before assuming the default 2,200 chars; this profile used 6,000 chars.

## Resolution pattern
1. Refresh context first: `memory_current_project`, relevant `memory_query`, and session recall if the drift relates to a prior session. Do not rewrite L1 memory from stale context.
2. Back up the exact file before rewriting.
3. Parse with `raw.split('\n§\n')`, inspect entry count, max entry length, serialized length, and `raw.strip() == '\n§\n'.join(entries)`.
4. Rewrite `MEMORY.md` as clean entries joined by the exact delimiter, with no blank lines around `§`.
5. Keep entries declarative and compact; move session narratives and stale runtime state to OBn/ContextForge/handoffs instead of L1.
6. Verify with the same round-trip check.
7. Prove the memory tool works by doing a real `memory(action='add')` for the durable fact that originally failed; the tool response is the operational verification.

## Minimal verifier

```python
from pathlib import Path
p = Path('~/.hermes/memories/MEMORY.md').expanduser()
s = p.read_text()
entries = [e.strip() for e in s.split('\n§\n') if e.strip()]
roundtrip = '\n§\n'.join(entries)
print('roundtrip_equal', s.strip() == roundtrip)
print('chars_roundtrip', len(roundtrip))
print('entry_count', len(entries))
print('max_entry_len', max(map(len, entries), default=0))
```

## Session outcome
On 2026-06-14, this procedure reduced `MEMORY.md` from a non-round-trippable ~7.4KB file to 5 clean entries at 3,844/6,000 chars, then `memory(action='add')` succeeded. The successful add documented that `/Users/jack.reis/ai-dev/hermes-main` is linked to ContextForge project Open Brain 1.
