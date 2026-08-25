# Vault Backups

The backup helper is a guarded snapshot primitive. Mutation workflows choose one
of two lifecycles so the active vault is recoverable while it changes and the
newest successful archive reflects the resulting state.

## Ordinary mutations

For an ordinary mutation against an existing current vault, `ordinary_commit`
owns the complete lifecycle and reports the result in one structured receipt.
Prepare semantic page bytes, explicit activation IDs when needed, and the small
log metadata, then invoke the helper. It stages and validates the proposal,
creates one provisional recovery snapshot, applies the bounded active write set
atomically, validates the active vault again, creates the final snapshot, and
performs guarded provisional cleanup only after final success.

Do not create a separate orchestration backup, run `sync_indexes.py --write`
against the active vault, append the log separately, or perform a second cleanup
step. After a successful `ordinary_commit`, do not invoke
`backup_vault.py --discard` separately. On a blocked or failed transaction, the
receipt identifies the source snapshot, rollback result, and retained
provisional archive. If final backup succeeds but guarded discard fails, the
helper keeps the provisional archive and reports a cleanup warning without
rolling back the valid committed vault. A semantic no-op creates no backup or
log entry.

The ordinary boundary supports only existing, current, compatible vaults and
CREATE/UPDATE writes. Missing or uninitialized vault bootstrap remains owned by
the existing [Initialization](initialization.md) procedure and is intentionally
not delegated to the ordinary helper. Schema migration and deep maintenance
retain their separate high-level backup lifecycles below.

## Deep maintenance and migration

For deep updates, schema migration, vertical adoption, and contract updates,
retain both snapshots. `upgrade vault latest` delegates to these existing
mutation owners and never adds an orchestration-level backup around them.

1. Create and record a pre-write recovery backup.
2. Apply the bounded maintenance transaction.
3. Validate the final state.
4. Create and record a post-write final-state backup.
5. Keep both the recovery and final archives for later rollback or analysis.

A transactional helper should roll back active changes when its final backup
fails, while preserving the recovery archive. A generic agent-directed
maintenance operation must stop and report the failure rather than claim a
successful backup.

## Helper

Run it from the repository root:

```bash
python3 .agents/skills/self-context/scripts/backup_vault.py vault
```

### Direct/manual backup management

For direct/manual backup management only, including manual recovery or
maintenance, discard a managed archive from the repository root with:

```bash
python3 .agents/skills/self-context/scripts/backup_vault.py \
  vault \
  --discard "$provisional_backup"
```

Ordinary current-vault mutations performed through `ordinary_commit` must not
invoke this command separately; `ordinary_commit` owns provisional cleanup and
reports it in its structured receipt. `--discard` accepts only a managed ZIP
inside the matching project-root `backups/` directory. It cannot remove an
arbitrary path, symlink, or file outside that directory.

The helper:

- rejects a supplied vault path that is itself a symlink;
- rejects every symlink anywhere inside canonical vault content rather than silently omitting linked content;
- verifies resolved archive paths stay below the resolved vault root;
- creates the project-root `backups/` directory beside `vault/` on the first snapshot;
- writes `backups/vault-YYYYMMDDTHHMMSSZ.zip` using a UTC timestamp;
- archives the vault state that exists when the helper runs. The backup
  directory is outside the vault, so archives cannot contain themselves or grow
  recursively;
- keeps only the ten newest managed backup ZIPs; and
- deletes older managed backups only after the new archive has been created.

The archive is built in a temporary file, fully read/tested as a ZIP, and moved
into place atomically only after validation. A failed validation leaves no
partial destination. Treat a non-zero exit as an incomplete mutation: stop
further writes, retain any recovery archive, and report that the resulting vault
still needs a successful final backup. Report every created archive, discarded
provisional archive, and retention cleanup after the operation completes.

The helper applies restrictive owner-only directory/file permissions where the
platform supports them without requiring POSIX behavior. ZIP archives contain
private vault content and are not encrypted. SelfContext does not add an
encryption dependency; use a separate user-controlled protection mechanism
when encryption is required.

Read-only retrieval, lint, or review that does not persist a log entry does not
need a backup. If the vault does not exist, the ordinary commit helper returns
an initialization-required state without creating `backups/`; the existing
initialization procedure may then create the empty layout and continue the
requested operation under its documented bootstrap lifecycle.

The project-root `backups/` directory is private operational state, not
canonical context. Do not index, search, lint, link to, or include its contents
as evidence. The ZIPs are Git-ignored separately from the vault and are
available for a separate user-controlled copy process.
