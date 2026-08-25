# SelfContext Architecture

SelfContext is how an existing AI harness/model can **think with context you
own**. It addresses meaningful conversations starting from zero even when
projects, decisions, goals, constraints, and previous thinking have history.
The benefit is to continue thinking instead of starting over. The technical
thesis is that context has a lifecycle.

## Layers

SelfContext has a replaceable execution layer above a durable file layer:

```text
existing AI harness/model
  |
  v
SelfContext skills
  |
  v
local Markdown Context Vault
(Markdown + YAML frontmatter + standard Markdown links)
```

The model and harness are already the agent. SelfContext does not ship a custom
agent runtime or dedicated SelfContext subagents. Optional Advisor Packs are
project-local specializations for a vertical; they help the current model
reason over retrieved context but do not add a runtime or own a second durable
context format.

Dependency direction is always:

```text
operational skills -> vault
```

The vault must never depend on a specific harness implementation.

## Horizontal Contextual Workflows

Contextual thinking and checkpoint run horizontally over this same architecture;
they are not additional layers, verticals, or storage systems. A conversation
is ephemeral by default, reasoning is not automatically memory, and the
operational loop is durable context -> targeted retrieval -> contextual
reasoning -> ephemeral exploration -> optional checkpoint -> smallest durable
update:

```text
durable context
      |
      v
targeted retrieval across relevant existing owners
      |
      v
contextual reasoning
(brainstorming, decisions, comparisons, tradeoffs)
      |
      v
ephemeral exploration
      |
      +--> optional checkpoint
                 |
                 v
       smallest durable update
       (existing ingest, query persistence, or review; or no mutation)
                 |
                 v
       existing Context Vault
```

Targeted retrieval may draw on multiple existing areas when the question needs
it. Each concept and vertical remains the canonical storage owner; cross-area
retrieval does not create a cross-vertical owner or copy claims between areas.
Brainstorming is an informal use case, not a vertical, and decision-making is
not a vertical. They are modes of contextual reasoning over existing context.

Generated reasoning, alternatives, and recommendations remain ephemeral unless
they pass the normal persistence rules. Read-only Query/contextual thinking does
not mutate canonical pages, operational logs, indexes, backups, vertical
markers, metadata, or generated artifacts by default. A checkpoint is an
optional inspection of the conversation that routes durable facts, decisions,
and project changes through existing ingest semantics, reusable conclusions
through existing query persistence, and unresolved items through existing review
semantics. A checkpoint dry-run only reports those routes and never starts a
write lifecycle. It is not a new storage system; it may legitimately result in
no mutation.
The checkpoint and Query procedures are the canonical lifecycle owners; other
documentation should link to them rather than define a parallel conversation
workflow.

An optional context receipt provides bounded reasoning provenance—the relevant
context, tradeoffs, uncertainty, and persistence outcome—without creating a
receipt file, provenance system, private reasoning transcript, or exposed
chain-of-thought. All of these workflows use the existing harness, model,
project-local skills, and local Markdown Context Vault; none requires a
dedicated SelfContext runtime or replacement harness.

## Optional Source Acquisition

When source material lives outside the vault, acquisition is an optional
boundary before SelfContext ingestion:

```text
External source
      |
      v
Harness-provided retrieval capability
      |
      v
SelfContext skills / normal ingest and provenance
      |
      v
Canonical Markdown vault
```

The current harness and model can be replaced, and retrieval capabilities can
be replaced independently. Depending on the harness, acquisition may use web
fetching, browser automation, repository or project tools, document parsers,
or MCP tools. These are examples of disposable harness capabilities, not
SelfContext integrations or supported dependencies. How they are configured,
secured, and maintained belongs to the harness/provider, not SelfContext;
SelfContext does not own or synchronize external systems. Retrieved information
enters through normal ingest and provenance; external systems do not become
another durable context store. The `vault/` remains the source of truth.

## User Mode and Project Maintenance

SelfContext has two deliberately separate modes:

- **User mode:** Normal ingest, review, lint, and explicitly retained advice
  may update the private vault and produce the user's response. Query and
  contextual thinking are read-only by default and do not update pages, logs,
  indexes, backups, metadata, or generated artifacts. User mode never modifies
  the tracked operational project, creates an improvement log, or starts an
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

## Backup Lifecycles

