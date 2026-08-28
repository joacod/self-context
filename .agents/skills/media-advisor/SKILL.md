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
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no separate media database, context store, or external service.
---

# Media Advisor

Media Advisor is an evidence-and-reasoning pack, not a media catalog, ratings
database, or second durable context store. SelfContext owns the vault, shared
schema, provenance, lifecycle, confirmation, persistence, and retrieval; this
pack reasons from the user's individual work reactions and taste observations.

## Boundary with SelfContext

For a personalized media or taste request:

1. Use the project-local `self-context` skill first. Choose the smallest Media
   scope and useful anchors, then use its bounded read-only
   `prepare_context.py` boundary before reasoning.
2. Read the [Media / Taste procedure](../self-context/references/media-taste.md)
   for ingest, update, review, and ownership rules. Read the [evidence and
   reasoning guide](references/evidence-and-reasoning.md) and [output and
   persistence guide](references/output-and-persistence.md) when their detail
   is needed.
3. Retrieve only relevant work pages, taste observations, source records,
   review items, and cross-vertical links. Do not build a complete catalog or
   use provider memory as personal evidence.
4. If reactions are missing, say so. Generic media knowledge or recommendations
   must be labeled generic rather than attributed to the user.

Media / Taste is available but not automatically enabled in schema 0.2. An
absent area is empty for read-only work and creates no files. For a request to
record, correct, abandon, revisit, supersede, or delete taste context, let
SelfContext apply the procedure, activation rule, provenance, and ordinary
commit boundary. The Advisor must not mutate the profile merely by answering.

For a task context packet, include only reactions and taste evidence relevant to
the task, plus conflicts, freshness, unknowns, paths, and exclusions. The
packet is derived and ephemeral unless explicitly retained under SelfContext's
persistence rules.

## Media / Taste scope

Media / Taste owns meaningful reactions to experienced cultural works,
consumption state when it helps interpret a reaction, recurring or competing
taste patterns, exceptions, and dated taste evolution. Learning owns what the
user learned, Relationships owns shared experiences, Writing owns
communication behavior, Career owns professional evidence, and `core/` owns
deliberately broad preferences. Link to those owners instead of copying claims.

## Evidence interpretation

- Individual user reactions are the primary evidence. Consumption or completion
  establishes exposure, not liking or preference.
- External metadata, plot summaries, copied reviews, and agent-generated
  reactions can identify or discuss a work but are not personal taste evidence.
- Do not infer a broad pattern from one work unless the user explicitly states
  that preference. Otherwise use multiple independent meaningful reactions and
  keep the pattern scoped and reviewable.
- Explain why supporting works fit, preserve exceptions, contradictions,
  medium differences, and dates, and treat review, stale, superseded, or
  inferred context as qualified.
- Never infer politics, religion, sexuality, identity, morality, health,
  personality, intelligence, or psychological traits from cultural consumption.

The [evidence and reasoning guide](references/evidence-and-reasoning.md) owns
the detailed pattern, recommendation, privacy, and insufficient-evidence rules.

## Reasoning modes

Adapt to the request:

- **Taste inventory:** group evidenced reactions by themes, styles, mechanics,
  pacing, creators, or media without flattening the user into a label.
- **Why this worked:** trace a liked work to the user's reaction and supporting
  patterns, including conflicts and uncertainty.
- **Recommendation:** compare a candidate with several evidenced works and
  explain matches and mismatches conditionally.
- **Cross-media pattern:** link work pages and state the shared feature the
  evidence supports without over-generalizing.
- **Exceptions:** preserve an outlier and why it mattered.
- **Taste evolution:** use dates and prior reactions to distinguish change from
  medium, mood, or context.
- **Capture or update:** route mutations through SelfContext, including
  no-update outcomes and noise prevention.

## Response contract

Use only the sections useful for the request, normally:

- **Bottom line:** direct answer or conditional recommendation.
- **Evidence:** individual works, reactions, dates, and linked patterns.
- **Matches and conflicts:** what fits and what cuts against the evidence.
- **Exceptions and evolution:** relevant outliers or changed preferences.
- **Uncertainty:** missing reactions, review pages, stale context, or generic
  assumptions.
- **Recommendation:** derived advice, never a new fact.

If the evidence does not support a pattern, say so instead of filling the gap
with a genre stereotype, rating, plot summary, or personality explanation.

## Persistence boundary

Ordinary recommendations, comparisons, and taste explanations remain
ephemeral. A substantial reusable synthesis, or a smaller result explicitly
requested for reuse, may be stored under `derived/` only through SelfContext's
duplicate, ownership, contradiction, freshness, metadata, link, log, backup,
and validation rules. Mark it `derived_synthesis`; it must not update a work
reaction, taste pattern, `core/` preference, or verification state automatically.
