# ADR 0008: Selective Confirmation and Freshness Review

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

Large ingests can create many source-derived and user-stated pages. Requiring a
confirmation prompt for every page would make ingestion difficult to use, but
leaving all pages with `verified: null` without an attention policy would make
important claims difficult to review later. Freshness has the same balance:
most pages do not need a deadline, while a small set of current-state claims can
become misleading if they are used indefinitely.

The vault must preserve the user's authority without treating model confidence,
repetition, or source presence as verification. It must also remain plain
Markdown without a queue database or a second memory format.

## Decision

Keep `verified` and `stale_after` nullable and use existing lifecycle metadata:

- `verified: null` means that no explicit confirmation event has been recorded;
  it is not false and does not automatically require review.
- `status: review` is the durable attention state for selected high-impact,
  ambiguous, contradictory, inferred, or explicitly requested items.
- Ingest remains non-blocking for ordinary context and asks at most one batched
  confirmation follow-up for selected items.
- In that follow-up, confirm verifies the named scope, revise updates it and
  verifies only an explicitly confirmed revision, later keeps review status,
  leave unconfirmed returns the item to active nullable context, and reject
  preserves the evidence while removing or superseding the normalized claim.
- Confirmation is page-scoped in v0.1. Mixed concepts should be split rather
  than verified as a unit after a partial confirmation.
- An agent may set `verified` only after an explicit user request or against a
  source the user explicitly selected as authoritative. Merely supplying or
  finding a source is not authorization. Model confidence and repeated evidence
  do not qualify.
- `stale_after: null` remains the default. A narrow automatic rule may assign a
  90-day deadline to important explicit current-state anchors such as an active
  role, employer, goal, availability, or hard constraint.
- Automatic deadlines apply only to user-stated or source-derived facts and are
  calculated from the ingest date, not a source publication date.
- Historical pages, ordinary source captures, stable skills, and general
  preferences remain without automatic freshness deadlines unless the user
  supplies a horizon.
- Expired context remains useful historical evidence. Current-sensitive queries
  must label it or ask whether it is still current before relying on it.
- Re-ingesting unchanged evidence preserves existing verification, freshness,
  status, assertion kind, provenance links, and linked review rationale.
  Materially new claims require a narrower scope or a new confirmation decision.
- Explicitly confirmed agent inferences become `user_stated_fact` only when the
  user confirms the interpretation as a factual statement. A user who only
  accepts an inference as a hypothesis does not promote it.

## Consequences

- Normal ingestion stays quiet while important uncertainty remains findable.
- The review queue does not grow merely because a page has `verified: null`.
- Query behavior carries the safety net for stale or dynamically untracked
  information without interrupting every ingest.
- Page design remains important because verification and freshness are shared
  metadata, not claim arrays.
- The deterministic linter remains structural and does not try to decide truth,
  importance, or the correct review horizon.

## Alternatives Rejected

- Prompting for every unverified page was rejected because it creates prompt
  fatigue and review debt during bulk ingestion.
- Model confidence, repetition, or source count as automatic verification was
  rejected because it creates a generated evidence loop.
- Automatic freshness deadlines for broad categories were rejected because
  categories do not reliably predict volatility.
- New confidence, claim-ID, verification-state, or freshness-kind fields were
  deferred until real usage demonstrates that existing page-level lifecycle
  metadata is insufficient.
