---
name: email-campaign-coordination
description: Coordinate approval-gated email campaigns.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Email, Campaigns, MailChimp, Approval, Coordination]
---

# Email Campaign Coordination

Use this skill to coordinate marketing or guest-list email campaigns from existing drafts, lists, and source content. It does not authorize sending email, importing contacts, or changing live campaign settings by itself; those actions require explicit user approval. Dependency stance: source-backed drafts first, private recipient data protected, test sends before full sends.

## When to Use

- User asks to coordinate an email campaign with another stakeholder.
- User says a campaign should use existing blog posts, docs, or source material.
- User asks whether an email can be sent to guests, prospects, customers, or a list.
- You find an existing campaign draft and need to revise it safely.
- You need to separate test sends, draft updates, and full audience sends.

## Prerequisites

- A clear send surface such as MailChimp, Google Workspace/Gmail, or another ESP.
- Source-backed audience metadata: list name, list id, and subscribed/eligible count.
- Public or internal source links that the email references, verified before use.
- Explicit approval from the user before any external coordination email, campaign update, test send, or full send.
- Private recipient exports kept local-only and never pasted into chat, public docs, or committed artifacts.

## How to Run

1. Use `search_files`, `read_file`, and session history to find canonical campaign artifacts and prior decisions.
2. Use `terminal` or the relevant API skill to verify live source links and list metadata.
3. Draft copy as a local artifact first, preserving merge tags and unsubscribe/footer semantics.
4. Ask for approval before sending a coordination email, changing ESP state, or sending a test.
5. Send one test to approved internal recipients; only after review, send to the audience.

## Quick Reference

- Full-send surface: prefer MailChimp or the ESP that owns the audience.
- Gmail/SMTP: acceptable for manual notes or small tests, not the default full-list path.
- Audience proof: list name, list id, subscribed count, and exclusion rules.
- Approval gates: copy, audience, subject, sender/reply address, CTA, test-send result, full-send approval.
- Private data rule: never print recipient rows or real guest emails.
- Blog/source rule: verify every referenced URL before including it.

## Procedure

1. **Recover prior decisions.** Search for campaign briefs, final rendered drafts, audience metadata, and previous send notes. Treat the latest dated decision as current unless a newer artifact contradicts it.
2. **Identify the canonical audience.** Record the list name, list id, total members, subscribed count, and why that audience is appropriate. Do not combine prior guests, warm prospects, and cold prospects unless the user explicitly approves that change.
3. **Verify the send surface.** Prefer the system that owns unsubscribe, bounces, analytics, and list consent. For MailChimp full sends, keep Gmail/SMTP as a test/manual fallback only.
4. **Gather source material.** If the email should reference blog posts, docs, or pages, verify each link with `terminal` or browser tools and summarize what role each link plays in the email.
5. **Draft without side effects.** Create or update a local markdown/HTML draft. Preserve ESP merge tags such as `*|FNAME|*`, `*|UNSUB|*`, `*|UPDATE_PROFILE|*`, and footer blocks. Do not replace merge tags with test values.
6. **Coordinate with stakeholders.** Draft the stakeholder email as text first and ask the user before sending it. Include concrete choices: subject line, offer/perk, CTA URL, audience, and next step. When the stakeholder is control-sensitive, elderly, ill, anxious, or personally invested, keep the tone gentle and patient: preserve their agency, frame drafts as options, avoid urgency theater, and ask for small confirmations rather than presenting a completed takeover.
7. **Credential and draft permissions are separate.** If the user approves credential use for a draft-only ESP update, limit the action to credential lookup plus draft creation/update. Do not send, test-send, import contacts, or alter audiences unless separately approved.
8. **Approval-gate every side effect.** Separate approval for: contacting the stakeholder, retrieving credentials, updating the campaign draft, sending the internal test, and sending to the full audience.
9. **Verify after action.** After a campaign draft update or test send, capture the actual status returned by the ESP/API and verify the campaign remains in the intended state before making success claims.

## Pitfalls

- Do not treat "can you coordinate" as permission to send. It means prepare the coordination path unless the user explicitly says to send.
- Do not update a live ESP draft merely because local copy is ready; draft mutation is still an external side effect.
- Do not send review requests to non-guests or mixed prospect lists unless the campaign is explicitly reframed.
- Do not paste private recipient rows into the chat or public docs. Counts and safe metadata are enough.
- Do not use a test-send result as approval for a full send. It proves rendering/deliverability, not stakeholder approval.
- Do not steamroll a stakeholder who wants tight control. Especially for family businesses, health-constrained collaborators, or older stakeholders, optimize for trust: make reversible draft-only changes, show exactly what changed, and let them make the visible choices.
- Do not treat “credential use approved” as blanket campaign approval. Credential access can be scoped to draft-only work; sending, test-sending, audience edits, and imports each need their own approval.
- If a credential lookup is blocked by the local safety guard, stop and ask for the exact next permission in plain language. Do not reroute around the guard with broader secret searches or alternate tools.
- Watch for empty body extraction from complex Gmail threads. If `google-workspace` `gmail get` returns an empty body while snippets show content, use a recursive Gmail MIME extraction pattern and treat the wrapper output as partial, not authoritative.

## Verification

Before claiming the campaign is ready for approval, produce a checklist with: source links verified, local draft path, audience metadata, sender/reply address, merge tags preserved, no private recipient rows exposed, and explicit remaining approval gates.

## References

- `references/osrh-blog-post-revision-20260627.md` — Example: revising a prior-guest campaign to include blog posts and a stakeholder approval email.
- `references/control-sensitive-family-stakeholder-mailchimp-20260627.md` — Pattern for gentle, draft-only Mailchimp coordination when a family stakeholder needs tight control.
