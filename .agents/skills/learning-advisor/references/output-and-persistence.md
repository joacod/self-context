# Learning Outputs and Persistence

## Response shape

Use only the sections needed for the question:

```markdown
## Bottom line
Direct answer about the person's knowledge or learning state.

## Evidence and state
Relevant Learning pages, source links, scope, and qualitative state.

## Gaps and uncertainty
Review items, contradictions, stale context, or missing evidence.

## Explanation or prerequisites
Generated teaching or recommendations, clearly labeled and grounded in the
supported starting point.
```

For a simple lookup, answer directly with the relevant page or source. For a
substantial question, keep evidence, interpretation, and recommendation
separate so a useful explanation cannot be mistaken for a personal fact.

## Teaching from prior knowledge

Before drafting an explanation, establish:

- the target concept and the user's objective;
- which prerequisites are supported, scoped, current, and not under review;
- the one or two bridges that make the new idea easier to understand; and
- the boundary where the vault does not establish prior knowledge.

Use concrete examples when they genuinely connect the known concept to the new
one. Do not force a historical mental model if it would obscure the idea. Mark
generic teaching as generated output and invite the user to correct an assumed
starting point.

## Gap and progression reports

A good gap report prioritizes a small number of meaningful unresolved items. It
should say why each gap matters, what evidence supports it, and what evidence
would resolve it. It must not be a list of every question or a claim that the
person is weak merely because the vault is silent.

A progression report links dates to evidence and preserves earlier states,
corrections, exceptions, and uncertainty. Avoid numeric scores, streaks, or
course-completion metrics. “No meaningful Learning update” is a valid result
when new evidence repeats an existing state.

## Cross-vertical answers

When a Career project or Writing artifact supplies evidence, name its owning
page and explain the limited Learning implication. Do not reproduce the career
outcome or communication pattern in the Learning profile. If a source only shows
that a resource was consumed, report exposure rather than understanding.

## Derived material

Ordinary explanations, recommendations, and study plans remain in the response.
A reusable synthesis may be persisted only when it combines substantial evidence,
exposes a durable gap, or the user explicitly asks to retain it for future use.
Before writing, SelfContext must check for a duplicate, ownership conflicts,
contradictions, and freshness. Store it under `vault/derived/` with:

```yaml
---
type: synthesis
title: Evidence-backed explanation starting points
description: Reusable explanation guidance linked to the person's known concepts.
tags:
  - learning
status: active
generated: 2026-03-05
verified: null
sources:
  - ../learning/example-concept.md
assertion_kind: derived_synthesis
stale_after: null
---
```

The body must identify the question, linked evidence, assumptions, uncertainty,
and recommendations. A derived page is not evidence, does not verify a
Learning concept, and does not change a goal or core preference.

Before any persisted result, create the provisional recovery backup. After
writing and validating, use the shared final backup and discard the provisional
only after final backup success. Report whether a Learning page changed, whether
only derived material changed, and what remains unconfirmed.
