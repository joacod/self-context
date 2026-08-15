---
name: self-context
description: >
  Use this skill whenever a user asks to ingest, remember, add, update,
  organize, connect, query, retrieve, review, lint, validate, reconcile,
  migrate, upgrade, or inspect their SelfContext Vault or personal context—even
  without naming SelfContext or a vault. Also use it for evidence-backed career,
  learning, writing, relationship, media/taste, or ventures/project advice;
  resumes, profiles,
  authored writing, recollections, or other durable sources that should become
  context; and vault initialization, copying, restoring, backing up, exporting,
  or migration. Recognize `upgrade vault latest`, “bring my SelfContext vault
  fully up to date,” `migrate vault latest`, `deep review vault`, `deep update
  vault`, and `migrate self-context latest`. Do not use it for generic resume
  writing, Obsidian organization, Git-ignore questions, or unrelated advice.
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
- Do not create a permanent page for a trivial retrieval or one-off answer by
  default. Store a substantial reusable synthesis, or a smaller future-use
  synthesis explicitly requested by the user, only when it passes the query
  persistence check.
- Before persisting query-derived material, check for duplicates, ownership,
  contradictions, and freshness. Keep recommendations visibly derived and do
  not update facts or goals automatically.
- Never put personal vault content in tracked project files, and never force-add
  anything from `vault/`.
- Treat `.obsidian/` and other viewer metadata as noncanonical vault state.
  Ignore it during discovery, indexing, review, and linting; preserve it unless
  the user explicitly asks to manage viewer configuration.
- Treat the project-root `backups/` directory and its ZIP archives as private
  operational state, not context. Never index, search, lint, link to, or use
  backup contents as evidence.
- For ordinary mutations, create a provisional recovery backup before the
  first active write, then create a final backup after the mutation and relevant
  validation. Discard the provisional only after the final backup succeeds. For
  migration and deep maintenance, retain both the pre-write recovery backup and
  the final-state backup. If any required backup fails, stop further writes and
  report the operation as incomplete; transactional helpers should roll back
  when they can.

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

## Latest-first runtime gate

Before any normal current SelfContext operation, orient the active vault through
the shared compatibility boundary:

```text
inspect schema and applied contracts
        |
        +-- current schema + current contracts -> continue normally
        +-- older recognized state -> stop and recommend `upgrade vault latest`
        +-- future state -> safe compatibility blocker
        +-- malformed/unversioned state -> recovery/diagnostic path
```

The latest schema is the only full runtime target. Older schemas and older
applied vertical contracts remain readable enough for diagnosis, migration
planning, and upgrade, but are not alternate live modes. Do not silently
upgrade during an ordinary query or ingest. Route a broad request to bring an
existing vault current to [Upgrade](references/upgrade.md); use
[Migration](references/migration.md) for schema/format-only work. A concise
normal-use response for an old vault is:

> This vault uses an older SelfContext model. Run `upgrade vault latest` to
> bring it current before normal use.

Future schema or contract state must not be downgraded or guessed. A disabled
vertical in a current vault is still simply absent; latest-first never means
enable every catalog entry.

## Select the Operation

Infer the operation from natural language:

- **Ingest:** add supplied information or update existing context, but only
  after the current-runtime gate succeeds.
- **Query:** retrieve or synthesize existing context when the vault is current;
  an older vault receives upgrade guidance rather than a native modern query.
- **Review:** surface stale, unresolved, contradictory, ambiguous, or
  insufficiently sourced context for human attention. Ordinary review remains
  targeted and current-model only.
- **Lint:** validate deterministic structural and metadata integrity for the
  current vault; use migration-source mode only for old-format diagnosis or
  migration validation.
- **Deep lint:** run the deterministic broad maintenance validator without
  deciding whether claims are true. Deep lint never migrates and does not turn
  an older schema into a normal runtime target.
- **Upgrade vault latest:** bring an existing vault to the current SelfContext
  model through the canonical [upgrade procedure](references/upgrade.md). Use
  it for `upgrade vault latest` and general requests to bring the vault fully
  up to date, including safe schema, contract, adoption, semantic, index, and
  validation work. It is the normal user-facing maintenance path.
- **Migrate vault:** assess or apply deterministic schema/format migrations only
  through the canonical [migration procedure](references/migration.md). Use
  schema-specific requests such as “migrate my vault,” “upgrade this vault to
  the latest schema,” “apply the required schema migrations,” `migrate vault
  latest`, or the backward-compatible `migrate self-context latest` alias. Do
  not route a general current-model upgrade here.
