# Vault Backups

Use the backup helper after every operation that creates, updates, deletes,
moves, or appends anything in the existing vault. This includes normalized
pages, source records, indexes, `log.md`, review resolutions, and persisted
derived or advice pages. Complete the intended writes and relevant validation
first, then make one backup for the operation, not one backup per file.

If another procedure already created the backup for the enclosing operation,
reuse that archive and do not create a second one.

Run it from the repository root:

```bash
python3 .agents/skills/self-context/scripts/backup_vault.py vault
```

The helper:

- rejects a supplied vault path that is itself a symlink;
- rejects every symlink anywhere inside canonical vault content rather than silently omitting linked content;
- verifies resolved archive paths stay below the resolved vault root;
- creates the project-root `backups/` directory beside `vault/` on the first
  backup;
- writes `backups/vault-YYYYMMDDTHHMMSSZ.zip` using a UTC timestamp;
- archives the vault state that exists when the helper runs, so callers must
  invoke it after the operation and its relevant validation. The backup
  directory is outside the vault, so archives cannot contain themselves or
  grow recursively;
- keeps only the three newest managed backup ZIPs; and
- deletes older managed backups only after the new archive has been created.

The archive is built in a temporary file, fully read/tested as a ZIP, and moved
into place atomically only after validation. A failed validation leaves no
partial destination. Treat a non-zero exit as an incomplete mutation: stop
further writes and report that the resulting vault still needs a successful
backup. Transactional helpers should roll back the mutation when they can;
ordinary agent-directed mutations cannot be assumed reversible. Report the
created backup and any retention cleanup after the operation completes.

The helper applies restrictive owner-only directory/file permissions where the
platform supports them without requiring POSIX behavior. ZIP archives contain
private vault content and are not encrypted. SelfContext does not add an
encryption dependency; use a separate user-controlled protection mechanism
when encryption is required.

Read-only retrieval, lint, or review that does not persist a log entry does not
need a backup. If the vault does not exist, there is no prior state to archive:
initialize the empty vault, complete the requested mutation and validation, then
create the first backup of that resulting state.

The project-root `backups/` directory is private operational state, not
canonical context. Do not index, search, lint, link to, or include its contents
as evidence. The ZIPs are Git-ignored separately from the vault and are
available for a separate user-controlled copy process.
