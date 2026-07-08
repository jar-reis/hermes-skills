---
name: scout-prioritization
description: Decide whether a concept is worth working on. Used by Atlas+Scout primitives.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [prioritization, decision-making, ideation]
    related_skills: [atlas-chunking, brainstorming]
---

# Scout Prioritization

## Overview

Decide whether a concept (or its chunks) is worth working on. Second half of the **Atlas+Scout compounding primitive** (Nate's AI Meeting Takeaways).

**Use Case**: Prototype Nate's primitives for fleet-wide adoption (e.g., "Prioritize 'source-of-truth discipline' for implementation").

## Input/Output

**Input**: A concept or chunk (e.g., "AI-enabled acquisitions: ownership structure").
**Output**: Prioritization score (1–5) + rationale.

## Procedure

1. **Assess**: Evaluate alignment, feasibility, and impact.
2. **Score**: Assign 1–5 (1 = low, 5 = high).
3. **Rank**: When producing a prioritized list for downstream automation, avoid ties. Use specificity, immediacy, and fit to the user's active systems as tie-breakers.
4. **Rationale**: Explain the score with concrete references to the concept/chunk and the user's likely implementation surface.

## Example

```python
delegate_task(
    goal="Prioritize 'AI-enabled acquisitions: ownership structure'",
    context="Use the Scout prioritization pattern: score 1–5 + rationale.",
    toolsets=['terminal']
)
```

## Verification

- **Score**: 1–5, no ties.
- **Rationale**: Specific, not generic.
- **Output**: JSON format (for downstream automation).