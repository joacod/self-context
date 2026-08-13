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
   +--> optional Advisor Pack for a specific vertical
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
|-- private operational state
|   `-- backups/
`-- private untracked data
    `-- vault/
```

Git ignore is a commit-safety boundary, not a promise that a provider cannot see data supplied to it by the user. The vault should also be independently copyable without the repository.

## Pre-Write Backups

Any operation that will mutate an existing vault creates one timestamped ZIP
before its first write. The dependency-free helper stores the archive under
the project-root `backups/` directory beside `vault/`, outside the portable
vault. It retains only the three newest managed ZIPs, and a failed backup blocks
the planned mutation. Read-only retrieval and validation do not create a backup
unless they also persist a log entry or other change.

The root `backups/` directory is private operational state rather than
canonical context and is ignored by Git. Because it is outside `vault/`, the
vault can be copied independently without backup archives. The local files can
be copied by a separate user-controlled process without introducing a
SelfContext sync service or changing the portable Markdown contract.

The repository must not depend on an ignored empty directory being present after clone. The SelfContext skill owns first-run initialization and must also accept an existing vault copied into `vault/`.

## Portable Vault

The portable taxonomy and schema are defined by the SelfContext skill in
`.agents/skills/self-context/references/vault-schema.md`. An initialized vault
will contain self-description equivalent to:

```text
vault/
|-- SCHEMA.md       # organization, metadata, and lifecycle rules
|-- index.md        # navigation and concept entry points
|-- log.md          # recent operations and continuity notes
|-- core/           # universal cross-domain personal context
|-- review/         # universal unresolved observations and review items
|-- sources/        # universal retained source or recollection material
|-- derived/        # universal reusable query/advice synthesis
|-- career/         # optional enabled Career area
|-- learning/       # optional enabled Learning area
|-- writing/        # optional enabled Writing area
|-- relationships/  # optional enabled Relationships area
`-- media/          # optional enabled Media / Taste area
```

Schema 0.2 initializes only universal areas. The SelfContext skill may create
an available vertical area on demand when a triggering mutation or explicit
adoption enables its recorded contract, but a read-only query treats an absent
vertical as empty. Any generated index catalog, lexical search result, or deep
review report is disposable/derived maintenance output and must not become
canonical evidence.

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

## Core, Verticals, and Advisor Packs

Core context contains information that may matter across domains, such as goals,
values, communication patterns, decision patterns, preferences, and recurring
constraints. A vertical contains domain-specific concepts in its own top-level
vault area. An Advisor Pack reasons over retrieved context for a vertical; it
does not own storage, provenance, or a second memory system.

### Available Vertical Catalog

The available verticals have separate scopes and ownership. A private vault
may enable only a subset; availability does not create an area:

| Vertical | Vault area | Scope | Advisor Pack |
| --- | --- | --- | --- |
| Career | `career/` | Roles, history, projects, skills, achievements, leadership examples, mentoring, public work, and professional goals | Career Advisor |
| Learning | `learning/` | Topics and concepts, qualitative knowledge states, meaningful gaps, misconceptions, corrections, mental models, prerequisites, and progression evidence | Learning Advisor |
| Writing | `writing/` | Observable communication behavior, reasoning-through-writing, reader awareness, editorial preferences, anti-patterns, and evidenced modes | Writing Advisor |
| Relationships | `relationships/` | The user's relationship with people: shared history, meaningful interactions, commitments, open loops, and dated evolution | Relationships Advisor |
| Media / Taste | `media/` | Reactions to experienced works, explainable taste patterns, exceptions, and dated taste evolution | Media Advisor |

Learning does not own generic notes, bookmarks, course records, or source
summaries. It records what the person understands and how that state changes;
resources, projects, and authored work remain evidence owned by their source
verticals. Knowledge state, gaps, corrections, mental models, prerequisites,
and progression use readable Markdown sections and the shared lifecycle rather
than numeric scores or a knowledge graph.

Writing does not own beliefs, opinions, career facts, technical knowledge, or
generated drafts as authentic evidence. Retained Writing source and
generated-artifact pages carry explicit authorship, AI-involvement, and
evidence-role metadata so their role is inspectable without a separate schema.

Relationships centers the user's relationship with another person rather than
facts about that person. It keeps sparse pages for shared history, meaningful
interactions, commitments, open loops, and dated evolution. Reported statements,
source-derived facts, user observations, and agent inferences remain distinct;
sensitive third-party characteristics and unsupported motives or personality
judgments are not inferred. Career, Writing, Learning, and Media pages remain
the owners of their distinct claims and are linked rather than copied.

Media / Taste centers the user's reaction to individual cultural works rather
than a complete consumption history or external catalog. Work pages are sparse,
and patterns must explain their supporting reactions, scope, exceptions, and
dates. Consumption is not preference, generated reviews are not evidence, and
recommendations remain derived. Neither vertical adds a competing schema,
confidence database, runtime, or cross-domain dependency.

Additional verticals should consume the same shared lifecycle rather than create
competing formats. To add one, define its scope, give it a separate area and
index, document it in the current vertical catalog and README, and add a
vertical procedure or Advisor Pack only when domain-specific rules justify it.

The architecture exposes a place for verticals without hardcoding the entire
system around one domain. Writing ingestion analyzes a source locally before
comparing it with durable context. The comparison can reinforce an existing
observation, add a scoped candidate, refine a mode or period, preserve a
contradiction, represent evolution, or make no meaningful update. The last
outcome is successful and prevents redundant context growth. Qualitative
evidence states such as candidate, emerging, established, and explicit
preference remain readable observation content rather than a new confidence
database.

### Writing Lifecycle Example

Using fictional data, the lifecycle looks like this:

```text
Nia Vale supplies a user-authored technical article
  -> SelfContext retains a source_record with authorship, date, and mode
  -> local analysis finds concrete examples before abstraction
  -> comparison finds the pattern already established for technical articles
  -> source provenance is preserved; profile updates: 0
  -> result: No meaningful update
  -> Nia later supplies a rough idea and a target reader
  -> Writing Advisor retrieves relevant Writing and project context, then helps
     develop the argument before drafting
  -> Nia edits an AI-assisted draft by removing generic phrasing and adding an
     example
  -> the generated draft remains derived; the human delta is candidate revision
     evidence for a future selective refinement
