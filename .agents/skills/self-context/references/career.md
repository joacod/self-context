---
vertical_id: career
contract_version: 1
vault_area: career
advisor_skill: career-advisor
---

# Career Vertical Procedure

## Scope and ownership

Career owns evidence and concepts about the user's professional history and
future work: roles, projects, technical and organizational decisions,
skills demonstrated in context, achievements, leadership and mentoring
examples, public work, and explicitly stated professional goals.

Career does not own cross-domain values, communication patterns, learning states,
relationship continuity, media reactions, or recommendations produced by an
Advisor. Link to those owning areas instead of copying their claims. A role or
project remains career context even when it is useful in a writing, learning, or
relationship task.

## Storage and evidence

Use the shared Markdown, YAML frontmatter, provenance, verification, freshness,
review, and relative-link contract. Common career groupings such as `roles/`,
`projects/`, `skills/`, `stories/`, `goals/`, and `public-work/` are optional;
create them only when a real collection benefits from the grouping.

Classify input before normalizing it:

- a direct user statement or confirmation is scoped `user_stated_fact`;
- a resume, profile, repository, talk, or other retained source can support a
  `source_record` and, when appropriate, a linked `source_derived_fact`;
- an interpretation about scope, leadership, or fit is an
  `agent_inference`, normally under `review/observations/`; and
- positioning advice or an interview comparison is a linked
  `derived_synthesis`, not a new career fact or goal.

Do not invent metrics, dates, ownership, outcomes, titles, or management scope.
A missing example is a missing piece of evidence, not evidence that the user
lacks the experience. Do not turn repeated generated drafts or Advisor prose
into career evidence.

## Ingest and update

1. Orient from `SCHEMA.md`, the root index, recent log entries, and the Career
   index when it exists.
2. Search for the existing role, project, skill, story, goal, or public-work
   page before creating a duplicate.
3. Preserve a useful source record for a supplied resume or substantial source.
4. Update the smallest coherent career pages, link them to provenance and
   related evidence, and keep current-state claims subject to the shared
   freshness and confirmation rules.
5. Preserve competing accounts, historical scope, and dated evolution rather
   than silently choosing or averaging them.
6. Leave `core/` unchanged unless the user explicitly states a genuinely
   cross-domain value, preference, communication pattern, or constraint.
7. Update the nearest index and operation log after the normal pre-write backup.

A source that repeats existing career evidence may produce **No meaningful
Career update**. Preserving provenance and making no profile change is a
successful result. A recommendation may remain ephemeral unless the user asks
to retain it or it has durable reuse value under the shared query-persistence
rules.

## Queries and Advisor use

Retrieve only career evidence relevant to the objective. Label each important
claim as supported, likely, stale, disputed, or unknown after checking its
assertion kind, status, verification, sources, and freshness. Compare role
paths against scope, outcomes, influence, technical decisions, people
leadership, communication, preferences, and missing evidence. Career Advisor
owns the reasoning output; SelfContext remains responsible for retrieval,
provenance, persistence, and mutation safety.

## Contract migrations

Version 1 has no prior migrations. Future versions must identify affected
career evidence, list safe structural changes separately from semantic review
requirements, and state forbidden automatic changes. A new contract version
never invents experience, changes a goal, promotes an inference, resolves a
contradiction, or removes historical evidence automatically.
