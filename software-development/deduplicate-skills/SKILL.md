---
name: deduplicate-skills
description: Detect and resolve duplicate skill names across the Hermes skill tree. Scans for name collisions between default skills and plugin skills, compares content, recommends canonical versions, and provides safe cleanup commands. Use when skills_list() shows unexpected duplicates, plugin skills shadow default skills, or context bloat from redundant skill loading is suspected.
version: 1.0.0
author: Hermes
metadata:
  hermes:
    tags: [skills, maintenance, deduplication, context-optimization]
    related_skills: [writing-skills, hermes-agent]
---

# Deduplicate Skills

Detect and resolve duplicate skill names across the Hermes skill tree. When plugin skills (e.g., from `pilot-sandbox/plugins/`) are symlinked into `~/.hermes/skills/`, they may collide with existing skills of the same name. Both versions get loaded into the LLM context window, causing token waste and potential conflicting instructions.

## When to Use

- `skills_list()` shows multiple skills with the same name
- Plugin skills shadow default skills (same trigger phrases, different content)
- Session context feels bloated with redundant skill definitions
- You want to clean up after bulk-importing plugin skills

## Glossary

- **Canonical skill** — the version kept after deduplication
- **Shadow skill** — the duplicate version removed or deprioritized
- **Name collision** — two skill directories with the same `name:` in their SKILL.md frontmatter
- **Context bloat** — redundant skill content consuming LLM context window tokens

## Detection Process

### 1. Scan for Collisions

Run this command to find all skills and detect name collisions:

```bash
find ~/.hermes/skills -name "SKILL.md" -print0 2>/dev/null | while IFS= read -r -d '' f; do
  dir=$(dirname "$f")
  skill_dir=$(basename "$dir")
  # Extract name from YAML frontmatter
  name=$(awk '/^---$/{found=1; next} found && /^---$/{exit} found && /^name:/{print $2; exit}' "$f" | tr -d '"' | tr -d "'" | xargs)
  # Fallback: search anywhere in file
  if [ -z "$name" ]; then
    name=$(grep "^name:" "$f" | head -1 | sed 's/^name: *//' | tr -d '"' | tr -d "'" | xargs)
  fi
  if [ -L "$dir" ]; then
    link_target=$(readlink "$dir")
    echo "COLLISION_CANDIDATE|name=$name|dir=$skill_dir|type=symlink|target=$link_target|path=$f"
  else
    echo "COLLISION_CANDIDATE|name=$name|dir=$skill_dir|type=directory|target=|path=$f"
  fi
done | sort -t'|' -k2,2
```

This outputs pipe-delimited records grouped by name. Any name appearing more than once indicates a collision.

### 2. Resolve Collisions

For each detected collision, apply this decision tree:

**Rule 1: Compare modification times**
- More recently modified = likely more actively maintained
- Check: `stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" <path>` (macOS) or `stat -c "%y" <path>` (Linux)

**Rule 2: Compare content depth**
- More linked files (templates, references, scripts) = more complete
- More lines in SKILL.md = more detailed
- Check: `wc -l <path>/SKILL.md` and count of linked files

**Rule 3: Prefer plugin versions for domain-specific skills**
- If one is from `pilot-sandbox/plugins/` and the other is from the default tree
- Plugin versions are often project-specific and more current
- Default tree versions may be generic/boilerplate

**Rule 4: Prefer symlinked versions if they point to actively maintained repos**
- Symlinks to plugin repos get updates when the repo updates
- Standalone directories in `~/.hermes/skills/` may be stale copies

### 3. Safe Cleanup Commands

Once you've decided which version is canonical, remove the shadow:

**If shadow is a symlink:**
```bash
# Just remove the symlink — the source remains intact
rm ~/.hermes/skills/<shadow-name>
```

**If shadow is a directory (not a symlink):**
```bash
# Move to archive instead of deleting
mv ~/.hermes/skills/<shadow-name> ~/.hermes/skills/.archived/<shadow-name>-$(date +%Y%m%d)
```

**If you want to keep both but avoid context loading:**
```bash
# Rename the shadow so it doesn't match the canonical name
# Edit the shadow's SKILL.md to change the name: field
grep "^name:" ~/.hermes/skills/<shadow-name>/SKILL.md
```

### 4. Verify Deduplication

After cleanup:
```bash
hermes skills list | grep <skill-name>
# Should show exactly one entry
```

Or programmatically:
```bash
# Count occurrences of each skill name
find ~/.hermes/skills -name "SKILL.md" -exec awk '/^---$/{found=1; next} found && /^---$/{exit} found && /^name:/{print $2; exit}' {} \; | tr -d '"' | sort | uniq -c | sort -rn | head -20
```

