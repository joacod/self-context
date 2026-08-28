---
name: learning-advisor
description: >
  Provide grounded reasoning about what a person understands and how that
  understanding evolves from a SelfContext Vault. Use this skill whenever a
  user asks what they know, what they are learning, knowledge gaps,
  misconceptions, corrected beliefs, prerequisites, mental models, progression,
  or an explanation that should start from their existing knowledge, even when
  they do not say "Learning Advisor" or "SelfContext." Always use the
  project-local self-context skill first. Do not use it for generic teaching
  or fictional learning content that does not rely on the user's context.
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no separate durable context store or external service.
---

# Learning Advisor

Learning Advisor is an Advisor Pack, not a knowledge database, course tracker,
notes system, or second durable context store. SelfContext owns the vault,
shared schema, provenance, lifecycle, confirmation, and retrieval; this pack
provides Learning-specific reasoning after evidence is retrieved.

## Boundary with SelfContext

For a request about the person's own knowledge:

1. Use the project-local `self-context` skill first. Choose the smallest
   Learning scope and useful anchors, then use its bounded read-only
   `prepare_context.py` boundary before reasoning.
2. Read the [Learning procedure](../self-context/references/learning.md) for
   ownership and mutations. Read the [evidence and reasoning guide](references/evidence-and-reasoning.md)
   and [output and persistence guide](references/output-and-persistence.md)
   when their detail is needed.
3. Retrieve only relevant Learning evidence and linked Career, Ventures, or
   Writing evidence. Do not use ad hoc search, provider memory, or a second
   schema.
4. If evidence is missing, say so and label any generic explanation as generic,
   not as a fact about the person.

Learning is available but not automatically enabled in a schema 0.2 vault. An
absent area is empty for read-only questions and creates no files. For an
ingest, correction, or update, let SelfContext apply the Learning procedure,
activation rule, provenance, and ordinary commit boundary. The Advisor does not
mutate Learning context merely by answering.

For a task context packet, include only demonstrated or explicitly stated
prerequisites, their scope and dates, relevant gaps, unknowns, evidence paths,
and exclusions. The packet is derived and ephemeral unless SelfContext's
retention rules justify a page.

## Learning scope

Learning owns topics and concepts relevant to the person's understanding,
qualitative knowledge states and scope, meaningful gaps, misconceptions,
corrections, mental models, prerequisites, and dated progression evidence.
Career outcomes, Ventures lifecycle, Writing behavior, Media reactions,
Relationships, and broad `core/` context remain with their owners; link them
as evidence instead of copying them into `learning/`.

## Evidence interpretation

- Treat explicit statements about understanding, uncertainty, or correction as
  scoped user context, never global mastery.
- Treat a resource, course, book, tutorial, or technology mention as exposure
  unless evidence also shows understanding or application.
- Treat an exercise, explanation, project, or initiative as evidence only for
  the demonstrated task and scope. Do not inflate it into general proficiency.
- Repeated questions can suggest a meaningful gap, but do not prove inability.
  Preserve an earlier model, correction, dates, and remaining boundary.
- Keep user-stated facts, source-derived facts, agent inferences, and derived
  syntheses distinct. Check status, verification, sources, dates, and
  `stale_after`; reviewable, stale, contradicted, and derived material needs
  qualification.
- An AI-generated explanation, summary, or recommendation is derived output,
  never evidence that the person understands the subject.

The [evidence and reasoning guide](references/evidence-and-reasoning.md) owns
the detailed inclusion rules, knowledge-state interpretation, prerequisite
bridges, and progression analysis.

## Reasoning modes

Adapt to the request:

- **Knowledge inventory:** group relevant concepts by qualitative state and
  scope, distinguishing demonstrated understanding from exposure.
- **Current learning:** identify intentional topics, recent evidence, and the
  next meaningful uncertainty without creating a course tracker.
- **Gaps and questions:** prioritize durable, actionable gaps rather than every
  question ever asked.
- **Misconceptions and corrections:** compare dated evidence, preserve the old
  model, and show what changed without treating the newest statement as
  automatically correct.
- **Explain from existing knowledge:** use supported prerequisites, state the
  bridge to the new concept, and label the explanation as generated output.
- **Progression:** use dated evidence and concept history, not numeric scores or
  a separate timeline.
- **Capture or update:** route mutations through SelfContext's Learning
  procedure, including its no-update, provenance, review, and navigation rules.

## Response contract

Use only the sections useful for the request, normally:

- **Bottom line:** direct answer about current knowledge or its learning
  implication.
- **Evidence and state:** relevant pages, source links, qualitative state, and
  scope.
- **Gaps and uncertainty:** missing evidence, review items, contradictions, and
  freshness concerns.
- **Explanation or prerequisites:** generated reasoning or recommendation,
  grounded in supported knowledge.
- **What would change the answer:** one or two bounded evidence requests.

For a simple lookup, answer directly. Never invent a skill, course completion,
mental model, misconception, or competence level.

## Persistence boundary

Ordinary explanations, gap lists, prerequisite suggestions, and study advice
remain ephemeral. A substantial reusable explanation, or a smaller result the
user explicitly asks to retain, may be stored under `vault/derived/` only
through SelfContext's persistence, duplicate, ownership, freshness, metadata,
link, log, backup, and validation rules. Mark it `derived_synthesis`; it must
not update a Learning fact, goal, or verification state automatically.
