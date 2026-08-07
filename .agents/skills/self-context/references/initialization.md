# Vault Initialization and Compatibility

## Missing Vault

When a request requires a vault and `<repository-root>/vault/` does not exist:

1. Create the `vault/` directory and the small top-level layout described in
   [the schema](vault-schema.md).
2. Create `SCHEMA.md`, `index.md`, `log.md`, and the category index pages from
   the templates below. Use the current ISO date in the initialization log.
3. Do not add personal placeholder concepts. Empty indexes may explain that
   context will be added through natural-language operations.
4. Continue the requested operation in the same turn. Initialization is not a
   reason to make the user repeat the request.

The private directory is intentionally not tracked. Never add a `.gitkeep` or
other vault file to the repository merely to preserve the directory.

## Existing Vault

An existing vault may have more files, a different ordering, or a previously
initialized schema. Preserve its knowledge and orient before changing it.

- If `SCHEMA.md` declares `schema_version: 0.1`, follow it and repair only
  missing control files or indexes that can be added without overwriting data.
- If `SCHEMA.md` is absent, treat the vault as unversioned. Read its visible
  indexes, recent log if present, and relevant pages. Do not reorganize or
  rename the existing taxonomy merely to match the v0.1 layout. Add a concise
  schema note only when it accurately describes the observed structure.
- If a schema declares a future or unknown major version, remain read-only,
  explain the compatibility issue, and ask before modifying content.
- If a required control file is missing, create only the missing file after
  checking that no conflicting file or convention exists. Preserve all existing
  pages and links.

Existing-vault support means the user can continue immediately; it does not
mean silently migrating or flattening their data.

## Obsidian Viewer State

Opening `vault/` in Obsidian may create `.obsidian/`. Do not create this
directory during initialization. If it already exists, preserve it as viewer
configuration, but ignore it during vault orientation, indexing, ingest, review,
and linting. It is not a source, concept, or other canonical vault page.

## Initialization Templates

Use these as content shapes, replacing `YYYY-MM-DD` with the current date. The
templates contain no personal information.

### `SCHEMA.md`

```markdown
# SelfContext Vault Schema

schema_version: 0.1

This directory is a portable SelfContext Context Vault. Markdown files are
canonical; standard relative Markdown links are canonical links.

Read this file, `index.md`, and recent `log.md` entries before significant
operations. See the category indexes for navigation. Keep user facts, source
records, agent observations, and derived syntheses visibly distinct.

Top-level areas:

- `core/`: cross-domain personal context.
- `career/`: the v0.1 career vertical.
- `review/`: unresolved observations and review items.
- `sources/`: retained source or recollection material.
- `derived/`: reusable query or advice syntheses.

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

Agent inferences normally remain `status: review` with `verified: null` until
the user confirms or rejects them. Derived syntheses remain derived and never
silently change a fact or goal. Do not use Obsidian wikilinks as canonical
syntax.
```

### Root `index.md`

```markdown
# SelfContext Vault

Portable personal context. Read [the schema](SCHEMA.md) before significant
changes and [the recent log](log.md) for continuity.

## Areas

- [Core context](core/index.md)
- [Career context](career/index.md)
- [Review queue](review/index.md)
- [Sources](sources/index.md)
- [Derived material](derived/index.md)
```

### Category indexes

Create these simple pages, changing only the heading and description:

```markdown
# Core Context

Cross-domain context such as goals, values, preferences, communication
patterns, decision patterns, and recurring constraints.
```

```markdown
# Career Context

Career-specific roles, history, projects, skills, stories, evidence, and
professional goals.
```

```markdown
# Review Queue

Unresolved observations, stale claims, contradictions, ambiguous assertions,
and missing provenance that need human attention.
```

```markdown
# Sources

Retained source material and important recollections that provide provenance.
```

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
- summary: Created the portable v0.1 vault structure.
- changed:
  - [schema](SCHEMA.md)
  - [index](index.md)
  - [core index](core/index.md)
  - [career index](career/index.md)
  - [review index](review/index.md)
  - [sources index](sources/index.md)
  - [derived index](derived/index.md)
- sources: none
- follow_up: Add context through natural-language operations.
```

Keep the initialization entry factual. The first requested ingest or query
should add its own operation entry rather than rewriting history.
