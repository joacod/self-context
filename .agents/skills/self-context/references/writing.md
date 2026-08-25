---
vertical_id: writing
contract_version: 1
vault_area: writing
advisor_skill: writing-advisor
---

# Writing Vertical

The Writing vertical records evidence-oriented patterns in how a person
communicates and develops ideas. It is not a personality profile, a collection
of generic writing advice, or a prompt that asks a model to imitate old prose.
Writing and brainstorming remain contextual workflows over the shared vault,
not separate product categories or storage owners.

SelfContext owns the source records, provenance, lifecycle, and durable Writing
context. A Writing Advisor may reason over that context, but it does not own a
second durable context store.

## Scope and Ownership

Use the current-schema activation rule in [Initialization](initialization.md);
this procedure does not redefine vertical enablement, contract markers, or
schema migration. A recognized older schema must be upgraded before Writing
activation or normal Writing operations.

Use the existing vault contract:

- `writing/` contains durable Writing concepts and the Writing index.
- `sources/` contains retained articles, notes, messages, drafts, and revision
  captures when preserving them makes provenance clear.
- `review/observations/` contains unresolved inferred patterns, contradictions,
  and other items needing human attention.
- `derived/` contains reusable analyses, drafts, critiques, and advice that are
  visibly derived rather than evidence of authentic writing.
- `core/` contains an explicitly cross-domain preference or communication
  pattern. A Writing observation does not belong in `core/` merely because it
  may matter in several situations.

Create only the directories that are useful. A new vault needs a
`writing/index.md`; it does not need a fixed tree of voice, modes, or style
files. Add a subdirectory only when a real collection of pages makes
navigation clearer.

Writing owns observable communication behavior, reasoning-through-writing,
reader-awareness, editorial preferences, anti-patterns supported by evidence,
and contextual writing modes. It does not own beliefs, opinions, career facts,
technical expertise, diagnoses, or unsupported psychological explanations.

## Evidence Roles

Classify the input before extracting a pattern.

| Input | Evidence role | Durable rule |
| --- | --- | --- |
| User-authored article, essay, note, email, message, documentation, or post | Primary evidence | Preserve a `source_record` when useful and link observations to it. |
| AI-assisted material with meaningful user edits | Strong secondary evidence | Preserve the original as generated or assisted material and analyze the human delta separately. |
| AI draft, summary, critique, rewrite, or style analysis | Derived artifact | It may inform the current task, but it is not independent evidence of the user's writing. |
| Explicit user preference or correction | User-stated evidence | Store the explicitly stated scope as `user_stated_fact`; do not generalize beyond it. |

When authorship or AI involvement is unknown, record the uncertainty and lower
the evidentiary weight. Do not silently treat a supplied document as authentic
user writing.

Source acquisition is separate from Writing modeling. If a user supplies a URL
or an existing source-capture mechanism already supports it, preserve the
resulting source through the normal source workflow. Do not add a scraper or
hardcode one person's public corpus into the generic implementation.

### Portable Artifact Roles

Every retained Writing source or generated Writing artifact must carry these
fields in its YAML frontmatter, in addition to the shared fields, and include a
short human-readable `## Authorship` section:

```yaml
writing_evidence_role: primary
authorship: user
ai_involvement: none
```

Use only these role combinations:

| `writing_evidence_role` | `authorship` | `ai_involvement` | Meaning |
| --- | --- | --- | --- |
| `primary` | `user` | `none` | Authored by the user without known generated text. |
| `human_edited_ai_assisted` | `shared` | `assisted` | AI assistance exists, but the user's meaningful edits are the evidence. |
| `generated_derived` | `agent` | `generated` | Draft, rewrite, summary, critique, or other generated artifact. |
| `unknown` | `unknown` | `unknown` | Authorship or AI involvement cannot be established. |

The deterministic linter validates these fields on `source` and `synthesis`
pages tagged `writing`. A `generated_derived` page may be retained for
traceability, but it must not appear in the `sources` metadata of a durable
Writing observation or be counted as independent evidence. A human-edited
revision may link to the generated original in its body under `Generated input
(not evidence)` while the observation links to the revision source itself.

A source record can use the shared frontmatter shape and explain its evidence
role in the body, for example:

```markdown
---
type: source
title: Synthetic technical essay
description: Fictional source record used to support a Writing observation.
tags:
  - writing
  - technical
status: active
generated: 2026-08-10
verified: null
sources: []
assertion_kind: source_record
stale_after: null
writing_evidence_role: primary
authorship: user
ai_involvement: none
---

## Authorship

- authorship: user
- ai_involvement: none
- writing_evidence_role: primary
- language: English
- mode: technical
- written_at: 2026-08-01

## Source

The retained text or a faithful capture belongs below this heading.
```

