#!/bin/bash
# Memory Sync State Verifier
# Quick health check for the canonical four memory systems during/after a sugar sync run.
# Usage: bash ~/.hermes/skills/note-taking/memory-sop/scripts/verify-memory-sync-state.sh

set -euo pipefail

fail=0

check() {
  local name="$1" cmd="$2" expect="$3"
  if eval "$cmd" 2>/dev/null | grep -q "$expect"; then
    echo "✅ $name"
  else
    echo "❌ $name"
    fail=1
  fi
}

echo "=== Memory Sync State Verifier ==="

check "Hindsight (8888)" "curl -s --max-time 3 http://localhost:8888/health" "healthy"
check "OBn Chroma v2 (8001)" "curl -s --max-time 3 http://localhost:8001/api/v2/heartbeat" "heartbeat"

# Honcho/Cortex on 8002 is optional and may still be stabilizing
if curl -s --max-time 3 http://localhost:8002/api/v2/heartbeat 2>/dev/null | grep -q heartbeat; then
  echo "✅ Cortex/Honcho Chroma (8002)"
else
  echo "⚠️  Cortex/Honcho Chroma (8002) not yet stable"
fi

# ContextForge MCP
check "ContextForge MCP" "hermes mcp list 2>/dev/null" "contextforge"

# Open Brain MCP
check "Open Brain MCP" "hermes mcp list 2>/dev/null" "open-brain"

# Coordination ledger
if [ -f "/Users/jack.reis/Documents/=notes/.hermes/state/memory-sync-2026-06-19.md" ]; then
  echo "✅ Coordination ledger present"
else
  echo "⚠️  Coordination ledger not found (run may not have started from this path)"
fi

if [ "$fail" -eq 0 ]; then
  echo "=== All required systems healthy ==="
else
  echo "=== Some required systems are down; see recovery steps in memory-sop SKILL.md ==="
  exit 1
fi
