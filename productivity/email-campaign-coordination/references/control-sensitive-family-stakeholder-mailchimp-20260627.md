# Control-sensitive family stakeholder campaign coordination — 2026-06-27

## Context

During an Our Sea Ranch Home prior-guest re-engagement campaign, Jack clarified that his dad wanted to keep tight control of the email even though he was older and seriously ill. The campaign work involved a Mailchimp draft, a guest stargazing photo, and existing prior-guest audience metadata.

## Reusable lesson

For family-business email campaigns, stakeholder psychology is part of the operational surface. A technically correct campaign draft can still fail if the collaborator feels displaced, rushed, or overruled.

## Pattern

1. Keep the stakeholder-facing draft short and editable.
2. Phrase agent work as support: “I made a draft you can adjust,” not “I finished it.”
3. Use draft-only changes first; do not test-send or full-send until explicitly approved.
4. Ask for small choices instead of broad approval:
   - photo treatment
   - subject line
   - CTA URL
   - whether to keep an offer/perk
5. Preserve existing templates and visual language when the stakeholder already trusts them.
6. If credential access is needed, ask for the narrowest scope: “Approve Mailchimp credential use for draft only.”
7. If a local safety guard blocks a credential lookup, stop and ask for the exact next permission; do not widen the search silently.

## Anti-patterns

- “I’ll just update the campaign and show him later.”
- “The draft is better now, so send a test.”
- “Credential approval means campaign approval.”
- “He is being slow, so bypass him.”

## Verification checklist

Before reporting completion, verify and report:

- Campaign status is still `save` / draft.
- `emails_sent` is zero or unchanged.
- No test-send endpoint was called.
- Audience/list id is unchanged unless explicitly approved.
- Local markdown/HTML artifacts are saved.
- Remaining approvals are named separately from completed draft work.
