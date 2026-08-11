# Media / Taste Outputs and Persistence

## Taste answers

A useful taste answer separates:

- individual work evidence and the user's stated reaction;
- a recurring pattern and the works that support it;
- exceptions, conflicts, dates, and missing reactions; and
- any recommendation or explanation generated for the current request.

Do not substitute an external review, plot summary, genre label, or provider
rating for personal evidence.

## Recommendations

For “would I like this?” explain the fit and the conflict:

- **Evidence match:** which described works and reasons resemble the candidate;
- **Evidence conflict:** which usual dislikes or missing features may count
  against it; and
- **Conclusion:** a conditional derived recommendation with uncertainty.

For “recommend something outside my usual taste,” preserve the user's normal
pattern and identify the deliberate distance from it. Do not erase exceptions
or invent an adventurousness trait.

## Capture and update

When the user supplies a work reaction, SelfContext decides whether to retain a
work page, source record, pattern observation, exception, or no update. A
recommendation or generated review is not a work reaction. If a user edits an
AI-generated review, preserve the human statement as the evidence and keep the
original generated text derived.

## Persistence decision

Ordinary taste explanations, comparisons, and recommendations remain ephemeral.
Evaluate persistence only when:

- the user explicitly asks to remember a reaction, pattern, exception, or
  recommendation;
- a source contains a meaningful personal reaction likely to help later;
- a comparison exposes durable cross-media evidence or a useful review item; or
- the user asks to update or supersede a taste page.

Before any write, SelfContext checks for an existing work or pattern, ownership,
contradictions, evolution, freshness, and noise. Store work evidence under
`media/`, reviewable patterns under `review/observations/` or a scoped media
observation, and reusable recommendations under `derived/`. A derived page
links to its evidence and cannot update the user's taste automatically.

If no continuity signal exists, report that no work page, pattern, `core/` page,
or derived synthesis was created.