- **Deep review:** perform the explicit, read-only full-vault maintenance
  protocol; the canonical shorthand is `deep review vault`. It needs no backup,
  never applies migration, and creates no report unless retention is asked.
- **Deep update:** perform an explicitly authorized mutating maintenance batch;
  the canonical shorthand is `deep update vault`. Use it after a reviewed plan,
  applying safe structural changes and only explicitly approved semantic
  proposals, with snapshot validation, a retained recovery backup, and a final
  validated backup.
  It must not silently migrate an old schema; an explicitly requested schema
  migration delegates to the canonical procedure.
- **Adopt vertical / update vertical contract:** assess read-only first, then
  mutate only after explicit authorization under the deep-update rules.
- **Task context packet:** produce the smallest relevant derived retrieval
  packet for a named task; keep it ephemeral unless explicitly retained.
- **Evidence retrieval:** gather grounded context for a domain-specific request.
  Do not turn the retrieval into unsupported advice.

## Context Layers

SelfContext owns the shared vault contract and lifecycle. Vertical context is
domain-specific and remains in its owning area. Advisor Packs provide optional
reasoning for a vertical after this skill retrieves the relevant evidence.

Current-schema vertical activation is canonical in
[Initialization](references/initialization.md). This rule applies only after
the runtime gate confirms the latest schema and current contracts. A schema 0.2
first meaningful mutation requiring a vertical adds only that vertical, records
its exact available `vertical@version`, and adds the root link before the
operation's backup lifecycle completes. Read-only operations never create or
enable verticals. Recognized older schema or contract state must go through
`upgrade vault latest` before normal operation; it never activates historical
semantics. Malformed or unknown schema state remains conservative. Use [Vault
Schema](references/vault-schema.md) for the distinct available/enabled/applied
states and version comparison rules.

| Area | Scope | Current reasoning owner |
| --- | --- | --- |
| `core/` | Cross-domain goals, values, preferences, communication and decision patterns, and recurring constraints | SelfContext |
| `career/` | Career-specific evidence and concepts | Career Advisor |
| `learning/` | Knowledge states, meaningful gaps, corrections, mental models, prerequisites, and progression evidence | Learning Advisor |
| `writing/` | Observable communication and writing context | Writing Advisor |
| `relationships/` | Intentional relationship context, shared history, commitments, and open loops | Relationships Advisor |
| `media/` | Reactions to experienced cultural works and evidence-backed taste patterns | Media Advisor |
| `ventures/` | Initiative lifecycle, project-specific decisions, commitments, milestones, evidence, outcomes, and evolution | Ventures Advisor |

More verticals may be added without changing the core schema. Identify a
vertical by its documented scope before writing, keep its pages in a separate
area, and do not copy its facts into `core/` or another vertical. A vertical may
have a dedicated procedure or Advisor Pack, but neither is required merely
because the area exists.

For an authored writing source, Writing profile query, or revision analysis, read
[the Writing vertical procedure](references/writing.md) in addition to the
general ingest, query, or review procedure. Writing analysis must compare local
observations with existing context before changing durable pages; a successful
operation may preserve the source and make no profile change.

For a Learning topic, knowledge-evidence, gap, misconception, correction,
mental-model, prerequisite, or progression request, read [the Learning
vertical procedure](references/learning.md) in addition to the general
procedure. Learning analysis must describe the person's knowledge and scope,
not turn source material, casual mentions, or generated explanations into
competence.

For a relationship, person, shared-history, interaction, commitment, open-loop,
relationship-evolution, or pre-interaction request, read [the Relationships
procedure](references/relationships.md) in addition to the general procedure.
Keep the subject as the user's relationship, preserve reported statements and
sources visibly, and never infer sensitive or psychological characteristics
about third parties.

For a media, work, reaction, taste-pattern, exception, recommendation, or taste-
evolution request, read [the Media / Taste procedure](references/media-taste.md)
in addition to the general procedure. Treat individual user reactions as the
primary evidence, distinguish consumption from preference, and keep patterns
explainable, scoped, and reviewable.

For a venture, project, experiment, opportunity, proposal, collaboration,
partnership, milestone, dogfooding, adoption, project-decision, or initiative-
continuity request, read [the Ventures / Projects procedure](references/ventures.md)
in addition to the general procedure. Keep initiative lifecycle separate from
page status, route professional, knowledge, relationship, writing, core, source,
and derived claims to their owners, and preserve unknowns.

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
2. If the vault exists, inspect its schema and applied contracts through the
   latest-first runtime gate before choosing a current operation. Older
   recognized state is an upgrade source, not a normal runtime mode; future or
   malformed state remains blocked.