```

The same pipeline can produce a scoped new observation, a mode refinement, a
reviewable contradiction, or a dated evolution. It never treats analysis or
generated prose as an automatic instruction to mutate the profile.

Relationships and Media / Taste use the same comparison principle: preserve
high-signal evidence, update an existing home when the identity matches, retain
contradictions and exceptions, and accept “No meaningful update” when a source
adds no durable personal context.

## Available and enabled vertical contracts

The repository's compact `verticals.json` catalog defines the available
verticals, their areas, indexes, procedures, Advisor Packs, ownership, and
activation rules. Each procedure has a machine-readable header and a Contract
migrations section. A private vault enables a subset and records the applied
contract versions in schema 0.2. Catalog paths are resolved from the installed
SelfContext skill, never from a project-local `.swe-forge` tree.

## Core Operations

The SelfContext skill recognizes natural-language intent and applies a lifecycle rather than a command vocabulary:

1. **Ingest** or update information, preserve useful provenance, avoid duplicate concepts, connect meaningful links, update navigation, and log the operation. Triage only high-impact or unresolved items for a bounded, batched confirmation follow-up. Authored Writing sources use a local-analysis and impact-comparison step before durable profile updates; Learning evidence uses a local comparison to separate exposure, understanding, demonstration, gaps, and corrections; Relationships separates shared context from third-party profiling; and Media / Taste separates consumption from reaction and pattern evidence.
2. **Query** through orientation, indexes, targeted file search, metadata, and link traversal. A trivial retrieval returns an answer without creating a page; a substantial reusable synthesis or explicitly retained future-use guidance may be stored under derived material after a duplicate, ownership, contradiction, and freshness check. Review status and freshness before using context as current.
3. **Review** unresolved inferences, stale context, contradictions, ambiguous claims, missing provenance, and important changes needing attention.
4. **Lint** structural and epistemic integrity, including frontmatter, links, indexes, duplicates, metadata consistency, freshness, and schema drift.
5. **Advise** through an Advisor Pack that retrieves evidence from the core skill and applies a domain-specific reasoning framework.
6. **Maintain** through ordinary lint, deterministic deep lint, read-only deep review, and explicitly authorized deep update. Deep review uses snapshots and bounded semantic passes but never writes by default. Deep update creates one backup before mutation and stops on failed post-write validation.

`sync_indexes.py` compiles managed catalog blocks from page metadata while
preserving user-written text outside markers. `search_vault.py` provides
read-only local lexical retrieval without a permanent index. Neither tool is a
second source of truth.

Before a significant operation on an existing vault, the skill orients from `SCHEMA.md`, `index.md`, and recent `log.md` entries. This reduces duplicate concepts, missed connections, schema drift, and accidental contradictions without requiring a full-vault scan every time.

## Provenance and Persistence

Important ingested information should retain enough source or raw material to explain where it came from. A substantial recollection may be preserved separately from normalized concepts; small conversational facts need not acquire unnecessary ceremony. Query persistence is driven by expected continuity, not by query count: an explicit request to retain a useful future-facing recommendation can justify a small derived synthesis, but cannot promote advice into a fact or goal.

Queries and advice are not all permanent documents. Every meaningful operation may be recorded in the log, but only a substantial reusable synthesis or a smaller explicitly retained result should become derived material. Before writing, the operation checks for an existing home, domain ownership, contradictions, and freshness. Derived pages must link to their evidence and remain visibly derived.

## Privacy and Rejected Infrastructure

SelfContext requires no cloud service, server, database, vector database,
embeddings, MCP server, background service, custom chat interface,
authentication system, external synchronization layer, telemetry, or analytics. The core skill
includes a small dependency-free deterministic linter for structural checks; it
remains subordinate to the Markdown vault and does not replace semantic review.

These exclusions keep the durable asset portable, local, inspectable, and replaceable. Future disposable search indexes or user-controlled off-device copies can be considered only without changing the vault's canonical role.

See the [architectural decisions](decisions/) for the reasoning behind these boundaries, including the [user-mode and project-maintenance separation](decisions/0007-user-mode-project-maintenance.md), the [selective confirmation and freshness policy](decisions/0008-selective-confirmation-and-freshness.md), the [pre-write backup policy](decisions/0009-pre-write-vault-backups.md), the [Writing vertical decision](decisions/0010-writing-vertical.md), the [query persistence triage decision](decisions/0011-query-persistence-triage.md), the [Learning vertical decision](decisions/0012-learning-vertical.md), the [Relationships vertical decision](decisions/0013-relationships-vertical.md), the [Media / Taste vertical decision](decisions/0014-media-taste-vertical.md), and the [Deep Maintenance and versioned vertical contracts decision](decisions/0015-deep-maintenance-and-versioned-vertical-contracts.md).
