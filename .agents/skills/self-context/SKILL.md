---
name: self-context
description: >
  Operate a user's local SelfContext Context Vault as the portable source of
  truth for personal context. Use this skill whenever the user asks to ingest,
  remember, add, update, organize, connect, query, retrieve, review, lint,
  validate, reconcile, or inspect information about themselves, their history,
  goals, preferences, constraints, experiences, or evidence, including when
  they do not say "SelfContext" or "vault." Use it for evidence retrieval that
  supports career questions, resumes, profiles, or professional positioning;
  a Career or Writing Advisor Pack may add specialized reasoning later. It also
  applies to requests involving resume text, recollections, profiles, authored writing,
  or other sources that should become durable personal context, and for
  initializing, copying, restoring, backing up, or exporting a Context Vault.
  Before any vault write, create the local retained backup described below. Do
  not use it for generic resume writing, generic Obsidian organization, Git
  ignore questions,
  or advice that does not rely on the user's Context Vault.
compatibility: Requires local filesystem access from the repository root. Uses standard Markdown, YAML frontmatter, relative Markdown links, and optional Python 3 for deterministic linting.
---

# SelfContext

SelfContext is a portable personal-context format and lifecycle, not a
database, chatbot, custom runtime, or provider memory. The local `vault/`
directory is the source of truth. Keep it useful as ordinary files if this
skill, the current harness, the model, Obsidian, or a search tool disappears.

## Operating Contract

- Treat user-stated facts, source-derived facts, agent inferences, and derived
  syntheses as different kinds of knowledge.
- Preserve useful provenance and freshness metadata without adding ceremony to
  trivial conversational details.
- Treat `verified: null` as "not explicitly confirmed," not as false and not as
  an automatic review item. Use `status: review` for selected items that need
  human attention.
- Use a bounded confirmation step for high-impact, ambiguous, contradictory, or
  inferred context. Batch questions after an ingest instead of interrupting
  extraction claim by claim.
- Keep `stale_after: null` as the default. Assign a 90-day review deadline only
  to narrow, important current-state anchors when the context clearly describes
  something current and likely to affect future answers.
- Prefer updating an existing concept over creating a duplicate.
- Use standard relative Markdown links. Never use `[[wikilinks]]` as the
  canonical format.
- Do not invent facts, fill gaps with plausible claims, or promote an inference
  to a user fact without confirmation.
- Do not create a permanent page for a trivial retrieval. Store substantial,
  reusable syntheses only when they are worth maintaining.
- Never put personal vault content in tracked project files, and never force-add
  anything from `vault/`.
- Treat `.obsidian/` and other viewer metadata as noncanonical vault state.
  Ignore it during discovery, indexing, review, and linting; preserve it unless
  the user explicitly asks to manage viewer configuration.
- Treat the project-root `backups/` directory and its ZIP archives as private
  operational state, not context. Never index, search, lint, link to, or use
  backup contents as evidence.
- Before the first write of any mutation-producing operation, create a backup
  using [the backup procedure](references/backups.md). If backup creation fails,
  do not modify canonical vault content.

## User Mode Boundary

Default to user mode. Normal ingest, query, review, lint, and evidence work may
read or update the private vault according to this skill, but must not change
the project skills, schema instructions, docs, evals, scripts, or repository
layout. Do not create a learning log or suggest an operational redesign as a
side effect of ordinary use.

Switch to project-maintenance mode only when the user explicitly asks to
diagnose or improve SelfContext itself. If the user specifically asks why an
operation behaves a certain way, explain the operational issue separately. Use
synthetic or abstract examples for any proposed reproduction or change.

Never copy, quote, paraphrase, or encode real vault facts, names, stories, or
examples into tracked operational files. Vault evidence may appear in the
user-facing answer when relevant, but it must not enter skills, docs, evals,
tests, scripts, or architecture decisions.

## Select the Operation

Infer the operation from natural language:

- **Ingest:** add supplied information or update existing context.
- **Query:** retrieve or synthesize existing context.
- **Review:** surface stale, unresolved, contradictory, ambiguous, or
  insufficiently sourced context for human attention.
- **Lint:** validate deterministic structural and metadata integrity.
- **Evidence retrieval:** gather grounded context for a career or other
  domain-specific request. Do not turn the retrieval into unsupported advice.

