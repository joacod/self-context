# ADR 0009: Create Pre-Write Vault Backups

- **Status:** Accepted
- **Date:** 2026-08-10

## Context

SelfContext cannot reliably detect when a user or harness session ends, so an
end-of-session backup would leave the most recent mutation unprotected. The
vault is private local data and may contain several writes during one
operation. It needs a recoverable point-in-time copy without adding a service,
database, or remote synchronization mechanism.

## Decision

Before the first write of each mutation-producing operation, create a ZIP of
the current vault under `vault/backups/`. Use a UTC timestamp in the filename,
build the archive before moving it into place, exclude `backups/` itself, and
retain only the three newest managed archives. A backup failure blocks the
planned mutation. Missing-vault initialization has no prior state to archive;
the first requested mutation is backed up after the empty structure exists.

The backup directory is operational state, not canonical context. SelfContext
ignores it during orientation, indexing, search, linting, and evidence use. A
separate user-controlled process may copy these local files elsewhere.

## Consequences

- The latest completed pre-write state remains locally recoverable across sessions.
- Retention is bounded and cannot recursively archive prior backups.
- A failed or unavailable backup prevents an unprotected vault write.
- Backups remain private and Git-ignored with the vault.
- Recovery and off-device copying remain user-controlled rather than becoming a
  background service or sync feature.

## Alternatives Rejected

- End-of-session backups were rejected because session termination is not
  reliably observable.
- A background watcher or service was rejected because it would add runtime
  infrastructure and make the vault less portable.
- Including the backup directory inside each archive was rejected because it
  would cause recursive growth and duplicate old snapshots.
