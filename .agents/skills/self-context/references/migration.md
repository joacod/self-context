# Vault Migration

This is the canonical user-mode procedure for deterministic SelfContext vault
schema migration. Resolve this file relative to the installed
`.agents/skills/self-context/` skill; do not substitute a project-local
`.swe-forge/` tree or another harness store.

## What migration means

Schema migration is a deterministic change from a detected vault schema to a
supported target schema. It may update versioned control metadata, required
control indexes, managed catalog blocks, unambiguous control links, and other
versioned structural conventions documented by the migration registry.

Migration does **not** decide whether personal claims are true. It does not
rewrite personal prose, merge concepts, split ambiguous pages, change assertion
kinds, set `verified`, resolve contradictions, promote inferences, delete or
redact context, or enable every available vertical. When a future schema needs
semantic judgment, migration stops with a human-decision finding instead of
inventing an answer.

Keep these operations distinct:

- **Lint** is deterministic structural validation. It never migrates.
- **Deep lint** is broader deterministic inventory and integrity validation. It
  never migrates.
- **Review** is targeted semantic review. It never migrates unless the user
  separately requests migration.
- **Deep review** is a read-only full-vault maintenance analysis. It may
  recommend migration, but it never applies one.
- **Deep update** is an explicitly authorized maintenance mutation. It may
  delegate an explicitly requested schema migration to this procedure, but it
  must not reimplement migration or migrate merely because an old schema was
  found.
- **Vertical-contract update** changes one enabled vertical's documented
  contract, such as `writing@1` to `writing@2`. It is not a schema migration.

Migration can expose lint findings, stale contracts, ambiguous areas, or
unresolved semantic questions. It reports them without silently solving them.

## Authorization and natural language

### Read-only migration assessment

Requests such as these are assessment-only:

- “Does my vault need migration?”
- “Check whether my vault is using the latest schema.”
- “Plan a migration for my old vault.”
- “Show me what migration would change.”
- “Dry-run my vault migration.”

For an assessment:

1. Inspect the current and latest supported schemas.
2. Run the read-only migration planner.
3. Create no backup.
4. Write no file and append no log entry.
5. Do not retain a report unless the user explicitly requests retention.

A dry-run is useful even when the plan is blocked: return the structured
blockers and the smallest safe next action.

### Authorized migration

Requests such as these explicitly authorize the deterministic migration:

- “Migrate my SelfContext vault.”
- “Upgrade my vault to the latest supported schema.”
- “Bring my old vault up to date.”
- “Apply the required schema migrations.”
- “Use the latest SelfContext format.”
- `migrate vault latest` (the canonical shorthand form of the same authorized request).
- `migrate self-context latest` (a backward-compatible legacy alias).

Do not ask for a second confirmation merely because migration writes
`SCHEMA.md`, indexes, or other control files. The request already authorizes
this bounded structural operation. In the shorthand form, `latest` resolves at
runtime to the latest target exposed by the repository migration registry; do
not hard-code a schema version in the natural-language routing.

For an authorized request:

1. Produce the read-only plan first.
2. Continue automatically when the plan is valid and unambiguous.
3. Let the migration helper create its one pre-write backup.
4. Apply the complete supported migration path as one bounded transaction.
5. Validate the active final state and run the independent checks below.
6. Report the result and any remaining warnings or human decisions.

The natural-language agent orchestration must **not** create a separate backup
before invoking the helper. The helper owns the single pre-write backup for the
migration operation.

Stop before mutation when any of the following applies:

- the current schema is malformed or cannot be identified;
- the vault declares a future unsupported schema;
- the requested target is unsupported;
- no complete migration path exists;
- the plan contains blocking findings;
- the staged proposed final state does not validate;
- the vault changed between planning and writing;
- the helper's backup fails;
- the helper reports that it is not write-ready.

When blocked, do not attempt partial repairs outside this procedure. Explain the
blocker and the smallest actionable human decision or repair.

## Canonical sequence

### A. Orient

From the repository root:

1. Resolve only `<repository-root>/vault/` as the default vault.
2. Read `vault/SCHEMA.md`.
3. Read the root `vault/index.md`.
4. Inspect only recent `vault/log.md` entries needed for continuity.
5. Read enabled vertical indexes when the plan needs their control state.
6. Determine the current schema from `SCHEMA.md`.
7. Determine the latest schema exposed by the repository migration registry.

Do not use provider memory, another directory, or a harness-specific store.
Do not scan `backups/` archives or `vault/.obsidian/`; they are private
operational/viewer state and are excluded from canonical migration discovery.

For a significant operation, also read the relevant schema and backup
references:

- [Vault Schema](vault-schema.md)
- [Vault Backups](backups.md)
- [Initialization](initialization.md)
- [Deep Maintenance](deep-maintenance.md)

### B. Produce a read-only migration plan

Invoke the helper from the repository root, using the default `vault/` only
when no explicit vault path was supplied:

