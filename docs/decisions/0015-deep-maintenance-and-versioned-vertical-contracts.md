# ADR 0015: Deep Maintenance and Versioned Vertical Contracts

- **Status:** Accepted
- **Date:** 2026-08-12

## Context

A small private vault can be navigated through its root and category indexes.
As a vault grows, stale catalogs, unreachable pages, duplicate concepts,
contract drift, and unclear ownership become expensive to find. A maintenance
system must improve retrieval without changing SelfContext into a generic
knowledge base or allowing generated interpretation to rewrite personal truth.

The existing project also has several optional verticals. Their procedures and
Advisor Packs need a versioned, selectively adopted contract surface without
forcing every vault to create every area. Legacy schema 0.1 vaults must remain
recoverable through migration, while current runtime behavior should not grow a
permanent branch for every historical format. The later latest-first policy is
recorded in ADR 0020.

## Decision

### Distinct maintenance modes

Keep five distinct operations:

- **Lint** is the fast deterministic structural validator for the current
  runtime; its explicit migration-source mode can still inspect schema 0.1 for
  upgrade validation.
- **Deep lint** is a deterministic read-only inventory and integrity pass. It
  adds symlink and UTF-8 safety, reachability, nearest-index ownership,
  managed-catalog synchronization, dead entries, duplicate title/alias/ID or
  meaningful content, type/assertion/path compatibility, provenance and
  derived-source relationships, supersession links, vertical contract checks,
  recent log links, and noncanonical-state exclusions. It does not decide
  whether a personal claim is true and has text/JSON output without full page
  bodies or a numeric health score.
- **Review** remains ordinary targeted semantic review. A request such as
  “review my current role” does not trigger a full-vault scan.
- **Deep review** is an explicit, read-only full-vault semantic maintenance
  review. It is the default for a deep-review request, requires no backup, and
  does not mutate files, append a log entry, create a report, or create an
  operations backlog unless the user asks to retain the report.
- **Deep update** is explicitly mutating. It reruns deep lint, compares the
  current snapshot with the reviewed snapshot, creates one pre-write recovery
  backup, applies safe structural changes and explicitly approved semantic
  proposals, leaves human decisions unresolved, synchronizes catalogs, validates
  the final state, creates one post-write backup, and retains both before
  recording one concise update entry.

Deep review uses bounded page-local, vertical, cross-vertical, contract/adoption,
and retrieval-readiness passes. Its findings identify severity, classification,
affected files, evidence trigger, recommended action, automation class, risk,
and status. `safe_structural`, `semantic_proposal`, `human_decision`, and
`no_change` make the boundary between automation and user authority visible.

### Available, enabled, and applied vertical contracts

The repository catalog is the source of truth for **available verticals**.
At the time of this decision it listed Career, Learning, Writing, Relationships,
and Media / Taste. It records each vertical's contract version, area, index,
procedure, optional Advisor Pack, ownership, exclusions, and activation rule;
subsequent extensions use the same catalog contract. Procedures contain
detailed semantic rules and a machine-readable header matching the catalog.

A schema 0.2 vault has an **enabled vertical** only when it records exactly one
`vertical@version` entry in `SCHEMA.md` and its area, index, and root link are
present. The **applied contract version** is the version recorded by the vault.
Availability does not mean enabled. Compare versions explicitly: equal is
current and valid; older is a recognized upgrade source that blocks normal
current semantic operation until
`upgrade vault latest` applies its documented path; newer is an error because
the repository cannot safely interpret a future contract. Unknown IDs, invalid
versions, and duplicate entries keyed by one vertical ID are errors, with
values preserved for reporting. A read-only query about an absent vertical
treats it as empty and creates nothing. Adoption is explicit and adds only the
necessary area, index, exact available contract marker, and root link; it does
not copy facts or create placeholder personal pages.

Schema 0.1 remains a legacy format without contract markers and is an
upgrade/migration source only. Normal first-use activation and mutation target
schema 0.2's current contract model; an older vault must be upgraded first.
Unrecognized or malformed schema state remains conservative and does not guess.

### Schema compatibility and migration

Schema 0.1 remains supported as a deterministic migration source. Current
SelfContext does not promise ordinary ingest, query, targeted review, advice,
lint, or maintenance semantics while a vault deliberately stays on 0.1. An
explicit schema migration, following the canonical procedure, or an explicitly
requested migration delegated by upgrade may upgrade a vault to schema 0.2.
Read-only orientation and migration-source validation may inspect it, while
deep review, deep lint, ordinary lint, and unrelated deep-update work do not
silently migrate or operate it as current.

Schema 0.2 records a selective parseable section such as:

```yaml
schema_version: 0.2
vertical_contracts:
  - career@1
  - writing@1
```

