# OSRH blog-post campaign revision — 2026-06-27

## Situation

The user asked whether Hermes could coordinate with his Dad to get an Our Sea Ranch Home guest email sent, based on earlier discussions. Dad wanted to use existing blog posts as part of the email and specifically include the Night Sky blog post.

## Evidence gathered

- Prior Gmail thread showed Dad's ask: send a MailChimp mailing to past guests because there were holes in the summer calendar.
- Prior campaign docs showed the current direction had shifted from a review request to a prior-guest re-engagement / repeat-booking campaign.
- Canonical audience metadata showed MailChimp list `Vista Del Mar - Prior Guests as of 11-30-25`, list id `59c388e378`, with 244 members and 232 subscribed recipients.
- Existing campaign notes showed a MailChimp draft had been created and test-sent, but the full guest send had not fired.
- Live blog links verified for the revised content:
  - Night Sky: `https://oursearanchhome.com/sea-ranch-night-sky-best-stargazing-spots-from-our-deck/`
  - Tide Pools: `https://oursearanchhome.com/sea-ranch-tide-pools/`
  - Hidden Trails: `https://oursearanchhome.com/hidden-sea-ranch-hiking-trails-only-locals-know/`
  - Book Now: `https://oursearanchhome.com/book-now/`

## Artifacts produced

- Coordination plan: `.hermes/plans/2026-06-27-osrh-guest-email-dad-coordination.md`
- Revised markdown draft: `Projects/Sea Ranch AI/docs/campaign-B-blog-post-revision-DRAFT-2026-06-27.md`
- Revised HTML draft: `Projects/Sea Ranch AI/docs/campaign-B-blog-post-revision-DRAFT.html`

## Reusable lesson

When a user asks to coordinate a campaign with a family/client stakeholder, do not jump straight to sending. Recover prior decisions, verify the current send surface and audience, draft the stakeholder coordination email, and ask for approval before any external side effect.

## Gmail body extraction pitfall

The Google Workspace wrapper returned empty `body` fields for a complex Outlook/Gmail thread even though snippets clearly showed content. The workaround was to use the Gmail API directly with `format='full'` and recursively walk nested MIME parts, decoding both `text/plain` and `text/html`. Treat wrapper `body: ""` as partial evidence when snippets indicate the message has body content.

## Approval gates used

- Ask before contacting Dad.
- Ask before updating the MailChimp draft.
- Ask before sending a test.
- Ask again before full-send to the prior-guest audience.

## Safe final status

No email to Dad was sent, no MailChimp draft was changed, and no guest campaign was sent. The correct final response was to present prepared artifacts and ask what approval path the user wanted.
