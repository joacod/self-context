# SelfContext

> Portable personal context for AI tools, stored in plain Markdown files you own.

People often repeat their history, preferences, goals, and constraints across AI
tools and sessions. SelfContext keeps that context in a local, inspectable vault
that you can edit, copy, back up, and carry between models.

SelfContext is not a hosted app or a separate AI runtime. It provides
project-local skills for an existing AI tool that supports Agent Skills; the
local `vault/` remains the source of truth.

The core vault lifecycle and six optional areas are implemented and available.
Future work is tracked as experiments in the [Roadmap](docs/ROADMAP.md), not
promises.

## Quick Start

SelfContext works with an AI tool that can load project-local Agent Skills. No
server or dependency installation is needed for normal use.

```bash
git clone https://github.com/joacod/self-context.git
cd self-context
```

Open the repository root in your AI tool and use natural language:

```text
ingest my resume into SelfContext
what does my context say about a skill or experience?
review my context for stale or conflicting information
help me position myself for a role based on my context
```

On first use, SelfContext initializes a missing `vault/` automatically. If you
already have a vault, place it at `vault/`; the skill will orient itself from
the vault's own files. No custom CLI is required.

## How It Works

```text
You
 |
 v
Existing AI tool + model
 |
 v
SelfContext skills
 |
 v
Local Context Vault
(Markdown + YAML frontmatter + standard links)
```

- The vault is the durable source of truth. You can inspect, edit, copy, and
  back it up independently.
- The existing AI tool provides the model and execution. SelfContext provides
  workflows for ingest, query, review, lint, advice, and maintenance.
- User-stated facts, source-derived facts, agent inferences, and derived
  analyses remain distinguishable.

## What It Supports

- **Portable storage:** ordinary Markdown, YAML frontmatter, and standard
  relative links.
- **Natural-language workflows:** ingest, query, targeted review, and structural
  validation.
- **Trustworthy context:** provenance, freshness, unresolved items,
  contradictions, and explicit confirmation for important inferences.
- **Optional areas:** Career, Learning, Writing, Relationships, Media / Taste, and Ventures / Projects.
  Each can be enabled independently and follows the shared vault rules.

### Available Verticals

These areas are available independently; a vault enables only the areas it
needs.

| Vertical | Vault area | Focus |
| --- | --- | --- |
| Career | `career/` | Career evidence and concepts |
| Learning | `learning/` | Knowledge states, gaps, corrections, and progression |
| Writing | `writing/` | Evidence-backed communication and writing context |
| Relationships | `relationships/` | Shared history, commitments, and open loops |
| Media / Taste | `media/` | Reactions to cultural works and evolving taste |
| Ventures / Projects | `ventures/` | Initiative lifecycle, decisions, commitments, evidence, and outcomes |

- **Maintenance:** deterministic validation and explicit, backed-up vault
  migrations. Advanced maintenance prompts include `migrate vault latest`,
  `deep review vault`, and `deep update vault`.
- **Obsidian:** use `vault/` as an Obsidian vault if you want a visual editor.
  Obsidian is optional.

## Privacy and Portability

- `vault/` is local and Git-ignored. Never commit it or force-add files from it.
- The canonical format remains useful without SelfContext, a particular model,
  AI tool, search implementation, or Obsidian.
- Git ignore helps prevent accidental commits, but it does not prevent a model
  or provider from seeing information you give its tool.
- No hosted service, database, embeddings, telemetry, background service, or
  custom runtime is required.

## Documentation

- [Vision](docs/VISION.md): the problem, thesis, and design commitments.
- [Architecture](docs/ARCHITECTURE.md): system boundaries, lifecycle, and vault
  structure.
- [Roadmap](docs/ROADMAP.md): the implemented foundation and future experiments.

For repository rules and skill changes, see [Repository guidance](AGENTS.md) and
[Skill maintenance](docs/SELF_CONTEXT_SKILL_MAINTENANCE.md).

## Development

From the repository root, run the canonical dependency-free validation:

```bash
python3 scripts/validate_repo.py
```

Detailed migration and deep-maintenance procedures live under
[the SelfContext skill references](.agents/skills/self-context/references/).

Licensed under the [MIT License](LICENSE).
