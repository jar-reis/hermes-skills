#!/bin/bash
# dedupe-skills.sh — Automated skill deduplication scanner
# Usage: bash dedupe-skills.sh [--auto-archive|--dry-run]
#
# Detects duplicate skill names across the Hermes skill tree and optionally
# archives shadow copies to prevent context bloat.

set -euo pipefail

SKILLS_DIR="${HERMES_HOME:-$HOME/.hermes}/skills"
ARCHIVE_DIR="$SKILLS_DIR/.archived"
MODE="${1:---dry-run}"  # --dry-run (default) or --auto-archive

mkdir -p "$ARCHIVE_DIR"

# Build a map: name -> [paths]
declare -A name_to_paths
declare -A name_to_types

while IFS='|' read -r _ name _ type _ path; do
  clean_name=$(echo "$name" | sed 's/name=//')
  clean_path=$(echo "$path" | sed 's/path=//')
  clean_type=$(echo "$type" | sed 's/type=//')
  
  if [ -n "$clean_name" ]; then
    if [ -z "${name_to_paths[$clean_name]:-}" ]; then
      name_to_paths[$clean_name]="$clean_path"
      name_to_types[$clean_name]="$clean_type"
    else
      name_to_paths[$clean_name]="${name_to_paths[$clean_name]},$clean_path"
      name_to_types[$clean_name]="${name_to_types[$clean_name]},$clean_type"
    fi
  fi
done < <(find "$SKILLS_DIR" -name "SKILL.md" -print0 2>/dev/null | while IFS= read -r -d '' f; do
  dir=$(dirname "$f")
  skill_dir=$(basename "$dir")
  
  # Extract name from YAML frontmatter (between --- markers)
  name=$(awk '/^---$/{found=1; next} found && /^---$/{exit} found && /^name:/{print substr($0,6); exit}' "$f" | tr -d '"' | tr -d "'" | xargs)
  
  # Fallback: search anywhere in file for name:
  if [ -z "$name" ]; then
    name=$(grep "^name:" "$f" | head -1 | sed 's/^name: *//' | tr -d '"' | tr -d "'" | xargs)
  fi
  
  if [ -L "$dir" ]; then
    echo "|name=$name|dir=$skill_dir|type=symlink|target=$(readlink "$dir")|path=$f"
  else
    echo "|name=$name|dir=$skill_dir|type=directory|target=|path=$f"
  fi
done)

# Report and optionally resolve collisions
found_collisions=0
for name in "${!name_to_paths[@]}"; do
  paths="${name_to_paths[$name]}"
  IFS=',' read -ra path_array <<< "$paths"
  count=${#path_array[@]}
  
  if [ "$count" -gt 1 ]; then
    found_collisions=1
    echo ""
    echo "=== COLLISION: $name ($count copies) ==="
    
    # Score each copy: prefer symlinks to plugins, then by modification time
    best_idx=0
    best_score=-1
    
    for i in "${!path_array[@]}"; do
      p="${path_array[$i]}"
      dir=$(dirname "$p")
      is_symlink=0
      is_plugin=0
      
      if [ -L "$dir" ]; then
        is_symlink=1
        target=$(readlink "$dir")
        if [[ "$target" == *"pilot-sandbox"* ]] || [[ "$target" == *"plugins"* ]]; then
          is_plugin=1
        fi
      fi
      
      # Score: symlink=+10, plugin=+20, newer=+5
      score=0
      [ "$is_symlink" -eq 1 ] && score=$((score + 10))
      [ "$is_plugin" -eq 1 ] && score=$((score + 20))
      
      # Modification time bonus (newer = higher)
      mtime=$(stat -f "%m" "$p" 2>/dev/null || stat -c "%Y" "$p" 2>/dev/null || echo "0")
      score=$((score + mtime / 1000000))  # rough time-based tiebreaker
      
      echo "  [$((i+1))] $p"
      echo "      symlink=$is_symlink plugin=$is_plugin score=$score"
      
      if [ "$score" -gt "$best_score" ]; then
        best_score=$score
        best_idx=$i
      fi
    done
    
    echo "  -> CANONICAL: [$((best_idx+1))] ${path_array[$best_idx]}"
    
    # Archive shadows
    for i in "${!path_array[@]}"; do
      if [ "$i" -ne "$best_idx" ]; then
        p="${path_array[$i]}"
        dir=$(dirname "$p")
        dir_name=$(basename "$dir")
        
        if [ "$MODE" = "--auto-archive" ]; then
          archive_path="$ARCHIVE_DIR/${dir_name}-$(date +%Y%m%d-%H%M%S)"
          echo "  -> ARCHIVING: $dir -> $archive_path"
          mv "$dir" "$archive_path"
        else
          echo "  -> WOULD ARCHIVE (dry-run): $dir"
        fi
      fi
    done
  fi
done

if [ "$found_collisions" -eq 0 ]; then
  echo "No collisions found. Skill tree is clean."
  exit 0
fi

echo ""
if [ "$MODE" = "--dry-run" ]; then
  echo "DRY RUN complete. Re-run with --auto-archive to move shadow copies to $ARCHIVE_DIR"
else
  echo "ARCHIVE complete. Shadow copies moved to $ARCHIVE_DIR"
fi
