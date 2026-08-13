# Vault Initialization and Compatibility

The repository catalog at `references/verticals.json` is the canonical list of
available verticals. A private vault enables only verticals it intentionally
contains and, in schema 0.2, records their applied contract versions. Schema
0.1 remains a legacy format during ordinary operations; do not add contract
markers or migrate it automatically.

## Missing Vault

When a request requires a vault and `<repository-root>/vault/` does not exist:

1. Create the `vault/` directory and universal schema 0.2 layout described in
   [the schema](vault-schema.md): `core/`, `review/`, `sources/`, and
   `derived/` plus the three root control files.
2. Create `SCHEMA.md`, `index.md`, `log.md`, and universal index pages from
   the templates below. Use the current ISO date in the initialization log.
3. Do not create every available vertical. Create and record only a vertical
   whose first requested mutation requires it, or one the user explicitly
   adopts. A read-only query about an absent vertical treats it as empty.
4. Do not add personal placeholder concepts. Empty indexes may explain that
   context will be added through natural-language operations.
5. Continue the requested operation in the same turn. Initialization is not a
   reason to make the user repeat the request.

There is no prior vault state to archive before first-run initialization. After
the empty structure exists, create a pre-write backup before continuing with
the requested ingest or other mutation. Subsequent writes follow
[the backup procedure](backups.md) before their first change.

The private directory is intentionally not tracked. Never add a `.gitkeep` or
other vault file to the repository merely to preserve the directory.

## Existing Vault

For a schema 0.2 vault, parse the `vertical_contracts` section and treat it as
selective. Do not create missing available verticals during read-only work. A
missing enabled area or index is a lint/maintenance finding. Use the explicit
migration helper for a 0.1 to 0.2 upgrade; it backs up before writing, preserves
pages and custom areas, and reports ambiguous structure.

A schema 0.1 vault remains supported without automatic migration. Ordinary
operations preserve its schema text and existing indexes.

An existing vault may have more files, a different ordering, or a previously
initialized schema. Preserve its knowledge and orient before changing it.

- If `SCHEMA.md` declares `schema_version: 0.1`, follow it and repair only
  missing control files or indexes that can be added without overwriting data.
- If `SCHEMA.md` is absent, treat the vault as unversioned. Read its visible
  indexes, recent log if present, and relevant pages. Do not reorganize or
  rename the existing taxonomy merely to match the default layout. Add a concise
  schema note only when it accurately describes the observed structure.
- If a schema declares a future or unknown major version, remain read-only,
  explain the compatibility issue, and ask before modifying content.
- If a required control file is missing, create only the missing file after
  checking that no conflicting file or convention exists. Create a pre-write
  backup first, then preserve all existing pages and links.

An existing vault may not have a `writing/` directory or `writing/index.md`. For
a read-only Writing query, treat the missing area as empty and do not create
files. For a Writing mutation, orient from the existing schema, index, and log,
create the pre-write backup, then add only `writing/` and `writing/index.md` and
add the Writing link to the root index. Do not rewrite `SCHEMA.md`, migrate other
pages, or reorganize an existing taxonomy merely to add the vertical.

An existing vault may not have a `learning/` directory or `learning/index.md`.
For a read-only Learning query, treat the missing area as empty and do not
create files. For a Learning mutation, orient from the existing schema, index,
and log, create the pre-write backup, then add only `learning/` and
`learning/index.md` and add the Learning link to the root index. Do not rewrite
`SCHEMA.md`, migrate other pages, or reorganize an existing taxonomy merely to
add the vertical.

An existing vault may not have a `relationships/` directory or
`relationships/index.md`. For a read-only Relationships query, treat the
missing area as empty and do not create files. For a Relationships mutation,
orient from the existing schema, index, and log, create the pre-write backup,
then add only `relationships/` and `relationships/index.md` and add the
Relationships link to the root index. Do not rewrite `SCHEMA.md`, migrate other
pages, or create a contact database merely to add the vertical.

An existing vault may not have a `media/` directory or `media/index.md`. For a
read-only Media / Taste query, treat the missing area as empty and do not create
files. For a Media / Taste mutation, orient from the existing schema, index,
and log, create the pre-write backup, then add only `media/` and `media/index.md`
and add the Media / Taste link to the root index. Do not rewrite `SCHEMA.md`,
migrate other pages, or create a media catalog merely to add the vertical.

Existing-vault support means the user can continue immediately; it does not
mean silently migrating or flattening their data.

## Obsidian Viewer State

Opening `vault/` in Obsidian may create `.obsidian/`. Do not create this
directory during initialization. If it already exists, preserve it as viewer
configuration, but ignore it during vault orientation, indexing, ingest, review,
and linting. It is not a source, concept, or other canonical vault page.

## Initialization Templates

Use the universal templates below as content shapes, replacing `YYYY-MM-DD`
with the current date. The optional vertical index templates are reference
shapes only; do not create them until a triggering mutation or explicit
adoption enables that vertical. The templates contain no personal information.

### `SCHEMA.md`

New vaults use the following schema 0.2 control metadata. Legacy 0.1 vaults
retain their existing schema text until an explicit migration.

