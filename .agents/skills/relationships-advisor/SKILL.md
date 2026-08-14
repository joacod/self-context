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
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no separate memory store or external service.
---

# Relationships Advisor

Relationships Advisor is an Advisor Pack, not a contact manager, CRM, social
graph, surveillance tool, or third-party profile database. SelfContext owns the
vault, shared schema, provenance, lifecycle, confirmation, deletion, and
retrieval. This pack supplies relationship-specific reasoning after SelfContext
retrieves the smallest relevant evidence set.

## Boundary with SelfContext

For every request that depends on the user's relationship context:

1. Use the project-local `self-context` skill first. Orient from `SCHEMA.md`,
   `index.md`, recent `log.md`, and `relationships/index.md` when it exists.
2. Read [the Relationships procedure](../self-context/references/relationships.md)
   before ingesting, updating, reviewing, or interpreting relationship evidence.
3. Read [the evidence and reasoning guide](references/evidence-and-reasoning.md)
   before answering questions about a person, shared history, commitments, or
   relationship evolution.
4. Read [the output and persistence guide](references/output-and-persistence.md)
   before preparing a substantial interaction brief or deciding whether a
   result deserves a derived page.
5. Retrieve only the relationship pages, source records, review items, and
   owning-vertical links needed for the request. Do not produce a dossier about
   a person merely because more files exist.

If the Relationships area or relevant evidence is missing, say so. Generic
social or communication expertise may still help, but it must be labeled
generic rather than presented as knowledge about the user's relationships.
Relationships is available but not automatically enabled in schema 0.2; a
read-only question about an absent area creates no person page or index.

Task context packets must exclude unrelated relationship or third-party detail
unless the named task directly requires it. Keep reported, observed,
reviewable, stale, and unknown context labeled, and keep the packet derived and
ephemeral unless the user explicitly asks to retain it.

For an ingest, correction, deletion, or request to update the vault, let
SelfContext apply the Relationships procedure, schema-specific activation, and
the provisional/final backup lifecycle. The Advisor does not define contract
markers or mutate relationship context merely by answering.

## Evidence discipline

- Distinguish what the user directly says, what the user reports another person
  said, what a retained source documents, what the user observed, and what the
  agent infers.
- Treat an explicit user statement about the relationship or a commitment as
  scoped context, not permission to infer unrelated facts about the other
  person.
- Treat a message, invitation, or recollection as evidence for the interaction
  it documents, not as a complete or objective profile of its author.
- Treat motives, reliability, closeness, psychological traits, and relationship
  strength as observations at most; never silently convert them into facts.
- Never infer or repeat sensitive third-party characteristics such as medical or
  mental-health information, sexuality, religion, politics, ethnicity, criminal
  history, finances, or diagnoses. If the user explicitly supplied a sensitive
  detail for a genuinely necessary narrow purpose, mention only the minimum
  stated context and its uncertainty.
- Treat `status: review`, `agent_inference`, stale pages, and contradictions as
  provisional. Explain the effect instead of selecting a convenient version.
- Keep Career, Writing, Learning, Media / Taste, and `core/` ownership intact.
  Link to their evidence rather than copying professional facts, writing
  patterns, knowledge states, media taste, or general values into a
  relationship answer.

## Request modes

Adapt reasoning to the task:

- **Orientation:** explain how the user knows the person and the relevant
  shared context, not everything known about them.
- **Interaction preparation:** retrieve only useful history, recent topics,
  commitments, open loops, and unresolved questions for the named interaction.
- **Commitments:** distinguish a promise, a reported promise, a tentative plan,
  and a resolved or obsolete thread. Do not invent due dates or turn the result
  into a task list.
- **Evolution:** use dated relationship entries and preserve earlier periods,
  scope changes, and uncertainty. Do not invent closeness scores.
- **Consolidation:** combine repeated evidence into the smallest relationship
  fact, preserve provenance, and avoid storing transcripts or duplicate pages.
- **Message support:** provide interpersonal context to Writing, while keeping
  the draft, audience analysis, and wording in the Writing operation.
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

Do not repeat sensitive details just because they are present in a source. A
useful answer may say that the vault does not establish something and avoid
speculation.

## Persistence boundary

Simple relationship lookups and interaction preparation remain ephemeral. Do
not create a person page or derived synthesis merely because an answer was
useful. A substantial reusable interaction brief, or a smaller result the user
explicitly asks to retain, may be stored by SelfContext under `derived/` as a
linked `derived_synthesis`; it must remain visibly derived and must not update
relationship facts, commitments, or core preferences automatically.

If the user asks to remember, update, redact, or delete relationship context,
route that mutation through SelfContext's backup, provenance, review, and
navigation rules. Honor deletion and retention choices rather than restoring a
removed fact from an old source.
