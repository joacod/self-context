# Repository Guidance

This repository exists to build, maintain, and use SelfContext: a portable personal-context format whose private source of truth is the local `vault/` directory.

## Skill Routing

- For any request that reads, creates, updates, ingests, queries, reviews, or validates vault content, load and follow the project-local SelfContext skill first.
- For career advice or career-related output based on personal context, use SelfContext for evidence retrieval and the Career Advisor Pack for reasoning.
- For personalized writing, communication, drafting, editing, reader analysis,
  or Writing-profile work, use SelfContext for evidence retrieval and the
  Writing Advisor Pack for generic writing reasoning.
- For creating or materially modifying a project skill, use the installed `skill-creator` workflow and place the canonical result under `.agents/skills/`.

Do not invent a competing vault schema or lifecycle ad hoc. Follow the SelfContext skill and the vault's `SCHEMA.md` once they exist. Prefer natural-language interaction; commands are optional conveniences, never the canonical interface.

## Operating Modes

Normal vault use is **user mode**. Ingest, query, review, lint, career advice,
and personalized writing advice operate on the private vault and the user's
response only. They must not
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

Consult [the build plan](docs/BUILD_PLAN.md) before starting or extending a bootstrap phase. Do not begin a later phase without explicit user direction.
