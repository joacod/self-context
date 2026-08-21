# Upgrade Vault to the Latest SelfContext Model

This is the canonical internal procedure for the user-facing operation
`upgrade vault latest`. Resolve this file relative to the installed
`.agents/skills/self-context/` skill. It is an orchestration procedure, not a
new schema registry, semantic review engine, vertical detector, backup system,
or permanent state store.

## Contents

- [Intent and routing](#intent-and-routing)
- [Meaning of latest](#meaning-of-latest)
- [Authorization and safety](#authorization-and-safety)
- [Phase A: orient and assess](#phase-a-orient-and-assess)
- [Phase B: resolve schema](#phase-b-resolve-schema)
- [Phase C: update enabled contracts](#phase-c-update-enabled-contracts)
- [Phase D: assess and apply selective adoption](#phase-d-assess-and-apply-selective-adoption)
- [Phase E: bounded semantic maintenance](#phase-e-bounded-semantic-maintenance)
- [Phase F: synchronize and validate](#phase-f-synchronize-and-validate)
- [Backups, idempotence, and no-op behavior](#backups-idempotence-and-no-op-behavior)
- [Blockers and deferred decisions](#blockers-and-deferred-decisions)
- [Reporting](#reporting)
- [Boundedness and future changes](#boundedness-and-future-changes)

## Intent and routing

Recognize the exact shorthand:

```text
upgrade vault latest
```

Also recognize a general request to make an existing SelfContext vault current,
including “bring my SelfContext vault fully up to date,” “update my vault to the
latest SelfContext model,” “make my vault current with this version of
SelfContext,” and “upgrade my existing vault to everything supported now.”
These requests authorize the bounded lifecycle below; do not ask the user to
approve migration, contract work, adoption, and semantic maintenance one layer
at a time.

Keep intent-specific operations distinct:

| User intent | Procedure |
| --- | --- |
| General current-model upgrade | This procedure, `upgrade.md` |
| Schema or format only, such as `migrate vault latest` or “upgrade this vault to the latest schema” | [Vault Migration](migration.md) |
| Read-only broad maintenance inspection | [Deep Maintenance](deep-maintenance.md), `deep review vault` |
| Explicit bounded semantic/structural maintenance | [Deep Maintenance](deep-maintenance.md), `deep update vault` |
| One vertical's adoption or contract work | The owning vertical procedure and the deep-maintenance adoption rules |

Do not route ordinary ingest, query, targeted review, lint, or advice into this
full lifecycle. Existing advanced commands remain valid and continue to route
to their direct procedures.

## Meaning of latest

`latest` is computed from repository sources of truth at operation time. It is
not a field stored in the vault and must not introduce a feature or product
version such as `selfcontext_version: 0.8`.

A vault is current when all applicable checks below are satisfied:

- the schema is the latest supported schema exposed by the migration registry;
- each enabled vertical has the current applicable catalog contract, or a
  documented no-change contract migration has established that no update is
  required;
- the shared runtime gate classifies the schema and every applied contract as
  current, so downstream normal operations can assume the current model;
- an available-but-disabled vertical remains disabled unless existing durable
  evidence gives it a concrete, documented reason to be adopted;
- safe, relevant historical ownership work triggered by the changes has been
  applied, while ambiguous meaning remains explicitly unresolved;
- managed catalogs and control links are synchronized; and
- ordinary and deep structural validation pass.

Runtime-only improvements, prompt changes, new evaluations, and improved
retrieval normally require no vault mutation. A repository change becomes an
upgrade concern only when its current schema, vertical contract, ownership
rules, or managed controls change what the existing durable vault needs.

## Authorization and safety

`upgrade vault latest` is explicit authorization for this bounded upgrade. It
covers deterministic schema migration, documented safe contract migration,
selective vertical adoption, safe historical reorganization, managed catalog
synchronization, and validation without a second confirmation for each phase.

It is not permission to invent semantic answers. Preserve facts, source-derived
facts, observations, inferences, derived syntheses, provenance, verification,
freshness, contradictions, and historical evolution. Never use confidence as
verification. Never automatically decide a contradiction, change a goal or
preference, promote an inference, infer sensitive third-party information,
claim employment/business/relationship meaning, delete important history, or
redact context unless separately requested. A human decision is a successful
deferred outcome, not a reason to guess.

Use only `<repository-root>/vault/` unless the user explicitly supplies another
vault path. Keep the repository's tracked operational files separate from the
private vault, and use fictional data in any tracked test, fixture, example,
documentation, or comment.

## Phase A: orient and assess

Read only the control and evidence needed to choose the next phase:

1. Resolve the repository root and orient from `vault/SCHEMA.md` and
   `vault/index.md`, use the bounded `recent_log.py` view for continuity, and
   inspect enabled vertical indexes when the upgrade phase requires their
   control state.
2. Determine the schema and run the canonical read-only migration planner:

   ```bash
   python3 .agents/skills/self-context/scripts/migrate_vault.py \
     vault --check --target latest --format json
   ```

   Read the structured result, including `latest_supported_schema`, migration
   path, `write_ready`, blockers, inferred/applied contracts, and proposed
   validation. Do not reproduce migration planning in this procedure. When the
   schema is already current, an older readable applied contract may appear as
   a warning because schema migration does not own contract migration; carry
   that finding to Phase C instead of treating it as a schema blocker.
3. Run the existing read-only structural checks against the active vault:

   ```bash
   python3 .agents/skills/self-context/scripts/lint_vault.py \
     vault --format json
   python3 .agents/skills/self-context/scripts/lint_vault.py \
     vault --deep --format json
   python3 .agents/skills/self-context/scripts/sync_indexes.py \
     vault --check --format json
   ```

4. Load the current catalog from `references/verticals.json` and the owning
   procedure headers only as needed. Compare enabled/applied contracts with
   available versions. Use deep-lint inventory metadata, indexes, links, and
   contract scope to narrow any later full-page reads.

This phase is read-only. Do not create a backup, log entry, retained report, or
maintenance queue while merely assessing. The shared runtime gate may report an
older schema or contract as an upgrade-required source; it must not let normal
current semantics continue on that state. A future or malformed schema,
missing migration path, unsafe control state, or other blocker that prevents
safe interpretation stops the upgrade before later semantic work.

If the schema is current, contracts are current, no disabled vertical has a
concrete adoption reason, no triggered semantic maintenance is needed, and
catalog/control validation is clean, return exactly:

```text
Your vault is already current. No files changed.
```

Do not create a backup or write a log/report for this no-op.

## Phase B: resolve schema

If the planner says the schema is behind and the path is write-ready, delegate
the complete mutation to the canonical migration procedure and helper:

```bash
python3 .agents/skills/self-context/scripts/migrate_vault.py \
  vault --write --target latest --format json
```

The helper owns its recovery backup, bounded transaction, post-write
validation, final-state backup, rollback, and retention behavior. Do not wrap
it in another backup or reimplement its registry, staging, or writes.

Treat migration as successful only when its structured result confirms the
complete path, active post-write validation, recovery/final backup information,
and a safe rollback result. If planning, backup, replacement, validation, final
backup, or rollback fails, stop before contract, adoption, or semantic writes.
Report the blocker and recovery path; never repair around a failed migration.

After a successful migration, re-read the active `SCHEMA.md`, root index, log,
enabled indexes, and current deep-lint/catalog results. Re-run the shared
runtime gate and re-orient from the migrated active vault rather than reusing
the pre-migration inventory. The migration's control-file changes and backups
remain part of the final summary.
If the planner says the schema is already current, do not invoke the write path
and do not create migration backups.

## Phase C: update enabled contracts

After the vault is safely interpretable, compare every schema 0.2 applied
`vertical@version` with the exact current catalog version.

- Equal versions need no work.
- An older applied version is a readable upgrade source, not a normal current
  semantic runtime. Read only the affected migration path and evidence scope
  from the owning procedure. Apply a complete safe path when it is unambiguous,
  preserves history/provenance/verification, and is covered by this explicit
  upgrade authorization. A documented migration may validly produce no page
  change, but the exact applied contract still needs to be updated only when
  the procedure says that is safe.
- A newer-than-repository version, unknown ID, malformed version, duplicate
  entry, or incomplete path is not downgraded or guessed. Stop or isolate the
  unsafe contract operation, report the blocker, and do not claim that contract
  is current.

Use the existing deep-maintenance contract/update rules for any mutation and
its snapshot/backup lifecycle. Do not add contract conditionals to ordinary
ingest, create a second contract engine, or rewrite a vertical merely because
its catalog version changed. If an older contract has no complete documented
migration, the runtime gate remains blocked for that vertical: stop or report
the vault as not fully current rather than keeping the old semantics live.
Distinguish that compatibility blocker from deferred semantic decisions.

## Phase D: assess and apply selective adoption

Use the existing Deep Maintenance Protocol's Contract and adoption pass. Do
not add `detect_career()`, `detect_ventures()`, or another vertical-specific
detector. The catalog and each vertical procedure's ownership/activation rules
are the semantic source of truth.

For each available-but-disabled vertical, inspect only the evidence suggested
by indexes, deep-lint metadata, recent meaningful logs, links, and the owning
procedure. Decide whether existing durable evidence gives a concrete reason for
the vertical to exist:

```text
concrete durable evidence or repeated meaningful use case?
  no  -> leave the vertical disabled; report successful "not needed"
  yes -> candidate for selective adoption
```

When adoption is clearly justified, use the existing adoption mutation rules:
create only the required area, index, exact current contract marker (for schema
0.2), and root navigation link. Do not create placeholder personal pages or
activate unrelated verticals. Then use the bounded historical pass to:

- move material only when ownership is clearly wrong and links can be safely
  updated;
- split a mixed page only at a clear coherent boundary;
- otherwise link the existing owner and leave the material where it is; and
- preserve provenance, dates, assertion kinds, verification, review state,
  historical evolution, and ambiguous material.

A newly available vertical with no relevant evidence is not a warning or a
failure. It remains absent and disabled, and the successful upgrade reports no
adoption for it.

## Phase E: bounded semantic maintenance

Reuse the existing deep-review/deep-update concepts; do not implement a second
semantic review engine. Run a semantic pass only for bounded evidence
triggered by a schema migration, a contract change, a clearly justified new
vertical, changed ownership rules, or structural findings that expose stranded
or misowned context. Use deep-lint inventory to select pages before opening
full bodies.

Apply only safe, unambiguous current-model improvements authorized by this
request, such as a clearly misowned project-lifecycle page moving to Ventures
while its professional impact remains in Career, or an exact link/catalog
repair caused by that move. Preserve the ownership boundaries documented by
Career, Learning, Writing, Relationships, Media / Taste, Ventures / Projects,
Core, Sources, Review, and Derived. Do not broadly rewrite every page merely
because the repository was updated.

For each semantic candidate, classify the outcome as:

- `safe_structural`: apply inside the existing bounded update transaction;
- `semantic_proposal`: apply only when the change is deterministic and
  unambiguous under the owning procedure;
- `human_decision`: preserve the current material and defer it; or
- `no_change`: leave it intact and report the successful no-op.

Mixed ownership without a clear split, conflicting project state, uncertain
retention, unknown relationship/business meaning, and any inference about a
sensitive person remain `human_decision`. The upgrade must not fail unrelated
safe work merely because these findings exist, but it must report them.

## Phase F: synchronize and validate

Use the existing managed-index synchronizer and deep-maintenance validation,
not a second index implementation. A required catalog/control repair is part of
the existing mutation boundary; run `sync_indexes.py --write` only inside the
authorized bounded update after its recovery gate. Do not create an
orchestration-level backup around a helper that already owns one.

At the end of every mutating phase, validate the active vault with the existing
ordinary lint, deep lint, and managed-catalog check. Re-run the relevant
retrieval/index probes when pages moved or a vertical was adopted. A required
validation failure stops further writes and follows the existing rollback or
recovery procedure. A successful upgrade must leave indexes/control links valid
and must not claim an unresolved contract migration is complete.

## Backups, idempotence, and no-op behavior

The operation hides lifecycle complexity from the user but does not combine
transaction boundaries:

- schema-only work delegates recovery/final snapshots to migration;
- semantic, contract, adoption, or index maintenance delegates recovery/final
  snapshots to deep maintenance or the existing mutation owner; and
- when both occur, migration may finish its transaction first, then the active
  vault is re-oriented before a separate semantic transaction.

Do not create redundant orchestration backups. Report recovery/final paths
briefly when a mutating helper creates them. Read-only assessment and a true
no-op create no backup, log entry, report, or semantic rewrite.

The second run against an unchanged successfully upgraded vault must repeat the
Phase A assessment, find no applicable work, and return:

```text
Your vault is already current. No files changed.
```

It must not duplicate a vertical, contract entry, page, log entry, report,
backup, or index churn. Snapshot freshness and current control metadata, rather
than a stored upgrade version, provide this idempotence boundary.

## Blockers and deferred decisions

Hard blockers stop before unsafe later mutation:

- malformed, unversioned, or future unsupported schema;
- an older schema or contract when the requested operation is ordinary current
  runtime work and no explicit upgrade path is being executed;
- no complete supported migration path;
- failed required recovery backup, migration validation, or rollback;
- future/unknown/duplicate/malformed applied contract state;
- no complete documented contract migration where interpretation is unsafe;
- active-vault snapshot drift between plan and write; or
- failed required control/index validation where safe state cannot be proven.

Deferred semantic decisions do not block unrelated safe work:

- mixed or uncertain ownership;
- an unresolved contradiction or project state;
- uncertain historical retention or whether a page deserves durable status; and
- unknown relationship, business, or third-party meaning.

Report hard blockers as an incomplete upgrade, and report deferred decisions as
`Needs review`. Do not call a vault fully current while a materially blocking
contract migration remains unresolved. Do not turn a deferred semantic finding
into a false success by silently classifying it.

## Reporting

Keep the normal result concise and user-facing:

```text
Vault upgraded to the latest SelfContext model.

Updated
- Schema: 0.1 -> 0.2
- Added Ventures / Projects
- Reorganized 5 historical project records
- Updated 1 vertical contract
- Synchronized indexes

Needs review
- 2 ambiguous historical ownership decisions

Validation passed.
```

Mention “Your vault is already current. No files changed.” for a true no-op.
For a blocker, state the phase, the reason, whether files changed, and the
recovery path if a helper created one. Advanced details such as exact contract
versions, changed control paths, validation findings, and backup paths may
follow briefly. Never include private page bodies or duplicate internal phase
narrative in the normal response.

## Boundedness and future changes

Prefer schema metadata, catalog records, deep-lint inventory, ownership/index
relationships, contract migration scope, and current review batching before
opening full page bodies. Do not add a database, embeddings, background service,
permanent index, external runtime, global feature-version field, or custom
vertical detector.

For every meaningful future SelfContext change, ask:

1. **Runtime-only:** does existing durable data already work unchanged? If so,
   add no vault-upgrade step.
2. **Additive semantic capability:** would historical data benefit from the new
   model? If so, document how upgrade's adoption/semantic pass can safely
   assess, move, split, link, or defer it.
3. **Vertical contract change:** did ownership or meaning change? If so,
   document a complete contract migration, affected evidence, safe changes, and
   forbidden automatic changes.
4. **Storage/schema change:** does portable representation require a
   transformation? If so, add a deterministic migration registry edge and let
   upgrade delegate to it.

A future vertical procedure should answer the historical-upgrade question:
where earlier evidence likely lives, what can be safely reorganized, and what
must remain ambiguous. Its procedure remains the source of semantic ownership;
the orchestrator only sequences those documented mechanisms.
