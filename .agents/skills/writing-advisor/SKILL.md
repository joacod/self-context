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
lifecycle, confirmation, and persistence; this pack provides generic writing
reasoning and consumes retrieved Writing context when it exists.

## Boundary with SelfContext

For a request that depends on the user's own communication or writing:

1. Use the project-local `self-context` skill first. Choose the smallest
   Writing scope and useful anchors, then use its bounded read-only
   `prepare_context.py` boundary before reasoning.
2. Read the [Writing procedure](../self-context/references/writing.md) for
   ownership, evidence classification, and mutations. Read the [evidence and
   reasoning guide](references/evidence-and-reasoning.md) and [output and
   persistence guide](references/output-and-persistence.md) when their detail
   is needed.
3. Retrieve only Writing evidence and other vertical context relevant to the
   objective. A missing Writing area is empty for read-only work; do not create
   it merely because this Advisor was invoked.
4. If personal evidence is missing, say so and use generic expertise without
   presenting the result as the user's authentic voice.

Use personal evidence in the answer or in explicitly retained private derived
material only. For ingest, revision analysis, or another update, let SelfContext
apply the Writing procedure, activation rule, provenance, and ordinary commit
boundary. The Advisor must not mutate the profile merely because it produced a
draft or critique, and project-maintenance work must use synthetic or abstract
examples.

A task context packet may include Writing context only when the communication
task needs it. Keep it scoped, exclude unrelated sensitive details, label
stale/provisional context, and leave it derived and ephemeral unless explicitly
retained.

## Writing scope and evidence

Writing owns observable communication behavior, reasoning-through-writing,
reader awareness, editorial preferences, evidence-backed anti-patterns, and
contextual writing modes. It does not own beliefs, opinions, career facts,
technical knowledge, diagnoses, or unsupported psychological explanations.

- Prefer explicit user preferences and corrections within their stated scope,
  genuine user-authored sources, and meaningful human edits to assisted drafts.
- Treat generated drafts, summaries, rewrites, critiques, and style analyses as
  derived artifacts, not independent evidence.
- Keep patterns separate from beliefs, opinions, and domain claims; retrieve
  those from their owning verticals rather than duplicating them.
- Check authorship, mode, audience, language, dates, contradictions, and
  superseded context before presenting a pattern as stable. One edit is a
  candidate signal, not a permanent preference.
- Do not infer intelligence, ideology, personality, diagnosis, demographics,
  or private motivation from prose.

The [evidence and reasoning guide](references/evidence-and-reasoning.md) owns
the detailed authorship, evidence-state, revision, reader, and evolution rules.

## Request modes

### Idea Development

Start with the thought rather than polished prose. Clarify the objective,
possible thesis or unresolved tension, assumptions, missing reasoning,
implications, reader value, and counterarguments. Do not force a thesis while
the idea is exploratory.

### Brainstorming

Brainstorming is an informal Writing use case over Query/contextual reasoning,
not a vertical or storage owner. Generate angles, questions, examples,
structures, titles, hooks, and endings. Evaluate them against the stated goal,
reader, novelty, context, and usefulness without treating them as user facts.

### Drafting

Use the idea, intended reader, writing mode, relevant SelfContext evidence, and
generic expertise. Produce compatible prose without copying sentences or
mechanically repeating old structures. Label generated text as a draft or
suggestion, never as user-authored evidence.

### Editing

For user-authored input, preserve the existing voice and change a sentence only
when the benefit to clarity, reasoning, reader comprehension, rhythm, structure,
precision, or impact is meaningful. Preserve intentional fragments, unusual
pacing, strong opinions, informal grammar, and conversational phrasing. It is
valid to conclude “keep this.”

For an AI draft, analyze a meaningful human-authored delta as a candidate
revision signal only. Do not claim that an untouched generated draft teaches
the Writing profile.

### Reader Analysis

Review from the intended reader's perspective: missing context, unexplained
terms, reasoning jumps, repetition, contestable points, examples, introduction,
and conclusion. Reconcile generic advice with the user's intentional
preferences and writing mode; generic best practice does not override a
deliberate choice automatically.

## Output contract

Use only the sections useful for the request, keeping distinctions visible:

- **Intent and reader:** purpose and audience.
- **Relevant evidence:** Writing and other linked SelfContext context, with
  provenance and scope.
- **Reasoning or options:** thesis, structure, alternatives, or critique.
- **Draft or edits:** generated work clearly labeled as a draft or suggestion.
- **Uncertainty and choices:** missing evidence, contradictions, and decisions
  that belong to the user.
- **Preservation notes:** what stayed and what changed.

For a generic request, omit personal-evidence claims. For a personalized
request, distinguish evidence, inference, recommendation, and generated text.

## Persistence boundary

Ordinary brainstorming, drafting, editing, and reader analysis remain
ephemeral and do not update Writing profile pages. A substantial reusable
analysis, or a smaller result explicitly requested for future reuse, may be
stored under `vault/derived/` only through SelfContext's duplicate, ownership,
freshness, metadata, link, log, backup, and validation rules. Mark it
`derived_synthesis`; it is not evidence and cannot update the Writing profile,
goals, beliefs, career facts, or preferences automatically.

Human-authored source material or requested revision analysis may be retained
as evidence through SelfContext. A no-op analysis is a valid success: it may
preserve the source while leaving the durable Writing profile unchanged.
