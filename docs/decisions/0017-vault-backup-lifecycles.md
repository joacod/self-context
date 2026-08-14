# ADR 0017: Use Provisional and Retained Recovery Backups

- **Status:** Accepted
- **Date:** 2026-08-14
- **Supersedes:** [ADR 0016](0016-post-write-vault-backups.md)

## Context

A final-state archive makes the newest successful backup match the active vault,
but an ordinary mutation can fail after its files have started changing. Deep
maintenance and schema migration already have bounded transactions and benefit
from retaining the state that existed before the operation. The backup history
also needs more room for rollback and later analysis than three archives provide.

## Decision

Use two backup lifecycles:

- **Ordinary mutations** create a provisional recovery ZIP before the first
  active write. After the mutation and validation succeed, create a final-state
  ZIP and discard only the provisional ZIP through the guarded backup helper.
  If the mutation or final backup fails, keep the provisional archive and stop
  further writes.
- **Deep maintenance and schema migration** create a pre-write recovery ZIP,
  apply their bounded work, validate the final state, and create a final-state
  ZIP. Retain both archives so the previous state remains available for rollback
  or analysis. Transactional helpers roll back active changes when final backup
  creation fails, while preserving the recovery archive.

The project-root `backups/` directory retains the ten newest managed ZIPs. The
existing UTC filenames, atomic archive validation, restrictive permissions,
private operational boundary, and no-backup read-only behavior remain unchanged.
The helper's discard mode accepts only a managed ZIP inside the matching
project-root backup directory and cannot remove arbitrary files or symlinks.

## Consequences

- Ordinary successful operations leave the final state as the newest archive
  without accumulating a redundant provisional snapshot.
- Failed ordinary operations retain a known pre-operation recovery point.
- Maintenance and migration preserve both before and after states for recovery
  and investigation.
- Ten retained archives provide more rollback and analysis room while remaining
  bounded and local.
- No background watcher, database, encryption dependency, or synchronization
  service is introduced.

## Alternatives Rejected

- A final-only ordinary lifecycle was rejected because a partial failed mutation
  could leave no immediate pre-operation recovery point.
- Discarding the pre-write archive for maintenance was rejected because deep
  updates and migrations benefit from retaining the prior state.
- Three retained archives were rejected as too narrow for rollback and analysis.
- A background watcher or service was rejected because it would add runtime
  infrastructure and make the vault less portable.
