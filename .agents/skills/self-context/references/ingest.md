# Ingest and Update Workflow

Use this procedure when the user supplies new information, a source document,
a recollection, or a correction to existing context.

After orientation and once the operation is known to require a write,
determine the schema-specific vertical activation plan in
[Initialization](initialization.md). Create one pre-write backup described in
[Vault Backups](backups.md) before applying that plan or changing a page, index,
source record, review item, or log. Schema 0.1 preserves its legacy schema
without contract markers; schema 0.2 records only the exact contract for the
required vertical. Read-only work never activates a vertical. Do not continue
with the write if backup creation fails.

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

- Put context that can materially inform more than one domain in `core/`, such
  as explicit cross-domain goals, preferences, communication or decision
  patterns, and recurring constraints.
- Put domain-specific concepts in the owning vertical area, such as
  `career/` for career evidence.
- Put retained source or recollection material in `sources/`.
- Put unresolved interpretations in `review/observations/` with
  `assertion_kind: agent_inference`, `status: review`, and `verified: null`.

Route by scope, not by importance. A major career achievement still belongs in
`career/`; do not copy it into `core/` merely to make core look complete. Apply
the same rule to every current or future vertical: keep domain facts in their
owning area and use the area's documented procedure when one exists. For every
meaningful ingest, explicitly check whether the supplied material adds or changes
cross-domain context. Update an existing core concept when it does, and leave
`core/` unchanged when it does not.

Use frontmatter from [the schema](vault-schema.md). Preserve the appropriate
assertion kind and link every important normalized claim to its source record or
other evidence. When a source is ambiguous or conflicts with existing context,
preserve both sides, state the uncertainty, and create a review item instead of
choosing silently.

Do not infer a user's values, personality, motivation, or goal from a single
example. Evidence-oriented recurring patterns can be observations, not facts,
until the user confirms them.

A derived synthesis may help locate a possible cross-domain pattern, but it is
not evidence that can promote itself into `core/`. Trace the pattern back to
user statements or source records and preserve the appropriate assertion kind;
keep an unresolved interpretation under review.

## 3a. Writing-specific comparison

When the supplied material is authored writing, a revision, or an AI-assisted
draft, apply [the Writing vertical procedure](writing.md) before changing the
vault. Identify authorship, AI involvement, language, date, likely mode, and
reader context. Extract local observations first, then compare each candidate
with existing Writing context.

Classify the impact explicitly:

- **No meaningful update:** preserve a useful source record, but leave durable
  Writing concepts unchanged when the source is consistent with what is already
  known.
- **Reinforcement:** link an independent source to the existing observation and
  update its evidence history without creating a duplicate, auto-verifying, or
  churning an already established evidence state.
- **Genuine new insight:** add one scoped, reviewable observation only when the
  pattern is materially new and strong enough to retain.
- **Context refinement:** narrow or split a pattern by mode, audience, language,
  or time instead of overwriting a global statement.
- **Contradiction:** preserve both evidence sets and create or retain a review
  item until mode, exception, weak evidence, or evolution explains the conflict.
- **Evolution:** preserve historical evidence and represent a dated change or
  supersession; newer evidence is not automatically better.

For AI-assisted writing, analyze meaningful human edits as separate revision
evidence. A generated draft, summary, rewrite, critique, or untouched model
output cannot independently establish a Writing pattern. One edit is a
candidate signal, not a permanent preference.

Include a compact Writing impact report after the operation. It should state
existing patterns reinforced, new meaningful patterns, context refinements,
contradictions, potential profile updates, redundant observations ignored, and
whether the result was a profile refinement or "No meaningful update." The
second result is successful and is not a reason to manufacture a trait.

## 3b. Learning-specific comparison

When the supplied material concerns what the user understands, is learning,
does not understand, corrected, or wants explained, apply [the Learning
vertical procedure](learning.md) before changing the vault. Analyze the evidence
locally first, then compare it with the relevant Learning concepts, gaps,
corrections, and review observations.

- Preserve a source, exercise, project, or explanation only when it provides
  useful evidence about the person's knowledge; do not create a resource or
  course archive.
- Record the smallest scoped qualitative state in the Learning page body:
  encountered, learning, partially understood, understood, demonstrated,
  uncertain, or outdated. These are not numeric scores or automatic confidence.
- Treat a user-stated understanding, uncertainty, or correction as scoped user
  context. Treat an agent interpretation of an exercise, repeated question, or
  misconception as reviewable until the user confirms it or the evidence is
  otherwise explicit.