3. If `vault/` does not exist and the request requires it, initialize it
   automatically using [the initialization procedure](references/initialization.md).
   Do not ask the user to create the taxonomy manually.
4. If the vault exists, read `SCHEMA.md`, `index.md`, the most recent
   entries in `log.md`, and enabled vertical indexes before a significant
   operation. Then search only the relevant indexes, metadata, filenames, and
   linked pages needed for the task. For a large or ambiguous vault, use the
   disposable local lexical helper only as a retrieval aid and inspect
   provenance, freshness, status, and source links before answering. Do not
   scan `.obsidian/` inside the vault or the project-root `backups/` directory;
   they are noncanonical operational state, not personal context.
5. If an ordinary operation will mutate the vault, read [the backup procedure](references/backups.md)
   and create its provisional recovery backup before the first active write,
   then its final backup after mutation and validation; discard the provisional
   only after final success. For schema migration or deep maintenance, read the
   relevant procedure and retain both backups. If the operation is read-only, do
   not create a backup merely because the vault was inspected.
6. Read the relevant reference procedure before writing or validating content:
   - [Vault backups](references/backups.md) for provisional/final archives,
     guarded discard, and ten-archive retention.
   - [Vault schema](references/vault-schema.md) for paths, frontmatter, links,
     and assertion categories.
   - [Initialization](references/initialization.md) for a missing or incomplete
     vault and schema-version handling.
   - [Ingest](references/ingest.md) for normalization, updates, provenance,
     linking, and logging.
   - [Query](references/query.md) for targeted retrieval and the persistence
     decision for reusable or explicitly retained syntheses.
   - [Writing vertical](references/writing.md) for authorship, observations,
     modes, revisions, selective profile impact, and generated artifacts.
   - [Relationships vertical](references/relationships.md) for sparse person
     context, shared history, commitments, privacy, and relationship evolution.
   - [Media / Taste vertical](references/media-taste.md) for work reactions,
     evidence-backed patterns, exceptions, and taste evolution.
   - [Ventures / Projects vertical](references/ventures.md) for initiative
     lifecycle, project decisions, commitments, milestones, evidence, outcomes,
     adoption, unknowns, and evolution.
   - [Review and lint](references/review-and-lint.md) for targeted review and
     ordinary/deep deterministic validation.
   - [Migration](references/migration.md) for first-class schema migration
     assessment, target resolution, authorization, transaction, rollback, and
     reporting. `upgrade vault latest` delegates schema work here.
   - [Upgrade](references/upgrade.md) for latest-first orchestration across
     schema, contracts, selective adoption, bounded semantic maintenance,
     synchronization, validation, no-op behavior, and reporting.
   - [Deep maintenance](references/deep-maintenance.md) for deep lint, read-only
     deep review, explicit deep update, vertical adoption/contract changes, and
     task context packets.

For a trivial query, orientation can be brief and no page needs to be created.
A limited read-only diagnosis of an older vault may inspect enough control state
to explain the required upgrade, but full modern retrieval and semantic
behavior require the current model. For lint, review, or an explicitly broad
request, a wider scan is appropriate.

## Write and Report

When changing the vault, follow the relevant procedure completely: preserve
source material when useful, update the smallest coherent set of concepts,
add meaningful links, update affected managed catalogs, and log the operation.
Never silently rewrite a conflicting claim; preserve the evidence and surface
the conflict for review. A current schema 0.2 vault records only explicitly
activated vertical contracts. Recognized older schemas and applied contracts
remain migration/upgrade sources and are not mutated by ordinary use; route
them through `upgrade vault latest` instead of continuing historical runtime
semantics.

End the response with a concise account of:

- files created, updated, or intentionally left unchanged;
- provenance and links added;
- unresolved review items, stale claims, contradictions, or missing evidence;
- whether the result is a fact, observation, source record, or derived
  synthesis; and
- any confirmation needed from the user.

For a mutation, report the provisional recovery archive, final-state archive,
any discarded provisional archive, and older archives removed by the ten-item
retention rule. If a required backup fails, report the mutation as incomplete,
keep the recovery archive, and do not perform further writes until the resulting
vault is safely backed up. If guarded discard fails after final backup success,
report the cleanup failure and keep the provisional rather than force-deleting it.

If a request asks for advice, distinguish retrieved evidence, likely
interpretations, unknowns, and recommendations. A recommendation must never
bootstrap itself into a goal or other personal fact.
