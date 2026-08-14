# SelfContext

SelfContext is a local, portable way to keep personal context that you own. It
stores durable information as ordinary Markdown files, so the context can be
read, edited, copied, and used across AI models and harnesses.

SelfContext is not a hosted app or a separate AI runtime. An existing AI
harness uses the project-local skills to work with the private Context Vault.

## Quick Start

Clone the repository and open it from the repository root in an AI harness that
supports project-local Agent Skills:

```bash
git clone <repository-url> self-context
cd self-context
```

Use natural language. For example:

```text
ingest my resume into SelfContext
what does my context say about [a skill or experience]?
review my context for stale or conflicting information
based on my context, how should I position myself for [a role]?
Migrate my SelfContext vault to the latest supported schema.
migrate vault latest
```

For migration, SelfContext plans first, stops safely when the plan is blocked,
creates one backup before writing, applies the supported migration chain, and
validates and rolls back when necessary. The user does not need to know schema
versions, migration paths, backup commands, index synchronization, or lint
commands.

After a schema or maintenance improvement, use these three copy-paste shortcuts
in order:

```text
migrate vault latest
deep review vault
deep update vault
```

`deep review vault` is read-only and returns a bounded plan. After reviewing and
approving that plan, `deep update vault` applies the canonical deep-update
procedure. These are natural-language shortcuts; no custom CLI is required.

The skills infer whether the request is for ingest, query, targeted review,
ordinary lint, deep lint, migration assessment or application, read-only deep
review, explicitly authorized deep update, or career, learning, writing,
relationships, and media/taste evidence and reasoning. No custom CLI or slash
command is required. Schema-specific activation, migration, and contract
comparison are defined once in the SelfContext initialization, migration, and
vault-schema references.

## Repository Validation

From the repository root, run the canonical dependency-free validation command:

```bash
python3 scripts/validate_repo.py
```

It checks test discovery and execution plus every tracked JSON file.

## How It Is Organized

SelfContext has a shared foundation, available domain-specific verticals, and
optional Advisor Packs. A private vault selectively enables only the verticals
it needs; an available vertical is not automatically enabled. Each layer has a
separate owner:

| Layer | Owns | Does not own |
| --- | --- | --- |
| SelfContext core | Vault format, lifecycle, provenance, retrieval, review, linting, and backups | Domain-specific reasoning or a second memory store |
| Vertical | Evidence and concepts for one domain in its own vault area | Shared schema rules or facts owned by another vertical |
| Advisor Pack | Reasoning and output for a vertical, using retrieved evidence | Vault storage, provenance, or automatic fact creation |

### Available Verticals

The available verticals are deliberately separate. A private vault enables only
the subset it needs. Their scopes and Advisor Packs are documented
independently so another vertical can be added without mixing its rules into the
core:

| Vertical | Vault area | Owns | Advisor Pack |
| --- | --- | --- | --- |
| Career | `career/` | Roles, projects, skills, achievements, goals, and professional examples | Career Advisor |
| Learning | `learning/` | What the person understands, meaningful gaps, corrections, mental models, prerequisites, and progression evidence | Learning Advisor |
| Writing | `writing/` | Evidence-backed communication patterns, reasoning-through-writing, readers, revision, and writing modes | Writing Advisor |
| Relationships | `relationships/` | Intentional relationship context, shared history, meaningful interactions, commitments, open loops, and relationship evolution | Relationships Advisor |
| Media / Taste | `media/` | Reactions to experienced cultural works, explainable taste patterns, exceptions, and taste evolution | Media Advisor |

A schema 0.2 vault starts with universal `core/`, `review/`, `sources/`, and
`derived/` areas. It creates only the required vertical area and records its
exact available contract when a triggering mutation or explicit adoption
requires it; unrelated available verticals remain disabled. A legacy schema
0.1 vault remains supported without automatic migration: first meaningful use
may add the needed legacy area/index/root link but never adds contract markers.
Read-only queries and assessments create nothing. Any vault can contain
retained `sources/`, unresolved `review/` items, and clearly labeled `derived/`
analyses. Vertical context stays in its owning area; an Advisor Pack may combine
relevant areas without duplicating them. Learning treats sources as evidence
about the person’s knowledge rather than as a resource archive. Relationships
centers the user's connection with another person rather than a third-party
profile. Media / Taste centers the user's reaction to a work rather than a
consumption catalog. Each vertical uses the shared lifecycle and remains useful
without the others.

## Your Vault

The private `vault/` directory is the source of truth and is ignored by Git.
On a fresh clone, it is initialized automatically when an operation needs it.
If you already have a Context Vault, copy it into `self-context/vault/`; the
skill will orient itself from the vault's own files.

The vault remains portable: its canonical content is Markdown, YAML frontmatter,
and standard Markdown links. Before a vault-changing operation, SelfContext
creates a local ZIP backup in the project-root `backups/` directory beside
`vault/` and retains the three newest backups. The backup directory is separate
from the portable vault and is ignored by Git.

Never force-add anything from `vault/`. Git-ignoring the directory helps prevent
accidental commits, but it does not prevent a model or provider from seeing
information that you give its harness.

## Optional Obsidian Use

Obsidian can be used as a human viewer and editor. Open `vault/` as the Obsidian
vault, not the repository root. Obsidian is not required; the portable format
remains ordinary Markdown.

## Current Scope

The implementation supports:

- the portable SelfContext core and shared vault lifecycle;
- the Career, Learning, Writing, Relationships, and Media / Taste verticals described above;
- natural-language ingest, query, review, and lint workflows;
- replaceable Career, Learning, Writing, Relationships, and Media Advisor Packs;
- Obsidian compatibility and multi-session continuity through the vault;
- evidence-backed Learning context that distinguishes exposure from
  understanding; and
- evidence-backed, selectively updated Writing context, where analysis may
  produce no profile change;
- privacy-sensitive Relationships context for shared history, commitments, and
  useful continuity; and
- evidence-backed Media / Taste context that distinguishes consumption from
  reaction and preserves exceptions.

The project does not require cloud services, telemetry, automatic sync, a
database, embeddings, MCP, a background service, an external synchronization
layer, or a custom runtime. Local lexical search and compiled index catalogs
are deterministic, disposable aids rather than canonical storage.

## Further Reading

- [Repository guidance](AGENTS.md): operational rules for using and maintaining
  the project.
- [Vision](docs/VISION.md): the product thesis and design commitments.
- [Architecture](docs/ARCHITECTURE.md): boundaries and lifecycle details.
- [Roadmap](docs/ROADMAP.md): current scope and future experiments.
- [Deep Maintenance Protocol](.agents/skills/self-context/references/deep-maintenance.md): explicit maintenance modes.
- [Vault Migration](.agents/skills/self-context/references/migration.md): first-class natural-language schema migration.
- [Deep Maintenance Release Checklist](docs/DEEP_MAINTENANCE_RELEASE_CHECKLIST.md): repeatable stabilization validation.
- [Build record](docs/BUILD_PLAN.md): historical bootstrap phases and validation
  history.
