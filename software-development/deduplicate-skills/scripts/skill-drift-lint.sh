#!/bin/bash
# skill-drift-lint.sh — Read-only within-skill content drift detector
# Scans all SKILL.md files under ~/.hermes/skills/ for:
#   1. Duplicated headings (same heading appearing 2+ times)
#   2. Stale version field (file modified recently but version not bumped)
#   3. Missing reference paths
#
# Output: Report to stdout. Caller redirects to ~/.hermes/synthesis/skill-drift-lint-YYYY-MM-DD.md
#
# Part of the deduplicate-skills skill. See SKILL.md "Within-Skill Content Drift Detection".
# This script is READ-ONLY — it never modifies files.

set -uo pipefail
# Note: no `set -e` — grep returns non-zero on no-match, which is expected here.

SKILLS_DIR="${HERMES_HOME:-$HOME/.hermes}/skills"
TODAY=$(date +%Y-%m-%d)
THIRTY_DAYS_AGO=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '-30 days' +%Y-%m-%d 2>/dev/null || echo "")

# Key headings to check for duplication
KEY_HEADINGS=(
  "## User Preferences"
  "## Pitfalls"
  "## Concise Responses"
  "## ACTIVE Update Discipline"
  "## Pitfall:"
  "## Red Flags"
)

echo "# Skill Drift Lint Report — $TODAY"
echo ""
echo "Scanned: $SKILLS_DIR"
echo ""

# Counters
TOTAL_SKILLS=0
DRIFT_SKILLS=0
HIGH_SEVERITY=0
MEDIUM_SEVERITY=0

# Find all SKILL.md files
while IFS= read -r -d '' skill_file; do
  skill_dir=$(dirname "$skill_file")
  skill_name=$(basename "$skill_dir")
  TOTAL_SKILLS=$((TOTAL_SKILLS + 1))
  
  has_drift=false
  
  # 1. Check for duplicated headings
  dup_headings=""
  for heading in "${KEY_HEADINGS[@]}"; do
    count=$(grep -c "^${heading}" "$skill_file" 2>/dev/null | head -1 | tr -d '[:space:]' || echo 0)
    if [ "$count" -gt 1 ] 2>/dev/null; then
      dup_headings="${dup_headings}\n  - DUPLICATED ($count): \"$heading\""
      has_drift=true
      HIGH_SEVERITY=$((HIGH_SEVERITY + 1))
    fi
  done
  
  # Also check any heading appearing 2+ times (general scan)
  all_dup=$(grep '^#' "$skill_file" 2>/dev/null | sort | uniq -d || true)
  if [ -n "$all_dup" ]; then
    while IFS= read -r dup_line; do
      # Skip if already caught by key headings check
      is_key=false
      for heading in "${KEY_HEADINGS[@]}"; do
        if [[ "$dup_line" == *"$heading"* ]]; then
          is_key=true
          break
        fi
      done
      if [ "$is_key" = false ]; then
        dup_headings="${dup_headings}\n  - DUPLICATED: \"$dup_line\""
        has_drift=true
        HIGH_SEVERITY=$((HIGH_SEVERITY + 1))
      fi
    done <<< "$all_dup"
  fi
  
  # 2. Check version freshness
  version_info=""
  version=$(grep '^version:' "$skill_file" 2>/dev/null | head -1 | sed 's/^version: *//' | tr -d '"' || echo "")
  mod_date=$(stat -f "%Sm" -t "%Y-%m-%d" "$skill_file" 2>/dev/null || stat -c "%y" "$skill_file" 2>/dev/null | cut -d' ' -f1 || echo "")
  
  if [ -n "$mod_date" ] && [ -n "$THIRTY_DAYS_AGO" ] && [[ "$mod_date" > "$THIRTY_DAYS_AGO" ]]; then
    if [ -z "$version" ]; then
      version_info="  - STALE: No version field, file modified $mod_date"
      has_drift=true
      MEDIUM_SEVERITY=$((MEDIUM_SEVERITY + 1))
    fi
    # Note: We can't easily detect "version unchanged despite modification" without
    # git history. The version field presence check is a basic heuristic.
  fi
  
  # 3. Check reference paths exist
  missing_refs=""
  grep -oE '`references/[^`]+`' "$skill_file" 2>/dev/null | tr -d '`' | sort -u | while IFS= read -r ref; do
    full_path="$skill_dir/$ref"
    if [ ! -f "$full_path" ]; then
      missing_refs="${missing_refs}\n  - MISSING: \`$ref\`"
      has_drift=true
      MEDIUM_SEVERITY=$((MEDIUM_SEVERITY + 1))
    fi
  done
  
  # Report
  if [ "$has_drift" = true ]; then
    DRIFT_SKILLS=$((DRIFT_SKILLS + 1))
    echo "## $skill_name"
    echo "  Path: $skill_file"
    if [ -n "$version" ]; then
      echo "  Version: $version"
    fi
    if [ -n "$mod_date" ]; then
      echo "  Modified: $mod_date"
    fi
    if [ -n "$dup_headings" ]; then
      echo ""
      echo "  ### Duplicated Headings (HIGH)"
      echo -e "$dup_headings"
    fi
    if [ -n "$version_info" ]; then
      echo ""
      echo "  ### Version Staleness (MEDIUM)"
      echo "  $version_info"
    fi
    if [ -n "$missing_refs" ]; then
      echo ""
      echo "  ### Missing References (MEDIUM)"
      echo -e "$missing_refs"
    fi
    echo ""
  fi
  
done < <(find "$SKILLS_DIR" -name "SKILL.md" -print0 2>/dev/null)

echo ""
echo "---"
echo "## Summary"
echo "- Total skills scanned: $TOTAL_SKILLS"
echo "- Skills with drift: $DRIFT_SKILLS"
echo "- HIGH severity findings: $HIGH_SEVERITY"
echo "- MEDIUM severity findings: $MEDIUM_SEVERITY"
echo ""
echo "This lint is READ-ONLY. Remediation requires \`skill_manage(action='edit')\` or \`skill_manage(action='patch')\`."