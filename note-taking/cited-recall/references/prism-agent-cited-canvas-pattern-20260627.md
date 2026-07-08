# Prism Agent — Historical Cited-Canvas Pattern (Khoj, 2026-04-15)

## Origin

Prism was a private Khoj cloud agent preset created by Jack Reis
(`jackareis@gmail.com`), exported from `app.khoj.dev` on 2026-04-15 during
the Khoj sunset migration. It ran on Kimi K2.5 with ~260 vault markdown files
attached as context.

## What Made Prism Distinctive

Prism implemented a **Verified Assistant — Anti-Hallucination Protocol**
that forced every factual claim to carry an inline citation:

```
### Response Format:
- Always cite sources inline: [claim](source-file.md#section)
- Flag uncertainty: "Based on available notes..." or "I don't have information about..."
- Distinguish fact from inference: "The notes show X. This suggests Y (inference)."
- Request clarification: When ambiguous, ask follow-up questions

### Forbidden Behaviors:
❌ Never fabricate file paths or note titles
❌ Never invent dates, names, or technical details
❌ Never claim certainty without a source
❌ Never fill gaps with "reasonable assumptions"

### Required Behaviors:
✅ State "I don't have information about X" when appropriate
✅ Cite specific files and line numbers when available
✅ Distinguish between "notes say" vs "I infer"
✅ Ask for clarification rather than guess
```

This is the "canvas report that always cited statements" pattern — every
response was a grounded canvas with explicit source attribution, not
ungrounded prose.

## Relationship to cited-recall

Prism's anti-hallucination protocol is the **agent-side mirror** of what
the `cited-recall` skill implements on the **retrieval side**:

| Prism (agent generation) | cited-recall (retrieval pipeline) |
|---|---|
| Every claim must cite a source file | Every chunk carries a citation_id |
| "I don't know" is preferred over guessing | Abstention when <2 sources or top RRF <0.3 |
| Distinguish "notes say" vs "I infer" | Synthesis prompt forbids inference beyond evidence |
| Forbidden: fabricate file paths | Forbidden: hallucinate beyond provided context |

The pattern is: **force citations at both the retrieval and generation
layers**. cited-recall handles retrieval-side citation; Prism's persona
prompt handles generation-side citation. A future fleet agent could combine
both by running cited-recall for context retrieval, then feeding the cited
chunks into a Prism-style persona for generation.

## Provenance

- Exported: 2026-04-15 from `app.khoj.dev` → `khoj-agent-presets-2026-04-15.json`
- Vault path: `efforts/current/khoj-sunset/khoj-agent-presets-2026-04-15.json`
- Restored locally: 2026-05-11 via `claude/agents/khoj/restore_local_khoj.py`
- Khoj local instance: DOWN as of 2026-06-27 (Docker not running on Talaris)
- Prism slug: `prism-796225`
- Chat model: Kimi K2.5
- Privacy: private