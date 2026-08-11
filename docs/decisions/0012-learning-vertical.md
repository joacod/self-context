# ADR 0012: Add an Evidence-Backed Learning Vertical

- **Status:** Accepted
- **Date:** 2026-08-11

## Context

SelfContext needs a durable way to answer questions about what a person
understands and how that understanding changes. Career can show that a person
used a technology in professional work, and Writing can show that a person
explained a subject, but neither vertical owns the resulting knowledge state.
A generic notes, resource, course, or book-summary system would preserve source
material without preserving the person’s understanding and would add noise to
the portable vault.

Learning also has a different epistemic risk from ordinary activity tracking.
A course completion, article, or casual technology mention does not prove
understanding. A project may demonstrate one scoped ability without proving
global proficiency. An agent can notice a gap or corrected misconception, but
that interpretation must not become a fact through repetition or generated
explanations.

## Decision

Add Learning as a first-class vertical that reuses the existing SelfContext
contract:

- durable context lives under an on-demand `learning/` area with an `index.md`;
- Learning pages use the existing Markdown, YAML frontmatter, provenance,
  freshness, review, verification, and relative-link rules;
- the durable subject is the person’s topic- or concept-level knowledge state,
  meaningful gaps, unresolved questions, misconceptions, corrections, mental
  models, prerequisites, and dated evidence of progression;
- qualitative states such as encountered, learning, partially understood,
  understood, demonstrated, uncertain, and outdated remain readable body
  content rather than a numeric score or confidence database;
- retained sources remain under shared `sources/`, unresolved interpretations
  remain reviewable under `review/observations/`, and reusable explanations or
  recommendations remain visibly derived under `derived/`;
- Learning evidence is compared with existing concepts before mutation. A
  repeated or unchanged source may result in “No meaningful Learning update”;
- resources, courses, books, articles, conversations, exercises, and projects
  are retained only when they provide useful provenance or evidence about the
  person. Consumption alone does not create a knowledge claim;
- Career owns professional roles, projects, and outcomes. Writing owns
  communication patterns and authored artifacts. Learning may link those pages
  as evidence but must not duplicate their records; and
- a replaceable Learning Advisor Pack supplies grounded retrieval, gap and
  progression reasoning, prerequisite-aware explanations, and conservative
  misconception handling. SelfContext remains responsible for storage and
  lifecycle.

Learning does not implement Relationships or Media / Taste, and it does not
introduce a universal knowledge graph, resource catalog, database, embeddings,
custom runtime, or separate schema.

## Evidence and lifecycle

A direct user statement about understanding, uncertainty, or a correction can be
stored as scoped user-stated context. A source can establish that an exercise or
project occurred, while the interpretation that it demonstrates a broader
concept may remain a reviewable agent inference. Repeated questions can expose a
meaningful gap but are not proof of inability. Dated evidence belongs on the
concept page; a generic timeline system is unnecessary.

When a mental model changes, Learning preserves the earlier model, the
correction, its evidence, and the remaining boundary. A newer source does not
automatically erase older context or become more authoritative merely because it
is newer. `verified` remains separate from qualitative evidence state and is
changed only through the shared confirmation rules.

## Consequences

- New vaults expose a Learning index while existing vaults remain compatible and
  add the area only for a requested Learning mutation.
- Generic SelfContext retrieval can find Learning pages, while the Advisor Pack
  can reason about them without owning a second memory format.
- Future explanations can start from supported prior knowledge and expose gaps
  instead of assuming a generic curriculum or competence level.
- Learning remains independently usable; it does not require Career or Writing
  pages to function.
- Semantic evidence thresholds remain agent judgment and human-review concerns;
  the deterministic linter continues to check only structural integrity.
- The vault stays small because incidental exposure, generated teaching, and
  duplicate cross-vertical records are not durable Learning context.

## Alternatives rejected

- A generic notes or resources directory was rejected because the durable asset
  should describe the person, not every source they encountered.
- Numeric proficiency or confidence scores were rejected because they create
  false precision and a second epistemic model.
- A universal prerequisite graph was rejected because personal relationships
  should remain few, useful, and evidence-backed.
- Automatic promotion from course completion, source count, project mention, or
  model confidence was rejected because it creates unsupported competence.
- Copying Career or Writing pages into Learning was rejected because each claim
  needs one clear owner and shared links are sufficient.
- Relationships and Media / Taste were intentionally deferred rather than
  represented through speculative shared abstractions.
