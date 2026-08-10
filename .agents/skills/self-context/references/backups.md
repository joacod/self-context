# Vault Backups

Use the backup helper before the first write of every operation that will
create, update, delete, move, or append anything in the existing vault. This
includes normalized pages, source records, indexes, `log.md`, review
resolutions, and persisted derived or advice pages. Make one backup for the
operation, not one backup per file.

If another procedure already created the backup for the enclosing operation,
reuse that archive and do not create a second one.

Run it from the repository root:

```bash
python3 .agents/skills/self-context/scripts/backup_vault.py vault
```

The helper:

- creates the project-root `backups/` directory beside `vault/` on the first
  backup;
- writes `backups/vault-YYYYMMDDTHHMMSSZ.zip` using a UTC timestamp;
- archives the vault state that exists before the operation. The backup
  directory is outside the vault, so archives cannot contain themselves or
  grow recursively;
- keeps only the three newest managed backup ZIPs; and
- deletes older managed backups only after the new archive has been created.

The archive is built in a temporary file and moved into place only after it is
complete. Treat a non-zero exit as a write blocker: do not modify canonical
vault content if the pre-write backup fails. Report the created backup and any
retention cleanup after the operation completes.

Read-only retrieval, lint, or review that does not persist a log entry does not
need a backup. If the vault does not exist, there is no prior state to archive:
initialize the empty vault first, then create a backup before continuing the
requested mutation.

The project-root `backups/` directory is private operational state, not
canonical context. Do not index, search, lint, link to, or include its contents
as evidence. The ZIPs are Git-ignored separately from the vault and are
available for a separate user-controlled copy process.
