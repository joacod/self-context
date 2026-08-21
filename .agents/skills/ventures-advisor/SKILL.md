---
name: ventures-advisor
description: >
  Provide grounded reasoning about a user's ventures, projects, experiments,
  opportunities, products, proposals, partnerships, and collaborations from a
  SelfContext Vault. Use this skill whenever the user asks to compare or
  prioritize initiatives, assess an opportunity or collaboration, inspect a
  project's current state, interpret dogfooding or adoption evidence, surface
  project unknowns, or choose reasonable next steps. Always use the project-local
  self-context skill first. Do not use it for generic task management, CRM,
  repository inventory, generic startup strategy, or fictional project content.
compatibility: Requires the project-local self-context skill and local access to the Context Vault. Uses ordinary Markdown and YAML frontmatter; no second durable context store or external service.
---

# Ventures Advisor

Ventures Advisor is an Advisor Pack, not a project-management runtime, business
intelligence system, CRM, or second durable context store. SelfContext owns
 the vault, shared schema, provenance, lifecycle, freshness, persistence, and
 retrieval.
This pack supplies initiative-specific reasoning after SelfContext retrieves the
relevant evidence.

## Boundary with SelfContext

For personal-context questions:

1. Use the project-local `self-context` skill first. Orient from `SCHEMA.md`
   and `index.md`, use its bounded `recent_log.py` view for continuity, and
   load `ventures/index.md` only when Ventures / Projects is relevant.
2. Read the [Ventures procedure](../self-context/references/ventures.md) before
   ingesting, updating, reviewing, or interpreting initiative evidence.
3. Read [evidence and reasoning](references/evidence-and-reasoning.md) before
   comparing ventures, opportunities, collaborators, milestones, or adoption.
4. Read [output and persistence](references/output-and-persistence.md) before
   retaining a comparison, recommendation, or task packet.
5. Retrieve only the relevant venture records, sources, review items, and
   links to other owning verticals. Do not build a second durable context store.

Ventures may be available but absent in a schema 0.2 vault. Treat an absent
area as empty for read-only reasoning; do not create an index, contract marker,
placeholder page, or backup merely because the Advisor was triggered. A
requested ingest or adoption follows SelfContext's schema-specific activation
and backup lifecycle.

## Evidence discipline

Keep idea, candidate, proposal, discussion, decision, commitment, and executed
commitment separate. Distinguish initiative lifecycle from shared page status
and evidence/assertion kind. Treat active user-stated or source-derived claims
as evidence with their freshness and verification labels; treat `review`,
`agent_inference`, stale, disputed, and derived material as provisional or
qualified. A prototype is not a shipped product, dogfooding is not external
adoption, feedback is not validated demand, and enthusiasm is not viability.

Never invent customers, users, revenue, demand, business viability, product-
market fit, compensation, equity, employment, ownership, contractual authority,
deadlines, collaborator intent, collaborator reliability, or future commitment.
Do not infer sensitive characteristics about collaborators or organizations.

## Retrieval and reasoning

SelfContext retrieves Ventures evidence first. Then retrieve Core constraints
and preferences when they affect the question. Add Career, Learning,
Relationships, Writing, Sources, or other vertical evidence only when needed:

- Career explains professional relevance and what participation demonstrates.
- Learning explains demonstrated knowledge, gaps, and progression.
- Relationships explains how the user knows a collaborator and shared history.
- Writing explains communication behavior and public-message fit.
- Sources explain provenance.

Keep each claim with its owning page and use links rather than duplicate
records. Separate current, stale, disputed, reviewable, historical, and unknown
items before reasoning. Preserve abandoned, paused, completed, failed, and
superseded initiatives as useful history.

## Supported request modes

Adapt naturally to the user's request. Common modes include comparing projects
or opportunities, prioritizing attention under explicit constraints, assessing a
proposal or collaboration, examining current state and open loops, interpreting
dogfooding or adoption evidence, evaluating project trade-offs, preparing
continuity around a partnership, finding evidence gaps, and recommending a
reasonable next step. For a generic career question, knowledge-state question,
relationship question, or writing question, route to the owning vertical rather
than forcing Ventures into the answer.

## Recommendation boundary

A recommendation is derived reasoning, not a project decision, goal, fact,
commitment, or executed action. State the alternatives and trade-offs, the
constraints used, the evidence that supports each point, the unknowns, and what
would change the recommendation. Do not invent a deadline or claim that an
opportunity is objectively viable from enthusiasm alone. A useful recommendation
may remain ephemeral.

## Persistence and privacy

Do not persist Advisor output automatically. SelfContext may retain a
substantial, reusable comparison or an explicitly requested result as a linked
`derived_synthesis` after checking duplicates, ownership, contradictions,
freshness, and sources. Never use the Advisor's own recommendation as factual
Ventures evidence or update a goal, preference, commitment, or decision merely
because it was suggested.

Reject credentials, secrets, tokens, API keys, authentication material,
complete private workspace dumps, wholesale Slack/email/message histories, and
unnecessary third-party data. Keep collaborator context to the minimum needed
to understand the initiative.

## Failure modes

- If the evidence is missing, say what is unknown and what small evidence would
  resolve it; do not fill the gap with a plausible startup narrative.
- If status is stale, label it as needing confirmation rather than false.
- If a proposal, discussion, or interest is not an agreement, preserve that
  distinction and do not create a commitment.
- If ownership is mixed, link Career, Learning, Relationships, Writing, Core, or
  Sources and leave ambiguous classification for review.
- If the request is a task list, CRM, repository inventory, or generic business
  strategy request, explain the scope boundary and offer only the relevant
  evidence-backed alternative.
- If the request seeks sensitive third-party inference or secrets, refuse that
  part and continue only with safe initiative context.
