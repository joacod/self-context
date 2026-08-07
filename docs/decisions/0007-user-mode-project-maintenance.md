# ADR 0007: Separate User Mode from Project Maintenance

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

SelfContext serves two different activities. A normal user wants to ingest,
query, review, lint, and receive advice without the system changing its own
implementation or interrupting the task with architecture suggestions. The
project also needs a way to improve its skills and operations when a problem is
explicitly identified.

Personal vault data is private user context, not a source of tracked project
fixtures or operational documentation.

## Decision

Default all normal interactions to **user mode**. User mode may read and update
the private vault according to the SelfContext lifecycle, but it must not modify
skills, schemas, docs, evals, scripts, architecture, repository structure, or
create an improvement log.

Enter **project-maintenance mode** only after the user explicitly asks to
diagnose, change, improve, evaluate, or redesign SelfContext's operational
behavior. If the user specifically asks about an operational issue, explain it
separately from the personal answer.

Never copy, quote, paraphrase, or encode real vault information into tracked
operational files. Reproductions, tests, examples, and proposed changes use
synthetic or abstract data only.

## Consequences

- Ordinary use stays focused and cannot silently grow a second project-workflow
  layer around the vault.
- Operational improvements are deliberate, reviewable, and user-authorized.
- A real vault may reveal that an operation is inconvenient, but the observation
  remains a user conversation until the user explicitly requests maintenance.
- Operational tests remain portable and privacy-safe because they use fictional
  fixtures rather than personal examples.
- The vault remains the durable personal asset without becoming an implicit
  feedback or telemetry channel for the repository.

## Alternatives Rejected

Automatic improvement logs, background architecture suggestions, implicit skill
rewrites, and copying real vault examples into evals were rejected because they
would interrupt normal use, blur the data boundary, and create privacy risk.
