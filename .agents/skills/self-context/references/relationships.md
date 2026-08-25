---
vertical_id: relationships
contract_version: 1
vault_area: relationships
advisor_skill: relationships-advisor
---

# Relationships Vertical Procedure

The Relationships vertical preserves intentional continuity about the user's
relationships with other people. It is not a contact database, CRM, social
graph, surveillance system, or complete record of third parties. The durable
subject is the user's relationship and shared context, not an objective profile
of another person.

## Scope and ownership

Relationships owns:

- how the user knows a person or group and the relationship scope the user
  chooses to preserve;
- meaningful shared history, conversations, meetings, trips, collaborations,
  introductions, conflicts, and events;
- commitments made by the user or another person when they matter to future
  relationship continuity;
- unresolved threads, plans, recommendations, gifts, and other context useful
  before communicating again;
- explicitly evidenced shared interests and dated changes in the relationship;
  and
- the user's observations about the relationship, with their uncertainty
  visible.

Relationships does not own:

- every contact, email, message, social-media profile, or incidental mention;
- a sales pipeline, address book, ranking, social graph, task manager, or
  reminder system;
- unrelated facts about a third party that do not help explain the user's
  relationship with them;
- career roles, professional outcomes, mentoring evidence, or initiative
  lifecycle and project history when Career or Ventures owns those claims;
- the user's general values, boundaries, communication style, or social
  preferences when `core/` owns them; or
- inferred diagnoses, medical information, sexuality, religion, political
  beliefs, ethnicity, criminal history, financial condition, personality
  labels, motives, or psychological profiles about third parties.

A person may appear in Career, Ventures, Writing, Learning, or Media context
for a separate purpose. Link to the owning page rather than copying its facts
into a relationship page. Ventures may retain the collaborator's project role
when it is needed to understand an initiative; Relationships owns how the user
knows them and the shared human continuity that makes an interaction
meaningful.

## Storage and page choices

Use the current-schema activation rule in [Initialization](initialization.md);
this procedure does not redefine vertical enablement, contract markers, or
schema migration. A recognized older schema must be upgraded before
Relationships activation or normal Relationships operations.

- `relationships/index.md` is the navigation page for durable relationship
  context.
- A sparse person or relationship page normally lives directly under
  `relationships/`, with a stable filename such as
  `relationship-with-alice.md`. Use `people/`, `groups/`, or another
  subdirectory only when a real collection makes navigation clearer; these are
  organizational choices, not required schemas.
- Do not create an interaction page for every event. Preserve a compact source
  record under shared `sources/` only when the original recollection, message,
  or other evidence has future value. Often the durable result is a dated fact
  on the relationship page.
- Unresolved interpretations and contradictions belong under
  `review/observations/` with the shared observation metadata.
- Reusable conversation preparation or relationship summaries belong under
  `derived/` only when they earn persistence and remain visibly derived.

Relationship pages use the shared frontmatter fields. Do not add a required
relationship-specific frontmatter schema, strength score, contact identifier,
or claim database. Put the richer detail in readable Markdown sections, and
keep each page as small as future retrieval requires.

A useful page may include sections like these, without forcing every section on
every person. The title or an identity section can hold a canonical name and
user-supplied aliases when they help retrieval; do not turn aliases into a
contact directory.

```markdown
## Identity in relationship context

Canonical name and relevant aliases, only as supplied or intentionally retained.

## Relationship to me

How we know each other and the scope the user intentionally preserves.

## Shared context

Meaningful history, projects, places, interests, or experiences.

## Conversations and events

Only retained interactions with future contextual value.

## Commitments and open loops

Actual promises and unresolved relationship threads, not generic tasks.

## Evolution

Dated changes in how the relationship is described, with older context retained
when it explains the change.

## Evidence and boundaries

What the user said, what the person reportedly said, what a source documents,
and what remains unknown or inferred.
```

## Epistemic and provenance discipline

Classify each durable claim before storing it:

| What the evidence says | Durable treatment |
| --- | --- |
| The user directly says how they know someone or what they intend to remember | A scoped `user_stated_fact`, if it has future value. |
| A retained message, note, invitation, or other source documents an interaction or a reported statement | A linked `source_record` plus the smallest `source_derived_fact` that matters, when normalization is useful. |
| The user reports what another person said | Preserve the report as such in the body; do not rewrite it as independently verified fact about that person. |
| The agent interprets behavior, motives, reliability, closeness, or relationship direction | A reviewable `agent_inference` under `review/observations/`, never a settled judgment. |
| A conversation summary combines several pages for future preparation | A `derived_synthesis` under `derived/`, not relationship evidence. |

Use separate pages or clearly labeled body sections when claims have different
assertion kinds. Prefer a narrower page over `mixed`; if `mixed` is necessary,
state which sentences are user-stated, source-derived, reported, or inferred.
Keep links to the source record or owning vertical so another person can inspect
why the context exists.

Do not turn repeated behavior into a personality diagnosis. For example, retain
that two planned meetings were cancelled if that interaction is useful; do not
store that the person is unreliable unless the user explicitly states a scoped
judgment and genuinely needs it retained. Even then, prefer the observable
history and make the judgment reviewable rather than treating it as objective.

## Privacy, retention, and redaction

The user controls whether relationship context is retained at all. Before
keeping third-party information, ask whether it is useful for the user's future
relationship continuity and whether the least detailed version is sufficient.
Do not ingest a whole contact list, transcript, inbox, or social profile by
default.

