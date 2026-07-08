---
name: atlas-chunking
description: Break a concept into chunks and generate questions to explore. Used by Atlas+Scout primitives.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [chunking, ideation, exploration]
    related_skills: [scout-prioritization, brainstorming]
---

# Atlas Chunking

## Overview

Break a concept into chunks and generate questions to explore. First half of the **Atlas+Scout compounding primitive** (Nate's AI Meeting Takeaways).

**Use Case**: Prototype Nate's primitives:
- **Atlas**: Chunk concepts (e.g., "source-of-truth discipline").
- **Scout**: Prioritize chunks (e.g., "Is this worth working on?").

## Input/Output

**Input**: A concept (e.g., "AI-enabled acquisitions").
**Output**: Chunks (subtopics) + questions (exploration prompts).

## Procedure

1. **Source**: When the input says "latest posts" or another moving target, resolve the source first. Prefer an available canonical connector/API; if unavailable, use the public RSS/feed/archive and record the source URL, lookback window, selected item count, and access limitations in the JSON.
2. **Decompose**: Split each concept/post into 3–5 non-overlapping subtopics.
3. **Question**: For each subtopic, generate 2–3 questions to explore.
4. **Validate**: Ensure questions are open-ended and actionable.
5. **Persist + verify**: For cron/downstream use, write the requested JSON artifact, then validate it with a real JSON parser and structural checks before reporting completion.

## Example

```python
delegate_task(
    goal="Break 'AI-enabled acquisitions' into chunks and questions",
    context="Use the Atlas chunking pattern: subtopics + exploration questions.",
    toolsets=['terminal']
)
```

## Verification

- **Chunks**: 3–5 subtopics, no overlaps.
- **Questions**: Open-ended, actionable.
- **Output**: JSON format (for Scout compatibility).
- **Cron artifacts**: See `references/cron-json-pattern.md` for moving-source cron jobs. The pattern documents source resolution metadata, access caveats, JSON structure, and validation steps for downstream automation.