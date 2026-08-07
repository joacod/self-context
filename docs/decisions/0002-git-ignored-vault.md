# ADR 0002: Keep the Vault Local and Git-Ignored

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

The operational project benefits from being versioned and shared, while the user's personal context is private data that must not enter ordinary repository commits. Git cannot distribute an ignored empty directory, so a fresh clone cannot assume that `vault/` exists.

## Decision

The repository root `vault/` directory is entirely Git-ignored. The SelfContext skill owns first-run initialization and must also recognize a complete vault copied into that path. The vault remains independently portable and may be backed up or copied without the rest of the repository.

## Consequences

- Operational documentation and skills can be tracked without tracking personal information.
- A first-run operation must create the vault when needed.
- Git ignore reduces accidental commits but is not a privacy boundary against a model or provider that the user explicitly gives access to.
- Tests and tracked examples must use synthetic data outside the real vault.

## Alternatives Rejected

Committing a template vault, requiring manual taxonomy setup, or storing personal context in tracked repository files was rejected because each creates privacy, onboarding, or portability problems.
