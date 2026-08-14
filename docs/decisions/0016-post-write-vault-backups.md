# ADR 0016: Create Post-Write Vault Backups

- **Status:** Accepted
- **Date:** 2026-08-14
- **Supersedes:** [ADR 0009](0009-pre-write-vault-backups.md)

## Context

SelfContext needs a local, bounded recovery archive without adding a service,
database, or remote synchronization mechanism. A pre-write archive protects the
state being replaced, but it means the newest backup is always one mutation
behind the active vault. Users primarily need the latest retained archive to
match the latest successfully ingested or modified state.

## Decision

After each mutation-producing operation completes its intended writes and
relevant validation, create exactly one ZIP snapshot of the resulting vault
under the project-root `backups/` directory beside `vault/`. Use the existing
UTC timestamped filename, atomic temporary-archive validation, restrictive
permissions, and three-managed-archive retention rules. Read-only operations
remain backup-free unless they explicitly persist a change.

A generic agent-directed mutation cannot be assumed reversible after a backup
failure. Therefore a failed post-write backup makes the operation incomplete:
report the failure, stop further writes, and retry the backup or use an existing
recovery archive before continuing. Transactional helpers that retain the
pre-mutation bytes may roll back when final-state backup creation fails. Schema
migration uses that boundary: it applies and validates its transaction first,
creates the final-state archive, and rolls back if the archive cannot be
secured.

The backup helper remains a current-state snapshot primitive rather than owning
mutation timing. Callers are responsible for invoking it after the operation
and its validation, and for reporting its path and retention cleanup.

## Consequences

- The newest successful backup represents the latest active vault state.
- Archives remain local, private, Git-ignored, and independently portable from
  the canonical Markdown vault.
- A backup failure after a generic mutation requires explicit recovery handling
  because the active files have already changed.
- Transactional operations preserve their stronger rollback guarantee without
  creating a second pre-write archive.
- Retention remains bounded at three managed ZIPs, and no background watcher or
  synchronization service is introduced.

## Alternatives Rejected

- Pre-write-only backups were rejected because the newest archive lags the
  resulting vault after every successful mutation.
- End-of-session backups were rejected because session termination is not
  reliably observable.
- A background watcher or service was rejected because it would add runtime
  infrastructure and make the vault less portable.
- Storing backups inside the vault was rejected because it couples private
  operational state to the portable vault and makes independent copies carry
  unrelated snapshots.
