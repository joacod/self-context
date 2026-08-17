# SelfContext

> Think with context you own.

Meaningful AI conversations repeatedly start from zero even though your
projects, decisions, goals, constraints, and previous thinking already have
history. SelfContext helps you **continue thinking instead of starting over**:
it keeps durable context worth carrying forward in portable Markdown you own
and lets the AI tool or harness you already use reason from the relevant parts.

The technical thesis is simple: **context has a lifecycle.** A conversation is
ephemeral by default. Reasoning is not automatically memory. Preserve what
will make a future useful conversation better; do not record everything by
default. Durable updates remain inspectable and user-correctable.

SelfContext is a context format and lifecycle, not a standalone chatbot, AI
harness, or provider-owned memory service. It provides project-local skills and
a local Markdown Context Vault; the existing AI harness and model remain the
execution layer. Its operational loop is:

```text
durable context
→ targeted retrieval
→ contextual reasoning
→ ephemeral exploration
→ optional checkpoint
→ smallest durable update
```

The current foundation supports natural-language ingest, targeted retrieval,
query, contextual thinking, checkpoint, targeted review, structural validation,
and vault maintenance. Checkpoint inspects a conversation for the smallest
durable changes without storing a transcript. These are horizontal workflows
over existing context, not a separate assistant, runtime, storage system, or
replacement harness.

The core vault lifecycle and focused context areas are implemented.
Future work is tracked as experiments in the [Roadmap](docs/ROADMAP.md), not
promises.

## Quick Start

SelfContext works with an AI tool that can load project-local Agent Skills.
The repository's `.agents/skills/` directory is the integration point. No server
or dependency installation is needed for normal use.

```bash
git clone https://github.com/joacod/self-context.git
cd self-context
```

Open the repository root in your AI tool and use natural language:

```text
ingest my resume into SelfContext
what does my context say about X?
help me think through X using my context
compare these options against my current goals
challenge this idea based on what you know
checkpoint this discussion
what from this conversation is actually worth keeping?
show me the context behind that recommendation
review my context for stale or conflicting information
```

When an operation needs it, a missing `vault/` is initialized automatically,
and you can inspect the result as ordinary Markdown. If you already have a
vault, place it at `vault/`; the skill will orient itself from the vault's own
files. No custom CLI is required.

## Update an Existing Vault

When you update this repository, pull the latest changes and ask your AI tool:

```bash
git pull
```

```text
upgrade vault latest
```

`upgrade vault latest` is the normal user-facing path for bringing an existing
vault fully up to date. It checks the latest schema and contracts, delegates
schema migration and other applicable bounded maintenance to their owning
procedures, synchronizes managed controls, and validates the result. Existing
evidence and history are preserved; ambiguous decisions are left for review.
If your vault is already current, nothing is changed. You do not need to choose
or run the underlying migration and maintenance procedures for a normal upgrade.

## How It Works

```text
existing AI harness/model
 |
 v
SelfContext skills
 |
 v
local Markdown Context Vault
(Markdown + YAML frontmatter + standard links)
```

- The vault is the durable source of truth. You can inspect, edit, copy, and
  back it up independently.
- The existing AI harness provides the model and execution. SelfContext
  provides workflows for ingest, query, review, lint, advice, and maintenance.
- User-stated facts, source-derived facts, agent inferences, and derived
  analyses remain distinguishable.

### Optional source retrieval

When source material lives outside the vault, SelfContext can use retrieval
capabilities already available in the selected AI harness—such as web fetching,
browser tools, repository access, document parsers, or MCP tools—to supply
material to the normal ingest workflow. These capabilities are optional and
disposable, not part of SelfContext's durable architecture. The Markdown vault
remains the canonical context store.

## Thinking with Context

SelfContext retrieves relevant existing context to support brainstorming,
decisions, comparisons, and challenges across areas such as Career, Learning,
Writing, Relationships, Media / Taste, and Ventures / Projects. This is a
Query mode, not a new area. Conversations remain ephemeral by default; an
explicit checkpoint can preserve only a durable outcome when it earns the
maintenance cost.

Query/contextual thinking is read-only by default. It does not update pages,
logs, indexes, backups, metadata, or generated artifacts. When requested, a
compact context receipt can explain scope, evidence coverage, freshness,
uncertainty, assertion kind, and persistence without exposing private
chain-of-thought.

## What It Supports

- **Portable storage:** ordinary Markdown, YAML frontmatter, and standard
  relative links.
- **Natural-language workflows:** ingest, targeted retrieval, contextual
  thinking, decision support, checkpoint, targeted review, structural
  validation, and keeping an existing vault current.
- **Trustworthy context:** provenance, freshness, unresolved items,
  contradictions, and explicit confirmation for important inferences.

## Explicit Non-Goals

The current non-goals are defined in the
[Vision](docs/VISION.md#explicit-non-goals). They include no standalone
chatbot, AI harness, hosted service, transcript archive, automatic recorder, or
Brainstorming vertical. These boundaries keep the product focused on durable
context and the existing harness boundary.

### Context Areas

SelfContext organizes durable context into focused areas such as Career,
Learning, Writing, Relationships, Media / Taste, and Ventures / Projects. It
uses the areas relevant to your context as needed.

| Vertical | Vault area | Focus |
| --- | --- | --- |
| Career | `career/` | Career evidence and concepts |
| Learning | `learning/` | Knowledge states, gaps, corrections, and progression |
| Writing | `writing/` | Evidence-backed communication and writing context |
| Relationships | `relationships/` | Shared history, commitments, and open loops |
| Media / Taste | `media/` | Reactions to cultural works and evolving taste |
| Ventures / Projects | `ventures/` | Initiative lifecycle, decisions, commitments, evidence, and outcomes |

- **Obsidian:** use `vault/` as an Obsidian vault if you want a visual editor.
  Obsidian is optional.

## Privacy and Portability

SelfContext is local-first: `vault/` is local and Git-ignored. Never commit it
or force-add files from it.
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

For operational procedures, see the
[upgrade procedure](.agents/skills/self-context/references/upgrade.md),
[migration procedure](.agents/skills/self-context/references/migration.md), and
[deep-maintenance procedure](.agents/skills/self-context/references/deep-maintenance.md).

Licensed under the [MIT License](LICENSE).
