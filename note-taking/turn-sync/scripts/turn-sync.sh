#!/usr/bin/env bash
# turn-sync.sh — convenience wrapper for OB1 per-turn sync operations
#
# Usage:
#   turn-sync.sh pull [limit]           # Pull recent thoughts (default 5)
#   turn-sync.sh search "<query>" [limit]  # Semantic search OB1
#   turn-sync.sh capture "<content>" [--source <agent>] [--task-id <ns>]
#   turn-sync.sh status                 # Check OB1 connectivity + thought count
#
# For non-Hermes agents that don't have mcp_open_brain_* MCP tools.
# Hermes agents should use the MCP tools directly — they're faster.

set -euo pipefail

OB1_PULL="/Users/jack.reis/Documents/=notes/bin/ob1-pull"

if [[ ! -x "$OB1_PULL" ]]; then
  echo "ERROR: ob1-pull not found at $OB1_PULL" >&2
  exit 1
fi

cmd="${1:-help}"
shift || true

case "$cmd" in
  pull)
    limit="${1:-5}"
    "$OB1_PULL" --recent --limit "$limit"
    ;;
  search)
    query="${1:?Usage: turn-sync.sh search '<query>' [limit]}"
    limit="${2:-5}"
    "$OB1_PULL" --query "$query" --limit "$limit"
    ;;
  capture)
    content="${1:?Usage: turn-sync.sh capture '<content>' [--source <agent>] [--task-id <ns>]}"
    source="hermes"
    task_id="session/$(date +%Y-%m-%d)-turn-sync"
    while [[ $# -gt 1 ]]; do
      case "$2" in
        --source) source="$3"; shift 2 ;;
        --task-id) task_id="$3"; shift 2 ;;
        *) shift ;;
      esac
    done
    "$OB1_PULL" --capture "$content" --source "$source" --task-id "$task_id"
    ;;
  status)
    echo "=== OB1 Turn-Sync Status ==="
    "$OB1_PULL" --recent --limit 1 2>&1 && echo "OB1: REACHABLE" || echo "OB1: UNREACHABLE"
    ;;
  help|*)
    cat <<'EOF'
turn-sync.sh — OB1 per-turn memory sync

Commands:
  pull [limit]              Pull recent thoughts (default 5)
  search "<query>" [limit]  Semantic search OB1
  capture "<content>"       Capture a thought to OB1
    --source <agent>        Agent identity (default: hermes)
    --task-id <namespace>   Session namespace (default: session/<date>-turn-sync)
  status                    Check OB1 connectivity

Examples:
  turn-sync.sh pull 5
  turn-sync.sh search "memory architecture" 10
  turn-sync.sh capture "[DECISION] Use OB1 for real-time sync" --source codex --task-id session/2026-06-19-codex-work
EOF
    ;;
esac