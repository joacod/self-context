# Query and Derived Material

## Contents

- [Deep-lint inventory versus search output](#deep-lint-inventory-versus-search-output)
- [Contextual thinking as a Query mode](#contextual-thinking-as-a-query-mode)
- [Optional Context Receipts](#optional-context-receipts)
- [Targeted Retrieval](#targeted-retrieval)
- [Verification and Freshness at Query Time](#verification-and-freshness-at-query-time)
- [Persistence Decision](#persistence-decision)
- [Derived Page Shape](#derived-page-shape)
- [Task context packets](#task-context-packets)
- [Log and Response](#log-and-response)

This is the canonical procedure for Query, contextual thinking, task context
packets, persistence decisions, and context receipts. Keep those semantics in
this reference; other procedures should link here rather than create parallel
conversation or reasoning workflows.

Keep index-first retrieval as the primary workflow. Use the disposable local
lexical helper only as a fallback when the index is ambiguous, aliases are
likely to matter, the vault is medium or large, the task spans a few verticals,
or historical context may matter:

```bash
python3 .agents/skills/self-context/scripts/search_vault.py "task words" vault
```

`search_vault.py` is read-only, dependency-free, builds no permanent index, and
never replaces the Markdown vault. Its deterministic priorities are exact stable
ID, exact normalized title, exact normalized alias, title/alias phrase, and
then lexical matches. For non-exact queries, unique query-term coverage is the
primary signal; matched-term count, field importance (title/alias, description/
tags, headings, body), phrase matches, term proximity, status, page type, and
assertion kind refine the ordering. Path is the final tie-breaker. A one-token
title match should not outrank a page covering nearly all task terms merely
because the token is in a prominent field.

JSON results include matched fields, bounded snippets, a match type, query-term
coverage, phrase fields, and a deterministic `rank_score`. The score explains
ordering only; it is not confidence, truth, or verification. Archived and
superseded pages are included by default with lower ranking. Use
`--exclude-archived` or `--exclude-superseded` to omit them. The accepted
`--include-archived` and `--include-superseded` options are deprecated
compatibility aliases for one cycle and will be removed in a future release;
they do not change the default inclusion behavior. Sources remain opt-in via
`--include-sources`.

Search is only a retrieval aid: inspect provenance, freshness, assertion kind,
review state, contradictions, and source links before answering. Deep-review
reports and noncanonical state remain excluded.

Before modern query semantics, require the shared latest-first runtime gate.
A current schema with current applied contracts may be queried normally. An old
recognized schema or stale applied contract must not receive a native modern
query answer or silently upgrade; return a concise `upgrade vault latest`
direction. Limited read-only orientation and migration planning may inspect
control state and selected old pages solely to explain or perform the upgrade.
Future, malformed, and unversioned state is a compatibility/recovery blocker.

## Deep-lint inventory versus search output

Deep-lint JSON is a deterministic maintenance inventory, not a second evidence
store. Use its compact page metadata to batch pages, compare ownership, select
provenance and stale-source candidates, and triage index/link relationships
before opening full files. Its `tags` and aliases are selection aids only; they
do not establish a personal claim. `outbound_links` and `inbound_links` are
ordinary internal navigation, while `source_relationships` is reserved for
frontmatter `sources` and remains a provenance pointer without authority or
truth scoring. A newer linked timestamp is a review candidate, not an automatic
rewrite instruction.

Search output may include a strictly bounded snippet to help answer a targeted
query. Do not copy those snippets, complete bodies, source transcripts, or task
packets into deep-lint JSON or a retained deep-review report. The inventory
points to evidence files; it does not replace reading the relevant page when
content is needed.

Use this procedure for retrieval, comparison, synthesis, or evidence gathering.

## Contextual thinking as a Query mode

Contextual thinking is a subtype of Query—not a separate operation—for problems
that ask the model to reason with the user's existing context: brainstorming,
decision support, comparisons, tradeoffs, challenges, alternatives, or
overlooked considerations.
It uses the same latest-first runtime gate, index-first retrieval, provenance,
freshness, contradiction, ownership, and persistence rules as every other
Query. It is not a new vertical, advisor, data model, runtime, CLI, or chat
subsystem.

Use this mode for prompts such as:

- help me think through whether I should continue this project
- challenge this idea using what you know about the project
- compare these two options against my priorities
- brainstorm approaches based on my existing goals and constraints
- what am I overlooking here?
- help me decide, explore alternatives based on my context, or argue against
  this based on what you know

Do not force this full flow onto a simple lookup. When the user is asking for
contextual reasoning, move through the following sequence and keep the labels
visible in the answer.

### Retrieve

Define the problem or decision narrowly, then retrieve only context that can
change the reasoning. Potentially relevant material includes:

- known facts and evidence;
- goals, values, constraints, and preferences;
- previous decisions, commitments, and their recorded rationale;
- related projects, initiatives, or current-state records;
- previous reusable derived conclusions, marked as derived rather than source
  evidence;
- contradictions, unresolved observations, and review items; and
- stale or otherwise provisional information that could affect the answer.

Find previous decisions wherever the existing vault records them and follow
relevant links; do not invent a decision-specific storage model or replay the
whole conversation history. Start from the relevant indexes and expand only to
linked pages needed for the problem. For every important item, inspect its
owner, assertion kind, status, provenance, and freshness before using it.
Include multiple owning areas only when the problem requires them. Cross-area
retrieval preserves each area's ownership; it does not copy facts between
verticals. Never indiscriminately load the vault just because the request says
"based on my context."

### Frame

Before proposing options, establish what the problem looks like from the
retrieved evidence. Separate:

- **Supported context:** user-stated or source-derived material, with its
  evidence path and scope;
- **Assumptions:** premises needed to proceed that the vault does not establish;
- **Unknowns:** missing information that could change the result;
- **Contradictions:** active or reviewable context that points in different
  directions; and
- **Stale or provisional context:** expired, dynamically untracked, or
  `status: review` material that cannot be treated as settled current evidence.

The frame is an explanation of the evidence, not a new durable fact. If a
contradiction or stale item is decisive, keep the conclusion conditional and
ask at most a bounded question when that is enough to resolve it.

### Explore

Generate meaningfully different possibilities rather than several phrasings
of one recommendation. Options may differ in scope, mechanism, sequence,
commitment, or reversibility, but each should connect to the retrieved goals,
constraints, preferences, decisions, and evidence. Include a status-quo or
pause option when it is a real alternative, not as a mandatory formality. Label
brainstormed alternatives as generated possibilities, not as facts about the
user or the project.

### Challenge

Evaluate serious options against the user's known goals, constraints, previous
decisions, evidence, preferences, and relevant project or cross-vertical
context. Surface conflicts, opportunity costs, reversibility, the strongest
argument against each option, and the evidence gap that would most change the
choice. Do not let a stale, provisional, or contradictory item silently decide
between options. A model-generated recommendation remains derived and does
not become a goal, decision, preference, or user fact automatically.

### Conclude

Separate the useful ending into whichever of these are relevant:

- supported observations;
- tradeoffs;
- unknowns and freshness limits;
- recommendations, clearly labeled as derived and conditional;
- assumptions; and
- questions worth resolving.

A conclusion may recommend a next step, but it must not rewrite the user's
goals, confirm a fact, or erase a contradiction. If the retrieved context is
insufficient, say what is missing and provide a bounded question or conditional
path instead of filling the gap with generic advice.

### Persistence for contextual thinking

A contextual thinking session is ephemeral by default. Do not persist generated
ideas, brainstorm alternatives, discarded options, temporary reasoning, or
speculative assistant conclusions merely because they appeared in the
conversation. The existing [Persistence Decision](#persistence-decision)
rules still apply: evaluate explicit retention or durable reuse, check for a
matching home, preserve ownership and provenance, compare conflicts and
freshness, and store only the smallest justified `derived/` synthesis. A
retained synthesis remains `derived_synthesis`; it is not evidence for a new
fact or goal, and its generated alternatives are not silently copied into
`core/` or a vertical. A permitted query log entry does not change this
boundary: it records the operation under existing logging rules, not generated
alternatives or temporary reasoning. If the user later supplies a durable fact
or decision, handle that separately through normal ingest and confirmation
semantics.

## Optional Context Receipts

A context receipt is a compact, on-demand explanation of the evidence and
epistemic status behind a Query answer. It is not an audit report, a transcript,
or a private reasoning dump, and it never exposes chain-of-thought. Offer one
when the user explicitly asks questions such as:

- Why did you reach that conclusion?
- What context or sources did you use?
- Show me the context behind that recommendation.
- What did you base that on?
- Was any of this stale or contradictory?
- Did you save anything from that?

Treat these requests as a presentation mode for the existing Query result, not
as a new operation or persistence signal. A receipt request must not create a
receipt file, a logging database, a provenance system, or a vault mutation. If
the underlying operation separately qualifies for the existing query-log or
persistence lifecycle, report that outcome accurately rather than attributing
it to the receipt request.

### Receipt contents

Match the surrounding response's communication style instead of forcing a rigid
template. For an explicit receipt request, include the non-empty items that
answer the request, using bounded labels such as:

- **Context used:** relevant durable concepts or source paths, with their role
  or provenance when useful. Identify only context that affected the answer;
  do not dump the vault or reproduce full page bodies.
- **Tradeoffs:** important competing goals, constraints, costs, or alternatives
  that materially shaped a recommendation. Summarize the decision-relevant
  comparison, not private token-by-token reasoning.
- **Uncertain:** assumptions, unsupported gaps, or provisional material that
  limits the result.
- **Contradictory:** relevant unresolved claims or pages that point in different
  directions, keeping their status or provenance visible.
- **Stale:** relevant context beyond its freshness expectation, or dynamic
  context whose currentness is unknown. Do not renew freshness merely by citing
  it.
- **Result:** classify the answer as a **direct answer**, **synthesis**,
  **derived recommendation**, or **contextual reasoning**. A recommendation
  built from evidence is derived output, not a direct fact from any source.
- **Persistence:** say what durable update was made through the existing
  lifecycle, or say that no durable context was persisted. Name the canonical
  page or area when something was stored. If only the existing operation log was
  written, say that no durable context update was made and distinguish the log
  entry instead of claiming that no file changed.

When the user asks specifically about stale or conflicting input, answer that
category even when the answer is “none identified.” When the user asks why,
include the relevant tradeoffs and uncertainty, but do not expose hidden
chain-of-thought, internal prompts, token-by-token deliberation, or unrelated
private context. The receipt identifies evidence and epistemic status; it does
not claim that evidence is verified merely because it was retrieved.

### Automatic behavior and persistence boundaries

Do not append a full receipt to a routine lookup, ordinary advice answer, or
normal contextual-thinking response. Continue to surface materially important
contradictions, stale decisive context, uncertainty, and confirmation needs in
ordinary responses even when no receipt was requested. If a checkpoint or
mutation leaves persistence ambiguous, explicitly report what was and was not
stored using its existing lifecycle report; do not create a second receipt
artifact.

Use “nothing persisted” only when the operation made no durable context or
operational-log change. For an ephemeral brainstorm whose normal operation did
not log anything, the accurate compact statement is: “Persistence: nothing
persisted; no page, transcript, or derived synthesis was stored.” If an existing
query log entry was permitted, say instead: “No durable context update; the
query was logged under the existing logging rules.” A receipt request itself
never changes that state.

### Compact examples

**Inspecting the sources behind a recommendation**

John Doe asks whether to keep the Harbor CLI in maintenance mode at MyContext
Systems. A useful receipt can say:

```text
Context used: the Ventures project page, the recorded repeat-adoption decision,
and the core six-hour weekly constraint.
Tradeoffs: expanding scope conflicts with the time constraint and the recorded
adoption threshold; maintenance preserves reversibility but delays new scope.
Result: derived recommendation — keep maintenance mode for now, not a recorded
fact or new decision.
Persistence: nothing persisted.
```

**Separating direct evidence from a derived recommendation**

```text
Context used: the existing Ventures decision records that expansion waits for
repeat adoption. That is direct recorded context.
Result: the suggestion to run a smaller reliability experiment is a derived
recommendation from that decision and the time constraint; it is not itself a
recorded decision.
Persistence: nothing persisted.
```

**Confirming that brainstorming persisted nothing**

```text
Context used: John Doe's documented goal and time constraint.
Result: contextual reasoning; the alternatives were generated for this session.
Persistence: nothing persisted; no page, transcript, or derived synthesis was
stored.
```

## Targeted Retrieval

Start with `SCHEMA.md`, `index.md`, recent log entries, enabled vertical
indexes, and the smallest relevant linked pages. Managed catalog blocks are
compiled navigation, not evidence; inspect the linked durable page and its
provenance before relying on an entry. If a catalog is missing, drifted, or has
invalid marker structure, treat it as an unreliable navigation aid and run
`sync_indexes.py --check` as a read-only diagnostic. Do not manually edit
managed entries. `sync_indexes.py --write` belongs only inside an authorized
current-model mutation workflow. For schema 0.2, an absent available vertical
is empty; a read-only query must not create its area or contract marker. A
schema 0.1 query is limited to orientation/diagnosis and must direct the user
to upgrade rather than promise current retrieval semantics. Use local lexical
search as the fallback described above, not as a replacement for index
orientation. Do not scan the entire vault for a narrow question unless
orientation shows that the relevant path is unclear.

Start with `SCHEMA.md`, `index.md`, and recent log entries. Use category indexes,
frontmatter, filenames, targeted text search, and links to locate relevant
pages. Do not scan the entire vault for a narrow question unless orientation
shows that the relevant path is unclear.

Separate the result into:

- what the vault directly supports;
- what appears likely from several pieces of evidence;
- what is unknown, stale, contradictory, or unverified; and
- any conclusion or recommendation, which is derived rather than fact.

Never use an agent inference or derived advice as if it were independent source
evidence. If the vault is insufficient, say so and identify the missing context
instead of guessing.

For Writing retrieval, include the relevant mode, audience, language, dates,
authorship, and evidence state. Generated drafts and derived style analyses are
not independent evidence of the user's communication. A Writing query may
report that no meaningful profile update was needed; retrieval and analysis do
not require a new durable page.

For Learning retrieval, read the relevant `learning/` concepts and linked
sources, then include the qualitative knowledge state, scope, dated evidence,
gaps, corrections, and prerequisite relationships. Distinguish exposure from
understanding or demonstrated application. Use reviewable Learning observations
as uncertainty, not settled knowledge. An explanation based on known concepts is
still derived output and does not update the Learning profile automatically.

For Relationships retrieval, read only the relevant relationship pages, shared
history, commitments, open loops, and linked source records. Keep reported
statements, user observations, source-derived facts, and agent inferences
separate. Do not expose unrelated third-party information or infer sensitive
characteristics. Context before an interaction is a focused derived answer, not
a complete person dossier.

For Media / Taste retrieval, read individual work reactions, supporting pattern
pages, exceptions, and dated evidence. Consumption is not preference, and
external metadata, copied reviews, and generated reactions are not personal
evidence. Explain recommendations through matches and conflicts in the user's
actual reactions; keep the recommendation derived and do not update taste or
`core/` automatically.

For Ventures / Projects retrieval, read the relevant initiative records, lifecycle
and current-state sections, decisions, commitments, milestones, outcomes,
dogfooding/adoption evidence, evolution, review items, and linked sources. Keep
ideas, candidates, proposals, engagements, discussions, agreements, decisions,
and executed commitments distinct. Treat stale current state as needing
freshness confirmation, not as false. Route professional meaning to Career,
knowledge state to Learning, relationship continuity to Relationships, writing
behavior to Writing, broad preferences to `core/`, and reusable recommendations
to `derived/` without copying the initiative record into those owners.

## Verification and Freshness at Query Time

Treat verification and freshness as separate dimensions:

- An active page with `verified: null` is usable as source-derived or user-stated
  evidence when its status and provenance are appropriate, but describe it as
  unconfirmed rather than presenting it as explicitly verified.
- A page with `status: review` is provisional. Use it to identify a question or
  uncertainty, not as settled evidence for a confident answer. If it is decisive
  to the question, give the user the supported conditional answer and ask one
  bounded confirmation question rather than silently promoting it.
- A page past `stale_after` may remain useful historical evidence, but do not use
  it as current without labeling the freshness problem or asking the user.
- `stale_after: null` means there is no automated deadline. It does not prove
  that dynamic information is current; if currentness is decisive, identify the
  freshness as unknown and ask a bounded question.

When a user confirms that an expired current-state claim is still true, update
the page's `verified` date when the claim was explicitly confirmed and set
`stale_after` from the current date using the selected or default horizon. If
the user reports a change, follow the correction workflow and preserve the old
evidence rather than silently rewriting it. Reading or citing a page alone must
not renew either field.

If a user defers or leaves a review item unconfirmed, do not repeat the prompt in
unrelated answers. Surface it again during an explicit review or when it becomes
decisive to the requested answer.

## Persistence Decision

Use the smallest durable result that serves the request:

- A simple lookup, such as a previous employer or project name, returns an
  answer and may be logged without creating a page.
- A meaningful query can be logged when it informs continuity or exposes a
  review item.
- A substantial, reusable comparison or synthesis may become a page under
  `derived/`, with `type: synthesis`, `assertion_kind: derived_synthesis`, and
  links to the evidence it combines.

### Continuity signals

Persistence is based on durable value, not only on importance or length. Treat
one or more of these as a reason to evaluate a small derived page:

- the user explicitly asks to remember, retain, save, or reuse the result;
- the user says the result would help with a similar future question;
- the answer captures a non-obvious decision, recommendation, or tradeoff that
  will be expensive to reconstruct;
- the answer combines several existing pages into a reusable synthesis; or
- the query exposes a meaningful review item, unresolved conflict, or missing
  evidence that should remain visible.

An explicit retention request is a continuity signal, not permission to promote
an interpretation into a fact. A positive reaction without a future-use signal
does not require persistence.

### Persistence checks

Before creating or updating a derived page, perform a lightweight semantic
check:

1. **Classify the result.** Separate retrieved facts, source material,
   observations, recommendations, and unknowns. Persist advice as
   `derived_synthesis`; route newly supplied factual context through ingest
   instead of hiding it in advice.
2. **Check for an existing home.** Search the relevant indexes and linked pages
   for an existing concept or synthesis. Update the smallest matching page
   rather than creating a duplicate.
3. **Check ownership.** Keep domain facts and goals in their owning vertical,
   cross-domain facts in `core/`, and reusable conclusions in `derived/`. A
   synthesis may link several areas without copying their facts into another
   owner.
4. **Check conflicts.** Compare the conclusion with active goals, facts,
   review items, and relevant derived pages. Preserve factual contradictions and
   surface them as uncertainty or review. A recommendation can remain
   conditional when it explores an option that differs from a current goal; do
   not rewrite the goal merely because the advice is useful.
5. **Check freshness.** If current metrics, role state, goals, or other dynamic
   context materially affects reuse, record a review horizon or explain the
   freshness limitation. Do not silently rely on stale decisive evidence.

If the result has no stable reuse value, no explicit future-use signal, and no
meaningful review value, keep it ephemeral. Do not create a page merely because
several queries were asked or because the answer sounds helpful.

Do not save every answer. A derived page should earn its maintenance cost by
being likely to be reused, difficult to reconstruct, explicitly requested for
future continuity, or important for later review. It must not modify `core/` or
vertical facts merely because the synthesis recommends something.

The number of queries is not the persistence threshold. Several simple lookups
may leave `derived/` unchanged, while one substantial reusable analysis may
justify a page. Do not create a synthesis only to make the folder appear
current.

## Derived Page Shape

When persistence is justified, use a stable descriptive filename and frontmatter
like this:

```yaml
---
type: synthesis
title: Evidence for technical leadership scope
description: Reusable synthesis of leadership evidence across several roles.
tags:
  - leadership
status: active
generated: 2026-08-07
verified: null
sources:
  - ../career/roles/example-role.md
  - ../career/projects/example-project.md
assertion_kind: derived_synthesis
stale_after: 2027-02-07
---
```

The body should state the question, summarize evidence with links, identify
uncertainty and freshness, and label conclusions as derived. If the result is
advice, label recommendations as recommendations. Never phrase a recommendation
as a newly confirmed goal.

For a persisted query result, create the provisional recovery backup before
creating or updating the derived page, index, or operation log. Validate the
resulting vault, create the final backup, and discard the provisional only after
final backup success as described in [Vault Backups](backups.md).

## Task context packets

When the user asks for a task context packet, return only the smallest relevant
material: the task objective, directly supported personal context, relevant
examples, constraints and explicit preferences, stale/provisional/contradictory
context, unknowns, evidence paths, and important exclusions. Keep relationship
and other sensitive context out unless directly relevant. The packet is derived
output, not evidence, and remains ephemeral unless the user explicitly asks to
retain a reusable packet under `derived/` through the normal persistence and
backup rules.

## Log and Response

Log a substantial query or a meaningful evidence retrieval, but not every
trivial lookup. Report whether a derived page was created, which evidence was
used, and what remains unknown or needs user confirmation. If no page was
created, briefly state that the answer did not meet the reusable-synthesis
threshold.
