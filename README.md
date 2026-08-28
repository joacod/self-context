# SelfContext

> Think with context you own.

SelfContext gives an existing AI tool a local-first context layer: project-local
Agent Skills plus a portable Markdown Context Vault you own. It carries useful
goals, decisions, projects, preferences, and evidence into future conversations
so you can continue thinking instead of starting over.

Use it if your AI tool can load project-local Agent Skills and you want to:

- bring durable context across sessions and tools;
- ask for answers, comparisons, and decisions grounded in relevant context; and
- choose what is worth keeping instead of archiving every conversation.

Your AI tool and model remain the execution layer. SelfContext is not a
standalone chatbot, AI harness, hosted memory service, or transcript archive.

## Quick Start

Normal use needs no server or dependency installation.

```bash
git clone https://github.com/joacod/self-context.git
cd self-context
```

Open the repository root in an AI tool that loads project-local Agent Skills.
Start with a source or fact that will be useful later:

```text
ingest my resume into SelfContext
```

The skill initializes a missing `vault/` when an operation needs it. If you
already have a vault, place it at `vault/`. The result is inspectable as
ordinary Markdown; no custom CLI is required.

Then try:

```text
what does my context say about X?
help me think through X using my context
compare these options against my current goals
challenge this idea based on what you know
checkpoint this discussion
what from this conversation is actually worth keeping?
show me the context behind that recommendation
review my context for stale or conflicting information
```

## The core idea

Context has a lifecycle:

```text
durable context
→ targeted retrieval
→ contextual reasoning
→ ephemeral exploration
→ optional checkpoint
→ smallest durable update
```

Conversations and generated reasoning are ephemeral by default. Query and
contextual thinking are read-only by default. A checkpoint inspects a
conversation and routes only durable outcomes through normal ingest, query
persistence, or review; it can leave the vault unchanged.

## What it supports

- **Ingest:** add supplied facts, documents, corrections, and source-backed
  context while preserving ownership and provenance.
- **Query and contextual thinking:** retrieve relevant context for lookup,
  brainstorming, comparisons, tradeoffs, and decisions.
- **Checkpoint:** save only a durable result from a conversation, not a
  transcript.
- **Review and validation:** find stale, unresolved, or conflicting context and
  check vault structure.
- **Portable context:** keep Markdown, YAML frontmatter, and standard links
  readable outside SelfContext.

### Context Areas

| Area | Vault path | Focus |
| --- | --- | --- |
| Career | `career/` | Career evidence and concepts |
| Learning | `learning/` | Knowledge states, gaps, corrections, and progression |
| Writing | `writing/` | Evidence-backed communication and writing context |
| Relationships | `relationships/` | Shared history, commitments, and open loops |
| Media / Taste | `media/` | Reactions to cultural works and evolving taste |
| Ventures / Projects | `ventures/` | Initiative lifecycle, decisions, commitments, evidence, and outcomes |

Areas are optional and created only when relevant durable context needs them.

## Your data

- `vault/` is the durable source of truth and is Git-ignored. `backups/` is
  private operational state and is also ignored. Never commit or force-add
  either directory.
- You can inspect, edit, copy, or back up the vault independently. Obsidian is
  optional.
- Git ignore helps prevent accidental commits; it does not prevent a model or
  provider from seeing information you give its tool.

## Updating an existing vault

Pull the latest skill and documentation:

```bash
git pull
```

Then ask your AI tool:

```text
upgrade vault latest
```

This is the normal path for bringing an existing vault up to date. It preserves
evidence and history, leaves ambiguous meaning for review, and changes nothing
when the vault is already current. See the
[upgrade procedure](.agents/skills/self-context/references/upgrade.md) for the
full lifecycle.

## Documentation

- [Vision](docs/VISION.md): the problem, thesis, and design commitments.
- [Architecture](docs/ARCHITECTURE.md): system boundaries, lifecycle, and vault
  structure.
- [SelfContext skill](.agents/skills/self-context/SKILL.md): the full operating
  contract and natural-language routing.
- [Workflow references](.agents/skills/self-context/references/): detailed
  ingest, query, checkpoint, migration, and maintenance procedures.
- [Roadmap](docs/ROADMAP.md): the implemented foundation and future experiments.

## Development

Run the dependency-free repository validation from the repository root:

```bash
python3 scripts/validate_repo.py
```

For skill changes, see [Skill maintenance](docs/SELF_CONTEXT_SKILL_MAINTENANCE.md).

Licensed under the [MIT License](LICENSE).
