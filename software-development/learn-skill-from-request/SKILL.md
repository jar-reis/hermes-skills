---
name: learn-skill-from-request
description: "Parse mixed source+requirement input to author and save a skill."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Skills, Authoring, Learning, Hermes]
    related_skills: [hermes-agent-skill-authoring, writing-skills]
---

# Learn Skill From Request

Parses a `/learn` request that mixes SOURCES (paths, URLs, pasted notes, conversation history) with REQUIREMENTS (focus, scope, naming, what to skip), gathers every source, applies every constraint, and authors one SKILL.md via `skill_manage(action='create')`. Does NOT duplicate the frontmatter/body standards already covered by `hermes-agent-skill-authoring` and `writing-skills` — it references those for the rules and focuses on the gather-and-author workflow.

## When to Use

- User sends a `/learn` request with mixed source paths and authoring requirements
- User says "save this as a skill" after pasting notes or a URL
- User references "what we just did" and wants it captured as a reusable skill

## Prerequisites

- `skill_manage` tool available (built-in)
- Source access: `read_file`, `search_files`, `web_extract`, `browser_navigate` for gathering
- Load `hermes-agent-skill-authoring` or `writing-skills` for the full frontmatter/body rules

## How to Run

1. Parse the request into SOURCES and REQUIREMENTS (see Procedure below).
2. Gather every source in parallel (batch independent reads/extracts).
3. Apply every requirement to shape the skill content.
4. Author one SKILL.md following the standards in `hermes-agent-skill-authoring`.
5. Save via `skill_manage(action='create')`.
6. Report skill name, category, and one-line summary.

## Quick Reference

```
Sources:   read_file, search_files, web_extract, browser_navigate, conversation history
Save:      skill_manage(action='create', name=..., category=..., content=...)
Scripts:   skill_manage(action='write_file', name=..., file_path='scripts/...', file_content=...)
Verify:    skill_view(name=...)
```

## Procedure

1. **Parse the request.** Split into two lists:
   - SOURCES: file paths, directory paths, URLs, "what we just did", pasted text blocks, screenshot paths.
   - REQUIREMENTS: focus instructions ("focus on X"), exclusions ("skip Y"), scope limits, naming hints, angle/tone directives, category preferences.
   - Rule: prose after a path or URL is NOT incidental — it is the user telling you what they want from that source. `<url> focus on auth, skip deprecated` means gather the URL AND honor both constraints.

2. **Gather every source.** Batch independent calls:
   - Local files/dirs: `read_file` or `search_files`
   - URLs: `web_extract` (up to 5 per call)
   - Screenshots: `vision_analyze`
   - Conversation history: `session_search` or the current transcript
   - Pasted text: use as-is, no tool needed
   - If scope is ambiguous, make a reasonable choice and note it. Do not stall.

3. **Apply every requirement.** Map each constraint to a skill decision:
   - "focus on X" → emphasize X in Overview, Procedure, Quick Reference
   - "skip Y" → omit Y entirely; note in Pitfalls if it's a common trap
   - "scope to Z" → narrow the skill to Z; cross-reference broader skills
   - "name it N" → use N as the skill name (lowercase-hyphenated)
   - "angle: practical/ reference/ troubleshooting" → shape body sections accordingly

4. **Author the SKILL.md.** Follow the hardline rules from `hermes-agent-skill-authoring`:
   - `name`: lowercase-hyphenated, <=64 chars
   - `description`: ONE sentence, <=60 chars, ends with period, states capability not implementation. Count chars after writing; cut if over 60.
   - `version`: 0.1.0
   - `author`: always literal `Hermes`
   - `platforms`: declare only if OS-bound primitives are used
   - `metadata.hermes.tags`: few Capitalized tags
   - Body order: Title+intro → When to Use → Prerequisites → How to Run → Quick Reference → Procedure → Pitfalls → Verification
   - Frame scripts as "invoke through the `terminal` tool"
   - Reference Hermes tools by name in backticks: `terminal`, `read_file`, `web_extract`, etc.
   - Prefer exact commands, URLs, signatures from the source. Never invent.
   - Keep tight: ~100 lines simple, ~200 complex. Don't re-paste source docs.
   - Non-trivial scripts go in `scripts/` via `skill_manage(action='write_file')`, referenced by relative path.

5. **Save.** Single call: `skill_manage(action='create', name=..., category=..., content=...)`.

6. **Report.** Tell the user: skill name, category, one-line summary.

## Pitfalls

- **Ignoring prose after a path.** `<url> focus on auth` means gather AND focus. Do not fetch the URL and skip the focus instruction.
- **Description over 60 chars.** The system-prompt skill index truncates at 60. Anything past that is silently cut and breaks skill routing. Always count.
- **Author field from environment.** Never fill `author` from the OS username, git config, or any probed identity. Always literal `Hermes`.
- **Stalling on ambiguity.** If the request is ambiguous about scope, make a reasonable choice, note it, and proceed. Do not ask the user to clarify unless the choice is genuinely high-stakes.
- **Duplicating existing skills.** Check `skills_list` before creating. If a peer covers the territory, patch it instead.
- **Inventing APIs/flags.** Only write what you saw in the source. If a detail is missing, omit it rather than fabricate.
- **Re-pasting source docs.** The skill teaches the technique, not the documentation. Reference sources by path/URL, don't inline them.

## Verification

```
skill_view(name='<skill-name>')
```
Confirm the skill loads, frontmatter parses, and the description is <=60 chars.