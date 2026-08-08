# Career Evidence and Reasoning

This guide explains how to reason over retrieved SelfContext evidence without
turning interpretation into personal fact.

## Evidence Set

Build the smallest relevant evidence set. Depending on the question, it may
include:

- roles and professional history;
- projects, technical decisions, and outcomes;
- skills demonstrated in context;
- leadership, mentoring, communication, and collaboration examples;
- public work, talks, writing, or profiles;
- professional goals, constraints, and preferences; and
- existing derived material, only as labeled analysis rather than independent
  evidence.

For each claim, inspect:

| Question | Why it matters |
| --- | --- |
| What is the assertion kind? | User fact, source-derived fact, inference, or synthesis have different trust. |
| Is it verified? | Unverified observations cannot be treated as established evidence. |
| Is it current? | `stale_after`, dates, and current-goal metadata affect relevance. |
| What supports it? | A source or linked page makes the claim auditable. |
| Is there a contradiction? | Conflicting pages require uncertainty, not silent selection. |
| Does it answer the objective? | Relevant evidence is better than a comprehensive biography. |

Use this default inclusion policy for current career reasoning:

- `active` pages with `user_stated_fact` or `source_derived_fact` are primary
  evidence when their freshness is appropriate.
- `draft` pages are provisional. Label them and avoid presenting them as
  settled facts.
- `review` pages and `agent_inference` claims can identify uncertainty or a
  question to confirm, but cannot support a confident recommendation by
  themselves.
- `archived` and `superseded` pages are historical unless the user asks about
  the earlier state.
- `source_record` pages establish provenance and can be quoted as source
  material, but they are not automatically normalized facts.
- `derived_synthesis` pages are reusable analysis, not independent evidence.

If a current page is past `stale_after`, either exclude it from a current
conclusion or label its historical use and explain the freshness concern.

An active user-stated or source-derived page with `verified: null` can still be
useful primary evidence when its provenance and freshness are appropriate. The
response should identify it as unconfirmed rather than silently upgrading it to
explicitly verified. A page with `status: review` is provisional and should
usually produce a bounded confirmation question when it materially affects the
answer.

When a dynamic page has `stale_after: null`, treat its freshness as unknown if
currentness is decisive. Do not turn a missing deadline into either a stale
warning for every query or an assumption that the page is current.

Use language that exposes epistemic status:

- **Supported:** "The vault records..." or "The supplied source states..."
- **Pattern:** "Across these examples, a recurring pattern appears to be..."
- **Uncertain:** "This is an unverified observation..." or "The evidence is mixed..."
- **Unknown:** "The vault does not currently establish..."
- **Advice:** "Given the objective, I recommend..."

Do not strengthen a claim merely because it appears in several derived pages.
Generated repetition is not independent evidence.

## Comparing Career Paths

When comparing paths such as Staff Engineer, Lead Engineer, or Engineering
Manager, compare the user's evidence and objective across relevant dimensions:

- scope and duration of influence;
- technical depth and system-level decisions;
- cross-team or organizational influence;
- delivery and measurable outcomes;
- people leadership, mentoring, and management evidence;
- communication and alignment across stakeholders;
- appetite or stated preference for the work; and
- gaps, stale context, and missing examples.

Do not assume that a title maps to the same scope everywhere. Explain which
evidence transfers and which target-specific evidence is missing.

## Strengths and Gaps

Call something a strength when multiple relevant examples support it or a
source explicitly documents it. Call something a gap only when the target
requires evidence that is absent, contradicted, or underdeveloped. Distinguish
"not in the vault" from "the user has not done this."

For a potentially useful but unverified pattern, point to the observation and
recommend confirmation rather than silently promoting it.

## Insufficient Evidence

When evidence is thin:

1. Answer the portion that is supported.
2. Name the missing evidence or uncertainty.
3. Offer a bounded next step, such as asking for one concrete example or
   recommending that the user confirm a goal.

Do not compensate with generic confidence, personality claims, or invented
stories.
