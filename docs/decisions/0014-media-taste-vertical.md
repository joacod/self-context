# ADR 0014: Add an Evidence-Backed Media / Taste Vertical

- **Status:** Accepted
- **Date:** 2026-08-11

## Context

A list of media consumed or rated is not enough to explain the user's taste.
The useful personal context is the reaction to individual works and the
reasons behind recurring preferences, exceptions, and changes over time. The
system must remain useful without becoming Goodreads, Letterboxd, Spotify,
IMDb, or a general media catalog.

The existing vault already separates source evidence, user context, agent
inferences, and derived analyses. Media / Taste should expose individual work
reactions as primary evidence, support explainable patterns, and retain the
portable Markdown contract without making external metadata or integrations
canonical.

## Decision

Add Media / Taste as a first-class, on-demand vertical:

- durable work and taste context lives under `media/`, with a stable `index.md`
  and no required taxonomy by medium;
- individual work pages preserve intentional consumption state and the user's
  reaction, reasons, comparisons, and memorable details when they have future
  value; completion or consumption alone never implies liking;
- inferred patterns use shared observation pages and readable evidence, scope,
  exceptions, and evolution sections. One work supports a pattern only when the
  user explicitly states it; otherwise the agent requires multiple independent
  meaningful reactions before treating recurrence as plausible and keeps the
  interpretation reviewable;
- exceptions and dated evolution remain visible rather than being averaged into
  rigid preferences. Qualitative labels are body content, not a numeric
  confidence or rating schema;
- external identifiers and small descriptive metadata are optional and
  user-supplied. No external service, scraper, catalog, tracker, or complete
  third-party metadata store is required;
- generated reviews, recommendations, plot summaries, and agent reactions are
  derived output, never independent taste evidence;
- the vertical does not infer identity, ideology, politics, religion, sexuality,
  health, personality, or other sensitive characteristics from cultural
  consumption; and
- a Media Advisor Pack retrieves evidence through SelfContext, explains
  recommendations conditionally, and does not mutate taste context merely by
  producing an answer.

## Consequences

- A copied vault remains useful without a media provider, database, network
  integration, or recommendation engine.
- Existing v0.1 vaults do not require migration. New initialization exposes a
  Media index, while an older vault adds it only for a requested mutation within
  the provisional/final backup lifecycle.
- Recommendations can be explained by links to works and patterns while
  conflicts, exceptions, and freshness remain visible.
- The vertical avoids thousands of meaningless consumption records by requiring
  intentional reaction or future contextual value.
- Semantic evidence thresholds and taste interpretation remain agent and human
  review work; the deterministic linter validates structure only.
- Learning, Relationships, Writing, Career, and `core/` retain their own
  claims. Shared works are linked rather than duplicated.

## Alternatives rejected

- A ratings database, favorites list, watchlist, collection manager, or
  automatic play-history import was rejected because consumption without
  reflection is low-signal personal context.
- A complete media catalog or mandatory provider IDs was rejected because
  external metadata is available elsewhere and would dominate the portable
  vault.
- Inferring personality, politics, identity, or ideology from taste was rejected
  because cultural response is not reliable evidence for those attributes.
- Automatic pattern generation from one work, source count, or model confidence
  was rejected because it creates false preferences and context pollution.
- A recommendation engine, vector store, or custom runtime was rejected because
  the vertical only needs to expose evidence for future explainable reasoning.
