#!/usr/bin/env python3
"""Generate a unified skills registry from all fleet skill directories.

Scans every SKILL.md under each source directory, parses YAML frontmatter,
infers runtime compatibility and capability requirements, and writes a
single registry.json that can be queried with jq or loaded by dashboards.

Usage:
    python3 generate_registry.py [--output registry.json]

Without --output, writes to stdout.
"""

import os, sys, json, re, glob, argparse
from datetime import date

DEFAULT_DIRS = [
    ("worker",   os.path.expanduser("~/.hermes/profiles/worker/skills")),
    ("default",  os.path.expanduser("~/.hermes/skills")),
    ("claude",   os.path.expanduser("~/.claude/skills")),
    ("codex",    os.path.expanduser("~/.codex/skills")),
    ("agents",   os.path.expanduser("~/.agents/skills")),
]


def parse_frontmatter(path):
    """Extract YAML frontmatter from SKILL.md — handles flow-style and block-style."""
    with open(path, "r", errors="replace") as f:
        content = f.read(6000)
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end]

    result = {}
    in_hermes = False
    hermes_dict = {}

    for line in fm_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue

        if not line.startswith(" "):
            in_hermes = False
            m = re.match(r"^(\w[\w\s]*?):\s*(.*)", line)
            if m:
                key, val = m.group(1).strip(), m.group(2).strip()
                if key == "metadata":
                    continue
                if val:
                    if val.startswith("[") and val.endswith("]"):
                        result[key] = [
                            x.strip().strip('"').strip("'")
                            for x in val[1:-1].split(",")
                            if x.strip()
                        ]
                    else:
                        result[key] = val.strip('"').strip("'")
        else:
            m = re.match(r"^\s+(\w[\w\s]*?):\s*(.*)", line)
            if m:
                nk, nv = m.group(1).strip(), m.group(2).strip()
                if nk == "hermes":
                    in_hermes = True
                    continue
                if in_hermes and nv:
                    if nv.startswith("[") and nv.endswith("]"):
                        hermes_dict[nk] = [
                            x.strip().strip('"').strip("'")
                            for x in nv[1:-1].split(",")
                            if x.strip()
                        ]
                    else:
                        hermes_dict[nk] = nv.strip('"').strip("'")

    if hermes_dict:
        result["metadata"] = {"hermes": hermes_dict}
    return result


def infer_requires(fm, name):
    requires = set()
    desc = (str(fm.get("description", "")) + " " + name).lower()
    if "mcp" in desc or "mcp" in name:
        requires.add("mcp-server")
    if "browser" in desc:
        requires.add("browser")
    if "terminal" in desc or "shell" in desc:
        requires.add("terminal")
    if "vision" in desc:
        requires.add("vision")
    if "artifact" in desc:
        requires.add("claude-artifacts")
    if "skill" in name and any(w in desc for w in ["manage", "author", "create", "save"]):
        requires.add("skills-system")
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        hm = meta.get("hermes", {})
        if isinstance(hm, dict):
            for t in hm.get("tags", []):
                tl = str(t).lower()
                if any(w in tl for w in ["api", "key", "credential"]):
                    requires.add("api-key")
    return sorted(requires) if requires else []


def infer_lane(desc, name):
    text = (str(desc) + " " + name).lower()
    if any(w in text for w in ["search", "read", "inspect", "monitor", "find", "query", "recall", "track"]):
        return "Sense"
    if any(w in text for w in ["review", "validate", "check", "verify", "audit", "test", "debug"]):
        return "Spec"
    if any(w in text for w in ["run", "execute", "deploy", "send", "commit", "push", "install", "control"]):
        return "Execute"
    if any(w in text for w in ["sync", "backup", "export", "handoff", "transfer", "publish"]):
        return "Transfer"
    return "Shape"


