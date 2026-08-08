# SelfContext Architecture

## Layers

SelfContext has a replaceable execution layer above a durable file layer:

```text
user
  |
  v
existing harness + selected model
  |
  +--> SelfContext skill
  |
  +--> Advisor Packs, such as Career Advisor
  |
  v
Context Vault: Markdown + YAML frontmatter + standard Markdown links
```

The model and harness are already the agent. SelfContext does not ship a custom agent runtime or dedicated SelfContext subagents. Advisor Packs specialize how the current model reasons over retrieved context; they do not own a second memory format.

Dependency direction is always:

```text
operational skills -> vault
```

The vault must never depend on a specific harness implementation.

## User Mode and Project Maintenance

SelfContext has two deliberately separate modes:

- **User mode:** Normal ingest, query, review, lint, and advice read or update
  the private vault and produce the user's response. They do not modify the
  tracked operational project, create an improvement log, or start an
  architectural review.
- **Project-maintenance mode:** Skill, schema, documentation, evaluation,
  script, or architecture changes happen only after the user explicitly asks to
  diagnose or improve SelfContext itself.

The data boundary is one-way. Personal vault evidence may inform a user-facing
answer, but it must never be copied, quoted, paraphrased, or used as a personal
example in tracked skills, documentation, evals, tests, scripts, or ADRs. Any
operational reproduction uses synthetic or abstract data. A suspected issue
may be explained when the user specifically asks about operations; routine use
does not turn it into a project task.

## Repository and Vault Boundary

The repository contains tracked operational instructions and documentation. The root `vault/` directory contains the user's private Context Vault and is ignored in its entirety by Git.

```text
self-context/
|-- tracked operational project
|   |-- .agents/
|   |-- docs/
|   |-- AGENTS.md
|   `-- README.md
`-- private untracked data
    `-- vault/
```

Git ignore is a commit-safety boundary, not a promise that a provider cannot see data supplied to it by the user. The vault should also be independently copyable without the repository.

The repository must not depend on an ignored empty directory being present after clone. The SelfContext skill owns first-run initialization and must also accept an existing vault copied into `vault/`.

## Portable Vault

The v0.1 taxonomy and schema are defined by the Phase 2 SelfContext skill in
`.agents/skills/self-context/references/vault-schema.md`. At minimum, an
initialized vault will contain self-description equivalent to:

```text
vault/
|-- SCHEMA.md       # organization, metadata, and lifecycle rules
|-- index.md        # navigation and concept entry points
|-- log.md          # recent operations and continuity notes
|-- core/           # cross-domain personal context
|-- career/         # the v0.1 vertical
|-- sources/        # retained source or recollection material where useful
`-- derived/        # reusable query/advice synthesis, visibly derived
```

The v0.1 skill may create additional domain subdirectories on demand, but it
keeps the vault understandable as ordinary files. Any generated index or cache
must be disposable and must not become canonical.

Canonical content uses Markdown, YAML frontmatter, and standard relative Markdown links. Obsidian may display and edit the same files, but Obsidian syntax is not required.

When a vault is opened in Obsidian, the application may create `.obsidian/`
viewer state. That directory is optional, noncanonical, and ignored by
SelfContext discovery and validation; it is not personal context.

## Concepts and Metadata

The smallest useful schema needs to support more than a title and body. Durable
pages carry shared metadata for type, title, description, tags, status,
generation, verification, sources, assertion kind, and freshness. Values may be
empty or null where the category allows it, but the metadata shape stays
consistent so generic tools can validate and navigate the vault.

Verification and attention are separate lifecycle dimensions. `verified: null`
means that no explicit confirmation event has been recorded; it does not mean
the claim is false or automatically requires a prompt. Selected high-impact,
ambiguous, contradictory, or inferred pages use `status: review` until the
user resolves them. `stale_after` is a nullable review deadline, not a claim of
currentness. Ingest may assign a narrow 90-day deadline, calculated from the
ingest date, to important explicit current-state user-stated or source-derived
facts, while most pages remain without an automated deadline.

At minimum, the lifecycle distinguishes:

- **User-stated facts:** directly stated or confirmed by the user.
- **Source-derived facts:** supported by a retained or referenced external source.
- **Agent inferences:** interpretations that remain visibly unverified until the user confirms them.
- **Derived syntheses:** analyses, queries, or advice created by combining existing evidence.

Inferences belong in a reviewable observation area until confirmed or rejected. Derived advice must never silently change a user's goals or other factual context.

## Core and Vertical Context

Core context contains information that may matter across domains, such as goals, values, communication patterns, decision patterns, preferences, and recurring constraints. Vertical context contains domain-specific concepts.

Career is the only v0.1 vertical. It may include roles, history, projects, skills, achievements, leadership examples, mentoring, public work, and professional goals. The architecture exposes a place for verticals without hardcoding the entire system around career or prematurely designing hypothetical domains.

## Core Operations

The SelfContext skill recognizes natural-language intent and applies a lifecycle rather than a command vocabulary:

1. **Ingest** or update information, preserve useful provenance, avoid duplicate concepts, connect meaningful links, update navigation, and log the operation. Triage only high-impact or unresolved items for a bounded, batched confirmation follow-up.
2. **Query** through orientation, indexes, targeted file search, metadata, and link traversal. A trivial retrieval returns an answer without creating a page; a substantial reusable synthesis may be stored under derived material. Review status and freshness before using context as current.
3. **Review** unresolved inferences, stale context, contradictions, ambiguous claims, missing provenance, and important changes needing attention.
4. **Lint** structural and epistemic integrity, including frontmatter, links, indexes, duplicates, metadata consistency, freshness, and schema drift.
5. **Advise** through an Advisor Pack that retrieves evidence from the core skill and applies a domain-specific reasoning framework.

Before a significant operation on an existing vault, the skill orients from `SCHEMA.md`, `index.md`, and recent `log.md` entries. This reduces duplicate concepts, missed connections, schema drift, and accidental contradictions without requiring a full-vault scan every time.

## Provenance and Persistence

Important ingested information should retain enough source or raw material to explain where it came from. A substantial recollection may be preserved separately from normalized concepts; small conversational facts need not acquire unnecessary ceremony.

Queries and advice are not all permanent documents. Every meaningful operation may be recorded in the log, but only a substantial reusable synthesis or advice result should become derived material. Derived pages must link to their evidence and remain visibly derived.

## Privacy and Rejected Infrastructure

SelfContext v0.1 requires no cloud service, server, database, vector database, embeddings, MCP server, background service, custom chat interface, authentication system, sync service, telemetry, or analytics. The core skill includes a small dependency-free deterministic linter for structural checks; it remains subordinate to the Markdown vault and does not replace semantic review.

These exclusions keep the durable asset portable, local, inspectable, and replaceable. Future disposable search indexes or user-controlled synchronization can be considered only without changing the vault's canonical role.

See the [architectural decisions](decisions/) for the reasoning behind these boundaries, including the [user-mode and project-maintenance separation](decisions/0007-user-mode-project-maintenance.md) and the [selective confirmation and freshness policy](decisions/0008-selective-confirmation-and-freshness.md).
