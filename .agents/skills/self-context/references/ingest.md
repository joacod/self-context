# Ingest and Update Workflow

Use this procedure when the user supplies new information, a source document,
a recollection, or a correction to existing context.

Ordinary ingest enters through the shared `prepare_context.py` boundary:
choose the smallest semantic scope and useful search anchors, call it, and
inspect the runtime state in the returned packet before planning a write. Do
not perform a separate schema/runtime compatibility or orientation read first.
Only a current schema with current applied contracts may continue to normal
ingest. If the packet reports schema 0.1 or an older applied contract, do not
run legacy ingest semantics or silently upgrade; tell the user to run
`upgrade vault latest`. Future, malformed, or unversioned state is a safe
blocker/recovery case.

For an existing current vault, determine the semantic page/source/review
proposal and any explicit current-schema vertical activation decision in
[Initialization](initialization.md), then invoke the ordinary commit boundary.
It stages the supplied bytes, activation controls, managed indexes, and
operation log; validates the complete proposed state; and owns the provisional
and final backups, active transaction, rollback, and guarded cleanup. Inspect
one structured receipt rather than coordinating those mechanics separately.
Read-only work never activates a vertical. If the helper reports
`initialization-required`, preserve this procedure's existing bootstrap
exception and use [Initialization](initialization.md); missing-vault
initialization is not owned by ordinary commit.

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

## 2. Choose scope and prepare context

Decide what the supplied material means, choose the smallest likely owner, and
select useful names, organizations, roles, dates, projects, skills, or
distinctive phrases as search anchors. Then call the bounded read-only
preparation helper with the explicit scope and anchors:

```bash
python3 .agents/skills/self-context/scripts/prepare_context.py \
  vault --scope career --anchor "organization" --anchor "project" \
  --recent-limit 10 --result-limit 10 --expand-linked-sources
```

The packet composes the latest-first runtime state, selected navigation,
bounded `recent_log.py` continuity, existing lexical ranking, and bounded
linked-source candidates. It does not infer semantic ownership, search every
enabled vertical, initialize a missing vault, run deep lint, or decide whether
pages represent the same concept. Read the relevant full pages and provenance
returned by the packet, and add another explicit scope only when it can
materially change the ingest. Follow links only as far as needed to understand
relationships; do not load unrelated verticals or the complete log by default.

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

### 3a. Apply vertical-specific procedure

When the material belongs to a vertical, read its procedure before deciding
what to retain. The procedure owns detailed scope, evidence interpretation,
page shapes, cross-vertical boundaries, and vertical-specific reporting.
Ingest owns shared normalization, duplicate checks, provenance, confirmation,
freshness, navigation, logging, and the commit boundary.

| Material | Canonical procedure |
| --- | --- |
| Career evidence or professional context | [Career](career.md) |
| Knowledge state, gap, correction, or progression | [Learning](learning.md) |
| Authored writing or communication evidence | [Writing](writing.md) |
| Shared history, relationship, commitment, or open loop | [Relationships](relationships.md) |
| Media reaction or taste evidence | [Media / Taste](media-taste.md) |
| Initiative lifecycle, project decision, milestone, or outcome | [Ventures / Projects](ventures.md) |

Keep these decision-point guardrails visible while routing:

- **Writing:** identify authorship, AI involvement, mode, and reader context;
  analyze locally before comparing with the Writing profile. Generated prose is
  not independent evidence, and a consistent source may produce no profile
  update.
- **Learning:** distinguish exposure, intentional learning, understanding, and
  demonstrated application. Record a scoped qualitative state, preserve
  corrections, and do not treat a source or explanation as competence.
- **Relationships:** keep the subject as the user's relationship. Separate
  direct statements, reported statements, sources, observations, and
  inferences; retain only useful continuity and never infer sensitive
  third-party characteristics.
- **Media / Taste:** separate consumption and external metadata from the user's
  reaction. Require independent meaningful evidence for inferred patterns and
  preserve exceptions, contradictions, and dated evolution.
- **Ventures / Projects:** keep initiative lifecycle separate from page status
  and distinguish ideas, proposals, discussions, decisions, and commitments.
  Preserve unknowns and route professional, learning, relationship, writing,
  core, source, review, and derived claims to their owners.
- **Career:** keep professional evidence and concepts in Career, distinguish
  source-supported evidence from inference, and do not invent scope, outcomes,
  dates, titles, or management responsibility.

Use each procedure's required impact or no-op report. A vertical-specific
source or observation can be retained without changing its durable profile when
the comparison finds no meaningful update.

## 3f. Triage Attention Without Blocking Ingest

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

## 3g. Assign Freshness Conservatively

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
a project to its skills and stories, or a goal to supporting evidence. Include
those semantic page bytes in the ordinary proposal. The commit boundary derives
managed catalog candidates in the staged vault, preserves user-written text
outside the markers, and includes the resulting index bytes in the same active
write set. Do not run `sync_indexes.py --write` against the active vault as a
separate step or manually edit generated entries. Do not add links to
nonexistent pages or link every page to every related page.

When a page enters `status: review`, keep the review index or a linked review
observation useful for finding the pending action. Do not create a separate
observation page for every ordinary unverified source-derived claim.

## 5. Log and Report

For a meaningful ingest, supply the operation identifier, concise semantic
summary, and affected canonical paths in the ordinary proposal's `log` object.
The shared log primitive owns the dated Markdown formatting and deterministic
append behavior in the staged vault; it does not invent the summary or infer
ownership. Do not copy an entire resume or personal narrative into the log.

Tell the user what was created or updated, what evidence was retained, what
remains uncertain, whether confirmation is needed, and what the one commit
receipt reports. A correction should preserve useful history and provenance; do
not silently erase a conflicting source.

### Ordinary commit boundary

The helper accepts only a thin filesystem proposal: optional
`expected_snapshot`, `writes` mapping canonical relative labels to prepared text
or bytes, explicit `activations` catalog IDs, and, when the staged state changes, `log` metadata containing `operation`,
`summary`, and `paths` (a byte-equivalent proposal may omit it). It supports
CREATE/UPDATE only. It rejects
unsafe paths, control/index writes, symlink traversal, non-regular targets,
private backup/viewer state, malformed labels, and deletion attempts. It
independently checks that the vault is existing/current/compatible; it does not
trust a preceding `prepare_context` packet. Missing or uninitialized vaults
return `initialization-required` and remain with the existing initialization
procedure.

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
