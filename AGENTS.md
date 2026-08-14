# Repository Guidance

This repository exists to build, maintain, and use SelfContext: a portable personal-context format whose private source of truth is the local `vault/` directory.

## Skill Routing

- For any request that reads, creates, updates, ingests, queries, reviews, or validates vault content, load and follow the project-local SelfContext skill first.
- For domain-specific advice based on personal context, use SelfContext for
  evidence retrieval first, then use the Advisor Pack for the owning vertical
  when one exists. Keep each pack within its documented scope.

Current vertical routing:

| Vertical | Owns | Advisor Pack |
| --- | --- | --- |
| Career | Career evidence and concepts | Career Advisor |
| Learning | Evidence-backed knowledge states and their evolution | Learning Advisor |
| Writing | Evidence-backed communication and writing context | Writing Advisor |
| Relationships | Intentional relationship context, shared history, commitments, and open loops | Relationships Advisor |
| Media / Taste | Evidence-backed reactions to cultural works and evolving taste patterns | Media Advisor |
| Ventures / Projects | Initiative lifecycle, project decisions, commitments, milestones, evidence, outcomes, and evolution | Ventures Advisor |

- A future vertical must define its scope and storage area before its procedure
  or Advisor Pack is added. The canonical available-vertical catalog is
  `.agents/skills/self-context/references/verticals.json`; keep detailed rules
  in the vertical procedure. Do not make a vertical's rules part of the core
  schema, and do not assume every available vertical is enabled in every vault
  or that every vertical needs an Advisor Pack.
- For creating or materially modifying a project skill, use the installed `skill-creator` workflow and place the canonical result under `.agents/skills/`.

Do not invent a competing vault schema or lifecycle ad hoc. Follow the SelfContext skill, the vault's `SCHEMA.md`, and the Deep Maintenance Protocol once they exist. Schema 0.1 remains supported without automatic migration; schema 0.2 records selective vertical contracts and compiled catalogs. Prefer natural-language interaction; commands are optional conveniences, never the canonical interface.

## Operating Modes

Normal vault use is **user mode**. Ingest, query, targeted review, ordinary
lint, career, learning, writing, relationships, and media/taste advice operate
on the private vault and the user's response only. Deep review is explicitly
read-only; deep update, vertical adoption, contract updates, and schema
migration are explicitly authorized project operations. They must not
modify skills, schemas, architecture, documentation, evals, scripts,
`.gitignore`, or repository structure as a side effect. Do not create a
learning log, improvement log, or automatic operations backlog.

Enter **project-maintenance mode** only when the user explicitly asks to
diagnose, change, improve, evaluate, or redesign SelfContext's operational
behavior. If the user specifically asks about an operational issue, explain it
separately from their personal answer and use synthetic or abstract examples.

Never copy, quote, paraphrase, or derive real personal vault content into
tracked skills, docs, evals, tests, scripts, ADRs, or other operational files.
Personal vault evidence may be used to answer the user's request, but any
operational reproduction must use fictional data.

## Boundaries

- Treat `vault/` as private data. It is Git-ignored; never commit it or force-add files from it.
- Keep the vault independent of OpenCode, Claude Code, Codex, Hermes, Obsidian, or any other harness.
- Do not introduce MCP, databases, embeddings, background services, dedicated runtime subagents, or another agent runtime without an explicit architectural decision.
- Keep ordinary Markdown, YAML frontmatter, and standard Markdown links as the portable contract.
- Operate from the repository root and preserve the tracked operational/private-data separation.

Consult [the build record](docs/BUILD_PLAN.md) only when historical bootstrap
context is relevant. Current operational changes require an explicit
project-maintenance request and are tracked through Git; do not treat the
historical phases as a current release or versioning process.
