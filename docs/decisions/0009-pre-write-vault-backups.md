# ADR 0009: Create Pre-Write Vault Backups

- **Status:** Superseded by [ADR 0016](0016-post-write-vault-backups.md)
- **Date:** 2026-08-10

## Context

SelfContext cannot reliably detect when a user or harness session ends, so an
end-of-session backup would leave the most recent mutation unprotected. The
vault is private local data and may contain several writes during one
operation. It needs a recoverable point-in-time copy without adding a service,
database, or remote synchronization mechanism.

## Decision

Before the first write of each mutation-producing operation, create a ZIP of
the current vault under the project-root `backups/` directory beside `vault/`.
Use a UTC timestamp in the filename, build the archive before moving it into
place, and retain only the three newest managed archives. A backup failure
blocks the planned mutation. Missing-vault initialization has no prior state to
archive; the first requested mutation is backed up after the empty structure
exists.

The root backup directory is operational state, not canonical context, and is
Git-ignored separately from the vault. Keeping it outside the vault means the
vault remains independently portable. A separate user-controlled process may
copy these local files elsewhere.

## Consequences

- The latest completed pre-write state remains locally recoverable across sessions.
- Retention is bounded and cannot recursively archive prior backups.
- A failed or unavailable backup prevents an unprotected vault write.
- Backups remain private and Git-ignored separately from the vault.
- Recovery and off-device copying remain user-controlled rather than becoming a
  background service or sync feature.

## Alternatives Rejected

- End-of-session backups were rejected because session termination is not
  reliably observable.
- A background watcher or service was rejected because it would add runtime
  infrastructure and make the vault less portable.
- Storing backups inside the vault was rejected because it couples private
  operational state to the portable vault and makes independent vault copies
  carry unrelated snapshots.