```bash
python3 .agents/skills/self-context/scripts/migrate_vault.py \
  vault \
  --check \
  --target latest \
  --format json
```

The existing commands remain backward compatible:

```bash
python3 .agents/skills/self-context/scripts/migrate_vault.py vault --check
python3 .agents/skills/self-context/scripts/migrate_vault.py vault --write
```

Without `--target`, both commands target the latest schema supported by this
repository. An explicit supported target may be supplied for maintainers or
controlled compatibility checks:

```bash
python3 .agents/skills/self-context/scripts/migrate_vault.py \
  vault --check --target 0.2 --format json
```

Inspect the JSON fields; do not infer results from console prose. A plan
exposes at least:

- current/source schema and requested/target schema;
- latest supported schema and supported target labels;
- complete ordered migration path and edge labels;
- source snapshot ID and proposed final snapshot ID when applicable;
- whether the vault is already current, whether migration is needed, and
  whether the plan is write-ready;
- `findings`, `blocking_findings`, warnings, human decisions, and registry
  validation findings;
- files to create and modify, files intentionally preserved, and the predicted
  write set;
- inferred enabled verticals and exact enabled contract versions;
- custom areas and ambiguous areas that remain preserved and unresolved;
- proposed-state validation and its ordinary/deep/catalog results where
  available.

The registry resolves a deterministic complete path. It rejects duplicate
edges, cycles, unsupported targets, future schemas, invalid registries, and
missing paths before any active-vault write. A future multi-step registry is
planned entirely in staging: every edge is composed into one proposed final
state before the final state is validated or one backup is created. The active
vault is never exposed to an intermediate schema.

### C. Decide

If the plan says the vault is already on the latest supported schema:

- create no backup;
- write nothing;
- append no migration log entry;
- report that no migration is needed;
- optionally report deterministic lint warnings separately.

If the request was assessment-only, stop after reporting the plan. Do not
create a backup or retain a report unless retention was explicitly requested.

If the user explicitly authorized migration and the plan is valid and
unambiguous, continue automatically to the write operation. If the plan is
blocked, stop without writing and report the blocker and safest next action.

### D. Apply

For an authorized, write-ready plan, invoke the helper without making another
backup first:

```bash
python3 .agents/skills/self-context/scripts/migrate_vault.py \
  vault \
  --write \
  --target latest \
  --format json
```

Treat success as valid only when the structured result reports:

- a completed migration from the detected source to the requested target;
- the complete path that was applied;
- the helper's backup path;
- successful post-write validation; and
- no failed rollback or unresolved active-vault inconsistency.

The helper constructs and validates the complete proposed state before the
first active replacement. It creates exactly one pre-write backup, uses
temporary sibling files and atomic replacement where supported, and owns
rollback after replacement or post-write validation failure.

If the helper reports a rollback:

- do not attempt further vault changes;
- report whether rollback completed or failed;
- report the preserved backup path;
- distinguish the failed proposed migration from the active restored vault;
- if rollback failed, direct the user to restore from the reported backup and
  do not claim the active vault is safe.

### E. Verify independently

After a successful migration, run these independent read-only checks against
the same vault:

```bash
python3 .agents/skills/self-context/scripts/lint_vault.py \
  vault --format json
```

```bash
python3 .agents/skills/self-context/scripts/lint_vault.py \
  vault --deep --format json
```

```bash
python3 .agents/skills/self-context/scripts/sync_indexes.py \
  vault --check --format json
```

Do not run `sync_indexes.py --write` merely as cleanup. A successful migration
must already produce synchronized managed indexes. If any independent check
unexpectedly fails, report a migration failure or inconsistency and identify
the migration backup. Do not perform unplanned semantic or structural repairs.

### F. Report

Keep the user-facing report concise and do not expose unnecessary private page
content. Include:

- original schema version;
- resulting schema version;
- migration path applied, or that no path was needed;
- whether migration was needed;
- backup path when a migration was applied;
- files created and modified;
- important files intentionally preserved;
- enabled vertical contracts recorded;
- custom or ambiguous areas preserved;
- ordinary lint result;
- deep-lint result;
- managed-catalog check result;
- rollback result when applicable; and
- unresolved warnings or decisions requiring a human.

A no-op is a successful result, not an error. A blocked plan is not a partial
migration. Preserve the distinction between deterministic warnings and
semantic decisions the user must make.

## Migration boundaries

A version-defined migration may update `SCHEMA.md`, add required control
metadata and missing control indexes, add or update managed catalog blocks,
repair a control link when its target is unambiguous, record destination
contract versions required by the schema, and update documented migration log
control information.

It must not automatically rewrite personal prose, merge concepts, split
ambiguous pages, change assertion kinds based on model judgment, set
`verified`, resolve contradictions, promote inferences, delete or redact
context, enable a vertical merely because it is available, or apply a new
vertical interpretation without a documented vertical-contract migration.

When a future schema requires semantic changes, emit an explicit human-decision
finding and leave the active vault unchanged.
