---
vertical_id: career
contract_version: 1
vault_area: career
advisor_skill: career-advisor
---

# Career Vertical Procedure

## Scope and ownership

Career owns evidence and concepts about the user's professional history and
future work: roles, project participation as professional evidence, technical
and organizational decisions, skills demonstrated in context, achievements,
leadership and mentoring examples, public work, and explicitly stated
professional goals.

Career does not own cross-domain values, communication patterns, learning states,
relationship continuity, media reactions, initiative lifecycle, or
recommendations produced by an Advisor. Link to those owning areas instead of
copying their claims. A project can remain Career context when the question is
about professional scope, impact, or relevance; Ventures owns the initiative's
purpose, lifecycle, current state, decisions, commitments, and outcomes.

## Storage and evidence

Use the shared Markdown, YAML frontmatter, provenance, verification, freshness,
review, and relative-link contract. Apply the current-schema activation rule in
[Initialization](initialization.md); this procedure does not redefine vertical
enablement, contract markers, or schema migration. A recognized older schema
must be upgraded before Career activation or normal Career operations. Common
career groupings such as
`roles/`,
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

1. Orient from `SCHEMA.md` and the root index, use the bounded
   `recent_log.py` view for continuity, and load the Career index when Career
   is the likely owner.
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
7. Create the provisional recovery backup before the page, index, and
   operation-log writes. Validate the result, create the final backup, and
   discard the provisional only after final backup success.

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

## Ventures compatibility

Career contract `career@1` remains valid. Its existing project language is
interpreted as the professional view of participation: what the work
demonstrates, its impact, scope, leadership or technical evidence, stories, and
career relevance. Ventures / Projects owns the living initiative lifecycle.
This is a boundary clarification and cross-linking rule, not a material
removal from Career's v1 contract, so no Career version bump is required.
Existing Career project pages remain readable and in place. Do not move,
rewrite, or bulk-split them automatically; ambiguous ownership is a review
decision.

## Contract migrations

Version 1 has no prior migrations. When a future version changes Career's
ownership or meaning, document the historical-upgrade question before
advertising it: where earlier evidence may be stranded in other areas, what
can be safely moved, split, or linked, and what remains ambiguous. `upgrade
vault latest` may apply only a complete documented safe path; it does not
replace this procedure or make ambiguous Career/project ownership decisions.
 Older applied Career contracts are migration sources, not permanent runtime
modes. Future versions must identify affected career evidence, list safe
structural changes separately from semantic review requirements, and state
forbidden automatic changes. A new contract version never invents experience,
changes a goal, promotes an inference, resolves a contradiction, or removes
historical evidence automatically.