- Keep Career projects and Writing artifacts in their owning areas and link them
  as evidence rather than copying their facts into `learning/`.
- Preserve prior models and dated evidence when understanding changes. A new
  source that repeats a known state is a successful no-op, not a reason to add a
  duplicate concept.

A Learning impact report should state evidence retained, concepts or gaps
updated, contradictions or review items, cross-vertical links, and whether the
result was a meaningful update or "No meaningful Learning update."

## 3c. Relationships-specific comparison

When the supplied material concerns a person, group, shared history,
interaction, commitment, open loop, or relationship change, apply [the
Relationships procedure](relationships.md) before changing the vault. Keep the
subject as the user's relationship and analyze the smallest useful evidence:

- Distinguish the user's direct statement, a report of what another person
  said, a retained message or recollection, an observable interaction, and an
  agent interpretation.
- Find the existing relationship page before creating a person record. Retain
  only interactions with future contextual value; prefer a compact dated fact
  or linked commitment over a transcript or contact list.
- Distinguish actual promises from vague conversation. Record actor, action,
  status, context, and evidence when known, without creating a task manager.
- Preserve meaningful relationship evolution and contradictions as dated,
  scoped context. Motives, closeness, reliability judgments, and third-party
  characteristics remain reviewable observations rather than facts.
- Do not infer sensitive characteristics about third parties. Honor explicit
  delete, redact, archive, and retention requests and do not recreate removed
  details from old sources.
- Keep Career, Writing, Learning, Media / Taste, and `core/` claims in their
  owning areas and link them when the relationship context needs them.

A Relationships impact report should state the pages or source records changed,
shared context or commitments retained, privacy or redaction decisions,
reviewable items, cross-vertical links, and whether the result was meaningful or
"No meaningful Relationships update."

## 3d. Media / Taste-specific comparison

When the supplied material concerns a work, consumption, reaction, taste
pattern, exception, recommendation, or taste change, apply [the Media / Taste
procedure](media-taste.md) before changing the vault. Analyze the user's
experience and reaction locally before comparing it with existing work and
pattern pages:

- Separate consumption state and external metadata from the user's actual
  reaction. Finishing or starting a work does not establish liking.
- Update an existing work page when identity and reaction scope match. Retain
  only intentional or future-useful reactions; do not create a catalog or
  store every play, view, article, or song.
- A single work supports a broad pattern only when the user explicitly states
  that preference. Otherwise require multiple independently meaningful
  reactions for a plausible inferred pattern, keep it scoped, and preserve
  exceptions and contradictions.
- Represent taste change with dated evidence rather than deleting older
  reactions. Generated reviews, summaries, recommendations, and agent
  reactions are derived output, not personal evidence.
- Do not infer identity, ideology, politics, religion, sexuality, health,
  personality, or other sensitive characteristics from cultural consumption.
- Keep Learning, Relationships, Writing, Career, and `core/` claims in their
  owning areas and link them rather than duplicating them.

A Media / Taste impact report should state works and reactions retained,
patterns reinforced or left unchanged, exceptions or evolution, review items,
cross-vertical links, and whether the result was meaningful or "No meaningful
Media / Taste update."

## 3e. Triage Attention Without Blocking Ingest

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

Confirmation is page-scoped. If a page contains unrelated claims and the user
confirms only some of them, split the concept or leave the page unverified; do
not mark the whole page verified by implication.

## 3f. Assign Freshness Conservatively

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
Do not automatically assign longer deadlines, and do not assign deadlines to
historical pages, ordinary source captures, stable skills, or general
preferences merely because they exist.

If the situation is ambiguous, ask one bounded freshness question or leave the
field null. Calculate an automatic deadline from the current ingest date, not a
source publication date. A deadline schedules review; it does not verify the
claim or prove that it is current.

## 4. Connect and Maintain Navigation

Add links that explain meaningful relationships, such as a role to its projects,
a project to its skills and stories, or a goal to supporting evidence. Update
the nearest category index and the root index when a new durable page is
created. Managed catalog blocks can be inspected with the read-only
`sync_indexes.py --check` and refreshed with `sync_indexes.py --write` only
inside the authorized mutation workflow. They are navigation surfaces, not
evidence. Preserve user-written index text outside the markers and never
manually edit generated entries. Do not add links to nonexistent pages or link
every page to every related page.

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

Also state whether `core/` and `derived/` changed or were intentionally left
unchanged. For `core/`, give the domain-scope reason. For `derived/`, explain
that ingest does not require a synthesis unless the operation produced a
substantial reusable analysis worth maintaining.

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
