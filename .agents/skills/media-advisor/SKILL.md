---
name: media-advisor
description: >
  Provide explainable, evidence-backed reasoning about a user's media taste and
  reactions. Use this skill whenever the user asks to record or update a
  meaningful reaction, abandon or revisit a work, or asks what kinds of books,
  films, shows, games, music, podcasts, or other works they tend to enjoy, why they
  liked or disliked something, whether they would probably like a work,
  exceptions, cross-media patterns, or taste changes, even when they do not say
  Media, Taste, or SelfContext. Always use the project-local self-context skill
  first. Do not use it for generic reviews, media catalogs, watchlists, or
  fictional recommendations that do not rely on the user's context.
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no separate media database or external service.
---

# Media Advisor

Media Advisor is an evidence-and-reasoning pack, not Goodreads, Letterboxd,
Spotify, IMDb, a ratings database, or a recommendation engine with its own
memory. SelfContext owns the vault, shared schema, provenance, lifecycle,
confirmation, persistence, and retrieval. This pack reasons from the user's
individual work reactions and taste observations.

## Boundary with SelfContext

For every personalized media or taste request:

1. Use the project-local `self-context` skill first. Orient from `SCHEMA.md`,
   `index.md`, recent `log.md`, and `media/index.md` when it exists.
2. Read [the Media / Taste procedure](../self-context/references/media-taste.md)
   before ingesting or updating work reactions, patterns, exceptions, or taste
   evolution.
3. Read [the evidence and reasoning guide](references/evidence-and-reasoning.md)
   before deciding what a work or pattern supports.
4. Read [the output and persistence guide](references/output-and-persistence.md)
   before making a recommendation or deciding whether a comparison should be
   retained.
5. Retrieve only relevant work pages, pattern pages, source records, review
   items, and cross-vertical links. Do not build a complete media catalog from
   whatever happens to be in the vault.

If the Media / Taste area or personal reactions are missing, say so. Generic
media knowledge and a generic recommendation can still be offered, but must be
labeled generic rather than attributed to the user. Media / Taste is available
but not automatically enabled in schema 0.2; read-only work does not create a
media area or catalog.

For a task context packet, include only the reactions and taste evidence that
serve the task, plus conflicts, freshness, unknowns, paths, and exclusions.
Never expose unrelated relationship details merely because they exist. The
packet is derived output and remains ephemeral unless explicitly retained.

For a request to record, correct, abandon, revisit, supersede, or delete taste
context, let SelfContext apply the Media / Taste procedure and pre-write
backup. The Advisor does not mutate the profile merely by answering.

## Evidence discipline

- Treat an individual work reaction as the primary evidence. Consumption or
  completion alone establishes exposure, not liking or preference.
- Prefer the user's explicit reaction and comparisons. External metadata,
  summaries, copied reviews, and an agent's interpretation are not personal
  taste evidence.
- Do not derive an inferred pattern from one work unless the user explicitly
  states that broader preference. Otherwise look for multiple independent,
  meaningful reactions and keep the pattern scoped and reviewable.
- Explain why each supporting work fits a pattern and retain exceptions,
  contradictions, medium differences, and dates.
- Never infer politics, religion, sexuality, identity, morality, health,
  personality, intelligence, or psychological traits from cultural consumption.
- Keep Learning ownership for what the user learned from a work, Relationships
  ownership for shared media experiences, Writing ownership for authored
  communication, and `core/` ownership for deliberately broad preferences.
- Treat `status: review`, `agent_inference`, stale pages, and superseded context
  as provisional or historical. Do not present them as current preference
  without qualification.

## Request modes

Adapt reasoning to the task:

- **Taste inventory:** group evidenced reactions by themes, styles, mechanics,
  pacing, creators, or media without flattening the user into a genre label.
- **Why this worked:** trace a liked work to the user's own reaction and the
  supporting patterns, including conflicts and uncertainty.
- **Recommendation:** compare the candidate with several evidenced works;
  explain matches and mismatches conditionally rather than predicting certainty.
- **Cross-media pattern:** link work pages across media and state the shared
  feature that the evidence supports, without over-generalizing.
- **Exceptions:** preserve a work that conflicts with a usual preference and
  the reason it was meaningful.
- **Taste evolution:** use dates and prior reactions to distinguish a real change
  from medium, mood, or context differences.
- **Capture or update:** route the mutation through SelfContext's Media / Taste
  procedure, including no-update outcomes and noise prevention.

## Response contract

Use only the sections useful for the request, normally:

- **Bottom line:** direct answer or conditional recommendation.
- **Evidence:** the individual works, reactions, dates, and linked patterns.
- **Matches and conflicts:** what fits the evidence and what cuts against it.
- **Exceptions and evolution:** relevant outliers or changed preferences.
- **Uncertainty:** missing reactions, review pages, stale context, or generic
  assumptions.
- **Recommendation:** clearly labeled derived advice, never a new fact.

If the evidence does not support a pattern, say so. Do not fill the gap with a
plot summary, genre stereotype, rating, or personality explanation.

## Persistence boundary

Ordinary recommendations, comparisons, and taste explanations remain ephemeral.
A substantial reusable synthesis, or a smaller recommendation the user
explicitly asks to retain, may be stored by SelfContext under `derived/` as a
linked `derived_synthesis`. It must remain derived and must not update a work
reaction, taste pattern, `core/` preference, or verification state automatically.

A supplied work reaction or explicit request to update taste context is an
ingest operation: preserve the smallest evidence, update the appropriate index,
create a backup before writing, and report whether the result was a meaningful
update or **No meaningful Media / Taste update**.
