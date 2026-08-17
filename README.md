# SelfContext

> Think with context you own.

Meaningful AI conversations often start from zero even when the underlying
project, decision, goal, or problem does not. SelfContext helps you continue
thinking instead of starting over: it keeps durable context worth carrying
forward in portable Markdown you own and lets the AI tool or harness you
already use reason from the relevant parts.

SelfContext is more than memory storage. It provides project-local skills and a
local Markdown Context Vault; the existing AI harness and model remain the
execution layer. Context has a lifecycle: a conversation is ephemeral by
default, reasoning does not automatically become memory, and the aim is to
preserve what can make a future conversation better—not to accumulate
everything that happens. Durable updates remain inspectable and
user-correctable.

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
checkpoint this discussion and keep only durable changes
help me position myself for a role based on my context
```

On first use, SelfContext initializes a missing `vault/` automatically. If you
already have a vault, place it at `vault/`; the skill will orient itself from
the vault's own files. No custom CLI is required.

## Keep Your Vault Current

After updating SelfContext, update the repository and ask your AI tool:

```bash
git pull
```

```text
upgrade vault latest
```

SelfContext is latest-first. After updating the repository, run
`upgrade vault latest` to bring an existing vault to the current model before
normal use. The upgrade checks your existing vault and applies only the updates
it needs, including supported format changes, relevant context areas, and safe
organization improvements. Existing evidence and history are preserved, and
ambiguous decisions are left for review. If your vault is already current,
nothing is changed.

## How It Works

```text
You
 |
 v
Existing AI harness + model
 |
 v
SelfContext project-local skills
 |
 v
Local Markdown Context Vault
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

SelfContext can support questions, brainstorming, decisions, comparisons, and
challenges by retrieving relevant existing context across areas such as
Career, Learning, Writing, Relationships, Media / Taste, and Ventures /
Projects. The aim is continuity around a useful line of thought, not a replay
of every prior conversation. The contextual-thinking Query mode provides this
contextual reasoning over retrieved context rather than adding a new operation
or area.

Brainstorming and decision-making are horizontal workflows, not additional
verticals. Retrieval can span multiple existing areas when needed while each
concept remains in its canonical owner. Exploration in a conversation remains
ephemeral by default. An optional checkpoint routes explicit durable outcomes
through the existing ingest, query persistence, or review semantics and may
make no mutation. When information has future reuse value, the user can
deliberately preserve it through the existing workflows; generated suggestions
are not facts about the user and are not stored automatically.

An on-demand context receipt can explain the relevant context, tradeoffs,
uncertainty, and persistence outcome without creating a receipt file or
exposing private chain-of-thought.

## What It Supports

- **Portable storage:** ordinary Markdown, YAML frontmatter, and standard
  relative links.
- **Natural-language workflows:** ingest, targeted retrieval, contextual
  thinking, decision support, checkpoint, targeted review, structural
  validation, and keeping an existing vault current.
- **Trustworthy context:** provenance, freshness, unresolved items,
  contradictions, and explicit confirmation for important inferences.

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

Operational migration and maintenance procedures live under
[the SelfContext skill references](.agents/skills/self-context/references/).

Licensed under the [MIT License](LICENSE).