Sensitive third-party characteristics must not be inferred from behavior,
conversation topics, media, appearance, or outside data. If the user explicitly
provides sensitive information and says it is genuinely necessary for a narrow
relationship purpose, preserve only the minimum scope, label its provenance,
and make it easy to review or remove. Do not turn an exceptional direct
statement into a general profile.

Honor an explicit request to delete, redact, archive, or stop retaining a
relationship fact. Do not resurrect removed context from an old source or
repeat sensitive details in `log.md`. A source record may also be deleted or
retained separately according to the user's instruction; normalized pages must
not silently preserve a claim the user asked to remove.

## Commitments and open loops

A commitment is more than a vague possibility. Record the actor, the action,
status, approximate date or context, and evidence when known. Examples include:

- `I told Martín I would send the repository.`
- `Sarah said she would introduce me to Alex.`
- `We agreed to revisit the trip plan after the conference.`

A conversation such as “we should see a concert sometime” is not an actual
commitment unless the user considers it a useful open loop. If retained, label
it as a tentative discussion and do not turn it into a due date or task. A
resolved or obsolete commitment should be marked in its relationship context
with the resolution and evidence; do not delete the history when the history
helps explain the relationship.

## Relationship evolution

Use dated prose or list entries on the relationship page to preserve meaningful
changes, for example `coworker -> former coworker -> friend` when those words
are explicitly supported. Preserve the reason and scope of the change. Do not
invent a closeness scale, compute a relationship score, or infer evolution from
message frequency alone. A conflicting description remains reviewable until
scope, time, exception, or explicit user correction explains it.

## Relationships ingest and update

After deciding Relationships is relevant, choose an explicit Relationships
scope and useful anchors, then use SelfContext's bounded read-only
`prepare_context.py` packet for compatibility, selected navigation, recent
continuity, and ranked candidate metadata. Read only the returned full
relationship pages and linked evidence before a mutation; the helper does not
infer ownership or load unrelated verticals.

1. Identify the person or group and the user's relationship purpose. Do not
   create a page for a stranger or incidental mention without a continuity
   signal.
2. Separate the user's statement, a reported statement, a retained source, an
   observable interaction, and any agent interpretation.
3. Find the existing relationship page and linked Career, Ventures, Writing,
   Learning, or Media pages before creating anything. Update the smallest matching page
   rather than creating a duplicate person record.
4. Retain only high-signal interactions. Prefer a durable relationship fact,
   commitment, or open-loop entry over a transcript or complete event log.
5. Distinguish an actual promise from a vague plan. Mark unresolved,
   completed, declined, or obsolete threads in readable body text rather than
   creating a task-management system.
6. Preserve contradictions, dated changes, and source provenance. An agent
   observation about motives, relationship strength, or a third-party trait
   remains under review with `verified: null`.
7. Update `relationships/index.md`, relevant review navigation, and `log.md`
   when a durable page or review item changes. Leave `core/` unchanged unless
   the user explicitly supplied a genuinely cross-domain personal value,
   boundary, or preference owned there.
8. For an existing current vault, prepare the semantic relationship/source
   bytes and explicit activation decision, then invoke the ordinary commit
   boundary. It stages navigation and the operation log, validates, owns
   backups and rollback, and returns one receipt. Missing or uninitialized
   bootstrap remains separate. A supplied message or source does not verify a
   relationship claim by itself.

A meaningful operation may result in **No meaningful Relationships update** when
the interaction is incidental, already represented, too private to retain, or
lacks future contextual value. That is a successful conservative outcome.

## Relationships queries

For “who is this person?” answer only how the user knows them and the relevant
shared context. For “before I meet them,” retrieve the smallest set of shared
history, current threads, commitments, and freshness/review notes needed for
the interaction. Treat review pages and stale claims as provisional. Do not
produce an unrelated dossier about the person.

For a message-drafting request, Relationships supplies interpersonal context;
Writing owns the draft, reader analysis, and communication behavior. A query
or preparation summary remains ephemeral unless the user asks to retain it or
it has clear future continuity value. Any persisted summary is a linked
`derived_synthesis` and cannot update the relationship facts automatically.

## Example boundaries

Good durable context:

> 2026-08-11 — Alice told the user she plans to move to Barcelona in
> September 2026. This is a reported statement from the user's recollection;
> the move has not been independently confirmed.

> The user and Alice worked together on the Atlas migration and still exchange
> recommendations about science-fiction films.

Not durable by default:

> Alice cancelled twice, therefore Alice is unreliable.

> Alice's public profile suggests a diagnosis or political belief.

> Every message exchanged with Alice, copied wholesale into the vault.

After a Relationships operation, report the pages or sources changed, the
relationship-specific evidence and links retained, commitments or review items
left unresolved, any redaction decision, and whether `core/` and `derived/`
were intentionally unchanged.

## Contract migrations

Version 1 has no prior migrations. When a future version changes Relationships'
ownership or meaning, document the historical-upgrade question before
advertising it: where earlier evidence may be stranded in other areas, what
can be safely moved, split, or linked, and what remains ambiguous. `upgrade
vault latest` may apply only a complete documented safe path; it does not
replace this procedure or infer motives, sensitive third-party details, or
ambiguous relationship meaning.
 Older applied Relationships contracts are migration sources, not permanent
runtime modes. Future versions must identify affected relationship evidence,
safe structural changes, semantic review requirements, and forbidden automatic
changes. A contract update never infers a sensitive third-party detail, decides
a motive or relationship judgment, resurrects redacted context, or deletes
historical evidence automatically.