Any line with `2` or higher indicates a remaining collision.

## Prevention

### Before bulk-importing plugin skills:

1. Check existing skill names:
   ```bash
   hermes skills list | awk -F': ' '{print $1}' | sort > /tmp/existing-skills.txt
   ```

2. Check plugin skill names:
   ```bash
   find /path/to/plugins -name "SKILL.md" -exec awk '/^---$/{found=1; next} found && /^---$/{exit} found && /^name:/{print $2; exit}' {} \; | tr -d '"' | sort > /tmp/plugin-skills.txt
   ```

3. Find intersections:
   ```bash
   comm -12 /tmp/existing-skills.txt /tmp/plugin-skills.txt
   ```

4. For each intersection, decide before symlinking:
   - Skip the plugin version (`# do not symlink`)
   - Archive the existing version first
   - Merge content manually

### Using skill_config for selective loading:

Hermes supports platform-specific skill enablement via `hermes skills config`. Even if duplicates exist in the tree, you can prevent both from loading in the same session context by disabling one for your platform.

## Full Deduplication Script

For automated deduplication of the current skill tree:

```bash
#!/bin/bash
# save as ~/.hermes/scripts/dedupe-skills.sh

SKILLS_DIR="${HERMES_HOME:-$HOME/.hermes}/skills"
ARCHIVE_DIR="$SKILLS_DIR/.archived"
mkdir -p "$ARCHIVE_DIR"

# Build a map: name -> [paths]
declare -A name_to_paths
declare -A name_to_types

while IFS='|' read -r record name dir type target path; do
  clean_name=$(echo "$name" | sed 's/name=//')
  clean_path=$(echo "$path" | sed 's/path=//')
  clean_type=$(echo "$type" | sed 's/type=//')
  
  if [ -n "$clean_name" ]; then
    if [ -z "${name_to_paths[$clean_name]}" ]; then
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
  name=$(awk '/^---$/{found=1; next} found && /^---$/{exit} found && /^name:/{print $2; exit}' "$f" | tr -d '"' | tr -d "'" | xargs)
  if [ -z "$name" ]; then
    name=$(grep "^name:" "$f" | head -1 | sed 's/^name: *//' | tr -d '"' | tr -d "'" | xargs)
  fi
  if [ -L "$dir" ]; then
    echo "|name=$name|dir=$skill_dir|type=symlink|target=$(readlink "$dir")|path=$f"
  else
    echo "|name=$name|dir=$skill_dir|type=directory|target=|path=$f"
  fi
done)

# Report collisions
for name in "${!name_to_paths[@]}"; do
  paths="${name_to_paths[$name]}"
  count=$(echo "$paths" | tr ',' '\n' | wc -l)
  if [ "$count" -gt 1 ]; then
    echo "COLLISION: $name ($count copies)"
    echo "$paths" | tr ',' '\n' | while read -r p; do
      dir=$(dirname "$p")
      if [ -L "$dir" ]; then
        echo "  [SYMLINK] $p -> $(readlink "$dir")"
      else
        echo "  [DIRECTORY] $p"
      fi
    done
  fi
done
```

Run with `bash ~/.hermes/scripts/dedupe-skills.sh`.

- Pitfalls during a real audit (architecture-truth rubric, 156 skills, 2026-06-03): `references/architecture-truth-evaluation-rubric-2026-06-03.md`.

## Within-Skill Content Drift Detection

Cross-skill name collisions are the primary detection target above. A separate but related problem is **within-skill content drift**: a single SKILL.md file that accumulates duplicated content blocks, stale verifier commands, and contradictory rerun caveats from repeated `skill_manage(action='patch')` calls across sessions.

This is NOT the same as a name collision — there is only one skill directory, but its content has internally diverged.

### Detection Signals

1. **Duplicated content blocks** — the same heading or preference section appears 2+ times in the same file. Example: a "Concise Responses" user-preference block duplicated 4+ times because each rerun patched it in without removing the previous copy.
2. **Stale verifier commands** — the skill references CLI commands that no longer exist (e.g., `hermes context`, `hermes compact` when only `hermes prompt-size` is available).
3. **Version field not bumped** — the `version:` in frontmatter hasn't been incremented despite visible content changes.
4. **Reference path drift** — `references/` files mentioned in SKILL.md no longer exist at the stated paths.
5. **Accumulated rerun caveats** — multiple `[date] Rerun` sections with contradictory findings, none superseded or consolidated.

### Detection Commands

