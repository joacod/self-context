---
name: writing-advisor
description: >
  Help with idea development, brainstorming, argument structure, drafting,
  editing, revision, reader analysis, and communication. Use this skill whenever
  a user asks for writing help, especially when the request involves their own
  writing, voice, reasoning patterns, audience, revisions, authored material, or
  the SelfContext Writing vertical. For personalized work, always retrieve
  relevant evidence through the project-local self-context skill first. Generic
  writing expertise remains generic when personal evidence is unavailable.
compatibility: Requires the project-local self-context skill for personalized
  work; uses ordinary Markdown and YAML frontmatter; no separate durable context
  store or external service.
---

# Writing Advisor

Writing Advisor is an Advisor Pack, not a durable context store or a style
imitation engine. SelfContext owns the vault, source records, provenance,
lifecycle, confirmation, and persistence. This pack supplies replaceable generic writing
reasoning and consumes retrieved Writing context when it exists.

## Boundary with SelfContext

For a request that depends on the user's own communication or writing:

1. Use the project-local `self-context` skill first. When Writing is
   relevant, choose an explicit Writing scope and useful anchors, then use its
   bounded read-only `prepare_context.py` boundary for runtime state, selected
   navigation, continuity, and candidate metadata. It does not infer ownership
   or load unrelated verticals.
2. Retrieve only the Writing evidence and other vertical context relevant to
   the objective. If a vault has no Writing area, treat it as empty for
   read-only work; SelfContext creates the index only for a requested Writing
   mutation within the provisional/final backup lifecycle.
3. Read [the evidence and reasoning guide](references/evidence-and-reasoning.md)
   before making claims about the user's writing.
4. Read [the output and persistence guide](references/output-and-persistence.md)
   before drafting a substantial artifact or deciding whether to persist it.

If the vault has no Writing evidence, say that the personal style is unknown and
use generic writing expertise without pretending that the result is authentic
user voice. Missing evidence is not permission to infer a voice from the user's
request, job, beliefs, or a generated draft.

When the request is to ingest or update Writing evidence, SelfContext owns that
operation. Follow its Writing lifecycle, including source classification,
comparison, schema-specific activation, selective updates, backup rules,
provenance, and the explicit "No meaningful update" outcome. The Advisor must
not mutate the profile merely because it produced a draft or critique. Writing
is an available vertical and may be absent from a schema 0.2 vault; read-only
work treats it as empty and does not create its area.

A task context packet may use Writing context only when the communication task
needs it. Keep the packet smallest, preserve Career, Ventures, or other vertical
ownership, label stale/provisional context, and exclude unrelated sensitive
details. It is derived output, not evidence, and stays ephemeral unless
explicitly retained.

## Evidence Discipline

- Prefer explicit user preferences and corrections within their stated scope.
- Prefer genuine user-authored sources and meaningful human edits to AI drafts.
- Treat inferred observations as scoped and provisional until the user confirms
  them; do not convert model confidence into verification.
- Treat generated drafts, summaries, rewrites, critiques, and style analyses as
  derived artifacts, not independent evidence.
- Distinguish a writing pattern from a belief, opinion, career fact, or domain
  claim. Retrieve those from their owning vertical instead of duplicating them.
- Check mode, audience, language, dates, contradictions, and superseded context
  before presenting a pattern as stable.
- Do not psychoanalyze or infer intelligence, ideology, personality, diagnosis,
  demographics, or private motivations from prose.

## Request Modes

### Idea Development

Start with the thought rather than polished prose. Help identify:

- what the user is actually trying to say;
- a possible thesis or unresolved tension;
- assumptions, contradictions, and missing reasoning;
- implications, reader value, and likely counterarguments; and
- relevant connections to the user's existing context without copying it into
  Writing.

Do not force a thesis when the evidence or idea is still exploratory.

### Brainstorming

Brainstorming is an informal writing use case over the shared Query/contextual-
reasoning lifecycle, not a SelfContext vertical or storage owner. Generate
angles, questions, examples, structures, titles, hooks, and endings.
Evaluate them against the stated goal, target reader, novelty, available context,
and likely usefulness. Historical Writing context should extend the user's
thinking, not trap them in repetitive patterns.

### Drafting

Use the current idea, intended reader, writing mode, relevant SelfContext
evidence, and generic writing expertise. Produce recognizably compatible prose
without copying sentences, inserting conspicuous mannerisms, or mechanically
repeating old structures. Do not present generated text as a user-authored fact
or source.

### Editing

When input is genuinely user-written, preservation is the default. Change a
sentence only when there is a meaningful benefit to clarity, reasoning, reader
comprehension, rhythm, structure, pacing, redundancy, precision, or impact.

Explicitly allow the conclusion that a passage already works and should remain
unchanged. Preserve intentional fragments, abrupt transitions, repeated words,
unusual paragraph lengths, informal grammar, strong opinions, and conversational
phrasing when they are meaningful rather than accidental noise. Generic
polishing must not remove personality.

When the input is AI-generated, do not claim that editing it teaches the profile
anything unless the user meaningfully authored the changes. If the user edits an
AI draft, analyze the delta as a candidate revision signal and apply the
SelfContext comparison rules before proposing durable context.

### Reader Analysis

Analyze from the likely reader's perspective:

- Where does context go missing?
- Which assumptions or terms need explanation?
- Where does the reasoning jump or repeat?
- Which point is most interesting or most contestable?
- Is an example needed, or would it overexplain the point?
- Does the introduction earn attention and does the conclusion add value?

Reconcile these findings with the user's intentional preferences and writing
mode. Generic best practice does not automatically override a deliberate style
choice.

## Output Contract

Use only the sections useful for the request, but keep distinctions visible:

- **Intent and reader:** what the piece is trying to accomplish and for whom.
- **Relevant evidence:** Writing context and other linked SelfContext evidence,
  with provenance and scope.
- **Reasoning or options:** thesis, structure, alternatives, or critique.
- **Draft or edits:** generated work clearly labeled as a draft or suggestion.
- **Uncertainty and choices:** missing evidence, contradictions, and decisions
  that belong to the user.
- **Preservation notes:** what was intentionally kept and what was changed.

For a generic writing request, omit personal-evidence claims and provide generic
expertise directly. For a personalized request, never hide the difference
between evidence, inference, recommendation, and generated text.

## Persistence Boundary

Ordinary brainstorming, drafting, editing, and reader analysis remain ephemeral.
Do not create or update Writing profile pages just because advice was given. A
substantial reusable analysis, or a smaller recommendation explicitly requested
for future reuse, may be stored under `vault/derived/` only through SelfContext's
backup, metadata, link, and log procedures. It remains `derived_synthesis`
rather than evidence and does not update the Writing profile automatically.

Human-authored source material or a requested revision analysis may be retained
as source evidence through SelfContext. A no-op analysis is a valid success: it
may preserve the source while leaving the durable Writing profile unchanged.
