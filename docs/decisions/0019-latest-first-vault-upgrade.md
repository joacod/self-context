# ADR 0019: Latest-First Vault Upgrade Orchestration

- **Status:** Accepted
- **Date:** 2026-08-15

## Context

SelfContext has several safe maintenance primitives: schema migration,
vertical initialization and contract procedures, deep review, deep update,
managed-index synchronization, and validation. They have deliberately separate
safety and ownership boundaries, but asking a normal user to choose the right
sequence makes repository updates feel like an implementation task. A user who
has pulled a newer SelfContext should be able to ask one question: keep my
existing vault current with the model now available.

The repository also needs to preserve selective vertical activation, schema 0.1
compatibility, evidence ownership, provenance, human decisions, and the
provisional/final backup lifecycles. A single user-facing operation must not
become a second migration framework or a global feature-version system.

## Decision

Make `upgrade vault latest` the normal user-facing orchestration layer for
bringing an existing vault as close as safely possible to the current
SelfContext model. General equivalents such as “bring my vault fully up to
date” route to the same procedure. Schema-specific requests, `migrate vault
latest`, `deep review vault`, and `deep update vault` remain valid direct
advanced operations with their existing boundaries.

The upgrade procedure assesses first, resolves schema through the existing
migration registry/helper, re-orients from the migrated active vault, applies
safe documented enabled-contract updates, uses the existing deep-maintenance
contract/adoption and bounded semantic reasoning, synchronizes managed
controls, and validates. It reports deferred ambiguity rather than guessing.
It does not add a new vertical detector, migration engine, semantic review
engine, index implementation, backup engine, database, background service,
permanent index, or vault feature-version field.

`latest` is derived dynamically from the existing migration registry, vertical
catalog and procedures, and validation mechanisms. Runtime-only repository
improvements may therefore require no vault mutation. A current vault is a
successful no-op: it receives no backup, log entry, report, semantic rewrite,
or index churn.

New verticals remain selective. Availability alone does not create a vertical.
The upgrade may adopt one only when existing durable evidence provides a
concrete reason under that vertical's documented ownership contract. It may
safely move, split, or link clearly owned historical material, but leaves
ambiguous ownership and epistemic meaning for review. This makes historical
adoption useful without inventing context or creating empty areas everywhere.

Schema migration remains deterministic and transactional within its existing
helper. Semantic adaptation remains evidence-aware and bounded within the
existing deep-maintenance lifecycle. If both are needed, their existing
recovery/final snapshot boundaries remain separate; user-facing simplicity does
not require a new transaction engine.

## Consequences

### Benefits

- Users have one latest-first workflow after updating the repository.
- Schema, contract, adoption, semantic, index, and validation complexity stays
  in the mechanisms that already own it.
- Current vaults are cheap and idempotent, with no unnecessary backup or log
  churn.
- Relevant new verticals can preserve historical value instead of creating an
  empty directory only.
- Ambiguity, verification, provenance, and historical evidence remain visible.
- Future changes have a small decision rule: runtime-only, additive semantic,
  contract, or storage/schema transformation.

### Costs and risks

- A full upgrade can still require bounded semantic analysis and may report
  decisions the user must review.
- Migration and deep maintenance may create separate recovery/final snapshots
  when both phases run; this preserves existing rollback guarantees.
- A contract with no complete documented migration can prevent the result from
  being called fully current even when unrelated safe work succeeds.
- Natural-language orchestration depends on current procedure documentation;
  vertical authors must document historical evidence locations and safe versus
  ambiguous changes.

## Rejected alternatives

- **Automatically enable every available vertical:** rejected because
  availability is not evidence of relevance and empty areas create noise.
- **Make README teach migration, contracts, deep review, and deep update:**
  rejected because those are internal mechanisms, not the normal product
  experience.
- **Combine migration and semantic maintenance into one new transaction
  engine:** rejected because it would duplicate safety boundaries and weaken
  the existing helper-owned rollback guarantees.
- **Introduce a global SelfContext feature/product version in the vault:**
  rejected because latest is already derivable from repository sources and a
  second version axis creates compatibility and migration burden.
- **Require custom detector code for every vertical:** rejected because the
  catalog and owning procedure already define activation, ownership, and
  historical adoption semantics; custom detectors would duplicate them.
- **Create a new compatibility, index, backup, or semantic engine for upgrade:**
  rejected because upgrade is orchestration, not a replacement for the existing
  primitives.

## Implementation rule for future maintainers

For each meaningful change, ask whether existing durable data works unchanged;
whether historical data benefits from an additive semantic capability; whether
an ownership/meaning change needs a documented vertical-contract migration; or
whether the portable representation needs a deterministic schema migration.
Document the answer in the owning procedure and let `upgrade vault latest`
sequence the existing mechanism. Do not add another version taxonomy merely to
label the change.