```bash
# Find duplicated headings (any heading appearing 2+ times)
grep -n '^#' ~/.hermes/skills/<skill-name>/SKILL.md | sort -t'#' -k2 | uniq -d -f1

# Count occurrences of a specific heading
grep -c '## User Preferences' ~/.hermes/skills/<skill-name>/SKILL.md
# Any count > 1 indicates drift

# Check for stale reference paths
grep -oP '`references/[^`]+`' ~/.hermes/skills/<skill-name>/SKILL.md | while read -r ref; do
  path="${ref//\`/}"
  full="$HOME/.hermes/skills/<skill-name>/$path"
  [ -f "$full" ] || echo "MISSING: $ref"
done
```

### Remediation

1. **For severe drift (3+ duplicated blocks)**: Use `skill_manage(action='edit')` to rewrite the entire file, merging all duplicated blocks into single canonical sections. This is the nuclear option but necessary when patch-based edits have compounded.
2. **For minor drift (1-2 duplicated blocks)**: Use `skill_manage(action='patch')` with `old_string` matching the duplicate block and `new_string=''` to remove it.
3. **Bump the `version:` field** after any consolidation.
4. **Move historical rerun caveats** to `references/changelog.md` to keep the SKILL.md body current.
5. **Verify reference paths** after consolidation with `search_files`.
6. **Add a "Skill Drift Prevention" pitfall** to the skill itself so future sessions catch drift early.

### Prevention

When using `skill_manage(action='patch')` to add user-preference blocks or pitfalls, always:
- Search for the heading first: `grep -c '## <Heading>' <path>/SKILL.md`
- If the heading already exists, patch the existing block rather than appending a new one
- Bump the version field in the same patch operation

### Pitfall: `set -e` with `grep -c` in Lint Scripts

Shell scripts that use `grep -c` to count matches return non-zero exit codes when there are zero matches. If `set -e` is active, this causes premature script exit on the first no-match heading. **Always use `set -uo pipefail` (without `-e`) in lint/scan scripts** that use `grep -c` for counting. The `grep -c` output is still correct — it returns `0` — but the non-zero exit code triggers `set -e` before the count can be evaluated.

### Pitfall: Patch-Based Drift in Daily Rerun Skills

Skills maintained by recurring cron jobs (e.g., daily-best-practices-extension) are especially prone to drift because each rerun patches the skill without a human reviewing the full file. The `writing-plans` skill was identified on 2026-06-23 with 4+ duplicated "Concense Responses" blocks from exactly this pattern. Daily rerun skills should be audited for duplicated sections at least weekly.

See `references/skill-drift-detection-2026-06-23.md` for the session-specific case study.

### Automated Lint Script

A read-only lint script is available at `scripts/skill-drift-lint.sh`. Run it to scan all SKILL.md files for:
- Duplicated headings (same heading 2+ times = HIGH)
- Stale version field (file modified recently but no version = MEDIUM)
- Missing reference paths (MEDIUM)

```bash
bash ~/.hermes/skills/software-development/deduplicate-skills/scripts/skill-drift-lint.sh > ~/.hermes/synthesis/skill-drift-lint-$(date +%Y-%m-%d).md
```

The lint is READ-ONLY — it reports drift but never auto-remediates. Schedule weekly via cron for proactive detection.

## Post-Deduplication Verification

Always run after cleanup:
1. `hermes skills list` — confirm no duplicates in output
2. `skill_view(name='<skill-name>')` — confirm the canonical version loads
3. Start a fresh session — verify no conflicting skill definitions in context

## Known Collisions in This Environment

As of the last scan, these collisions exist between the default skill tree and `pilot-sandbox/plugins/`:

| Skill | Default Location | Plugin Location | Recommendation |
|-------|-----------------|-----------------|----------------|
| `grill-me` | `software-development/grill-me` | `grill-each-other/skills/grill-me` | Keep plugin version (more recent dialectical protocol) |
| `grill-me-agents` | `software-development/grill-me-agents` | `grill-each-other/skills/grill-me-agents` | Keep plugin version |
| `grill-me-with-agents` | `software-development/grill-me-with-agents` | `grill-each-other/skills/grill-me-with-agents` | Keep plugin version |
| `grill-with-docs` | `software-development/grill-with-docs` | `grill-each-other/skills/grill-with-docs` | Keep plugin version |
| `peer-grill` | `software-development/peer-grill` | `grill-each-other/skills/peer-grill` | Keep plugin version |
| `peer-grill-with-agents` | `software-development/peer-grill-with-agents` | `grill-each-other/skills/peer-grill-with-agents` | Keep plugin version |
| `fleet-ratify` | `autonomous-ai-agents/fleet-ratify` | `grill-each-other/skills/fleet-ratify` | Compare — may be different scopes |

Note: The plugin versions are often evolutions of the default versions. Before removing, diff the SKILL.md files to confirm the plugin version is strictly superior.
