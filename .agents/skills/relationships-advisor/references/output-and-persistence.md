# Relationships Outputs and Persistence

## Interaction preparation

A useful brief should answer only what the user needs before the named
interaction:

- who the person is in relation to the user;
- relevant shared history or the last meaningful topic;
- actual commitments and unresolved threads;
- recent or stale context that needs qualification; and
- a few derived conversation considerations, clearly labeled as suggestions.

Do not present an interaction brief as a complete biography of the other
person. Omit unrelated or sensitive details even if a source contains them.

## Message and conversation support

Relationships supplies history and interpersonal constraints. Writing owns the
actual draft, reader analysis, and communication choices. Keep statements like
“the user promised to send the repository” separate from a generated suggestion
for how to mention it. A generated message is not evidence that the relationship
changed.

## Review and corrections

When a page contains a reported statement, contradiction, stale commitment, or
agent inference, show the uncertainty and the smallest action that would resolve
it. A user can confirm, revise, defer, redact, archive, or delete context. Do
not silently verify an important claim because it appears in a message.

## Persistence decision

Ordinary lookups, conversation preparation, and message advice remain
ephemeral. Evaluate a durable result only when:

- the user explicitly asks to retain a useful interaction brief;
- the result captures non-obvious relationship continuity likely to be reused;
- the result exposes a meaningful unresolved thread; or
- the user asks to update a relationship page with new evidence.

Before persistence, SelfContext checks for an existing relationship page or
synthesis, ownership conflicts, contradictions, freshness, and the user's
retention intent. Store factual relationship context in `relationships/`,
reviewable interpretations in `review/observations/`, and reusable advice in
`derived/`. A derived page should link to the evidence and state its uncertainty;
it cannot promote a recommendation into a commitment or fact.

If persistence is not justified, report that the answer remains ephemeral and
that no relationship page, `core/` page, or derived synthesis was changed.
