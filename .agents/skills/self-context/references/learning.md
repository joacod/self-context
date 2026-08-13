---
vertical_id: learning
contract_version: 1
vault_area: learning
advisor_skill: learning-advisor
---

# Learning Vertical Procedure

The Learning vertical preserves a small, evidence-backed model of what the
person understands and how that understanding changes. It is not a notebook,
reading list, course tracker, resource catalog, or general-purpose knowledge
base. The durable subject is the person’s knowledge state; source material is
kept only when it explains or supports that state.

## Scope and ownership

Learning owns:

- topics and concepts that are intentionally relevant to the person’s
  understanding;
- qualitative knowledge states and the scope in which they apply;
- meaningful gaps, unresolved questions, misconceptions, corrections, mental
  models, prerequisites, and personal concept relationships;
- exercises, explanations, projects, and learning experiences when they are
  evidence about understanding; and
- dated evidence that shows progression, uncertainty, or a changed model.

Learning does not own:

- every topic, article, book, course, bookmark, certificate, or resource the
  person encountered;
- generic facts or AI-generated explanations that do not say something about
  the person’s knowledge;
- broad goals, habits, values, or cross-domain preferences owned by `core/`;
- employment history, professional outcomes, or project ownership owned by
  `career/`; or
- authored communication behavior owned by `writing/`.

A Career or Writing page can be evidence for a Learning claim. Link to that
page instead of copying its record. Media / Taste owns a reaction to a book,
film, podcast, or other work; Learning owns only what the person's reaction or
work demonstrates about their understanding. Relationships owns the shared
relationship context around a learning interaction. Neither vertical is
implemented by this Learning procedure.

## Storage and page choices

Use the schema-specific activation rule in [Initialization](initialization.md);
this procedure does not redefine vertical enablement, contract markers, or
schema migration. The shared contract remains the only storage schema.

- `learning/index.md` is the navigation page for durable Learning concepts.
- `learning/` contains the smallest useful set of topic or concept pages. Add a
  subdirectory only when a real collection makes navigation clearer.
- Retained source or recollection material stays under shared `sources/` and
  uses `assertion_kind: source_record`. Do not turn `sources/` into a reading
  archive.
- An unresolved interpretation belongs under `review/observations/` with a
  Learning tag and a link to the relevant Learning concept or evidence. Use
  `type: observation`, `assertion_kind: agent_inference`, `status: review`, and
  `verified: null` until the user resolves it.
- A reusable explanation or recommendation belongs under shared `derived/`
  with `assertion_kind: derived_synthesis`. It is not evidence of knowledge and
  must not update a Learning page merely because it was useful.

All durable pages use the shared frontmatter contract. Learning does not add a
second schema, numeric score, confidence field, claim database, graph store, or
special lifecycle. Knowledge state, scope, evidence rationale, and history are
readable Markdown sections in the page body.

## Concept granularity and noise control

Create or update a Learning page only when at least one of these is true:

- the user explicitly asks to retain what they understand, are learning, do not
  understand, corrected, or want to revisit;
- a source, exercise, project, or explanation provides reusable evidence about
  understanding in a meaningful scope; or
- an unresolved gap, misconception, or prerequisite is likely to matter again
  and is specific enough to guide a future answer.

Do not create a page for an incidental technology mention, a single resource
opened, a definition supplied by the agent, or a question that has no evidence
of a durable gap. Consolidate adjacent concepts when their distinction would
not change retrieval or explanation. A topic is a navigation anchor for
relevant personal evidence, not a page for every noun in a source.

An exposure record can remain a source record or an ephemeral answer. Reading a
book, completing a course, or using a technology once does not establish
understanding. A casual statement such as “I used Rust yesterday” is not by
itself evidence of proficiency.

## Qualitative knowledge states

Use one or more of these human-readable labels in a `## Knowledge state` or
similar body section. They are not frontmatter fields and are not a numerical
scale:

- **encountered:** the person has seen or interacted with a concept; normally
  too weak for a durable concept page unless the exposure itself is useful.
- **learning:** the person is intentionally working toward understanding it.
- **partially understood:** some explanation or application is supported, with
  a meaningful boundary or gap remaining.
- **understood:** the person explicitly reports a coherent understanding within
  a stated scope, without implying mastery everywhere.
- **demonstrated:** an exercise, explanation, project, or other evidence shows
  the person can apply or explain the concept in a stated context. This is not
  a global proficiency claim.
- **uncertain:** the person reports uncertainty or the available evidence is
  mixed, provisional, or under review.
