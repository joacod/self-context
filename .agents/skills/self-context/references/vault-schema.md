# SelfContext Vault Schema

The vault is ordinary Markdown, YAML frontmatter, standard relative links, and
small control files. It is a personal-context format, not a generic wiki or
knowledge base. The private `vault/` is the source of truth; scripts compile
disposable navigation and reports but never replace it.

## Schema versions and vertical contract states

Schema 0.1 remains supported exactly as a legacy vault. Ordinary ingest, query,
review, lint, and advice preserve its schema text and do not add contract
markers or silently migrate it. A first meaningful mutation may create the
required vertical area, index, and root link using the legacy layout. Only an
explicit schema migration may upgrade it to schema 0.2.

Schema 0.2 is a backward-compatible maintenance upgrade. Its `SCHEMA.md`
contains a selective enabled-contract section:

```yaml
schema_version: 0.2
vertical_contracts:
  - career@1
  - writing@1
```

Keep these states distinct:

- **Available** means the repository catalog defines the vertical and its
  current contract version. Availability alone does not create files or make a
  vertical part of a vault.
- **Enabled** means a schema 0.2 vault records one applied `vertical@version`
  entry. The area, index, and root link are required structural companions;
  missing companions are errors. A schema 0.1 vault has no contract markers;
  its existing area/index/root-link evidence is reported as an inferred legacy
  vertical for inspection only.
- **Applied** is the exact version recorded in schema 0.2. Contract validity
  and currency are separate: an older applied version remains structurally
  valid and produces an update-available warning; the repository does not
  migrate it automatically. A matching version produces no update finding. A
  newer applied version is an error because this repository cannot safely
  interpret a future contract.

The contract list is keyed by vertical ID. Unknown IDs, malformed versions, and
more than one applied entry for the same ID are errors, and their values are
preserved for reporting rather than silently rewritten. The current parser
accepts only a single non-negative decimal integer after `@` (for example,
`writing@1`); semantic-version strings, ranges, and other formats are
intentionally unsupported. An available but disabled vertical is not missing.
A known schema 0.2 area without an applied marker is an error, not a reason to
delete or move it.

The migration helper infers enabled verticals conservatively from existing
areas, indexes, and schema text. It creates one backup before its first write,
preserves every page and custom area, adds only control metadata and managed
index blocks, and reports ambiguity rather than relocating anything. Optional
page metadata is not bulk-added.

## Top-level layout

A new schema 0.2 vault starts with only universal areas. It records an empty
`vertical_contracts:` section and does not create optional vertical areas until
needed:

```text
vault/
|-- SCHEMA.md
|-- index.md
|-- log.md
|-- core/
|   `-- index.md
|-- review/
|   `-- index.md
|   `-- observations/       # created when needed
|-- sources/
|   `-- index.md
`-- derived/
    `-- index.md
```

Create a vertical directory and index only when a triggering mutation requires
that vertical or the user explicitly adopts it. A read-only query about an
absent vertical treats it as empty and creates no files. On first required use, follow [Initialization](initialization.md): schema 0.1
adds only legacy area/index/root navigation without a contract marker; schema
0.2 makes one normal backup, creates only that vertical, records its exact
available contract, adds its root-index link, and continues the operation in
the same turn.

Schema 0.1 vaults may have the historical default areas, custom areas, or only
some verticals. Preserve their taxonomy. The current available verticals are
Career, Learning, Writing, Relationships, and Media / Taste; detailed
ownership/exclusion rules are canonical in the vertical procedures and the
catalog.

## Durable page metadata

Durable concept, observation, source, and synthesis pages use:

```yaml
---
type: concept
title: Synthetic example concept
description: Fictional navigation-oriented description.
tags:
  - example
status: active
generated: 2026-08-12
verified: null
sources: []
assertion_kind: user_stated_fact
stale_after: null
---
```

Required shared fields are `type`, `title`, `description`, `tags`, `status`,
`generated`, `verified`, `sources`, `assertion_kind`, and `stale_after`.
`type` is `concept`, `observation`, `source`, or `synthesis`. `status` is
`active`, `draft`, `review`, `archived`, or `superseded`. Assertion kinds are
`user_stated_fact`, `source_derived_fact`, `agent_inference`,
`derived_synthesis`, `source_record`, and `mixed`.

Optional durable-page fields:

- `id`: a stable identifier unique in the vault;
- `aliases`: a YAML list of alternate names useful for retrieval; and
- `superseded_by`: a relative Markdown link to the canonical successor.

Do not bulk-add empty optional fields to existing pages. Alias values must be a
list of non-empty strings. Exact normalized title and alias collisions are deep
lint findings. A `status: superseded` page without a valid `superseded_by` link
gets a warning, but its history is preserved.

Sources are provenance, not automatic verification. `verified: null` means no
explicit confirmation has been recorded; it is not false and does not itself
create a review item. Agent inferences remain reviewable, and derived
syntheses never become source evidence.

## Ownership and compatibility

- `core/` holds explicit cross-domain goals, values, preferences,
  communication/decision patterns, and recurring constraints.
- A vertical owns its domain-specific evidence in its own area.
- `review/` holds unresolved observations and human decisions.
- `sources/` holds retained source or recollection material when provenance is
  useful.
- `derived/` holds reusable query/advice syntheses, visibly derived.

Deep lint checks type/assertion/path compatibility, source and synthesis
assertion kinds, active inferences outside the review lifecycle, source cycles,
derived-only support chains, and stale derived syntheses relative to decisive
sources. It does not decide whether any personal claim is true.

## Links and indexes

Use standard relative Markdown links with `.md` targets. The nearest ancestor
`index.md` owns a durable page's managed catalog entry. The root index must
reach every canonical durable page through index links; parent indexes may list
child indexes. A managed block is delimited by:

```markdown
<!-- selfcontext:catalog:start -->
- [Synthetic concept](concepts/synthetic.md) — Fictional description. `active`
<!-- selfcontext:catalog:end -->
```

`sync_indexes.py` generates entries from the page's existing `title`,
`description`, `status`, and path, in stable order. Aliases help search but do
not create duplicate catalog entries. Text outside markers remains user-written
and is preserved byte-for-byte when possible. Generated catalog blocks are
navigation surfaces, never evidence.

`.obsidian/` viewer state and project-root `backups/` operational archives are
noncanonical and excluded from indexing, search, lint, snapshot IDs, and
retrieval. A deep report under `review/deep-reviews/` is also maintenance
output, not personal evidence.