Ordinary mutations create one provisional recovery ZIP before their first
active write, then one final-state ZIP after writes and relevant validation. The
provisional is discarded only after final backup success; failures retain it and
block further writes. Deep maintenance and migration create the recovery ZIP,
apply and validate their bounded changes, then create and retain a final-state
ZIP alongside it. The dependency-free helper stores archives under the
project-root `backups/` directory beside `vault/`, outside the portable vault,
and retains the ten newest managed ZIPs. Read-only retrieval and validation do
not create a backup unless they also persist a log entry or other change.

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
|-- log.md          # complete operation history and continuity notes
|-- core/           # universal cross-domain personal context
|-- review/         # universal unresolved observations and review items
|-- sources/        # universal retained source or recollection material
|-- derived/        # universal reusable query/advice synthesis
|-- career/         # optional enabled Career area
|-- learning/       # optional enabled Learning area
|-- writing/        # optional enabled Writing area
|-- relationships/  # optional enabled Relationships area
|-- media/          # optional enabled Media / Taste area
`-- ventures/       # optional enabled Ventures / Projects area
```

Schema 0.2 is the current runtime schema. It initializes only universal
areas, and the SelfContext skill may create only the required vertical area on
first mutating use, record its exact available contract, and add its root link;
unrelated available verticals stay disabled. A recognized schema 0.1 vault is
not a normal activation target: it is inspected only enough to diagnose or plan
migration, then directed to `upgrade vault latest`. Any generated index
catalog, lexical search result, or deep review report is disposable/derived
maintenance output and must not become canonical evidence.

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
| Career | `career/` | Roles, history, project participation as professional evidence, skills, achievements, leadership examples, mentoring, public work, and professional goals | Career Advisor |
| Learning | `learning/` | Topics and concepts, qualitative knowledge states, meaningful gaps, misconceptions, corrections, mental models, prerequisites, and progression evidence | Learning Advisor |
| Writing | `writing/` | Observable communication behavior, reasoning-through-writing, reader awareness, editorial preferences, anti-patterns, and evidenced modes | Writing Advisor |
| Relationships | `relationships/` | The user's relationship with people: shared history, meaningful interactions, commitments, open loops, and dated evolution | Relationships Advisor |
| Media / Taste | `media/` | Reactions to experienced works, explainable taste patterns, exceptions, and dated taste evolution | Media Advisor |
| Ventures / Projects | `ventures/` | Initiative lifecycle, project-specific decisions, commitments, milestones, evidence, outcomes, dogfooding, adoption, and evolution | Ventures Advisor |

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
judgments are not inferred. Career, Ventures, Writing, Learning, and Media pages
remain the owners of their distinct claims and are linked rather than copied.

Media / Taste centers the user's reaction to individual cultural works rather
than a complete consumption history or external catalog. Work pages are sparse,
and patterns must explain their supporting reactions, scope, exceptions, and
dates. Consumption is not preference, generated reviews are not evidence, and
recommendations remain derived. Neither vertical adds a competing schema,
confidence database, runtime, or cross-domain dependency.

Ventures / Projects centers the living lifecycle of meaningful initiatives,
experiments, opportunities, proposals, collaborations, and projects. Its sparse
records preserve purpose, origin, lifecycle, current state, role, decisions,
commitments, milestones, evidence, outcomes, dogfooding or adoption, unknowns,
and dated evolution. Initiative lifecycle remains readable body content rather
than a second status machine. Ventures does not become a task manager, CRM,
repository catalog, generic business system, or source archive; Career owns what
participation demonstrates professionally, Learning owns knowledge state,
Relationships owns interpersonal continuity, and recommendations remain derived.

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
John Doe supplies a user-authored technical article
  -> SelfContext retains a source_record with authorship, date, and mode
  -> local analysis finds concrete examples before abstraction
  -> comparison finds the pattern already established for technical articles
  -> source provenance is preserved; profile updates: 0
  -> result: No meaningful update
  -> John later supplies a rough idea and a target reader
  -> Writing Advisor retrieves relevant Writing and project context, then helps
     develop the argument before drafting
  -> John edits an AI-assisted draft by removing generic phrasing and adding an
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

## Latest-first runtime compatibility

SelfContext targets one current runtime state rather than multiplying every
operation by every historical format:

