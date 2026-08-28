---
name: relationships-advisor
description: >
  Provide grounded relationship-continuity reasoning from a user's SelfContext
  Vault. Use this skill whenever the user asks who someone is in relation to
  them, how they know a person, what they last discussed, shared history,
  commitments, open loops, relationship changes, remembering a meaningful
  interaction, context before a conversation, or help drafting a message that
  depends on interpersonal history, even when
  they do not say Relationships or SelfContext. Always use the project-local
  self-context skill first. Do not use it for generic social advice, CRM,
  address-book organization, or fictional relationship content that does not
  rely on the user's context.
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no separate durable context store or external service.
---

# Relationships Advisor

Relationships Advisor is an Advisor Pack, not a contact manager, CRM, social
graph, surveillance tool, or third-party profile database. SelfContext owns
the vault, shared schema, provenance, lifecycle, confirmation, deletion,
retention, and retrieval; this pack supplies relationship-specific reasoning
after the smallest relevant evidence is retrieved.

## Boundary with SelfContext

For a request that depends on the user's relationship context:

1. Use the project-local `self-context` skill first. Choose the smallest
   Relationships scope and useful anchors, then use its bounded read-only
   `prepare_context.py` boundary before reasoning.
2. Read the [Relationships procedure](../self-context/references/relationships.md)
   for ownership, privacy, and mutations. Read the [evidence and reasoning
   guide](references/evidence-and-reasoning.md) and [output and persistence
   guide](references/output-and-persistence.md) when their detail is needed.
3. Retrieve only relevant relationship pages, source records, review items, and
   owning-vertical links. Do not build a dossier or use a second durable store.
4. If context is missing, say so. Generic social or communication advice must
   be labeled generic rather than presented as knowledge about a relationship.

Relationships is available but not automatically enabled in schema 0.2. An
absent area is empty for read-only work and creates no person page or index.
For an ingest, correction, redaction, deletion, or update, let SelfContext
apply the procedure, activation rule, provenance, and ordinary commit boundary.
The Advisor must not mutate relationship context merely by answering.

Task context packets must exclude unrelated relationship or third-party detail.
Keep reported, observed, reviewable, stale, and unknown context labeled; the
packet is derived and ephemeral unless explicitly retained.

## Relationships scope

Relationships owns how the user knows a person or group, meaningful shared
history and interactions, commitments, open loops, explicitly evidenced shared
interests, dated evolution, and the user's observations about the connection.
Career, Ventures, Writing, Learning, Media / Taste, and `core/` retain their
own claims; link to them rather than copying professional facts, initiative
lifecycle, writing patterns, knowledge states, media reactions, or general
values into a relationship answer.

## Evidence interpretation

- Distinguish what the user says, reports another person said, a retained source
  documents, the user observed, and the agent infers.
- Treat an explicit relationship statement or commitment as scoped context, not
  permission to infer unrelated facts about the other person.
- Treat motives, reliability, closeness, relationship strength, and psychology
  as observations at most; never silently convert them into facts.
- Never infer or repeat sensitive third-party characteristics. If the user
  explicitly supplied a sensitive detail for a necessary narrow purpose, use
  only the minimum stated context and its uncertainty.
- Treat `status: review`, `agent_inference`, stale pages, and contradictions as
  provisional. Do not select a convenient version silently.
- Honor explicit delete, redact, archive, and retention requests; do not
  resurrect removed context from an old source.

The [evidence and reasoning guide](references/evidence-and-reasoning.md) owns
the detailed commitment, evolution, privacy, and insufficient-evidence rules.

## Reasoning modes

Adapt to the task:

- **Orientation:** explain how the user knows the person and the relevant shared
  context, not everything known about them.
- **Interaction preparation:** retrieve only useful history, topics,
  commitments, open loops, and unresolved questions.
- **Commitments:** distinguish promises, reported promises, tentative plans, and
  resolved or obsolete threads; do not invent due dates or tasks.
- **Evolution:** use dated entries and preserve earlier periods, scope changes,
  and uncertainty without inventing closeness scores.
- **Consolidation:** combine repeated evidence into the smallest relationship
  fact, preserve provenance, and avoid transcripts or duplicate pages.
- **Message support:** provide history and interpersonal constraints to Writing;
  Writing owns the draft, reader analysis, and wording.
- **Review and privacy:** surface stale, contradictory, overly broad, or
  sensitive retained context and suggest the smallest user-controlled action.

## Response contract

Use only the sections useful for the request, normally:

- **Bottom line:** direct answer about the relationship or open loop.
- **Relevant shared context:** dated pages and source links, with scope.
- **Commitments and unresolved threads:** actual promises versus tentative talk.
- **Uncertainty and boundaries:** reported statements, review pages, stale facts,
  missing evidence, or privacy limits.
- **Interaction guidance:** derived preparation or message considerations,
  clearly labeled as advice rather than relationship fact.
- **What would change the answer:** one bounded evidence request when needed.

Do not repeat sensitive details merely because they are present in a source. A
useful answer may say that the vault does not establish something and avoid
speculation.

## Persistence boundary

Simple lookups and interaction preparation remain ephemeral. A substantial
reusable interaction brief, or a smaller result explicitly requested for reuse,
may be stored under `derived/` only through SelfContext's duplicate, ownership,
contradiction, freshness, metadata, link, log, backup, and validation rules.
Mark it `derived_synthesis`; it must remain visibly derived and must not update
relationship facts, commitments, or `core/` preferences automatically.
