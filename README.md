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
```

The skills infer whether the request is for ingest, query, review, lint, or
career, learning, and writing evidence and reasoning. No custom CLI or slash
command is required.

## How It Is Organized

SelfContext has a shared foundation, domain-specific verticals, and optional
Advisor Packs. Each layer has a separate owner:

| Layer | Owns | Does not own |
| --- | --- | --- |
| SelfContext core | Vault format, lifecycle, provenance, retrieval, review, linting, and backups | Domain-specific reasoning or a second memory store |
| Vertical | Evidence and concepts for one domain in its own vault area | Shared schema rules or facts owned by another vertical |
| Advisor Pack | Reasoning and output for a vertical, using retrieved evidence | Vault storage, provenance, or automatic fact creation |

### Current Verticals

The current verticals are deliberately separate. Their scopes and Advisor Packs
are documented independently so another vertical can be added without mixing its
rules into the core:

| Vertical | Vault area | Owns | Advisor Pack |
| --- | --- | --- | --- |
| Career | `career/` | Roles, projects, skills, achievements, goals, and professional examples | Career Advisor |
| Learning | `learning/` | What the person understands, meaningful gaps, corrections, mental models, prerequisites, and progression evidence | Learning Advisor |
| Writing | `writing/` | Evidence-backed communication patterns, reasoning-through-writing, readers, revision, and writing modes | Writing Advisor |

The same vault can contain shared `core/` context, the vertical areas above,
retained `sources/`, unresolved `review/` items, and clearly labeled `derived/`
analyses. Vertical context stays in its owning area; an Advisor Pack may combine
relevant areas without duplicating them. Learning treats sources as evidence
about the person’s knowledge rather than as a resource archive. A future
vertical should define its scope, own a separate area and index, and be added to
the vertical catalog before its procedures or Advisor Pack are used.

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
- the Career, Learning, and Writing verticals described above;
- natural-language ingest, query, review, and lint workflows;
- replaceable Career, Learning, and Writing Advisor Packs;
- Obsidian compatibility and multi-session continuity through the vault;
- evidence-backed Learning context that distinguishes exposure from
  understanding; and
- evidence-backed, selectively updated Writing context, where analysis may
  produce no profile change.

The project does not require cloud services, telemetry, automatic sync, a
database, or a custom runtime.

## Further Reading

- [Repository guidance](AGENTS.md): operational rules for using and maintaining
  the project.
- [Vision](docs/VISION.md): the product thesis and design commitments.
- [Architecture](docs/ARCHITECTURE.md): boundaries and lifecycle details.
- [Roadmap](docs/ROADMAP.md): current scope and future experiments.
- [Build record](docs/BUILD_PLAN.md): historical bootstrap phases and validation
  history.
