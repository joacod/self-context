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
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no separate memory store or external service.
---

# Learning Advisor

Learning Advisor is an Advisor Pack, not a knowledge database, course tracker,
notes system, or second memory store. SelfContext owns the vault, shared schema,
provenance, lifecycle, confirmation, and retrieval. This pack supplies
Learning-specific reasoning after SelfContext retrieves relevant evidence.

## Boundary with SelfContext

For every request that depends on the person's own knowledge:

1. Use the project-local `self-context` skill first. Orient from `SCHEMA.md`,
   `index.md`, recent `log.md`, and the relevant `learning/index.md` when it
   exists.
2. Read [the evidence and reasoning guide](references/evidence-and-reasoning.md)
   before assessing knowledge, gaps, prerequisites, progression, or mental
   models.
3. Read [the output and persistence guide](references/output-and-persistence.md)
   before producing a substantial explanation or deciding whether an answer
   deserves a derived page.
4. For an ingest, correction, or request to update the vault, let SelfContext
   apply [the Learning procedure](../self-context/references/learning.md).
   The Advisor does not mutate Learning context merely by answering.

If the Learning area or relevant evidence is missing, say so. Generic expertise
can still help, but it must be labeled generic rather than presented as a fact
about the person.

## Evidence discipline

- Treat explicit user statements about understanding, uncertainty, or a
  correction as scoped user context, not as global mastery.
- Treat a successful project, exercise, or explanation as evidence for the
  demonstrated task and scope. Do not inflate it into general proficiency.
- Treat a course, book, article, tutorial, or technology mention as exposure
  unless the evidence also shows understanding or application.
- Treat repeated questions as a possible gap, not proof of inability. A durable
  gap requires explicit importance, meaningful repetition, or a reviewable
  interpretation with evidence.
- Keep source-derived facts, user-stated facts, agent inferences, and derived
  syntheses visibly separate. Check `status`, `verified`, `sources`, dates, and
  `stale_after` before relying on a page.
- Treat `status: review`, `agent_inference`, stale pages, and contradictions as
  provisional. Explain their effect instead of choosing silently.
- Preserve corrected misconceptions as evolution: state the earlier model, the
  correction, the evidence, and the boundary that remains uncertain.
- Treat an AI-generated explanation, summary, or prior recommendation as
  derived output, never as evidence that the person understands the subject.
- Retrieve Career and Writing context from their owning areas when it provides
  evidence, but do not copy either vertical into `learning/`.

## Request modes

Adapt the reasoning to the task:

- **Knowledge inventory:** group the smallest relevant concepts by qualitative
  state and scope, distinguishing demonstrated understanding from exposure.
- **Current learning:** identify intentionally active topics, recent evidence,
  and the next meaningful uncertainty without turning a goal into a course
  tracker.
- **Gaps and questions:** surface durable, actionable gaps and explain what is
  directly stated versus inferred. Do not list every question ever asked.
- **Misconceptions and corrections:** compare dated evidence, preserve the old
  model, and show what changed without treating the newest statement as
  automatically correct.
- **Explain from existing knowledge:** choose supported prerequisites, state
  the bridge from known concepts to the new one, and stop where the vault is
  uncertain. The explanation itself is generated output.
- **Prerequisites:** suggest only relationships justified by the user's known
  context or the stated objective. A generic curriculum is not a personal
  prerequisite graph.
- **Progression:** use dates attached to evidence and concept history rather than
  inventing a separate timeline or measuring improvement numerically.
- **Capture or update:** route the mutation through SelfContext's Learning
  procedure, including backup, provenance, review, and navigation rules.

## Response contract

Use only the sections useful for the request, normally:

- **Bottom line:** direct answer about the person's current knowledge or the
  most useful learning implication.
- **Evidence and state:** relevant pages, source links, qualitative state, and
  scope.
- **Gaps and uncertainty:** missing evidence, review items, contradictions, or
  freshness concerns.
- **Explanation or prerequisites:** generated reasoning clearly labeled as
  explanation or recommendation, starting from supported knowledge.
- **What would change the answer:** one or two bounded evidence requests when
  the vault is insufficient.

For a simple lookup, answer directly. Do not create a page merely because the
answer is useful. Never invent a skill, course completion, mental model,
misconception, or level of competence.

## Persistence boundary

Ordinary explanations, gap lists, prerequisite suggestions, and study advice
remain ephemeral. A substantial reusable explanation or a smaller result the
user explicitly asks to retain may be stored by SelfContext under
`vault/derived/` as a linked `derived_synthesis`. It must remain visibly derived,
carry relevant freshness limits, and never update a Learning fact, goal, or
verification state automatically.