Career and Writing are verticals, but neither is the core schema. Keep
cross-domain context under `core/`, career-specific context under `career/`, and
observable writing and communication context under `writing/`. A Writing
Advisor may add generic writing reasoning after this skill retrieves personal
evidence.

For an authored writing source, Writing profile query, or revision analysis, read
[the Writing vertical procedure](references/writing.md) in addition to the
general ingest, query, or review procedure. Writing analysis must compare local
observations with existing context before changing durable pages; a successful
operation may preserve the source and make no profile change.

## Attention and Confirmation

Importance and verification are separate decisions. The agent may identify a
claim as worth the user's attention, but it must not turn relevance, repetition,
source presence, or model confidence into verification.

- Normal source-derived or user-stated pages may remain `status: active` with
  `verified: null`.
- Selected high-impact, ambiguous, contradictory, or inferred pages may use
  `status: review` and remain unverified until the user confirms, revises,
  rejects, or explicitly defers them.
- During ingest, ask at most one concise, batched follow-up for selected items.
  Silence does not confirm anything.
- A direct user statement can remain `verified: null` under the same policy;
  preserve its `assertion_kind` and ask for explicit confirmation only when the
  item is important enough to justify the interruption.
- An agent may set `verified` after an explicit user request to confirm a named
  page or claim against specified evidence, including a source the user has
  explicitly designated as authoritative. It must not do so autonomously.
- Treat page-level verification as covering the coherent claims on that page.
  Split mixed concepts rather than marking unrelated claims verified together.

At query time, use active unverified evidence with an explicit source-derived or
user-stated label. Treat review pages as provisional. If a stale or dynamically
untracked claim is decisive to a current answer, ask one bounded freshness or
confirmation question instead of silently using it as current.

## Start Every Vault Operation

1. Resolve the repository root and use only `<repository-root>/vault/` as the
   default Context Vault. Do not silently use a provider memory, another
   directory, or a harness-specific store.
2. If `vault/` does not exist and the request requires it, initialize it
   automatically using [the initialization procedure](references/initialization.md).
   Do not ask the user to create the taxonomy manually.
3. If the vault exists, read `SCHEMA.md`, `index.md`, and the most recent
   entries in `log.md` before a significant operation. Then search only the
   relevant indexes, metadata, filenames, and linked pages needed for the task.
   Do not scan `.obsidian/` inside the vault or the project-root `backups/`
   directory; they are noncanonical operational state, not personal context.
4. If the operation will mutate the vault, read [the backup procedure](references/backups.md)
   and create the pre-write backup before the first write. If it is read-only,
   do not create a backup merely because the vault was inspected.
5. Read the relevant reference procedure before writing or validating content:
   - [Vault backups](references/backups.md) for the pre-write archive and
     retention rule.
   - [Vault schema](references/vault-schema.md) for paths, frontmatter, links,
     and assertion categories.
   - [Initialization](references/initialization.md) for a missing or incomplete
     vault and schema-version handling.
   - [Ingest](references/ingest.md) for normalization, updates, provenance,
     linking, and logging.
   - [Query](references/query.md) for targeted retrieval and persistence of
     substantial syntheses.
   - [Writing vertical](references/writing.md) for authorship, observations,
     modes, revisions, selective profile impact, and generated artifacts.
   - [Review and lint](references/review-and-lint.md) for human review and the
     deterministic validator.

For a trivial query, orientation can be brief and no page needs to be created.
For lint, review, or an explicitly broad request, a wider scan is appropriate.

## Write and Report

When changing the vault, follow the relevant procedure completely: preserve
source material when useful, update the smallest coherent set of concepts,
add meaningful links, update affected indexes, and log the operation. Never
silently rewrite a conflicting claim; preserve the evidence and surface the
conflict for review.

End the response with a concise account of:

- files created, updated, or intentionally left unchanged;
- provenance and links added;
- unresolved review items, stale claims, contradictions, or missing evidence;
- whether the result is a fact, observation, source record, or derived
  synthesis; and
- any confirmation needed from the user.

For a mutation, also report the timestamped backup created before the write and
which older backups were removed by the retention rule.

If a request asks for advice, distinguish retrieved evidence, likely
interpretations, unknowns, and recommendations. A recommendation must never
bootstrap itself into a goal or other personal fact.
