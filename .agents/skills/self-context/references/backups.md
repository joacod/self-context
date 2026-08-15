# Vault Backups

The backup helper is a guarded snapshot primitive. Mutation workflows choose one
of two lifecycles so the active vault is recoverable while it changes and the
newest successful archive reflects the resulting state.

## Ordinary mutations

For an ordinary ingest, persisted query result, targeted review, or vertical
update, make a provisional recovery snapshot before the first active write:

1. Run the helper and retain the returned archive path as `provisional_backup`.
2. Apply the requested mutation, indexes, and log changes.
3. Validate the resulting vault.
4. Run the helper again and retain the returned path as `final_backup`.
5. Only after the final backup succeeds, discard exactly `provisional_backup`
   with the helper's guarded `--discard` mode.

The provisional archive protects the previous state if the mutation or final
backup fails. Keep it in that case, stop further writes, and report the
incomplete operation. Do not discard it before a valid final archive exists. If
final backup succeeds but guarded discard fails, keep the provisional, report
the cleanup failure, and do not force-delete it. Make one provisional and one
final backup for the operation, not one backup per changed file.

Run the final cleanup from the repository root:

```bash
python3 .agents/skills/self-context/scripts/backup_vault.py \
  vault \
  --discard "$provisional_backup"
```

`--discard` accepts only a managed ZIP inside the matching project-root
`backups/` directory. It cannot remove an arbitrary path, symlink, or file
outside that directory.

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
need a backup. If the vault does not exist, initialize the empty vault, create a
provisional snapshot of that initialized state, complete the requested mutation
and validation, create the final snapshot, and discard the provisional snapshot
only after final backup success.

The project-root `backups/` directory is private operational state, not
canonical context. Do not index, search, lint, link to, or include its contents
as evidence. The ZIPs are Git-ignored separately from the vault and are
available for a separate user-controlled copy process.
