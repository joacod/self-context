# SelfContext

SelfContext is a local, portable way to keep personal context that you own. It
stores durable information as ordinary Markdown files, so the context can be
read, edited, copied, and used across AI models and harnesses.

SelfContext is not a hosted app or a separate AI runtime. An existing AI
harness uses the project-local skills to work with the private Context Vault.

> **Status:** v0.1 bootstrap complete. The project is experimental and
> local-first.

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
```

The skills infer whether the request is for ingest, query, review, lint, or
career evidence and reasoning. No custom CLI or slash command is required.

## How It Is Organized

Think of SelfContext as a shared foundation with domain-specific verticals and
replaceable Advisor Packs.

- **SelfContext core:** owns the portable vault format, ingestion, retrieval,
  review, linting, provenance, lifecycle, and backup rules.
- **Career vertical:** stores career-specific evidence such as roles, projects,
  skills, achievements, goals, and professional examples.
- **Writing vertical:** stores evidence-backed patterns in how you communicate,
  develop ideas, explain concepts, consider readers, revise drafts, and adapt
  across writing modes. It distinguishes authentic writing from generated text.
- **Advisor Packs:** provide domain reasoning over retrieved context. Career and
  Writing Advisors can help with career decisions or writing work, but they do
  not own a second memory system or silently turn generated output into facts.

The same vault can contain shared `core/` context, vertical areas such as
`career/` and `writing/`, retained `sources/`, unresolved `review/` items, and
clearly labeled `derived/` analyses. Vertical context stays in its owning area;
an Advisor can combine relevant areas without duplicating them.

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

The implementation supports a portable core, Career and Writing context
verticals, natural-language ingest/query/review/lint workflows, Career and
Writing Advisor Packs, Obsidian compatibility, and multi-session continuity
through the vault. Writing context is evidence-backed and selectively updated:
analyzed source material may produce no profile change. The project does not
require cloud services, telemetry, automatic sync, a database, or a custom
runtime.

## Further Reading

- [Repository guidance](AGENTS.md): operational rules for using and maintaining
  the project.
- [Vision](docs/VISION.md): the product thesis and design commitments.
- [Architecture](docs/ARCHITECTURE.md): boundaries and lifecycle details.
- [Roadmap](docs/ROADMAP.md): current scope and future experiments.
- [Build plan](docs/BUILD_PLAN.md): bootstrap phases and validation history.
