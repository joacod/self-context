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
   `derived/` plus the three root control files. Include an explicit empty
   `vertical_contracts:` section in `SCHEMA.md`.
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
the empty structure exists, create one normal pre-write backup before
continuing with the requested ingest or other mutation. The same backup covers
any first-use vertical activation in that operation. Subsequent writes follow
[the backup procedure](backups.md) before their first change.

The private directory is intentionally not tracked. Never add a `.gitkeep` or
other vault file to the repository merely to preserve the directory.

## Existing Vault

First determine the schema state from `SCHEMA.md`:

- **Schema 0.1:** preserve its text and legacy layout. A first meaningful
  mutation may create the required vertical area, index, and root link after
  the normal pre-write backup, but must not add contract markers or silently
  migrate to 0.2.
- **Schema 0.2:** parse `vertical_contracts` strictly and treat it as
  selective. An available vertical is not enabled merely because it exists in
  the repository catalog. A first meaningful mutation that requires a vertical
  creates only that vertical's area and index, records the exact available
  `vertical@version`, adds its root link, and continues the original operation
  after one normal pre-write backup. It does not enable unrelated available
  verticals. Missing area/index/root-link companions for an already applied
  contract are lint/maintenance errors.
- **Unrecognized or malformed state:** remain conservative and report the
  ambiguity. Do not guess a migration, infer a contract version, or create a
  vertical until the schema state is repaired or explicitly resolved.

Read-only queries, lint, assessments, and deep review never enable or create a
vertical and never create a backup merely because a vertical is absent. Use the
explicit migration helper for a 0.1-to-0.2 upgrade; it backs up before writing,
preserves pages and custom areas, and reports ambiguity.

An existing vault may have more files, a different ordering, or a previously
initialized schema. Preserve its knowledge and orient before changing it.

- If `SCHEMA.md` is absent, treat the vault as unversioned. Read its visible
  indexes, recent log if present, and relevant pages. Do not reorganize or
  rename the existing taxonomy merely to match the default layout. Add a concise
  schema note only when it accurately describes the observed structure, and
  otherwise remain conservative.
- If a schema declares a future or unknown major version, remain read-only,
  explain the compatibility issue, and ask before modifying content.
- If a required control file is missing, create only the missing file after
  checking that no conflicting file or convention exists. Create a pre-write
  backup first, then preserve all existing pages and links.

All available verticals follow the same schema-specific activation rule above.
The individual vertical procedures define ownership and evidence handling; they
must not redefine activation, contract markers, or schema migration behavior.

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

Vertical areas are optional and are created only when a triggering mutation
or explicit adoption requires them, following the schema-specific activation
rule below. Available verticals are Career, Learning, Writing, Relationships,
and Media / Taste.

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

Follow the schema-specific activation rule above. The `vertical_contracts:`
line in a new schema 0.2 `SCHEMA.md` is the explicit empty contract list; a
first vertical activation appends its exact `vertical@version` entry there.

- schema 0.1: after the normal pre-write backup, create only the required area,
  `index.md`, and root-index link; preserve the schema text and do not add a
  `vertical_contracts` entry;
- schema 0.2: after the normal pre-write backup, create only the required area
  and `index.md`, add the exact available `vertical@version` entry, add its
  root-index link, and continue the original operation;
- unrecognized or malformed state: report ambiguity and do not initialize the
  vertical.

Never create or enable a vertical for a read-only query, assessment, lint, or
review.

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
