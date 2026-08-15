# ADR 0020: Latest-First Runtime Compatibility

- **Status:** Accepted
- **Date:** 2026-08-15

## Context

Schema 0.1 was the first SelfContext model, and schema 0.2 improved the vault
controls and selective vertical contracts. SelfContext now has the unified
`upgrade vault latest` workflow. Schemas, verticals, and semantic contracts will
continue to evolve, so indefinite runtime compatibility would multiply branches
across every operation while making the current model harder to reason about.

## Decision

- The latest schema and current applied vertical contracts are the only
  first-class runtime targets.
- Older recognized schemas and contract versions remain supported as
  deterministic upgrade/migration sources.
- The shared orientation gate classifies current, older, future, and malformed
  state before normal operations. Older state is directed to `upgrade vault
  latest`; future state is a safe blocker; malformed or unversioned state uses
  recovery/diagnostic behavior.
- Ordinary query, ingest, activation, lint, review, advice, and mutation do not
  silently auto-upgrade an old vault.
- `upgrade vault latest` is the user-facing bridge: it inspects state, migrates
  schema through the registry, applies documented contract migrations, performs
  selective vertical adoption and bounded current-model maintenance, then
  synchronizes and validates the current vault.
- No global SelfContext product-version field or per-feature compatibility
  matrix is introduced. `latest` remains derived from the migration registry,
  catalog, procedures, and validators.

## Consequences

### Positive

- Current runtime behavior has one schema/contract target instead of a growing
  cross-product of feature and historical-version branches.
- Existing knowledge remains recoverable and can move forward through strongly
  tested migration and upgrade paths.
- The normal user experience is simple: update the repository, run
  `upgrade vault latest`, then continue using SelfContext.
- Selective vertical activation remains intact; availability does not mean
  adoption.

### Trade-offs

- Users with old vaults must upgrade before using current functionality.
- Migration and documented contract paths are more important and require
  preservation, backup, validation, and idempotence coverage.
- Safe inspection and migration planning may still understand historical data,
  but they must not be mistaken for a promise of full old-format runtime
  support.

## Rejected alternatives

- **Indefinite full runtime support for every historical schema:** rejected
  because every query, ingest, lint, maintenance, and activation path would
  accumulate permanent compatibility branches.
- **Deleting old migration support:** rejected because backward-compatible
  upgrades are the product promise and existing knowledge must remain movable.
- **Silently auto-upgrading during normal query or ingest:** rejected because a
  read or ordinary mutation must not unexpectedly perform structural and
  semantic writes.
- **A global product or SelfContext version field:** rejected because latest is
  already derived from repository sources and a second version axis adds
  migration burden.
- **A per-feature compatibility matrix:** rejected because it recreates the
  combinatorial runtime complexity this decision removes.
