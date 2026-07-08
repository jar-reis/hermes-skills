# Memory Drift Resolution

## Problem
`MEMORY.md` or `USER.md` has **drift** (concurrent edits, manual changes, or tool failures), causing the `memory` tool to reject writes with:
```
Refusing to write MEMORY.md: file on disk has content that wouldn't round-trip through the memory tool.
```

## Root Cause
- **Concurrent Edits**: Two Hermes sessions (e.g., cron + interactive) wrote to the file simultaneously.
- **Manual Edits**: The user or another tool modified the file outside Hermes.
- **Tool Failure**: A `write_file` or `patch` operation failed mid-write.

## Resolution Steps

### 1. Backup the Drifted File
```bash
cp ~/.hermes/memories/MEMORY.md ~/.hermes/memories/MEMORY.md.bak.$(date +%s)
```

### 2. Identify the Drift
Compare the backup with the current file:
```bash
diff ~/.hermes/memories/MEMORY.md ~/.hermes/memories/MEMORY.md.bak.$(date +%s)
```

### 3. Merge Changes
- **Manual Merge**: Edit `MEMORY.md` to reconcile differences.
- **Automated Merge**: Use `patch` to apply changes from the backup:
  ```bash
  patch ~/.hermes/memories/MEMORY.md <(diff -u ~/.hermes/memories/MEMORY.md.bak.$(date +%s) ~/.hermes/memories/MEMORY.md)
  ```

### 4. Validate the File
Ensure the file is **well-formed** (e.g., `§` delimiters, no duplicate entries):
```bash
grep -c "§" ~/.hermes/memories/MEMORY.md  # Should be ≥ 1
wc -c ~/.hermes/memories/MEMORY.md           # Should be ≤ 2200 chars
```

### 5. Retry the Memory Write
```bash
hermes memory add --target memory --content "Your fact here"
```

## Session Artifact
- **Document the Drift**:
  ```markdown
  - Memory Drift: Resolved conflict in `MEMORY.md` (backup: `MEMORY.md.bak.1781231873`).
  ```

## References
- [Hermes Memory Docs](https://hermes-agent.nousresearch.com/docs/memory)
- [`memory-sop` Skill](file:///Users/jack.reis/.hermes/skills/note-taking/memory-sop/SKILL.md)