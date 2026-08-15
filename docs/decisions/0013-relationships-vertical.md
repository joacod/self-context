# ADR 0013: Add an Evidence-Backed Relationships Vertical

- **Status:** Accepted
- **Date:** 2026-08-11

## Context

SelfContext needs a way to preserve useful continuity about people without
turning the vault into a CRM, address book, social graph, or dossier of third
parties. Relationship context is about the user's connection with another
person: shared history, meaningful interactions, commitments, open loops, and
what will help before communicating again. It has a stronger privacy boundary
than ordinary domain context because much of the evidence concerns people who
are not the vault owner.

The existing vault already provides Markdown, relative links, provenance,
review, freshness, and epistemic categories. Relationships must reuse those
contracts and remain useful without Career, Writing, Learning, or Media / Taste.

## Decision

Add Relationships as a first-class, on-demand vertical:

- durable relationship context lives under `relationships/`, with a stable
  `index.md` and sparse person or group pages;
- relationship pages use shared frontmatter and readable body sections for
  relationship scope, shared context, meaningful interactions, commitments,
  open loops, evidence, and dated evolution; no relationship-strength score or
  third-party profile schema is added;
- individual interactions are retained only when they have future contextual
  value. A compact relationship fact is preferred to a full transcript, and
  source records remain under shared `sources/` when provenance benefits from
  them;
- user statements, reported statements, retained sources, agent observations,
  and derived preparation summaries remain visibly distinct;
- commitments distinguish actual promises from vague conversation and remain
  relationship context rather than becoming a task manager;
- inferred motives, reliability judgments, sensitive characteristics, and
  psychological profiles about third parties are not stored as facts. Explicit
  sensitive information is retained only when the user says it is genuinely
  necessary for a narrow purpose and the minimum detail is enough;
- explicit deletion, redaction, archive, and retention choices are honored, and
  removed relationship context is not silently recreated from old sources; and
- a Relationships Advisor Pack retrieves relevant context through SelfContext,
  supports conservative continuity and pre-interaction reasoning, and does not
  own another store or mutate the vault merely by answering.

## Consequences

- A copied vault remains inspectable without a relationship database, social
  graph, provider integration, or dedicated runtime.
- At the time of this decision, existing v0.1 vaults could remain operational.
  ADR 0020 supersedes that runtime policy: current SelfContext directs
  recognized older vaults through `upgrade vault latest` before normal
  Relationships operations, while migration still preserves the old vault.
- Career can retain professional evidence and Relationships can retain the
  ongoing human relationship when both have distinct purposes; links prevent
  uncontrolled duplication.
- The vertical can answer useful continuity questions while deliberately
  omitting incidental interactions and unrelated third-party information.
- Privacy review remains semantic and user-controlled; the deterministic linter
  validates shared structure but cannot decide whether a retained relationship
  detail is appropriate.

## Alternatives rejected

- A contact manager, CRM, social graph, relationship score, or automatic social
  profiling system was rejected because it centers the other person or volume
  of contacts rather than the user's intentional continuity.
- Retaining every email, chat, or calendar event was rejected because it creates
  surveillance-like noise and increases third-party exposure.
- Automatic personality, motive, reliability, or sensitive-trait inference was
  rejected because behavior is evidence, not a diagnosis or objective profile.
- A separate relationship schema, database, or runtime was rejected because the
  shared Markdown lifecycle is sufficient and keeps the vault portable.
