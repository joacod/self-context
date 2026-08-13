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
usable without an automatic migration.

## Decision

### Distinct maintenance modes

Keep five distinct operations:

- **Lint** is the fast deterministic structural validator and remains
  backward-compatible with schema 0.1.
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
  current snapshot with the reviewed snapshot, creates one pre-write backup,
  applies safe structural changes and explicitly approved semantic proposals,
  leaves human decisions unresolved, synchronizes catalogs, validates again,
  and records one concise update entry.

Deep review uses bounded page-local, vertical, cross-vertical, contract/adoption,
and retrieval-readiness passes. Its findings identify severity, classification,
affected files, evidence trigger, recommended action, automation class, risk,
and status. `safe_structural`, `semantic_proposal`, `human_decision`, and
`no_change` make the boundary between automation and user authority visible.

### Available, enabled, and applied vertical contracts

The repository catalog is the source of truth for **available verticals**:
Career, Learning, Writing, Relationships, and Media / Taste. It records each
vertical's contract version, area, index, procedure, optional Advisor Pack,
ownership, exclusions, and activation rule. Procedures contain detailed
semantic rules and a machine-readable header matching the catalog.

A schema 0.2 vault has an **enabled vertical** only when it records exactly one
`vertical@version` entry in `SCHEMA.md` and its area, index, and root link are
present. The **applied contract version** is the version recorded by the vault.
Availability does not mean enabled. Compare versions explicitly: equal is
current and valid; older is valid but reports an available update without
automatic migration; newer is an error because the repository cannot safely
interpret a future contract. Unknown IDs, invalid versions, and duplicate
entries keyed by one vertical ID are errors, with values preserved for
reporting. A read-only query about an absent vertical treats it as empty and
creates nothing. Adoption is explicit and adds only the necessary area, index,
exact available contract marker, and root link; it does not copy facts or create
placeholder personal pages.

Schema 0.1 remains a legacy format without contract markers. Its first
meaningful mutation may add the needed legacy area, index, and root link, but it
never silently migrates to schema 0.2. Unrecognized or malformed schema state
remains conservative and does not guess.

### Schema compatibility and migration

Schema 0.1 remains supported exactly as a legacy vault. Ordinary ingest, query,
targeted review, advice, and lint do not add contract markers, rewrite indexes,
or bump the schema. An explicit schema migration or authorized deep update may
upgrade a vault to schema 0.2.

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
index, records its exact available contract, adds the root link, creates one
normal pre-write backup at the documented point, and continues the operation.
Read-only queries and assessments create nothing, and unrelated available
verticals remain disabled. The migration helper backs up before its first
write, infers enabled verticals conservatively from existing areas, indexes,
and schema text, preserves every page and taxonomy, adds only control metadata
and managed blocks, leaves unknown optional metadata empty, and reports
ambiguous or custom areas instead of deleting or relocating them.

Durable pages may optionally contain an `aliases` YAML list and a relative
Markdown `superseded_by` link. Empty optional fields are not bulk-added. Exact
normalized title/alias collisions are findings. A superseded page without a
valid successor link is warned about but retained.

### Compiled catalogs and retrieval

`sync_indexes.py` compiles managed catalog blocks delimited by explicit markers.
Entries use the durable page's existing title, description, status, and path,
with stable ordering. Aliases affect retrieval only, not catalog duplication.
The nearest ancestor index owns the entry; parent indexes may list child
indexes. Text outside marker blocks is preserved byte-for-byte when possible.
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
than applying a stale plan. One pre-write ZIP backup is created before the
first write. The hardened helper rejects symlink vault paths and canonical
content, verifies archive paths remain below the root, validates a temporary
ZIP before atomic replacement, retains the three newest managed archives, and
uses restrictive permissions where portable. ZIPs contain private content and
are not encrypted; no encryption dependency is added.

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
reviewable. Schema 0.1 users keep ordinary compatibility, while schema 0.2
users gain selective contract tracking and managed catalogs.
