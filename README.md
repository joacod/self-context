# SelfContext

> Think with context you own.

SelfContext is a local, portable context layer for AI tools. It helps you carry
goals, decisions, projects, preferences, and evidence across conversations and
tools, so you can continue thinking instead of starting over.

Your durable context lives in a plain-Markdown `vault/` that you can inspect,
edit, copy, and back up. SelfContext is not a standalone chatbot or hosted
memory service; your existing AI tool remains the interface.

## Quick start

Normal use needs no server or dependency installation.

```bash
git clone https://github.com/joacod/self-context.git
cd self-context
```

Open the repository root in an AI tool that loads project-local Agent Skills,
then ask it:

```text
ingest my resume into SelfContext
```

On the first ingest, SelfContext creates `vault/` and stores the useful context
there. If you already have a vault, place it at `vault/` before using the
repository.

## Everyday use

These are natural-language requests to your AI tool, not shell commands:

| Request | Use it when |
| --- | --- |
| `ingest ...` | You know exactly what fact, document, correction, or decision to save. |
| `query ...` | You want to retrieve context or think through a question using it. |
| `checkpoint ...` | A meaningful conversation may contain durable outcomes, but you want SelfContext to decide what is worth keeping. |

For example:

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

Query is read-only by default. Checkpoint does not save a transcript or every
brainstorm: it keeps only worthwhile facts, decisions, corrections, or reusable
conclusions, and may leave the vault unchanged.

### Context Areas

Context can cover cross-domain goals and preferences, as well as:

| Area | Path | What it covers |
| --- | --- | --- |
| Career | `career/` | Career evidence and concepts |
| Learning | `learning/` | Knowledge states, gaps, corrections, and progression |
| Writing | `writing/` | Evidence-backed communication and writing context |
| Relationships | `relationships/` | Shared history, commitments, and open loops |
| Media / Taste | `media/` | Reactions to cultural works and evolving taste |
| Ventures / Projects | `ventures/` | Initiative lifecycle, decisions, commitments, evidence, and outcomes |

Areas are optional and created only when relevant durable context needs them.

## Your data

`vault/` is the durable source of truth. It is Git-ignored and remains ordinary
Markdown, independent of any particular AI tool or viewer. Do not commit or
force-add it to the repository.

## Updating an existing vault

After pulling a newer version of SelfContext:

```bash
git pull
```

Then ask your AI tool:

```text
upgrade vault latest
```

This brings an existing vault up to date while preserving its context and
history. See the [upgrade workflow](.agents/skills/self-context/references/upgrade.md)
for details.

## Learn more

- [Vision](docs/VISION.md) — the problem SelfContext addresses and its design goals.
- [Architecture](docs/ARCHITECTURE.md) — how the skill, vault, and deterministic tools fit together.
- [Full SelfContext skill](.agents/skills/self-context/SKILL.md) — operating rules and routing.
- [Ingest workflow](.agents/skills/self-context/references/ingest.md)
- [Query workflow](.agents/skills/self-context/references/query.md)
- [Checkpoint workflow](.agents/skills/self-context/references/checkpoint.md)
- [Skill maintenance](docs/SELF_CONTEXT_SKILL_MAINTENANCE.md) — guidance for contributors changing the skill.

## Development

Run the repository validation from the repository root:

```bash
python3 scripts/validate_repo.py
```

Licensed under the [MIT License](LICENSE).