| Vault state | Runtime policy |
| --- | --- |
| Latest supported schema and current applied contracts | Full normal runtime support. |
| Older recognized schema or applied contract | Upgrade/migration source. Diagnose or plan as needed, but do not run normal current ingest, query, activation, lint, review, advice, or mutation semantics. Use `upgrade vault latest`. |
| Future schema or contract | Safe compatibility blocker. Do not downgrade, guess, or mutate. |
| Malformed or unversioned state | Recovery/diagnostic path only until it can be safely interpreted. |

The shared orientation gate owns this distinction before downstream current
operations. Migration retains old-format parsing and deterministic conversion;
normal features do not each carry branches for 0.1, 0.2, and every future
version. This preserves backward-compatible upgrades without creating a
`query × schema`, `ingest × schema`, or `activation × schema` runtime matrix.
Historical schemas therefore behave like first-party import/upgrade formats,
not alternate live modes.

Applied vertical contracts follow the same boundary. An exact catalog version
is current; an older supported version requires its documented contract
migration through `upgrade vault latest`; a future, unknown, malformed, or
duplicate version blocks unsafe semantic operation. Availability is still
separate from adoption: a disabled vertical is not enabled merely because it
exists in the catalog.

## Available, enabled, and applied vertical contracts

The repository's compact `verticals.json` catalog defines the available
verticals, their areas, indexes, procedures, Advisor Packs, ownership, and
activation rules. Each procedure has a machine-readable header and a Contract
migrations section. Catalog paths are resolved relative to the SelfContext
skill that owns the catalog.

The canonical current-schema activation procedure is
[Initialization](../.agents/skills/self-context/references/initialization.md):
a current vault's first mutating use records the exact available
`vertical@version` for only the required vertical, completes the operation, and
follows the ordinary provisional/final backup lifecycle. Read-only queries and
assessments create nothing. A historical vault must pass the shared runtime
gate and upgrade before this activation semantics applies.

In schema 0.2, **available** means present in the repository catalog, **enabled**
means recorded in `SCHEMA.md` with its area, index, and root link, and **applied**
means the exact recorded version. Equal applied/available versions are current;
an older applied version requires its documented contract migration through
`upgrade vault latest` and blocks normal semantic operation until that path is
applied; a newer applied version is an unsafe blocker. Unknown IDs, invalid
versions, and duplicate entries for one ID are errors. The small parser accepts
only non-negative integer versions such as `writing@1`; semantic-version strings
and ranges are unsupported. Schema 0.1 has no contract markers and remains a
migration source only. An explicit migration follows the canonical [Vault
Migration procedure](../.agents/skills/self-context/references/migration.md):
the helper detects the current and latest supported schema, resolves a validated
registry path, creates a recovery backup, stages the complete final state,
applies and validates one bounded transaction, creates a final-state backup, and
rolls back when final validation or backup creation fails. It never rewrites
personal evidence.

## Latest-first upgrade orchestration

The normal user-facing way to keep an existing vault current is
`upgrade vault latest`. It hides lifecycle choices without collapsing the
internal responsibilities that make each change safe:

```text
upgrade vault latest
        |
        v
inspect state
        |
  +-----+-----------+----------------+
  |                 |                |
 schema          contracts       semantics
  |                 |                |
  v                 v                v
migration       documented       deep maintenance
registry        contract paths   review/update + adoption
  |                 |                |
  +-----------------+----------------+
                    |
                    v
          managed indexes + validation
                    |
                    v
             current vault
```

The architecture keeps these responsibilities separate:

- **Schema migration:** deterministic structural transformation of a historical
  vault into the latest schema.
- **Vertical contract migration:** semantic ownership and contract evolution
  for an enabled vertical; older applied contracts are upgrade inputs, not
  ongoing runtime modes.
- **New vertical adoption:** selective adoption and backfill when relevant
  durable evidence gives a disabled vertical a concrete reason to exist.
- **`upgrade vault latest`:** the user-facing orchestration layer over those
  mechanisms, including final synchronization and validation.

Together, these rules mean historical schemas and contracts move forward
through documented migration paths, while the latest schema and current
contracts remain the only normal runtime target. The orchestrator re-orients
after a schema transaction and leaves genuinely ambiguous meaning unresolved.
A new vertical is not a schema version and is adopted only when existing
durable evidence gives it a concrete reason. Runtime-only improvements may
require no vault change, and `latest` is derived from the current migration
registry, vertical catalog, procedures, and validators rather than stored as
another vault version field. The detailed lifecycle belongs to the canonical
[upgrade procedure](../.agents/skills/self-context/references/upgrade.md).

