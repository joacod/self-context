# SelfContext

SelfContext is a **portable personal-context format and lifecycle**. It stores durable information about a person as ordinary, interconnected Markdown files so that the context belongs to the user rather than to a model, AI provider, harness, application, or chat session.

The model and harness provide intelligence and execution. SelfContext provides the data format, organization, lifecycle, and operating instructions.

> Status: v0.1 bootstrap complete. The project remains experimental and local-first; the next useful experiment is dogfooding with real career information.

## What It Is

SelfContext is a **local Context Vault** made from:

- Markdown files with YAML frontmatter.
- Standard Markdown links rather than Obsidian-specific wikilinks.
- Human-readable indexes, provenance, lifecycle metadata, and operation logs.
- Local pre-write ZIP backups with three-backup retention.
- Agent Skills that teach an existing harness how to work with the vault.
- Advisor Packs that specialize reasoning over the shared context.

The Context Vault is the durable asset. It should remain understandable and useful if the operational skills, harness, model, Obsidian, or search tooling are replaced.

## What It Is Not

SelfContext is not a chatbot, personal AI, model, agent runtime, custom chat interface, database, vector store, MCP server, background service, or replacement for Obsidian. It does not require a cloud service, telemetry, automatic synchronization, or hidden remote storage.

## Quick Start

Clone the repository and open the repository root in a compatible AI harness:

```bash
git clone <repository-url> self-context
cd self-context
```

The harness should be opened from the repository root. With the project-local skills available, ask for work naturally, for example:

```text
ingest my resume into SelfContext
what does my context say about my experience with [tech or skill]?
based on my context, how should I position myself for [specific role]?
```

No slash command or custom CLI is required. The skills infer the intended operation from the request.

## First Run

The private `vault/` directory is intentionally not committed and may not exist after a fresh clone. On the first operation that needs a vault, the SelfContext skill will initialize it automatically. The initialized vault will describe its own organization and schema, including files equivalent to `SCHEMA.md`, `index.md`, and `log.md`.

If a Context Vault already exists, copy it into `self-context/vault/`. The skill should recognize and orient against an existing vault without requiring the user to reconstruct its internal taxonomy.

Before a mutation, the skill creates a timestamped ZIP in
`vault/backups/`. The three newest managed backups are retained; the backup
directory is operational state and is not treated as context.

Never force-add files from `vault/`.

## Usage Boundary

Normal use changes only the private vault and the answer to the user's request.
Ingesting, querying, reviewing, linting, or receiving career advice does not
modify skills, documentation, evaluations, architecture, or repository
structure, and does not create an improvement log.

To change how SelfContext operates, explicitly ask to diagnose or improve the
project itself. Operational discussions must use synthetic or abstract
examples; real vault information must never be copied into tracked project
files.

## Obsidian

Obsidian is an **optional human viewer** and editor. Open `self-context/vault/` as the Obsidian vault, not the repository root. Obsidian may create a `.obsidian/` viewer-state directory there; it is noncanonical and ignored by SelfContext.

The canonical format remains ordinary Markdown and standard Markdown links, so the vault is not dependent on Obsidian but totally compatible.

## Privacy

The Context Vault is local by default. SelfContext provides no telemetry, analytics, automatic sync, or hidden remote storage. Git-ignoring `vault/` protects it from ordinary repository commits; it does not hide information from a model or provider that **the user gives access to through their harness**. 

> IMPORTANT: **The user's model, provider, retention, and local-versus-hosted privacy configuration remain their responsibility.**

## v0.1 Scope

The first version focuses on a portable core and one vertical:

- First-run vault initialization and existing-vault orientation.
- Natural-language ingest, query, review, and lint workflows.
- Provenance, freshness, lifecycle, and explicit separation of facts, inferences, and derived material.
- A career context vertical.
- A Career Advisor Pack implemented as an Agent Skill.
- Multi-session continuity through the vault rather than chat history.
- A pre-write backup before every mutation, retaining the latest three local
  ZIPs.
- Obsidian compatibility without an Obsidian dependency.

Guided Discovery, additional verticals, additional Advisor Packs, sync, encryption workflows, and optional disposable search indexes remain future possibilities. See the [roadmap](docs/ROADMAP.md).

## Repository Structure

```text
self-context/
|-- .agents/                  # Project-local operational skills
|-- docs/                     # Product, architecture, roadmap, build plan, and ADRs
|-- AGENTS.md                 # Repository-level harness guidance
|-- README.md
|-- .gitignore
`-- vault/                    # Private, local, ignored data; may not exist after clone
    `-- backups/              # Optional pre-write ZIPs; noncanonical vault state
```

The tracked operational project and private vault share a working directory but have strictly separated concerns. Read [the architecture](docs/ARCHITECTURE.md) before changing that boundary.

## Project Documents

- [Vision](docs/VISION.md): the durable product thesis.
- [Architecture](docs/ARCHITECTURE.md): layers, boundaries, lifecycle, and rejected infrastructure.
- [Roadmap](docs/ROADMAP.md): current scope and future possibilities.
- [Build plan](docs/BUILD_PLAN.md): phased implementation status and acceptance criteria.
- [Architectural decisions](docs/decisions/): decisions that preserve the reasoning behind the design.

This project prefers simple, portable files and explicit user confirmation over infrastructure or inferred certainty.
