# Latest-posts cron JSON pattern

Use this when Atlas is run from a scheduled job over a moving source such as "Nate's latest posts".

## Source resolution

1. Resolve the source before chunking.
2. Prefer a canonical/private connector when it is available and authorized.
3. If the connector is unavailable, use the public RSS/feed/archive and record the limitation explicitly.
4. Capture source metadata in the JSON:
   - feed/archive URL
   - selection rule and lookback start
   - selected post count
   - access caveat such as public excerpt/read-more gating

## Output shape

For each selected post or source item:

- `title`
- `url`
- `published_at`
- `concept`
- `evidence_snippets`
- `atlas_chunks[]`
  - `id`
  - `subtopic`
  - `questions[]` with 2–3 open-ended actionable questions
  - optional downstream `scout` object when Atlas+Scout are being run together

Include an `overall_scout_priorities[]` block when combining with Scout so a user can immediately see what to work on first.

## Verification

Before reporting completion, validate both syntax and structure:

- JSON parses with a real parser.
- Each post has 3–5 chunks.
- Each chunk has 2–3 questions.
- Scout scores are integers 1–5.
- If downstream automation expects ranking, avoid score ties within a post and in the overall priority list.
- The artifact exists at the requested path.

## Reporting

The final response should report the artifact path, source, selected item count, chunk count, validation evidence, and caveats. Do not use `[SILENT]` if a new artifact was created.