For maintainers, classify a meaningful change with this small rule:

- **Runtime-only improvement:** existing durable data works unchanged -> no
  upgrade step.
- **Additive semantic capability:** historical data benefits from the new model
  -> document how upgrade can assess and safely adopt, move, split, link, or
  defer it.
- **Vertical contract change:** ownership or meaning changed -> document a
  contract migration and its safe/forbidden historical changes.
- **Storage/schema change:** portable representation needs transformation -> add
  a deterministic migration registry edge and let upgrade delegate to it.

## Core Operations

The SelfContext skill recognizes natural-language intent and applies a lifecycle rather than a command vocabulary:

1. **Ingest** or update information, preserve useful provenance, avoid duplicate concepts, connect meaningful links, update navigation, and log the operation. Triage only high-impact or unresolved items for a bounded, batched confirmation follow-up. Authored Writing sources use a local-analysis and impact-comparison step before durable profile updates; Learning evidence uses a local comparison to separate exposure, understanding, demonstration, gaps, and corrections; Relationships separates shared context from third-party profiling; and Media / Taste separates consumption from reaction and pattern evidence.
2. **Query** through orientation, scoped indexes, targeted file search, metadata,
and link traversal. A read-only lookup or contextual-thinking answer does not
write pages, logs, indexes, backups, markers, metadata, or generated artifacts
by default. A trivial retrieval returns an answer without creating a page; a
substantial reusable synthesis or explicitly retained future-use guidance may
be stored under derived material only after a duplicate, ownership,
contradiction, and freshness check. Review status and freshness before using
context as current.
3. **Checkpoint** an explicit natural-language request by inspecting the current conversation for durable changes rather than summarizing or storing it. Classify supported facts, corrections, decisions, goals, preferences, project changes, derived conclusions, unresolved items, inferences, and ephemeral discussion; route each candidate through existing ingest, query persistence, ownership, provenance, contradiction, confirmation, backup, and review semantics. Assistant suggestions, brainstorms, rejected options, and transcripts remain non-durable unless the user's explicit decision independently justifies retention. A checkpoint may successfully make no mutation.
4. **Review** unresolved inferences, stale context, contradictions, ambiguous claims, missing provenance, and important changes needing attention.
5. **Lint** structural and epistemic integrity, including frontmatter, links, indexes, duplicates, metadata consistency, freshness, and schema drift. Current-vault lint requires the latest runtime state; migration-source validation can still inspect recognized old formats. Lint and deep lint never migrate.
6. **Upgrade** an existing vault through the latest-first orchestration above. It assesses first, delegates schema work to migration, uses deep maintenance for documented contracts/adoption/semantic work, synchronizes managed controls, validates, and reports deferred decisions.
7. **Migrate** through the canonical migration procedure for schema/format-only assessment or authorization. The natural-language workflow plans first and delegates the recovery/final backup lifecycle and transaction to the migration helper; `upgrade vault latest` may invoke it after its own assessment.
8. **Advise** through an Advisor Pack that retrieves evidence from the core skill and applies a domain-specific reasoning framework.
9. **Maintain** through current-vault lint, deterministic deep lint, read-only deep review, and explicitly authorized deep update. Deep review uses snapshots and bounded semantic passes but never writes by default. Direct deep maintenance does not operate as a legacy runtime; an old schema or stale contract is reported as requiring `upgrade vault latest`. The upgrade orchestration may delegate semantic phases after compatibility is current.

### Ordinary current-vault commit boundary

For an existing schema 0.2 vault with current applied contracts, ordinary
CREATE/UPDATE persistence accepts a thin prepared filesystem proposal rather
than a semantic mutation language:

```text
agent-owned semantic bytes + explicit activation + log metadata
    -> ordinary_commit.commit_mutation
    -> current runtime/input gate
    -> temporary staged vault
       -> explicit control activation
       -> managed catalog synchronization
       -> deterministic operation-log append
       -> ordinary validation
    -> one bounded active write set through file_transaction
       -> active validation and proposed-snapshot check
       -> final backup
       -> guarded provisional cleanup
    -> structured receipt
```

