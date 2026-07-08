---
name: hermes-config-memory-provider-update
created: 2026-06-18
updated: 2026-06-18
author: Hermes
---

# Hermes Config: Memory Provider Update

## Session Context
- **Task**: Update Hermes config to enable triple memory (`holographic,contextforge,honcho`).
- **Trigger**: Hindsight (L2) offline; user requested concurrent memory systems.
- **Constraints**:
  - Direct file edits blocked by Hermes security guard.
  - `hermes config get` does not exist.

## Workflow

### 1. List Current Config
```bash
hermes config show | grep -A 5 "memory:"
```
**Output**:
```yaml
memory:
  provider: hindsight
  memory_file: /Users/jack.reis/Documents/=notes/claude/memory/hermes_memory.md
  user_file: /Users/jack.reis/Documents/=notes/claude/memory/hermes_user.md
```

### 2. Update Memory Providers
```bash
hermes config set memory.provider holographic,contextforge,honcho
```
**Output**: `✓ Set memory.provider = holographic,contextforge,honcho in /Users/jack.reis/.hermes/config.yaml`

### 3. Update L1 File Paths
```bash
hermes config set memory.memory_file ~/.hermes/memories/MEMORY.md
hermes config set memory.user_file ~/.hermes/memories/USER.md
```
**Output**:
```
✓ Set memory.memory_file = /Users/jack.reis/.hermes/memories/MEMORY.md in /Users/jack.reis/.hermes/config.yaml
✓ Set memory.user_file = /Users/jack.reis/.hermes/memories/USER.md in /Users/jack.reis/.hermes/config.yaml
```

### 4. Verify
```bash
hermes config show | grep -A 5 "memory:"
```
**Expected Output**:
```yaml
memory:
  provider: holographic,contextforge,honcho
  memory_file: ~/.hermes/memories/MEMORY.md
  user_file: ~/.hermes/memories/USER.md
```

## Pitfalls
- **`hermes config get`**: Non-existent command. Use `hermes config show` or `hermes config set`.
- **Direct file edits**: Blocked by Hermes security guard. Use `hermes config set`.
- **Provider order**: Comma-separated, no spaces (e.g., `holographic,contextforge,honcho`).

## References
- [Hermes Config Documentation](https://hermes-agent.nousresearch.com/docs/configuration)
- [Memory SOP: Config Management](#config-management)