# Greek Chorus Pattern (2026-06-19)

## Summary
5-attendant parallelism for dynamic multi-model audits (Hermes, Claude Code, Codex, Antigravity, Kimi).

## Session Evidence
- **Tool Bug**: `delegate_task` ignores model overrides (tracked as Linear JAC-XXX).
- **Workaround**: Use `execute_code` with `hermes_tools.terminal()`.
- **Memory Gaps**: Hindsight/OBn not seeded for Greek chorus.

## Next Actions
1. Seed Hindsight lesson:
   ```bash
   curl -X POST http://localhost:8888/api/lessons -d '{"content": "Greek chorus pattern: 5-attendant parallelism for dynamic multi-model audits. Use execute_code workaround for delegate_task model override bug."}'
   ```
2. Verify OBn capture in turn-sync wrappers:
   ```bash
   grep -r "mcp_open_brain_capture_thought" ~/Documents/=notes/scripts/turn-sync
   ```