The helper rejects absolute/traversal/symlink/private-state/non-regular paths,
control/index writes, malformed labels, and deletion attempts. It independently
checks runtime compatibility and does not trust a prior `prepare_context` packet.
A no-op is detected before the log entry and backup lifecycle. Missing or
uninitialized vaults return `initialization-required` and remain owned by the
existing Initialization procedure; schema migration and deep maintenance are
separate high-level workflows that may share only the low-level transaction
kernel and deterministic control helpers.

`sync_indexes.py` compiles deterministic managed catalog blocks from page
metadata while preserving user-written text outside markers. It requires one
unambiguous marker pair per managed index, escapes Markdown-significant text,
percent-encodes unsafe path characters, and plans all index writes before an
atomic replacement/rollback sequence. `--check` is read-only; `--write` is
reserved for an authorized mutation workflow and, for ordinary commit, is run
only against the disposable staged vault. Catalog entries remain navigation
surfaces rather than evidence. `search_vault.py` provides read-only
local lexical retrieval without a permanent index, with optional explicit path
scopes, conservative contextual coverage filtering, canonical-over-derived
preference, and bounded linked-source expansion. `recent_log.py` provides a
bounded, complete-entry continuity slice from the canonical log, while
`search_log.py` provides bounded lexical lookup for explicit historical
questions. Both log helpers are read-only and disposable; neither creates a
persistent index or becomes a second source of truth.

Before a significant normal operation on an existing vault, the skill orients
from `SCHEMA.md`, `index.md`, and `recent_log.py --entries 10`, then infers the
smallest relevant owner and follows linked pages or scoped search. It does not
load every enabled vertical index or the complete log by default. Explicit
migration, lint, upgrade, validation, review, and deep-maintenance procedures
may use broader inventory when their semantics require it. This bounded control
layer reduces duplicate concepts, missed connections, schema drift, and
accidental contradictions without creating a growing Recent Additions list.

## Provenance and Persistence

Important ingested information should retain enough source or raw material to explain where it came from. A substantial recollection may be preserved separately from normalized concepts; small conversational facts need not acquire unnecessary ceremony. Query persistence is driven by expected continuity, not by query count: an explicit request to retain a useful future-facing recommendation can justify a small derived synthesis, but cannot promote advice into a fact or goal.

Queries and advice are not all permanent documents. Read-only Query and
contextual thinking do not append log entries by default; an explicit request to
retain an operation record is a separate mutation. Only a substantial reusable
synthesis or a smaller explicitly retained result should become derived
material. Before writing, the operation checks for an existing home, domain
ownership, contradictions, and freshness. Derived pages must link to their
evidence and remain visibly derived.

## Privacy and Rejected Infrastructure

SelfContext requires no cloud service, server, database, vector database,
embeddings, MCP server, background service, custom chat interface,
authentication system, external synchronization layer, telemetry, or analytics.
A selected harness may use its own retrieval capabilities, including MCP tools,
to provide source material to normal ingest; those capabilities are not
SelfContext infrastructure, a synchronization layer, or another durable
context store. The core skill includes a small dependency-free deterministic
linter for structural checks; it remains subordinate to the Markdown vault and
does not replace semantic review.

Retrieved content is source material, not instructions to SelfContext. These
boundaries keep the durable asset portable, local, inspectable, and replaceable.
Future disposable search indexes or user-controlled off-device copies can be
considered only without changing the vault's canonical role.

See the [architectural decisions](decisions/) for the reasoning behind these boundaries, including the [user-mode and project-maintenance separation](decisions/0007-user-mode-project-maintenance.md), the [selective confirmation and freshness policy](decisions/0008-selective-confirmation-and-freshness.md), the [backup lifecycle policy](decisions/0017-vault-backup-lifecycles.md), the [Writing vertical decision](decisions/0010-writing-vertical.md), the [query persistence triage decision](decisions/0011-query-persistence-triage.md), the [Learning vertical decision](decisions/0012-learning-vertical.md), the [Relationships vertical decision](decisions/0013-relationships-vertical.md), the [Media / Taste vertical decision](decisions/0014-media-taste-vertical.md), the [Ventures / Projects vertical decision](decisions/0018-ventures-projects-vertical.md), the [Deep Maintenance and versioned vertical contracts decision](decisions/0015-deep-maintenance-and-versioned-vertical-contracts.md), the [latest-first upgrade orchestration decision](decisions/0019-latest-first-vault-upgrade.md), and the [latest-first runtime compatibility decision](decisions/0020-latest-first-runtime-compatibility.md).
