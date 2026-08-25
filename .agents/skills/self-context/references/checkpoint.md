# Checkpoint Workflow

Checkpoint is an explicit, natural-language request to inspect the current
conversation and decide whether anything in it should become durable
SelfContext context. It reuses the existing Ingest, Query persistence, review,
provenance, ownership, and backup semantics. It is not a conversation summary,
a transcript export, a chat-history database, or a new storage lifecycle.

A conversation is ephemeral by default. A successful checkpoint may retain
nothing.

## When to use it

Use this procedure when the user says things such as:

- “checkpoint this discussion” or “checkpoint this conversation”;
- “save anything from this that is actually worth keeping”;
- “what from this conversation should become context?”;
- “update my context with the decisions we actually made”;
- “preserve the useful outcome of this discussion”; or
- “preview/dry-run this checkpoint” or “show what would be retained without applying it.”

Do not require a slash command. Treat the natural-language intention as the
interface. If the user only asks for a recap or summary, use the ordinary
response mode unless they also ask to preserve durable context.

## Boundary and ownership

Checkpoint owns candidate triage, not a second ingest or persistence system.
After triage, route each legitimate candidate through the existing operation
that owns it:

| Candidate | Existing owner |
| --- | --- |
| New fact, correction, explicit goal, preference, or decision | [Ingest](ingest.md) and the existing canonical concept |
| Career evidence or professional context | Career procedure and `career/` |
| Knowledge state, gap, correction, or progression | Learning procedure and `learning/` |
| Authored writing or communication evidence | Writing procedure and `writing/` |
| Shared history, relationship commitment, or open loop | Relationships procedure and `relationships/` |
| Media reaction or taste evidence | Media / Taste procedure and `media/` |
| Initiative lifecycle, project decision, milestone, or outcome | Ventures / Projects procedure and `ventures/` |
| Cross-domain goal, value, preference, or recurring constraint | `core/` |
| Reusable derived conclusion explicitly worth retaining | [Query persistence](query.md#persistence-decision) and `derived/` |
| Unresolved inference or contradiction | Existing review semantics and `review/observations/` when retention is justified |
| No durable candidate | No mutation |

Use the existing vertical procedures and the current schema's ownership rules.
Do not create a “conversation” page, a generic notes area, a new vertical, or a
parallel checkpoint archive. A project decision belongs to its existing
Ventures record, a relationship fact belongs to its relationship record, and a
cross-domain preference belongs in `core/`; importance does not move a claim
into a different owner.

### Dry-run and preview behavior

A checkpoint dry-run is a read-only candidate assessment. It may classify a
candidate and identify the canonical owner and existing page that would be
updated, but it must not call ingest or query persistence, append an operational
log entry, create a backup, update an index, change metadata, or create a
checkpoint artifact. Use it when the user asks for a preview or when an
operational evaluation must prove ephemerality.

Keep the outcome distinct from a normal no-op:

- **Nothing durable identified:** no candidate met the persistence threshold.
- **Durable candidate identified; not applied:** a candidate met the threshold,
  but the dry-run or explicit safety boundary prevented the write.
- **Durable change applied:** the owning operation completed its normal write,
  validation, and backup lifecycle.

## 1. Inspect the conversation, not just its ending

For ordinary checkpoint orientation, choose the smallest explicit scope and
useful anchors, then call the bounded read-only `prepare_context.py` packet.
Inspect its returned runtime state as the latest-first compatibility gate: if it
is current, continue from the packet; if it is old, future, malformed, or
otherwise incompatible, stop the ordinary checkpoint path and follow the same
upgrade or recovery boundary as the operation it would invoke. Do not perform a
separate schema/runtime compatibility or orientation read first. The packet
supplies selected navigation, bounded continuity, and candidate metadata
without inferring ownership or writing state. Read only the relevant full pages
before planning any mutation.

Then inspect the current conversation and make a transient candidate list. Do
not copy the conversation into a file, log, source record, task packet, or
report merely to perform the checkpoint. Read user messages, supplied source
material, and relevant retrieved evidence as evidence; inspect assistant
messages and generated alternatives only to determine what must *not* be
promoted.

The candidate list is working state, not durable context. For each possible
outcome, classify it as one of:

1. newly stated factual context;
2. correction to existing factual context;
3. explicit decision made by the user;
4. goal or constraint change;
5. explicit preference change;
6. project or venture state change;
7. reusable derived conclusion;
8. unresolved question or observation worth revisiting;
9. agent inference requiring confirmation; or
10. ephemeral discussion with no durable value.

A candidate can be rejected as non-durable even when it fits one of the first
nine labels. The labels organize inspection; they do not lower the evidence or
persistence threshold.

## 2. Evaluate every candidate

For every candidate, answer these questions before choosing an action:

- **Evidence:** Is it supported by a direct user statement, a valid supplied
  or retrieved source, or explicit confirmation? What is the provenance?
- **Generation boundary:** Is it only an assistant suggestion, brainstorm,
  recommendation, summary, or inference? Generated assistant content is not
  evidence about the user.
- **Reuse:** Is there likely future value, an explicit request to retain it, a
  meaningful review value, or a costly reconstruction? If not, prefer no
  storage.
- **Home:** Does an existing canonical concept, vertical page, source record,
  review item, or derived synthesis already own it?
- **Conflict:** Does it contradict, narrow, supersede, or merely repeat active,
  stale, provisional, or historical context? Preserve competing evidence and
  use the existing contradiction rules.
- **Confirmation:** Does the item need a bounded user confirmation because it
  is high-impact, ambiguous, contradictory, or inferred? Checkpoint itself is
  not confirmation.
- **Representation:** Is the candidate already represented? Unchanged context
  should not cause duplicate pages, provenance churn, verification changes, or
  freshness renewal.
- **Maintenance cost:** Would storing it create a page, review burden, or
  future synchronization cost without meaningful benefit? If so, leave it
  ephemeral and say that it was intentionally not stored.

Use this evaluation to choose one of the existing outcomes: route it to
normal ingest, route it to the existing query persistence check, retain a
reviewable item when justified, ask one batched confirmation question, or do
nothing.

## Evidence boundaries

Apply these rules before persistence:

- An assistant-generated suggestion is not a user preference, goal, decision,
  fact, or source merely because the user discussed it.
- Brainstormed alternatives are generated possibilities, not evidence of what
  the user wants. A rejected option is not a user fact. Retain the rejection
  only when the user explicitly made the rejection a durable decision or
  constraint worth future use.
- An assistant recommendation remains derived. It cannot silently become a
  goal, project state, preference, or factual claim.
- An agent inference may be retained only as the existing reviewable
  `agent_inference`/`status: review` form when it has genuine future review
  value. It remains unresolved with `verified: null` until the user confirms,
  revises, rejects, or defers it. Do not store an inference merely to make the
  checkpoint look productive.
- A direct user statement can be durable without automatic verification. Apply
  the normal selective confirmation and freshness policies rather than treating
  the checkpoint request as blanket confirmation.
- A correction updates the smallest existing coherent concept through normal
  ingest. Preserve the old source or historical evidence where it explains the
  change; do not silently erase a contradiction.
- A useful synthesis may be retained only when it passes the existing query
  persistence checks. It must remain a linked `derived_synthesis`, not evidence
  for a new fact, goal, preference, or decision.

## 3. Route and persist the smallest result

After candidate evaluation, group only compatible updates and use their normal
procedures:

1. **Facts, corrections, explicit decisions, goals, preferences, and project
   changes:** route through [Ingest](ingest.md), including orientation,
   provenance, duplicate detection, ownership, conflict handling, confirmation,
   freshness, linking, indexes, logging, validation, and persistence.
2. **Reusable derived outcomes:** route through the existing Query persistence
   decision. Search for an existing synthesis first, preserve evidence links,
   record uncertainty and freshness limits, and create or update the smallest
   `derived/` page only when justified.
3. **Inferences and unresolved contradictions:** use the existing review
   semantics. Preserve the evidence, keep the item provisional, and ask at
   most one concise batched confirmation question when the normal policy calls
   for it. Never resolve a contradiction from assistant confidence.
4. **Ephemeral or already represented material:** make no durable change. Do
   not append a transcript, create a checkpoint page, or mutate a catalog just
   to record that the conversation was inspected.

When a routed result mutates an existing current vault, let the owning ingest
or persistence procedure prepare the semantic proposal and invoke the ordinary
commit boundary. The helper stages the page/source/control candidates, managed
indexes, and operation log; validates them together; owns the provisional/final
backup lifecycle, rollback, and guarded cleanup; and returns one receipt. A
checkpoint must not create a second backup or bypass provenance,
contradiction handling, confirmation, or semantic ownership. A dry-run never
starts that lifecycle. If no candidate is durable, there is no active write and
no backup or log mutation solely for checkpoint. A missing or uninitialized
vault remains with the existing initialization procedure rather than the
ordinary commit helper.

A checkpoint can produce more than one normal update when the conversation
contains distinct, supported changes, but prefer the smallest coherent set and
avoid cross-vertical duplication. Never store the entire conversation to
preserve the outcome. Keep source records to the smallest original material
needed for provenance, not a transcript dump.

## 4. Report the checkpoint

Finish with a concise report that separates durable results from discussion:

```text
Checkpoint result
- Mode: <applied | dry-run>
- Outcome: <nothing durable identified | durable candidate identified; not applied | durable change applied>
- Candidate: <durable candidate, or “none”>
  - classification: <fact, decision, correction, synthesis, inference, or ephemeral>
  - owner: <canonical owner>
  - existing page: <page that would be updated/created, or “none”>
  - confirmation: <required question, or “none”>
  - persistence: <applied | not applied | not durable>
- Locations: <canonical pages/areas, or “none”>
- Updated: <existing pages, provenance, review state, indexes, or “none”>
- Unresolved: <conflicts, inferences, unknowns, or “none”>
- Not stored: <suggestions, rejected options, ephemeral reasoning, transcript, or other intentional exclusions>
```

If a normal ingest or persisted synthesis ran, include its ordinary backup and
validation result without expanding the report into a transcript. Say when a
candidate was already represented and therefore caused no update. Distinguish
“nothing durable was found” from “a durable change is waiting for
confirmation”; both are successful checkpoint outcomes, but only the latter
has pending work.

## Compact examples

- **Decision:** John Doe explicitly decides to keep the Harbor CLI in
  maintenance mode until repeat use is demonstrated. Update the existing
  Ventures record through normal ingest; do not create a conversation page.
- **Correction:** John Doe corrects the current role recorded on an existing
  Career page. Update the coherent claim, preserve source history, and apply
  the normal conflict and confirmation rules.
- **Generated suggestion:** The assistant suggests that John Doe prefers
  morning work, but John never says this. Do not store it as a preference.
- **Rejected brainstorm:** The assistant proposes enterprise expansion and
  John rejects it during exploration without making a durable project decision.
  Do not store the option as a fact or preference. If John explicitly decides
  not to pursue enterprise expansion, route that decision to Ventures instead.
- **Derived outcome:** John Doe explicitly asks to reuse a supported comparison
  of Harbor CLI options. Retain the smallest linked derived synthesis, keep the
  recommendation visibly derived, and do not rewrite his goals or project
  facts.
- **Nothing durable:** A hypothetical discussion changes no user-stated fact,
  decision, goal, preference, project state, or reusable conclusion. Report a
  successful no-op and leave the vault byte-for-byte unchanged.
