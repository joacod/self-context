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

1. Retrieve the relevant verified and source-supported evidence through
   SelfContext.
2. Preserve the meaning and scope of the underlying experience.
3. Improve clarity, emphasis, ordering, and audience fit.
4. Mark missing metrics, dates, outcomes, or ownership details as placeholders
   or questions instead of inventing them.
5. Identify claims in the draft that require user confirmation.

The draft itself is not automatically a new vault fact. Do not overwrite a
source or normalized career page to make it match a polished artifact.

## Derived Advice Pages

Do not create a page for a one-off recommendation or ordinary draft. A reusable
analysis may be stored only when it is substantial, expensive to reconstruct,
or likely to guide future work.

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

After creating a derived page, update the relevant derived index and log the
operation through SelfContext. If persistence is not clearly valuable, keep the
answer ephemeral.
