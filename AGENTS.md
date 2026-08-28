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

Do not invent a competing vault schema or lifecycle ad hoc. Follow the SelfContext skill, the vault's `SCHEMA.md`, and the Deep Maintenance Protocol once they exist. SelfContext is latest-first: the current schema and applied contracts are the only normal runtime target; recognized historical schemas remain upgrade/migration sources, and schema 0.2 records selective vertical contracts and compiled catalogs. Prefer natural-language interaction; commands are optional conveniences, never the canonical interface.

Default context-loading paths must remain bounded as vault history and page count
grow. Prefer disposable, targeted retrieval over adding always-loaded summaries,
catalogs, or duplicate recent-page lists.

## Operating Modes

Normal vault use is **user mode**. Ingest, query, targeted review, ordinary
lint, career, learning, writing, relationships, media/taste, and ventures/project
advice operate on the private vault and the user's response only. Deep review is explicitly
read-only; deep update, vertical adoption, contract updates, and schema
migration are explicitly authorized project operations. They must not
modify skills, schemas, architecture, documentation, evals, scripts,
`.gitignore`, or repository structure as a side effect. Do not create a
learning log, improvement log, or automatic operations backlog.

Enter **project-maintenance mode** only when the user explicitly asks to
diagnose, change, improve, evaluate, or redesign SelfContext's operational
behavior. If the user specifically asks about an operational issue, explain it
separately from their personal answer and use synthetic or abstract examples.

## Future Architecture Tests

For future SelfContext changes, ask:

- **Markdown, skills, or instruction changes:** Is this semantic policy the
  model genuinely needs, or are we repeating an invariant already owned
  somewhere else?
- **Deterministic code changes:** Is this deterministic vault mechanics, or are
  we accidentally teaching Python to make semantic decisions the model/skill
  should own?
- **New concepts or abstractions:** Does this improve continuity of context
  enough to justify another concept in the system?

Do not pursue DRYness mechanically in Agent Skill instructions. Repeating a
critical behavioral guardrail where it materially improves correct agent
behavior can be intentional. Remove duplication when it has no behavioral
value; do not remove useful guardrails merely to reduce line count.

## CI and repository validation

- Keep `.github/workflows/ci.yml` thin: it has one Ubuntu job running
  `python scripts/validate_repo.py` as the single repository gate under Python
  3.12.
- `scripts/validate_repo.py` owns Agent Skill metadata validation, tracked JSON
  validation, full unittest discovery and execution, and the repository
  consistency checks included in that suite. Do not repeat those checks as
  separate CI steps.
- Do not add an operating-system or Python-version matrix unless the repository
  gains platform-specific behavior or an explicit compatibility requirement.
  Add another CI step only for an independent check that the canonical
  validator cannot cover, and update this policy when validation ownership
  changes.

Never copy, quote, paraphrase, or derive real personal vault content into
tracked skills, docs, evals, tests, scripts, ADRs, or other operational files.
Personal vault evidence may be used to answer the user's request, but any
operational reproduction must use fictional data.

- For tracked synthetic examples and evals, use `John Doe` (or `John`) as the
  synthetic user and `MyContext Systems` whenever a company name is needed.
  Other named people remain acceptable only when a scenario genuinely needs
  relationship participants; they are not alternate synthetic user identities.

## Boundaries

- Treat `vault/` as private data. It is Git-ignored; never commit it or force-add files from it.
- Keep the vault independent of OpenCode, Claude Code, Codex, Hermes, Obsidian, or any other harness.
- Do not introduce MCP as SelfContext infrastructure, databases, embeddings, background services, dedicated runtime subagents, or another agent runtime without an explicit architectural decision. MCP tools or other retrieval capabilities already exposed by a user's harness may supply source material to normal ingest, but they are optional harness capabilities, not a required SelfContext runtime, synchronization layer, or memory store.
- Keep ordinary Markdown, YAML frontmatter, and standard Markdown links as the portable contract.
- Operate from the repository root and preserve the tracked operational/private-data separation.

Consult [the build record](docs/BUILD_PLAN.md) only when historical bootstrap
context is relevant. Current operational changes require an explicit
project-maintenance request and are tracked through Git; do not treat the
historical phases as a current release or versioning process.