New schema 0.2 vaults initialize only `core/`, `review/`, `sources/`, and
`derived/`. A vertical appears only when a triggering mutation or explicit
adoption requires it. The first mutating use creates only the required area and
index, records its exact available contract, adds the root link, completes the
operation, and follows the ordinary provisional/final backup lifecycle.
Read-only queries and assessments create nothing, and unrelated available
verticals remain disabled. The canonical [Vault Migration procedure](../../.agents/skills/self-context/references/migration.md) defines the natural-language assessment and authorized sequence. The migration helper creates a recovery backup, applies and validates its transaction, then backs up the final state while retaining both, infers enabled verticals conservatively from existing areas, indexes, and schema text, preserves every page and taxonomy, adds only control metadata and managed blocks, leaves unknown optional metadata empty, and reports ambiguous or custom areas instead of deleting or relocating them. The helper owns both migration snapshots; agent orchestration does not create separate ones.

The helper uses a dependency-free migration registry whose production latest is
schema 0.2 and whose supported edge is `0.1 -> 0.2`. The registry validates
duplicate edges and cycles, resolves a deterministic complete path, and reports
unsupported targets, future schemas, and missing paths. A future chain is
staged and validated as one final proposed state and applied in one bounded
transaction; test-only registry edges do not add a production schema.

Durable pages may optionally contain an `aliases` YAML list and a relative
Markdown `superseded_by` link. Empty optional fields are not bulk-added. Exact
normalized title/alias collisions are findings. A superseded page without a
valid successor link is warned about but retained.

### Compiled catalogs and retrieval

`sync_indexes.py` compiles managed catalog blocks delimited by explicit markers.
Each managed index must contain exactly one unambiguous start/end pair; duplicate,
nested, overlapping, reversed, or unmatched markers are reported without
choosing an authoritative block. Entries use the durable page's existing title,
description, status, and path, with stable ordering. Markdown text is escaped,
path components are percent-encoded, and presentation whitespace is normalized
without repairing the underlying metadata. Aliases affect retrieval only, not
catalog duplication. The nearest ancestor index owns the entry; parent indexes
may list child indexes. Text outside marker blocks is preserved byte-for-byte
when possible. `--check` is read-only; `--write` plans every affected index and
uses temporary sibling files plus atomic replacement and bounded rollback.
Catalog blocks are navigation surfaces, never evidence.

`search_vault.py` is a dependency-free, read-only lexical helper. It builds no
permanent index and ranks exact ID/title/alias matches, title/alias tokens,
description/tag matches, heading matches, and body matches in that order. It
keeps active concepts ahead of raw sources and prior syntheses by default,
keeps relevant review items visible, ranks archived/superseded pages lower,
and excludes deep reports and noncanonical state. Search results expose bounded
metadata/snippets; agents still inspect provenance, freshness, status, and
links. Query remains index-first.

### Update safety and backups

Before deep update mutation, the snapshot is compared with the reviewed
snapshot. A changed snapshot causes affected findings to be re-evaluated rather
than applying a stale plan. One pre-write recovery ZIP and one post-write final
ZIP are retained after the final validated write. The hardened helper rejects
symlink vault paths and canonical content, verifies archive paths remain below
the root, validates a temporary ZIP before atomic replacement, retains the ten
newest managed archives, and uses restrictive permissions where portable. ZIPs
contain private content and are not encrypted; no encryption dependency is
added.

Safe structural changes include managed index refreshes, unambiguous catalog
entries/dead generated entries, explicitly authorized schema-control migration,
deterministic formatting that preserves values, and exact-target link repairs.
Never automatically set `verified`, promote an inference, resolve a
contradiction, change goals/preferences, delete/redact context, merge
ambiguous pages, infer sensitive third-party details, or enable a vertical
solely because it is available. A default deep-update batch changes no more
than 25 personal durable pages unless the user explicitly requests a full
deterministic migration; control files do not count.

Retained deep-review reports live only under `vault/review/deep-reviews/` when
requested or while a deep update is being performed. They are private derived
maintenance artifacts, excluded from ordinary retrieval, and not personal
evidence.

## Rejected alternatives

- **Embeddings or a vector database:** rejected because deterministic local
  lexical retrieval and compiled Markdown catalogs are sufficient, portable,
  inspectable, and easier to validate for privacy and provenance.
- **A database or graph store:** rejected because Markdown remains the source
  of truth and a second canonical store would create synchronization and
  migration risk.
- **Background agents or services:** rejected because maintenance must not
  mutate a private vault without explicit user authority and the project does
  not add another runtime.
- **Automatic web enrichment:** rejected because external metadata is not
  evidence of the person, introduces network/privacy dependence, and could
  silently add context.
- **Wholesale vault rewrites:** rejected because they risk taxonomy loss,
  provenance changes, semantic reinterpretation, and difficult recovery. The
  migration is conservative and control-file-oriented.
- **Always enabling every vertical:** rejected because an available vertical
  may not be useful, and empty areas create noise and false expectations.
- **Numeric vault-health scores:** rejected because a single score would hide
  epistemic distinctions and imply a false precision that review findings do
  not support.

## Consequences

The vault gains deterministic maintenance and better task-oriented retrieval
without adding a database, embeddings, MCP, background service, custom runtime,
or synchronization layer. Deep review can identify semantic work while staying
read-only; deep update makes mutation explicit, backed up, bounded, and
reviewable. Schema 0.1 users retain backward-compatible migration, while
schema 0.2 users gain the latest-first runtime, selective contract tracking, and
managed catalogs.
