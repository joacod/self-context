# Optional Query Modes

Read [Query](query.md) first. Load only the relevant section below for contextual
reasoning, a requested context receipt, or a task context packet. These modes
retain the same runtime, scope, evidence, freshness, and read-only contract.

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

Define the problem or decision narrowly, then declare the smallest likely
scope before retrieving context. Use the [Query scope rules](query.md#contextual-retrieval-scope-rules): begin with `core/`
or the primary vertical, add only materially relevant owners, and expand linked
source records only when their provenance, freshness, or verification can
change the answer. Potentially relevant material includes:

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
whole conversation history. Use the same `--include-evidence` preparation call
as ordinary Query. Start from the relevant indexes and expand only to linked
pages needed for the problem. Complete evidence already returned satisfies
reading that page. For every important item, inspect its owner, assertion
kind, status, provenance, freshness, and any explicit replacement before using
it.
Include multiple owning areas only when the problem requires them. Cross-area
retrieval preserves each area's ownership; it does not copy facts between
verticals. Never indiscriminately load the vault just because the request says
"based on my context."

### Frame

Before settling a consequential recommendation, check whether a relevant
exception, review item, or competing constraint could reverse it. Follow the
selected pages' useful explicit links; if those do not resolve the question,
make at most one bounded counterevidence search in `review/` or another justified
owner using the same entity and decision anchors. Explain any scope expansion.
Do not search every review item by default. If the pass finds no counterevidence,
say none was found in that scope, not that none exists. Retain contradictions,
source dates, and review status in the resulting conditional answer.

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

A contextual thinking session is ephemeral and read-only by default. Do not
mutate canonical pages, operational logs, indexes, backups, vertical markers,
frontmatter metadata, or generated persistent artifacts while retrieving or
reasoning. Do not persist generated ideas, brainstorm alternatives, discarded
options, temporary reasoning, or speculative assistant conclusions merely
because they appeared in the conversation.

The existing [Persistence Decision](query-persistence.md#persistence-decision) rules still apply
when the user explicitly asks to retain a durable fact, decision, or reusable
synthesis: evaluate explicit retention or durable reuse, check for a matching
home, preserve ownership and provenance, compare conflicts and freshness, and
store only the smallest justified result. A retained synthesis remains
`derived_synthesis`; it is not evidence for a new fact or goal, and its
alternatives are not silently copied into `core/` or a vertical. An operation
log entry is also a mutation and requires a separate explicit request; it is
never an automatic side effect of read-only Query. If the user later supplies a
durable fact or decision, handle that separately through normal ingest and
confirmation semantics.

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
the user separately and explicitly authorized a query-log or persistence
operation, report that outcome accurately rather than attributing it to the
receipt request.

### Receipt contents

Match the surrounding response's communication style instead of forcing a rigid
template. For an explicit receipt request, include the non-empty items that
answer the request, using bounded labels such as:

- **Context used:** only the relevant durable concepts or source paths, with
  their owner and role/provenance. Identify only context that affected the
  answer; do not dump the vault or reproduce page bodies.
- **Scope used:** include this only when cross-vertical scope materially shaped
  the result, for example `core, ventures`; optionally say which clearly
  unrelated areas were not expanded.
- **Coverage/as-of:** when relevant, name the source or evidence coverage date,
  generated date, or other as-of boundary.
- **Freshness:** distinguish an automatic `stale_after` horizon from dated
  source coverage. Say “no automatic stale horizon; currentness unknown” when
  `stale_after: null` governs dynamic evidence; never describe null as fresh
  forever.
- **Assertion:** identify important `user_stated_fact`, `source_derived_fact`,
  `source_record`, `agent_inference`, or `derived_synthesis` status when it
  affects the answer.
- **Tradeoffs:** important competing goals, constraints, costs, or alternatives
  that materially shaped a recommendation. Summarize the decision-relevant
  comparison, not private token-by-token reasoning.
- **Uncertain / contradictory:** unsupported gaps, provisional material, or
  relevant claims that point in different directions, keeping status and
  provenance visible.
- **Result:** classify the answer as a **direct answer**, **synthesis**,
  **derived recommendation**, or **contextual reasoning**. A recommendation
  built from evidence is derived output, not a direct fact from any source.
- **Persistence:** say what durable update was made through the existing
  lifecycle, or say that no durable or operational-log change was made. Name
  the canonical page or area when something was stored. A receipt request never
  creates a receipt file.

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
operational-log change. Read-only Query makes neither change by default. For an
ephemeral brainstorm, the accurate statement is: “Persistence: nothing
persisted; no page, transcript, derived synthesis, or log entry was stored.” If
the user explicitly authorized a separate query-log mutation, name that log
entry without calling it a durable context update. A receipt request itself
never changes that state.

### Compact examples

**Inspecting the sources behind a recommendation**

John Doe asks whether to keep the Harbor CLI in maintenance mode at MyContext
Systems. A useful receipt can say:

```text
Context used: the Ventures project page, the recorded repeat-adoption decision,
and the core six-hour weekly constraint.
Scope used: core, ventures. Not expanded: relationships, media.
Freshness: no automatic stale horizon on the dynamic project state; currentness
would need confirmation if decisive. Assertion: the decision is recorded
project context; the recommendation is derived.
Tradeoffs: expanding scope conflicts with the time constraint and the recorded
adoption threshold; maintenance preserves reversibility but delays new scope.
Result: derived recommendation — keep maintenance mode for now, not a recorded
fact or new decision.
Persistence: nothing persisted; no page, log entry, or receipt file was created.
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

## Task context packets

When the user asks for a task context packet, return only the smallest relevant
material: the task objective, directly supported personal context, relevant
examples, constraints and explicit preferences, stale/provisional/contradictory
context, unknowns, evidence paths, and important exclusions. Keep relationship
and other sensitive context out unless directly relevant. The packet is derived
output, not evidence, and remains ephemeral unless the user explicitly asks to
retain a reusable packet under `derived/` through the normal persistence and
backup rules.