```markdown
# SelfContext Vault Schema

schema_version: 0.2

vertical_contracts:

This directory is a portable SelfContext Context Vault. Markdown files are
canonical; standard relative Markdown links are canonical links.

Read this file, `index.md`, and recent `log.md` entries before significant
operations. See the category indexes for navigation. Keep user facts, source
records, agent observations, and derived syntheses visibly distinct.

Top-level areas:

- `core/`: cross-domain personal context.
- `review/`: unresolved observations and review items.
- `sources/`: retained source or recollection material.
- `derived/`: reusable query or advice syntheses.

Vertical areas are optional and are created only when their contract is enabled
by a triggering mutation or explicit adoption. Available verticals are Career,
Learning, Writing, Relationships, and Media / Taste.

Durable pages use YAML frontmatter described in this file's operational
documentation. The common fields are:

- `type`: `concept`, `observation`, `source`, or `synthesis`.
- `title`, `description`, and `tags`: navigation metadata.
- `status`: `active`, `draft`, `review`, `archived`, or `superseded`.
- `generated`: the ISO date or datetime when the page was normalized.
- `verified`: the ISO date or datetime of confirmation, or `null`.
- `sources`: relative Markdown paths or URLs supporting the page.
- `assertion_kind`: `user_stated_fact`, `source_derived_fact`,
  `agent_inference`, `derived_synthesis`, `source_record`, or `mixed`.
- `stale_after`: an ISO date when freshness review is due, or `null`.

Writing-tagged source and synthesis pages also require
`writing_evidence_role`, `authorship`, and `ai_involvement`. Use one of these
combinations: `primary/user/none`, `human_edited_ai_assisted/shared/assisted`,
`generated_derived/agent/generated`, or `unknown/unknown/unknown`.

Agent inferences normally remain `status: review` with `verified: null` until
the user confirms or rejects them. Derived syntheses remain derived and never
silently change a fact or goal. Do not use Obsidian wikilinks as canonical
syntax.
```

### Optional vertical initialization

When a first mutation requires a vertical, create only its area and
`index.md`, add the matching `vertical_contracts` entry, and add its link to the
root index after the normal pre-write backup. Never create a vertical for a
read-only query.

### Root `index.md`

```markdown
# SelfContext Vault

Portable personal context. Read [the schema](SCHEMA.md) before significant
changes and [the recent log](log.md) for continuity.

## Areas

- [Core context](core/index.md)
- [Review queue](review/index.md)
- [Sources](sources/index.md)
- [Derived material](derived/index.md)
```

### Universal category indexes

Create only the Core, Review, Sources, and Derived pages at initialization,
changing only the heading and description:

```markdown
# Core Context

Cross-domain context such as goals, values, preferences, communication
patterns, decision patterns, and recurring constraints.
```

### Optional vertical index shapes

When a vertical is enabled, create its index using the corresponding shape:

```markdown
# Career Context

Career-specific roles, history, projects, skills, stories, evidence, and
professional goals.
```


<!-- selfcontext:catalog:start -->
<!-- selfcontext:catalog:end -->
```markdown
# Learning Context

What the person understands and how that understanding evolves: knowledge
states, meaningful gaps, corrections, mental models, prerequisites, and dated
evidence. This is not a resource or course archive.
```


<!-- selfcontext:catalog:start -->
<!-- selfcontext:catalog:end -->
```markdown
# Writing Context

Evidence-backed communication, reasoning-through-writing, reader awareness,
editorial preferences, anti-patterns, and useful context-specific writing modes.
Generated drafts and generic writing advice are not authentic Writing evidence.
```


<!-- selfcontext:catalog:start -->
<!-- selfcontext:catalog:end -->
```markdown
# Relationships Context

Intentional context about the user's relationships: shared history, meaningful
interactions, commitments, open loops, and dated evolution. This is not a
contact database or a profile of everything known about another person.
```


<!-- selfcontext:catalog:start -->
<!-- selfcontext:catalog:end -->
```markdown
# Media / Taste Context

Reactions to cultural works and the evidence behind taste patterns, exceptions,
and evolution. This is not a complete media catalog or consumption tracker.
```


<!-- selfcontext:catalog:start -->
<!-- selfcontext:catalog:end -->
```markdown
# Review Queue

Unresolved observations, stale claims, contradictions, ambiguous assertions,
and missing provenance that need human attention.
```


<!-- selfcontext:catalog:start -->
<!-- selfcontext:catalog:end -->
```markdown
# Sources

Retained source material and important recollections that provide provenance.
```


<!-- selfcontext:catalog:start -->
<!-- selfcontext:catalog:end -->
```markdown
# Derived Material

Reusable queries, comparisons, analyses, or advice. Derived material is not
automatically personal fact.
```

### `log.md`

```markdown
# SelfContext Operation Log

## YYYY-MM-DD - initialize

- operation: initialize
- summary: Created the portable vault structure.
- changed:
  - [schema](SCHEMA.md)
  - [index](index.md)
  - [core index](core/index.md)
  - [review index](review/index.md)
  - [sources index](sources/index.md)
  - [derived index](derived/index.md)
- sources: none
- follow_up: Add context through natural-language operations.
```

Keep the initialization entry factual. The first requested ingest or query
should add its own operation entry rather than rewriting history.
