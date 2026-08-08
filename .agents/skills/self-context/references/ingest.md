# Ingest and Update Workflow

Use this procedure when the user supplies new information, a source document,
a recollection, or a correction to existing context.

## 1. Understand the Input

Identify what the user actually stated, what a supplied source says, and what
is still unknown. Do not fill gaps. Decide whether the material is:

- a direct user statement or confirmation;
- a source record to preserve;
- a normalized source-derived fact;
- a correction or contradiction; or
- an agent observation that needs review rather than storage as fact.

Importance is an attention decision, not an epistemic category. Do not mark a
claim verified because it sounds important, appears repeatedly, or has a source.

For a resume, profile, or other meaningful document, preserve a Markdown source
record under `sources/` when practical. Keep the original wording or a faithful
text capture sufficient to explain later normalized claims. Do not create an
arbitrary binary document dump as the durable representation.

## 2. Orient and Find Related Concepts

Read the schema, root index, and recent log first. Search relevant category
indexes and pages for names, organizations, roles, dates, projects, skills, and
distinctive phrases from the new information. Follow links only as far as
needed to understand relationships.

Do not search `.obsidian/` or treat viewer configuration as supplied context.

Prefer an existing concept when the identity and subject match. A new page is
appropriate when it represents a distinct durable concept, not merely a new
sentence about an existing one.

## 3. Normalize Conservatively

Create or update the smallest coherent set of pages:

- Put broadly reusable context in `core/`.
- Put career-specific concepts in `career/`.
- Put retained source or recollection material in `sources/`.
- Put unresolved interpretations in `review/observations/` with
  `assertion_kind: agent_inference`, `status: review`, and `verified: null`.

Use frontmatter from [the schema](vault-schema.md). Preserve the appropriate
assertion kind and link every important normalized claim to its source record or
other evidence. When a source is ambiguous or conflicts with existing context,
preserve both sides, state the uncertainty, and create a review item instead of
choosing silently.

Do not infer a user's values, personality, motivation, or goal from a single
example. Evidence-oriented recurring patterns can be observations, not facts,
until the user confirms them.

## 3a. Triage Attention Without Blocking Ingest

After normalizing the supplied material, decide whether a small number of items
deserve immediate human attention. Keep ordinary ingestion smooth; do not ask a
question for every unverified page.

Use `status: review` with `verified: null` for selected items such as:

- a current role, employer, goal, availability, or hard constraint that could
  materially change a future answer;
- an important claim with ambiguous wording, competing versions, or missing
  provenance;
- an agent inference that should not be treated as a fact until confirmed; or
- a source-derived claim where the user explicitly asked for confirmation.

Leave routine source records, historical facts, ordinary skills, and low-impact
user-stated context as `status: active` with `verified: null`. A null value by
itself is not a review queue entry.

For a batch ingest, present one short summary after the pages are created. Group
questions by coherent page or concept and offer the actions `confirm`, `revise`,
`later`, or `leave unconfirmed`. `Confirm` records the explicit verification;
`revise` updates the claim and verifies it only when the user's wording clearly
confirms the revision; `later` keeps `status: review`; and `leave unconfirmed`
leaves the page active with `verified: null` without keeping it in the attention
queue. A rejection preserves the source and removes, supersedes, or archives
the normalized claim according to the user's instruction. Do not turn silence
into confirmation. If the user defers an item, keep it reviewable but do not
interrupt unrelated future answers unless the item is decisive to the question
or the user requests review.

Confirmation is page-scoped for v0.1. If a page contains unrelated claims and the
user confirms only some of them, split the concept or leave the page unverified;
do not mark the whole page verified by implication.

## 3b. Assign Freshness Conservatively

Keep `stale_after: null` unless a simple review deadline is useful. The default
automatic deadline is 90 days, and it applies only when all of these are true:

- the material clearly describes a current or active state;
- the state is likely to affect future retrieval, advice, or decisions; and
- the page represents a narrow concept such as a current role, employer, active
  goal, availability, or hard constraint; and
- the normalized assertion is a user-stated or source-derived fact, not a source
  record, agent inference, or derived synthesis.

Mention an automatically assigned deadline in the ingest summary so the user can
change or remove it. Respect an explicit date or review horizon from the user.
A user choice about a review horizon belongs in the same batched follow-up as
confirmation; do not open a separate freshness interview.
Do not automatically assign 180-day or 360-day deadlines in v0.1, and do not
assign deadlines to historical pages, ordinary source captures, stable skills,
or general preferences merely because they exist.

If the situation is ambiguous, ask one bounded freshness question or leave the
field null. Calculate an automatic deadline from the current ingest date, not a
source publication date. A deadline schedules review; it does not verify the
claim or prove that it is current.

## 4. Connect and Maintain Navigation

Add links that explain meaningful relationships, such as a role to its projects,
a project to its skills and stories, or a goal to supporting evidence. Update
the nearest category index and the root index when a new durable page is
created. Do not add links to nonexistent pages or link every page to every
related page.

When a page enters `status: review`, keep the review index or a linked review
observation useful for finding the pending action. Do not create a separate
observation page for every ordinary unverified source-derived claim.

## 5. Log and Report

Append a concise dated entry to `log.md` for meaningful ingests and updates.
Include the operation, summary, changed pages, source records, and unresolved
follow-up items. Do not copy an entire resume or personal narrative into the
log.

Tell the user what was created or updated, what evidence was retained, what
remains uncertain, and whether confirmation is needed. A correction should
preserve useful history and provenance; do not silently erase a conflicting
source.

## Corrections and Confirmation

When the user corrects a page:

1. Update the normalized claim to match the user's correction.
2. Set `verified` to the current date when the user is confirming the claim.
3. Preserve a source link or note the user confirmation in the body when useful.
4. If the old claim remains in a source record, do not edit the source to make
   it agree; explain the discrepancy or mark the old normalized page
   superseded.
5. Resolve or archive the associated observation only after the user's intent
   is clear, and log the change.

## Confirmation and Re-ingest Rules

When the user explicitly confirms a named page or claim:

1. Set `verified` to the current date for the confirmed scope.
2. Change a pending page from `status: review` to `status: active` when no other
   unresolved issue remains.
3. Preserve its source links and record the confirmation in the operation log
   when the change is meaningful.

When the user explicitly asks for evidence-based verification, compare the
named claim with the specified source or a source the user explicitly designated
as authoritative. Merely supplying or finding a source does not authorize
verification. If the evidence conflicts or remains ambiguous, leave
`verified: null` and create or retain a review item instead of choosing silently.

Repeated ingestion of unchanged evidence must preserve existing `verified` and
`stale_after` values, `status`, assertion kind, provenance links, and any linked
review rationale. If a page gains material new claims that are not covered by
its previous confirmation, split the page or reset verification for the affected
coherent scope rather than silently extending the old confirmation. Do not clear
a pending review item merely because the same source was ingested again.

If the user explicitly confirms an agent inference as a factual statement, move
the confirmed scope to `assertion_kind: user_stated_fact` before making it
active. If the user only accepts it as a useful hypothesis, keep it an
`agent_inference` with `status: review`.

When a user confirms that a stale current-state claim is still true, update
`stale_after` from the current date using the selected or default horizon. Do not
renew a deadline merely because another source was ingested or because a page
was read.
