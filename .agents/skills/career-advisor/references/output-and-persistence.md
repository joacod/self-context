# Career Outputs and Persistence

## Response Shape

Use only the sections useful for the request, but keep the distinctions clear:

```markdown
## Bottom line
Direct answer or recommendation.

## Evidence
Relevant claims with links or page names from SelfContext.

## Interpretation
What the evidence suggests, clearly labeled as interpretation.

## Uncertainty and gaps
Stale, unverified, contradictory, or missing context.

## Recommendation or draft
Advice or generated career material, never presented as a new fact.
```

For a simple factual question, answer directly and cite the evidence without
forcing this entire structure. For a substantial decision, keep the sections
so the user can distinguish evidence from advice.

## Professional Artifacts

When drafting a resume bullet, profile, bio, interview answer, or networking
message:

1. Retrieve the relevant verified, source-supported, or explicitly labeled
   unconfirmed user-stated evidence through SelfContext. Do not treat review or
   stale context as settled current evidence.
2. Preserve the meaning and scope of the underlying experience.
3. Improve clarity, emphasis, ordering, and audience fit.
4. Mark missing metrics, dates, outcomes, or ownership details as placeholders
   or questions instead of inventing them.
5. Identify claims in the draft that require user confirmation.

The draft itself is not automatically a new vault fact. Do not overwrite a
source or normalized career page to make it match a polished artifact.

## Derived Advice Pages

Do not create a page for a one-off recommendation or ordinary draft. A reusable
analysis may be stored when it is substantial, expensive to reconstruct, likely
to guide future work, or when the user explicitly asks to retain a smaller piece
of guidance for a similar future question. Treat that request as a continuity
signal, not as evidence that the recommendation is true.

Before persisting career advice:

- check existing career and derived pages for a matching analysis or duplicate;
- compare the recommendation with current goals, role positioning, and relevant
  core constraints;
- keep career facts in `career/`, cross-domain facts in `core/`, and the advice
  itself in `derived/`; and
- preserve factual conflicts or missing evidence, while expressing a competing
  recommendation conditionally instead of silently changing a goal.

Create it under a suitable `vault/derived/` subdirectory, such as
`derived/advice/`, using the SelfContext schema:

```yaml
---
type: synthesis
title: Evidence-based role positioning analysis
description: Reusable career analysis linked to supporting context.
tags:
  - career
status: active
generated: 2026-08-07
verified: null
sources:
  - ../../career/projects/example-project.md
  - ../../career/stories/example-story.md
assertion_kind: derived_synthesis
stale_after: null
---
```

The body must include the question or objective, linked evidence, uncertainty,
and clearly labeled recommendations. A derived page is not a source for a new
fact, current goal, or agent confidence loop.

Before creating a derived page, updating the relevant derived index, or
logging persisted advice in an existing current vault, prepare the semantic
proposal and invoke SelfContext's ordinary commit boundary. It stages the page,
managed index, and log, validates the result, owns both backups and rollback,
and returns one receipt. If persistence is not clearly valuable, keep the answer
ephemeral and do not create a backup solely for the read-only advice. Missing or
uninitialized bootstrap remains with SelfContext's Initialization procedure.
