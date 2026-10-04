# Retain schema 0.2 after context evaluation

- Status: accepted for the Pass 2 implementation
- Date: 2026-10-03
- Scope: project mechanics and semantic procedures; no production migration

## Decision

Keep schema 0.2 and the existing page-scoped metadata contract. The fictional
[evaluation](../CONTEXT_EVALUATION.md) did not establish a semantic gap that
justifies adding mandatory claim metadata or migrating existing vaults.

| Case | Representation in 0.2 | Cost and limit |
| --- | --- | --- |
| Historical role versus availability | Explicit as-of dates in their owning pages; `generated`, `verified`, and `stale_after` retain their distinct meanings | The model must read the dated body; generation cannot establish currentness |
| Confirm one claim without another | Confirm an existing coherent remote-work page; leave availability and composite-page verification unchanged | Independent confirmation may justify separate coherent pages; do not split every statement |
| Partial supersession | Replace the current Availability section, keep its dated history and unchanged Location section/source links, leave whole-page `verified: null` | Page-level metadata cannot express section-level confirmation; prose must identify that scope |

Two independently dated confirmations on a composite page can likewise be
recorded beside their corresponding sections while whole-page verification
stays null unless its full scope was confirmed. This is a representation
argument, not a new automatic section-verification feature or a measured model
success rate. The exercised partial-confirmation and partial-supersession cases
validate the conservative path without adding fields.

An explicit validity/section provenance schema might enable deterministic
section filtering, but would impose authoring, parser, migration, validation,
and partial-supersession rules. No observed case required that capability.
Ambiguous historical dates and claim scopes could not be migrated safely by
inventing values. Keeping 0.2 avoids that migration cost and preserves portable,
readable Markdown.

## Consequences

Semantic guidance now compares new, repeated, corrected, narrowed and superseded
context before writing. Confirmation applies only to its supported scope;
re-ingestion is not renewed verification. Retrieval preserves original dates,
uncertainty and competing evidence.

Revisit this decision only with repeated failures that dated sections and
coherent independent pages cannot address, or a concrete requirement for
machine-readable section-level filtering. Such a change needs an exact schema
and migration contract, preserving unknown dates, original content, backups,
rollback, latest-first gates, and explicit authorization. No new schema version,
registry edge, contract version, or private-vault modification is part of this
implementation.