The example is fictional and describes a source record, not a Writing trait.

## Observation Shape

Writing observations use the shared durable-page metadata. Keep the richer
Writing detail in readable Markdown sections instead of adding a fixed taxonomy
or fake numerical precision to frontmatter.

An observation or concept can explain:

```markdown
## Observation

Observable pattern stated without a personality or belief claim.

## Evidence state

- state: candidate | emerging | established | explicit preference
- assertion: source-derived observation, agent inference, or user statement
- scope: global, technical, opinion, message, English, or another evidenced mode

## Evidence

- [Synthetic technical essay](../sources/synthetic-technical-essay.md),
  2026-08-01: concrete example precedes the abstraction.

## Timeline

- first observed: 2026-08-01
- last observed: 2026-08-01
- historical notes: none yet

## Contradictions and exceptions

None identified.

## Update history

- 2026-08-01: candidate created from one independent source.
```

The labels are guidance for human-readable observation bodies, not new required
schema fields. Keep `verified` separate from evidence state: an established
inference can remain unverified, while an explicit user preference can be
verified only through an explicit confirmation event under the normal lifecycle.

Use `type: observation`, `assertion_kind: agent_inference`, `status: review`,
and `verified: null` for a candidate inferred from writing. When the user
explicitly confirms a factual preference, promote only the confirmed scope to
`user_stated_fact` according to the shared confirmation procedure. A source
record or source-derived claim is not automatically confirmed.

## Analyze Before Updating

Every genuine writing source deserves local analysis. Analysis does not imply a
profile mutation.

1. **Identify the source.** Record source type, authorship, date, language, known
   AI involvement, likely mode, and any target reader or context.
2. **Analyze locally.** Extract observable candidate patterns from the document
   and, for assisted material, from meaningful human changes. Do not update the
   durable profile yet.
3. **Prepare and compare with context.** Choose an explicit Writing scope and
   useful anchors, use SelfContext's bounded read-only `prepare_context.py`
   packet, then read the returned Writing index and relevant full pages. The
   helper does not infer ownership or load unrelated verticals. Classify each
   candidate as known, redundant, reinforcing, genuinely new,
   contextual, contradictory, temporal, incidental, or too weak to retain.
4. **Assess impact.** Decide whether the new source changes SelfContext's
   understanding. Independent sources and distinct contexts matter more than
   repeated phrases inside one source.
5. **Update selectively.** Strengthen, refine, supersede, or add only the
   smallest justified set of durable pages. Preserve the source even when the
   durable profile does not change, when retaining it is useful or requested.
6. **Report the result.** Include the comparison counts and say explicitly when
   there was no meaningful update.

The impact report may use this shape:

```text
Writing analysis:

Source: synthetic technical article
Existing patterns reinforced: 3
New meaningful patterns: 0
Context-specific refinements: 0
Contradictions: 0
Potential profile updates: 0
Redundant observations ignored: 5

Result: No meaningful update. The source is consistent with the existing
technical-writing profile.
```

"No meaningful update" is a successful outcome. Do not invent a new trait,
rename a known trait, or churn confidence merely because an analysis ran.

## Evidence State and Confidence

Use qualitative evidence states rather than exact scores:

- **Candidate:** one weak, narrow, or ambiguous observation; normally reviewable
  and not a universal instruction.
- **Emerging:** repeated or diverse evidence supports a pattern, but important
  uncertainty or scope remains.
- **Established:** multiple independent, consistent sources support a scoped
  pattern and no material contradiction is unresolved.
- **Explicit preference:** the user directly stated or confirmed the preference;
  the user's scope takes precedence over weak behavioral inference.

When deciding whether evidence justifies a state change, consider source quality,
independence, diversity of contexts, consistency, dates, and meaningful human
edits. Repeated statements in one article are not independent evidence. Source
#31 does not need to change an already established state. Confidence must not
become a counter that grows with ingestion volume.

Do not use source count as automatic verification. Do not make a weak global
claim from one article, and do not delete a prior observation merely because a
new source differs.

## Modes, Readers, and Time

Keep shared patterns separate from mode-specific behavior. Create a mode only
when evidence makes it useful, such as technical article, opinion essay,
documentation, email, message, Spanish, or another observed context. Do not
create a page for every possible mode.

For each scoped pattern, preserve enough context to answer:

- what kind of writing or reader it concerns;
- what prior knowledge appears to be assumed;
- when terms or background are explained;
- how examples, objections, tradeoffs, and uncertainty are handled; and
- whether the pattern appears stable, recent, historical, or superseded.

If evidence shows a behavior changed over time, preserve both periods and link
the newer state to the earlier one. Newer evidence is not automatically better.
If the difference could be an exception or a mode change, keep the contradiction
reviewable until the context is clear.

