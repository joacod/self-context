# ADR 0010: Add an Evidence-Backed Writing Vertical

- **Status:** Accepted
- **Date:** 2026-08-10

## Context

Writing is more than a surface style prompt. A person's authored material can
show how they communicate, develop arguments, explain concepts, anticipate
readers, revise ideas, and adapt to context. At the same time, generated prose
can create a feedback loop if it is later treated as evidence of the person's
voice. New writing may also confirm what SelfContext already knows without
teaching it anything new.

SelfContext already has a portable Markdown vault, shared provenance and
lifecycle metadata, Career as a vertical, and Advisor Packs that consume rather
than own context. A Writing implementation must fit those boundaries.

## Decision

Add Writing as a first-class vertical that reuses the existing vault contract:

- durable Writing context lives under an on-demand `writing/` area and uses the
  shared page metadata and relative Markdown links;
- retained Writing source and generated-artifact pages carry explicit
  `writing_evidence_role`, `authorship`, and `ai_involvement` metadata so a
  generic model can distinguish primary, human-edited assisted, generated, and
  unknown material;
- authored sources remain source records under shared `sources/`, unresolved
  inferences and contradictions use shared review pages, and reusable analyses
  remain derived;
- Writing ingestion identifies authorship, AI involvement, language, mode,
  reader context, and dates, performs local analysis, compares candidates with
  existing context, and updates only when evidence materially changes the
  model;
- "No meaningful update" is a successful result. Source provenance may be
  preserved while the durable Writing profile remains unchanged;
- qualitative evidence states such as candidate, emerging, established, and
  explicit preference are readable observation content, not a new numerical
  confidence store. Existing `status`, `verified`, `sources`, `assertion_kind`,
  and dates remain authoritative;
- contradictions are preserved and reviewed, contextual differences are
  scoped by mode or audience, and dated changes are represented as evolution
  rather than silently averaged or overwritten;
- AI-generated material remains derived/generated. Meaningful human edits can
  become revision evidence only after comparison and aggregation; generated
  prose never validates itself;
- a Writing Advisor Pack supplies generic writing expertise and workflows for
  ideas, brainstorming, drafting, editing, and reader analysis. It retrieves
  Writing and other vertical context through SelfContext and never owns or
  mutates the vault merely by producing output.

## Consequences

- A copied vault remains inspectable without a model, provider, or Writing
  Advisor.
- Existing v0.1 vaults do not require a schema migration; Writing navigation is
  added during new initialization or, for a requested mutation, minimally
  created within the provisional/final backup lifecycle. Read-only work treats a
  missing Writing area as empty.
- More sources can improve accuracy without requiring more durable traits.
- Generic writing advice remains replaceable and is not confused with personal
  evidence.
- Semantic duplicate detection, confidence assessment, authorship, and
  contradiction reasoning remain agent workflows; the deterministic linter
  continues to validate structural integrity only.
- A Writing request can retrieve career, core, knowledge, or belief context
  without duplicating those domains into `writing/`.

## Alternatives Rejected

- A style-only prompt or universal list of adjectives was rejected because it
  cannot explain reasoning, readers, modes, evidence, or evolution.
- A Writing-specific database, claim graph, embeddings, scraper, or custom
  runtime was rejected because it would make the durable context less portable.
- Automatic promotion of every analyzed source, source count, model confidence,
  or generated draft was rejected because it creates context pollution and an AI
  feedback loop.
- A mandatory taxonomy of hundreds of traits and modes was rejected because
  context quality matters more than context quantity and useful modes should
  emerge from evidence.