- **outdated:** prior understanding or practice is retained as history because
  the person or evidence says it is no longer current. Do not infer forgetting
  merely from time passing.

State changes are evidence-led. Preserve earlier states when they explain a
correction, progression, or loss of currentness; do not silently overwrite the
history with the newest wording.

## Evidence classification

Classify the input before deciding whether to create or update durable context:

| Input | Durable treatment |
| --- | --- |
| The user explicitly says they understand, are learning, or are confused about a concept | Store the named scope as `user_stated_fact` when it is useful; do not broaden it to general proficiency. |
| A user-authored explanation or answer | Preserve it as evidence when useful. A clear explanation may support a scoped `demonstrated` state; the page must retain the actual source or recollection. |
| A successful exercise, implementation, or project | Link the exercise or owning Career project. Record what it demonstrates, not everything the source mentions. If the knowledge interpretation is agent-derived, keep it reviewable. |
| A course, book, article, conversation, or tutorial was consumed | Keep a source record only when provenance matters. Consumption alone does not create a knowledge claim. |
| Repeated questions or failed attempts | Treat the pattern as a possible gap or misconception. It becomes durable only when the user says it matters or the evidence is strong enough for a scoped review item. |
| The user corrects a previous belief | Preserve the earlier belief and the correction with dates. An explicit correction can be `user_stated_fact`; an agent-detected correction remains an inference under review. |
| Career evidence demonstrates a technology in use | Keep the professional project in `career/` and link it as Learning evidence. Do not copy the project, role, or outcome into `learning/`. |
| Writing evidence explains a subject | Keep the article and communication pattern in `writing/`; link it as evidence for the Learning claim only when it reveals the person’s understanding. |
| An agent-generated explanation, summary, or recommendation | It is derived output, not evidence of the person’s knowledge. Persist it only under the shared query-persistence rules when future reuse justifies it. |

The source’s assertion kind and the Learning claim’s assertion kind may differ.
For example, a source can establish that an exercise was completed while an
agent’s interpretation that it demonstrates a broader concept remains a
reviewable observation.

## Learning ingest and update

After the normal SelfContext orientation, apply this sequence for Learning
material:

1. **Classify the evidence.** Separate what the user said, what a retained
   source documents, what the agent observes, and what remains unknown. Do not
   infer competence from exposure or from a single casual mention.
2. **Find the existing home.** Read `learning/index.md`, search relevant titles
   and tags, and follow only the linked pages needed to distinguish an update
   from a new concept. Look for existing gaps, correction history, and review
   observations before creating another page.
3. **Analyze before mutating.** State locally what the evidence demonstrates,
   what it does not demonstrate, the likely scope, and whether it changes the
   existing state. Repeated wording in one source is not independent evidence.
4. **Choose the smallest page.** Update an existing concept when identity and
   scope match. Create a new page only for a distinct durable concept or a
   meaningful gap. Keep a candidate interpretation in `review/observations/`
   rather than presenting it as settled knowledge.
5. **Record the state and boundary.** In the body, state the qualitative
   knowledge state, the scope, what is understood, what remains uncertain, and
   the evidence links. Use `status: review` for selected unresolved or
   contradictory pages; do not mark every `verified: null` page for review.
6. **Preserve evolution.** Add dated evidence entries for progression. When a
   misconception is corrected, retain the previous model, the correction, and
   the evidence that changed the interpretation. When evidence conflicts,
   preserve both sides until mode, scope, exception, or time explains it.
7. **Connect without copying.** Link meaningful prerequisites and related
   concepts only when the relationship helps future reasoning. Link Career and
   Writing pages at their owning paths. Do not create a universal knowledge
   graph or duplicate cross-vertical records.
8. **Maintain navigation and provenance.** Update `learning/index.md`,
   `review/index.md` when a review observation is added or resolved, the root
   index when the area is first created, and `log.md` for a meaningful
   operation. Keep source records under `sources/` when retaining them makes
   the claim auditable.
9. **Use the shared backup and confirmation rules.** Before the first write,
   create the project-root pre-write backup. Batch at most one concise follow-up
   for selected high-impact, ambiguous, contradictory, or inferred items. A
   source alone never verifies a Learning claim.

For an existing vault without `learning/`, a read-only request treats the area
as empty. A requested Learning mutation follows the schema-specific activation
rule in [Initialization](initialization.md) and does not move pages or migrate
the rest of the vault.

## Gaps, questions, and misconceptions

A durable gap should help a future answer or learning decision. Prefer a
specific statement such as:

> Understands React reconciliation but remains unclear about the exact
> scheduling behavior of concurrent rendering.

