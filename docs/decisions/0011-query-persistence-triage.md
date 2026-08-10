# ADR 0011: Query Persistence Triage

- **Status:** Accepted
- **Date:** 2026-08-10

## Context

SelfContext queries usually produce ephemeral answers, but some answers are
useful continuity anchors for later work. A result does not need to be high
impact or long to be worth retaining: a user may explicitly ask to keep a
recommendation because a similar question is likely to recur. At the same time,
automatic persistence would pollute the vault, duplicate existing analyses, and
make generated advice look like personal fact.

The existing lifecycle already separates source-derived facts, user-stated
context, reviewable observations, and derived syntheses. Query persistence needs
an explicit decision rule that connects those boundaries to user-signaled future
reuse and checks for conflicts across core, vertical, and derived material.

## Decision

Before persisting query-derived material, SelfContext performs a lightweight
triage:

- treat explicit requests to remember, retain, or reuse an answer as continuity
  signals, while treating positive feedback without future-use intent as
  insufficient by itself;
- classify the result as facts, source material, observations,
  recommendations, and unknowns before choosing a durable page type;
- search for an existing concept or synthesis and update it instead of creating
  a duplicate;
- keep domain facts in their owning vertical, cross-domain facts in `core/`, and
  reusable conclusions in `derived/`;
- compare the conclusion with active goals, facts, review items, and relevant
  derived pages, preserving factual contradictions and expressing competing
  recommendations conditionally; and
- record freshness limits when current context materially affects future reuse.

A small derived synthesis is allowed when it has stable future-use value or the
user explicitly requests retention. The request does not verify the advice,
change a goal, or authorize copying facts across ownership boundaries. If the
result has no continuity or review value, it remains ephemeral.

## Consequences

- Useful low-stakes guidance can remain available without treating every answer
  as memory.
- The user's future-reuse intent becomes an explicit persistence signal while
  the vault remains protected from automatic advice-to-fact promotion.
- Derived advice can connect evidence across verticals without duplicating the
  facts those verticals own.
- Query behavior must do a small semantic comparison before a write; the
  deterministic linter remains responsible only for structural integrity.
- No new schema type, database, index, or runtime is required.

## Alternatives Rejected

- Persisting every helpful answer was rejected because it would create context
  noise and duplicate pages.
- Persisting only high-impact or long analyses was rejected because it would
  lose small but explicitly reusable continuity guidance.
- Updating goals or vertical facts from recommendations was rejected because
  advice is not evidence of changed personal context.
