# ADR 0018: Add the Ventures / Projects Vertical

- **Status:** Accepted
- **Date:** 2026-08-14

## Context

SelfContext needs a durable home for the lifecycle of meaningful initiatives:
projects, experiments, opportunities, collaborations, proposals, milestones,
commitments, outcomes, and deliberate pauses or endings. These facts are not
the same as professional positioning, knowledge state, relationship history,
writing behavior, or cross-domain preferences. Without an owning area, project
continuity is likely to be duplicated across Career or reduced to task tracking.

## Decision

Add `ventures` as an available, optional vertical at contract version 1, using
`ventures/` and `ventures/index.md`, the shared page contract, and a flexible
venture/project record. Initiative lifecycle is readable body content rather
than a required frontmatter state machine; page status, assertion kind, and
freshness remain shared SelfContext concepts.

Ventures owns the initiative itself: purpose, origin, current state, role and
evidenced authority, project-specific collaborators, decisions, milestones,
commitments, evidence, outcomes, dogfooding, adoption evidence, assumptions,
unknowns, and evolution. Career owns the professional relevance of
participation, Learning owns knowledge states, Relationships owns interpersonal
continuity, Writing owns communication behavior, Core owns cross-domain
patterns, Sources owns provenance, Review owns unresolved decisions, and
Derived owns reusable analyses. Links are preferred to copied facts.

Career `career@1` remains valid. Its existing project language is interpreted as
professional project evidence and relevance, while Ventures owns the living
initiative lifecycle. This clarification does not materially narrow Career's
v1 contract, so no version bump or migration is introduced. Existing Career
pages remain in place and ambiguous ownership remains a human review decision.

Ventures is selectively activated. Availability does not enable it; read-only
queries do not create it; the current schema records exactly `ventures@1` only
when a meaningful mutation or explicit adoption requires it. Recognized schema
0.1 vaults must use `upgrade vault latest` before this current activation
semantics applies; migration preserves their historical structure without
adding legacy runtime behavior. Activation creates only the required area,
index, marker, and root link. No placeholder project pages or automatic Career
relocation is performed.

A `ventures-advisor` pack performs evidence-first comparison, prioritization,
trade-off, adoption, collaboration, and next-step reasoning. It is not a
durable context store, project manager, CRM, or autonomous business strategist. Unknowns,
stale state, proposals, dogfooding, feedback, and recommendations remain
explicitly qualified. The implementation adds no new schema, database,
embeddings, runtime, external integration, or state-management system; ordinary
Markdown and the existing catalog-driven tooling are sufficient.

## Privacy and rejected alternatives

Credentials, secrets, tokens, private workspace dumps, wholesale transcripts,
and unnecessary third-party data are outside the vertical. The procedure never
infers employment, compensation, equity, authority, ownership, contractual
status, demand, adoption, revenue, viability, collaborator intent, or
reliability without evidence.

A generic task manager, CRM, repository inventory, startup database, product
management system, separate initiative schemas, automatic business analysis,
and a copy of Career projects were rejected. They either duplicate ownership,
create unsupported certainty, or add infrastructure that would reduce
portability and privacy without improving the canonical Markdown lifecycle.