Record the boundary and evidence rather than a generic “learn React” task. A
question becomes durable when it is explicitly important, repeated across
meaningful attempts, blocks a future explanation or project, or exposes a
misconception worth remembering. A single question with no continuity signal
stays ephemeral.

For a misconception or correction, use a readable section such as:

```markdown
## Misconception history

- 2026-01-10 — Previous model: X behaves because of Y. Evidence: [source](../sources/example.md).
- 2026-02-04 — Correction: the relevant mechanism is Z. Evidence: [exercise](../sources/example-exercise.md).
- Current boundary: the corrected model is demonstrated for A; behavior in B remains uncertain.
```

Do not erase the previous model when it helps explain how understanding changed.
Do not create a correction history for an agent-generated textbook explanation
that the user never held.

## Mental models and prerequisites

A mental model is the person’s demonstrated or explicitly adopted way of
reasoning about a concept. It is not an AI-generated textbook explanation. Keep
it scoped, link the evidence that shows the model is useful, and label an agent
interpretation as reviewable.

Prerequisites are personal relationships, not a universal curriculum. Add a
standard relative link only when the user’s known context or evidence supports a
useful relationship, for example:

```markdown
## Prerequisites and relationships

- [Parametric polymorphism](parametric-polymorphism.md) is a useful existing
  foundation for this topic.
- Comfort with [asynchronous control flow](async-control-flow.md) is still
  partial and may be worth reviewing first.
```

Do not create placeholder prerequisite pages or infer a complete dependency
graph from generic subject matter. A prerequisite recommendation in an answer
is derived advice until the user adopts it or evidence supports it.

## Queries and explanations

For a Learning query, retrieve the smallest relevant set from the Learning
index, linked evidence, and selected review items. Report separately:

- what the vault directly supports about the person’s knowledge;
- the qualitative state and scope of that evidence;
- meaningful gaps, uncertainty, outdated or contradictory evidence; and
- any derived explanation, prerequisite recommendation, or next step.

To explain a subject using prior knowledge, start from active, appropriately
scoped user-stated or source-supported concepts. Use `status: review` pages as
questions or conditional foundations, not settled prerequisites. Do not claim
that an adjacent topic is known merely because it has been mentioned. If the
known context is insufficient, say what is missing and offer a generic bridge
without writing it into the vault automatically.

To answer how understanding changed, use dates attached to evidence and the
concept’s progression or correction sections. There is no separate timeline
system. A newer source is not automatically better; preserve real evolution and
scope differences.

## Core, other verticals, and persistence

Stable cross-domain learning preferences may eventually belong in `core/` only
when explicitly broad and deliberately promoted. A concept-level knowledge
state, gap, or misconception remains in `learning/`. Career owns professional
history and outcomes; Writing owns communication patterns; Learning may link
both as evidence without duplicating them. Media / Taste and Relationships are
future boundaries, not part of this implementation.

Ordinary answers, explanations, and prerequisite suggestions remain ephemeral.
A substantial reusable explanation or an explicitly retained recommendation may
be stored under `derived/` after the shared duplicate, ownership, contradiction,
and freshness checks. It remains `derived_synthesis`, never becomes a Learning
fact by itself, and does not verify an unconfirmed page.

## Example shapes

Good durable context describes the person and its evidence:

```markdown
## Knowledge state

- state: demonstrated
- scope: can explain lexical closures in JavaScript and use them in a small
  callback-based implementation

## Evidence

- 2026-03-02 — [user explanation](../sources/lexical-closures-explanation.md)
- 2026-03-05 — [exercise](../sources/closure-exercise.md)

## Boundary

The user has not established familiarity with the performance implications of
large closure graphs.
```

Bad durable context is source material without a claim about the person:

```markdown
Chapter 4 explains closures as functions that capture variables...
```

Keep that explanation in a retained source or leave it ephemeral. The Learning
page should say what the person can explain or do, what supports it, and where
the boundary remains.

After a Learning operation, report the pages and sources changed, the state or
scope updated, links added, unresolved review items, and whether `core/` and
`derived/` were intentionally left unchanged. For a no-op, say “No meaningful
Learning update” rather than manufacturing a topic or trait.

## Contract migrations

Version 1 has no prior migrations. If the repository later advertises a newer
version, an older applied Learning contract remains readable and reviewable;
read only the documented migrations before proposing an update. Future versions
must identify affected Learning evidence, safe structural changes, semantic
review requirements, and forbidden automatic changes. A contract update never
invents competence, promotes an inference, erases a prior model, or converts a
generated explanation into evidence.