def build_registry(skill_dirs=None, host_label=None):
    if skill_dirs is None:
        skill_dirs = DEFAULT_DIRS

    all_skills = {}
    for dir_label, dir_path in skill_dirs:
        if not os.path.isdir(dir_path):
            continue
        for skill_md in sorted(glob.glob(os.path.join(dir_path, "**", "SKILL.md"), recursive=True)):
            fm = parse_frontmatter(skill_md)
            name = fm.get("name", os.path.basename(os.path.dirname(skill_md)))
            if name not in all_skills:
                skill_dir = os.path.dirname(skill_md)
                rel = os.path.relpath(skill_dir, dir_path)
                category = rel.split("/")[0] if "/" in rel else rel
                all_skills[name] = {
                    "id": name,
                    "name": name,
                    "description": str(fm.get("description", "")),
                    "author": str(fm.get("author", "")),
                    "version": str(fm.get("version", "")),
                    "category": category,
                    "available_in": [],
                    "frontmatter": fm,
                }
            if dir_label not in all_skills[name]["available_in"]:
                all_skills[name]["available_in"].append(dir_label)

    skills = []
    for name, info in sorted(all_skills.items()):
        fm = info["frontmatter"]
        dirs = info["available_in"]
        runtimes = set()
        if "worker" in dirs or "default" in dirs or "repo" in dirs:
            runtimes.add("hermes")
        if "claude" in dirs:
            runtimes.add("claude")
        if "codex" in dirs:
            runtimes.add("codex")
        if "agents" in dirs:
            runtimes.add("agents")
        platforms = fm.get("platforms", [])
        if isinstance(platforms, list):
            for p in platforms:
                runtimes.add(f"platform:{p}")
        elif isinstance(platforms, str):
            for p in re.findall(r"\w+", platforms.lower()):
                runtimes.add(f"platform:{p}")

        tags = []
        meta = fm.get("metadata", {})
        if isinstance(meta, dict):
            hm = meta.get("hermes", {})
            if isinstance(hm, dict):
                tags = hm.get("tags", [])

        skills.append({
            "id": info["id"],
            "name": info["name"],
            "description": info["description"],
            "author": info["author"],
            "version": info["version"],
            "category": info["category"],
            "runtimes": sorted(runtimes),
            "requires": infer_requires(fm, name),
            "lane": infer_lane(info["description"], name),
            "available_in": dirs,
            "tags": tags if isinstance(tags, list) else [],
        })

    # Stats
    by_runtime, by_lane, by_category, by_author = {}, {}, {}, {}
    for s in skills:
        for r in s["runtimes"]:
            by_runtime[r] = by_runtime.get(r, 0) + 1
        by_lane[s["lane"]] = by_lane.get(s["lane"], 0) + 1
        by_category[s["category"]] = by_category.get(s["category"], 0) + 1
        a = str(s["author"])
        if a:
            by_author[a] = by_author.get(a, 0) + 1

    return {
        "generated": str(date.today()),
        "host": host_label or (os.uname().nodename if hasattr(os, "uname") else "unknown"),
        "source_dirs": {label: path for label, path in skill_dirs},
        "total_skills": len(skills),
        "stats": {
            "by_runtime": dict(sorted(by_runtime.items(), key=lambda x: -x[1])),
            "by_lane": dict(sorted(by_lane.items(), key=lambda x: -x[1])),
            "by_category": dict(sorted(by_category.items(), key=lambda x: -x[1])[:15]),
            "by_author": dict(sorted(by_author.items(), key=lambda x: -x[1])[:10]),
        },
        "skills": skills,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate unified skills registry")
    parser.add_argument("--output", "-o", default=None, help="Output path (default: stdout)")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Deterministically index SKILL.md packages in this repository instead of scanning fleet home directories",
    )
    args = parser.parse_args()

    if args.repo_root is not None:
        registry = build_registry([("repo", args.repo_root)], host_label="github-repository")
    else:
        registry = build_registry()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(registry, f, indent=2)
        print(f"Registry: {registry['total_skills']} skills -> {args.output}", file=sys.stderr)
    else:
        print(json.dumps(registry, indent=2))
