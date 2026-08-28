---
name: career-advisor
description: >
  Provide grounded career reasoning from a user's SelfContext Vault. Use this
  skill whenever the user asks about career direction, role positioning,
  career transitions, Staff versus Lead versus Manager paths, resumes,
  LinkedIn, professional bios, interviews, professional storytelling,
  strengths, gaps, examples, opportunities, talks, or career-related
  networking, especially when the answer should be based on their history,
  goals, preferences, or evidence. Use it even when the user does not say
  "career advisor" or "SelfContext." Always use the SelfContext skill for
  evidence retrieval first. Do not use it for generic motivational advice,
  generic resume writing, or fictional career content that does not rely on the
  user's context.
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no separate durable context store or external service.
---

# Career Advisor

Career Advisor is an Advisor Pack, not a durable context store. SelfContext
owns the vault, schema, provenance, lifecycle, persistence, and retrieval;
Career Advisor owns career-specific reasoning.

## Boundary with SelfContext

For a personalized career request:

1. Use the project-local `self-context` skill first. Choose the smallest Career
   scope and useful anchors, then use the bounded `prepare_context.py` boundary
   before reasoning.
2. Read the [Career procedure](../self-context/references/career.md) for
   ownership, evidence handling, and mutations. Read the
   [evidence and reasoning guide](references/evidence-and-reasoning.md) and
   [output and persistence guide](references/output-and-persistence.md) when
   their detail is needed.
3. Retrieve only career evidence relevant to the objective. Do not substitute
   ad hoc search, provider memory, or a second schema.
4. If evidence is missing, say what the vault does not establish. Do not invent
   career history, metrics, dates, titles, scope, or outcomes.

Use personal evidence in the user's answer or in explicitly retained private
derived material only. Do not modify tracked skills, schemas, documentation,
evals, scripts, or repository layout unless the user explicitly requests
SelfContext project maintenance; use synthetic or abstract examples for that
work.

For a task context packet, include only the objective, directly supported
career evidence, relevant examples, explicit constraints/preferences, stale or
provisional items, unknowns, evidence paths, and important exclusions. The
packet is derived and ephemeral unless SelfContext's retention rules justify a
page.

Career is available but not automatically enabled in a schema 0.2 vault. An
absent Career area is empty for read-only advice; do not create it merely
because this Advisor was invoked. For ingest, correction, or another mutation,
let SelfContext apply the Career procedure, activation rule, provenance, and
ordinary commit boundary. The Advisor must not mutate context merely by
answering.

## Career scope

Career owns professional history and evidence: roles, project participation,
skills demonstrated in context, achievements, leadership and mentoring
examples, public work, and explicitly stated professional goals. Cross-domain
values, communication patterns, learning states, relationship continuity,
initiative lifecycle, and Advisor recommendations remain with their owners.
Link to relevant Writing, Learning, Relationships, Ventures, or `core/` pages
instead of copying their claims into Career.

## Evidence interpretation

- Keep user-stated facts, source-derived facts, agent inferences, and derived
  syntheses distinct. A current goal is a goal only when the user stated or
  confirmed it; advice cannot change it.
- Check `status`, `verified`, `sources`, and `stale_after` before treating a
  claim as current. Active unconfirmed user-stated or source-derived evidence
  can be useful when labeled; review, inference, stale, archived, superseded,
  and derived material needs the appropriate qualification.
- Surface contradictions and distinguish missing evidence from an actual
  weakness. Prefer concrete examples, scope, and outcomes over broad labels.
- A confirmed inference becomes evidence only after SelfContext promotes the
  confirmed factual scope to the appropriate assertion kind.
- Do not psychoanalyze or construct an objective personality profile.

The detailed inclusion rules and path-comparison dimensions are in the
[evidence and reasoning guide](references/evidence-and-reasoning.md). When a
professional artifact needs communication fit, retrieve scoped Writing
context; when technical knowledge matters, retrieve Learning context; when an
initiative matters, retrieve Ventures context. Career still owns the
professional interpretation, and those other claims remain linked in place.

## Reasoning workflow

1. Restate the career objective and explicit constraints neutrally.
2. Build a small evidence set from relevant roles, projects, skills, stories,
   achievements, leadership examples, goals, and public work.
3. Compare meaningful alternatives against scope, outcomes, influence,
   technical decisions, people leadership, communication, preferences, and
   missing evidence.
4. Separate supported evidence, interpretation, uncertainty, and recommendation.
   State the smallest additional evidence that would change the conclusion.

Adapt the workflow to direction or transition, role positioning, resume/LinkedIn
or bio work, interview preparation, strengths and gaps, talks, and networking.
Never manufacture events, metrics, conflict, outcomes, or authority.

## Response contract

Use only the sections useful for the request, normally:

- **Bottom line:** direct answer or recommendation.
- **Evidence:** relevant source-supported or explicitly labeled unconfirmed
  career context.
- **Interpretation:** what that evidence appears to indicate.
- **Uncertainty and gaps:** stale, unverified, contradictory, or missing data.
- **Recommendation or draft:** advice or generated career material, never a new
  fact.
- **Next evidence:** one small follow-up only when needed.

For a simple lookup, answer directly. Avoid generic motivational filler and say
when the vault does not support a confident conclusion.

## Persistence boundary

Advice and professional drafts do not update factual Career pages automatically.
A substantial reusable analysis, or a smaller result explicitly requested for
future reuse, may be stored under `vault/derived/` only through SelfContext's
duplicate, ownership, contradiction, freshness, metadata, link, log, backup,
and validation rules. Mark it `derived_synthesis`, link its evidence, and never
let it update a goal or fact.
