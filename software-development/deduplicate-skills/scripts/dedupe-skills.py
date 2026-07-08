#!/usr/bin/env python3
"""
dedupe-skills.py — Automated skill deduplication scanner
Usage: python3 dedupe-skills.py [--auto-archive|--dry-run]

Detects duplicate skill names across the Hermes skill tree and optionally
archives shadow copies to prevent context bloat.
"""

import argparse
import os
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path

SKILLS_DIR = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "skills"
ARCHIVE_DIR = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / ".archived-skills"


def extract_skill_name(skill_md_path: Path) -> str:
    """Extract the name: field from SKILL.md frontmatter."""
    content = skill_md_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    in_frontmatter = False
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break
        if in_frontmatter and stripped.startswith("name:"):
            return stripped[5:].strip().strip('"').strip("'")
    # Fallback: search anywhere
    for line in lines:
        if line.strip().startswith("name:"):
            return line.strip()[5:].strip().strip('"').strip("'")
    return ""


def scan_skills() -> dict:
    """Return dict: skill_name -> list of copy dicts. Scans recursively, follows symlinks."""
    skills = {}
    # Use os.walk with followlinks=True so symlinked plugin skills are discovered
    for root, dirs, files in os.walk(SKILLS_DIR, followlinks=True):
        root_path = Path(root)
        # Skip .archived subtree and hidden directories within the skills tree
        if ".archived" in str(root_path):
            continue
        # Only skip if the directory name itself is hidden (e.g., .git, .curator_backups)
        # .hermes in the path prefix is fine — it's the Hermes home
        if root_path.name.startswith(".") and root_path != SKILLS_DIR:
            continue
        skill_md = root_path / "SKILL.md"
        if skill_md.exists():
            name = extract_skill_name(skill_md)
            if not name:
                continue
            is_symlink = root_path.is_symlink()
            target = os.readlink(root_path) if is_symlink else ""
            skills.setdefault(name, []).append({
                "path": root_path,
                "skill_md": skill_md,
                "is_symlink": is_symlink,
                "target": target,
                "mtime": skill_md.stat().st_mtime,
            })
    return skills


def score_copy(copy: dict) -> int:
    """Score a skill copy. Higher = more likely to be canonical."""
    score = 0
    if copy["is_symlink"]:
        score += 10
    if "pilot-sandbox" in copy["target"] or "plugins" in copy["target"]:
        score += 20
    # Modification time as tiebreaker (newer = slightly better)
    score += int(copy["mtime"] / 1000000)
    return score


def main():
    parser = argparse.ArgumentParser(description="Detect and resolve duplicate skill names")
    parser.add_argument("--auto-archive", action="store_true", help="Move shadow copies to archive")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done (default)")
    args = parser.parse_args()

    dry_run = not args.auto_archive
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    skills = scan_skills()
    collisions = {name: copies for name, copies in skills.items() if len(copies) > 1}

    if not collisions:
        print("No collisions found. Skill tree is clean.")
        sys.exit(0)

    for name, copies in sorted(collisions.items()):
        print(f"\n=== COLLISION: {name} ({len(copies)} copies) ===")

        # Score and pick canonical
        scored = [(score_copy(c), i, c) for i, c in enumerate(copies)]
        scored.sort(reverse=True)
        best_idx = scored[0][1]

        for i, copy in enumerate(copies, 1):
            sym = "SYMLINK" if copy["is_symlink"] else "DIRECTORY"
            target = f" -> {copy['target']}" if copy["is_symlink"] else ""
            print(f"  [{i}] {sym}: {copy['path']}{target}")

        canonical = copies[best_idx]
        print(f"  -> CANONICAL: [{best_idx + 1}] {canonical['path']}")

        for i, copy in enumerate(copies):
            if i == best_idx:
                continue
            if dry_run:
                print(f"  -> WOULD ARCHIVE (dry-run): {copy['path']}")
            else:
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                archive_path = ARCHIVE_DIR / f"{copy['path'].name}-{ts}"
                shutil.move(str(copy["path"]), str(archive_path))
                print(f"  -> ARCHIVED: {copy['path']} -> {archive_path}")

    print("")
    if dry_run:
        print(f"DRY RUN complete. Re-run with --auto-archive to move shadow copies to {ARCHIVE_DIR}")
    else:
        print(f"ARCHIVE complete. Shadow copies moved to {ARCHIVE_DIR}")


if __name__ == "__main__":
    main()