## What to Model

Prefer behavioral descriptions such as:

- moves from a concrete observation to a broader conclusion in technical essays;
- introduces an implementation example before naming the abstraction;
- states tradeoffs and counterarguments instead of presenting absolutes;
- establishes reader relevance before detailed mechanics;
- uses short direct paragraphs in messages but more background in long-form work;
- removes generic intensifiers and abstract corporate phrasing during revision.

Reasoning patterns may describe how an argument is built, not what the person
believes. Reader patterns describe observable audience assumptions, not the
reader's identity. Editorial preferences and anti-patterns require explicit
statements or repeated evidence from the user's writing or revisions.

Do not infer intelligence, ideology, personality, mental health, demographic
identity, or private motivation. Do not convert a recurring topic into a belief
or place a substantive opinion in Writing merely because it appears in a source.

## Contradictions and Evolution

When new evidence conflicts with an observation:

1. Preserve both source records and their dates.
2. Check whether the difference is a mode, an exception, a real change over
   time, different authorship, or weak prior evidence.
3. Refine the scope when the evidence supports a contextual explanation.
4. Create or retain a `status: review` observation when the explanation is not
   resolved.
5. If explicit dated evidence shows evolution, preserve the historical state
   and mark it superseded or historical rather than erasing it.

Never let a single recent document overwrite a longer, differently scoped
history. Never average historical periods into an uninformative universal voice.

## Revisions as Evidence

When a user edits an AI draft, keep the generated original visibly generated and
analyze the human-authored delta separately. Meaningful deltas include deleted
generic phrases, shorter constructions, added context, changed examples,
reordered reasoning, altered openings or conclusions, and tone changes.

One edit is a candidate signal, not a permanent preference. Aggregate repeated
signals across independent revisions and compare them with authentic writing.
If the user explicitly says a preference is intentional or wants an earlier
observation replaced, treat that statement as stronger evidence within its
stated scope. Do not treat an untouched generated draft as evidence of the
user's voice.

## Cross-Vertical Retrieval

Writing work may retrieve relevant core, career, Ventures, Learning, project,
belief, or knowledge context. It should link to that context rather than copy
it into `writing/`. Ventures owns initiative lifecycle and project-specific
state; Career owns the professional view of participation.

- A career achievement remains in `career/`.
- A Learning knowledge state, gap, or prerequisite remains in `learning/`.
- A cross-domain preference explicitly stated by the user belongs in `core/`.
- A substantive belief or opinion belongs in the appropriate domain.
- A Writing page can explain how the user communicates an idea without asserting
  that the idea is true or that the user believes it.

Likewise, a Career, Ventures, or other Advisor Pack may use Writing context for
an artifact's communication fit, but Writing observations do not become career
or project evidence.

## Persistence and Safety

Writing source preservation, profile changes, managed index updates, and
operation logs are vault mutations. For an existing current vault, prepare the
semantic source/profile bytes and explicit activation decision, then invoke the
ordinary commit boundary. It stages the complete proposal, validates it, owns
the provisional/final backup lifecycle and rollback, and returns one receipt.
Read-only local analysis and a no-op comparison do not require a backup unless a
source or log is actually persisted. Missing or uninitialized bootstrap remains
with [Initialization](initialization.md), and schema migration remains a
separate high-level workflow.

Drafts, brainstorming, critiques, and reader analyses normally remain in the
response. A substantial reusable synthesis may be stored under `derived/` with
`assertion_kind: derived_synthesis`, links to its evidence, and clear labels. It
must never become a source for a new Writing trait.

The complete lifecycle is therefore:

```text
authentic source
  -> source record and local observations
  -> comparison with Writing context
  -> no-op or selective refinement
  -> new idea plus relevant cross-vertical context
  -> Advisor draft or reader critique
  -> human revision
  -> revision analysis as possible future evidence
```

The durable asset is the user's inspectable evidence and selectively refined
context, not any particular Skill, Advisor, model, or generated draft.

## Contract migrations

Version 1 has no prior migrations. When a future version changes Writing's
ownership or meaning, document the historical-upgrade question before
advertising it: where earlier evidence may be stranded in other areas, what
can be safely moved, split, or linked, and what remains ambiguous. `upgrade
vault latest` may apply only a complete documented safe path; it does not
replace this procedure or turn generated prose into evidence or resolve
ambiguous authorship.
 Older applied Writing contracts are migration sources, not permanent runtime
modes. Future versions must identify affected Writing evidence, safe structural
changes, semantic review requirements, and forbidden automatic changes. A
contract update never treats generated prose as primary evidence, changes
authorship, resolves a contradiction, or removes historical writing context
automatically.
