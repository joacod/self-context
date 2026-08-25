---
vertical_id: ventures
contract_version: 1
vault_area: ventures
advisor_skill: ventures-advisor
---

# Ventures / Projects Vertical Procedure

## Scope and ownership

Ventures / Projects owns the living lifecycle of meaningful initiatives the
user is considering, pursuing, operating, collaborating on, testing, or
concluding. This includes independent software projects, experiments,
prototypes, products or possible products, partnerships, external proposals,
client or studio opportunities, business exploration, meaningful roadmaps and
milestones, project decisions and trade-offs, commitments and open loops,
dogfooding, adoption evidence, outcomes, changing scope, collaborators,
organizations, assumptions, unknowns, pauses, abandonment, completion, and
supersession.

It is not a generic task manager, todo system, CRM, contact database, Jira or
project-management replacement, product-management system, repository or
source-code catalog, startup database, sales pipeline, course tracker,
generic knowledge base, automatic business-intelligence system, or autonomous
business strategist. Keep credentials, tokens, secrets, API keys,
authentication data, wholesale Slack/Notion/email/message histories, and
unnecessary third-party personal information out of the vault. Retain useful
source material through the shared provenance model instead of archiving whole
workspaces.

Use aspect ownership rather than copying the same claim into several areas:

| Owner | Durable authority |
| --- | --- |
| Ventures / Projects | What the initiative is, why it exists, how it originated, its lifecycle, current state, the user's project role and evidenced authority, project collaborators and organizations as context, decisions, trade-offs, commitments, milestones, evidence, outcomes, dogfooding, adoption, commercial exploration, unknowns, assumptions, and evolution. |
| Career | What participation demonstrates professionally: achievements, scope, impact, leadership or technical evidence, career stories, positioning, and professional goals. The initiative lifecycle remains in Ventures. |
| Learning | What the user understands, knowledge-state evidence, corrections, gaps, mental models, and progression. A project can be evidence, but activity or completion does not prove understanding. |
| Relationships | How the user knows a collaborator, their relationship, shared history, and relationship-level commitments or open loops beyond the initiative record. Ventures links rather than creates a CRM dossier. |
| Writing | Evidence-backed communication behavior and writing context. A proposal or announcement may be a project context, but generated project messaging is not automatically Ventures or Writing evidence. |
| Core | Cross-domain values, preferences, recurring constraints, and broad decision or communication patterns. A preference does not move into Ventures merely because it influenced one initiative. |
| Sources | Retained source and provenance material. |
| Review | Unresolved inferences, contradictions, ambiguous high-impact claims, and items needing human attention. |
| Derived | Reusable comparisons, prioritization analyses, recommendations, and decision syntheses. Derived advice is not a project fact, goal, commitment, or preference. |

Link to the owning page when another vertical is relevant. Do not duplicate a
complete Career history, Learning state, relationship dossier, writing profile,
source record, or recommendation into a venture page.

## Contract and durable record

Ventures uses the shared Markdown, YAML frontmatter, provenance, verification,
freshness, review, and standard relative-link contract. A recognized older
schema must be upgraded before Ventures activation or normal Ventures
operations. Durable pages retain the common fields `type`, `title`,
`description`, `tags`, `status`, `generated`, `verified`, `sources`,
`assertion_kind`, and `stale_after`. Do not add required Ventures-specific
frontmatter or a database. In particular, do not overload shared page `status`
with initiative lifecycle state.

The initiative lifecycle is readable body content, normally using the smallest
useful vocabulary: candidate, proposed, active, paused, completed,
abandoned/declined, or superseded. A page may state a different lifecycle when
the user's evidence needs it; automation must not depend on parsing a rigid
project-management state machine. Keep page lifecycle (`active`, `review`,
`archived`, and so on), initiative lifecycle, and assertion kind separate.

The primary durable unit is a flexible venture/project record. Start with only
`ventures/index.md`; do not create `projects/`, `opportunities/`,
`collaborations/`, or `products/` taxonomies unless a real collection later
benefits from one. A record may use these body sections when useful, without
creating empty headings on every page:

```markdown
## Purpose
## Origin
## Initiative lifecycle
## Current state
## User role and authority
## Collaborators and organizations
## Decisions and trade-offs
## Commitments and open loops
## Evidence and outcomes
## Dogfooding or adoption
## Related learning
## Career relevance
## Unknowns and boundaries
## Evolution
```

An index is navigation, not evidence. Use the normal managed catalog and update
it only through the shared authorized mutation workflow.

## Evidence and epistemic safeguards

Classify each claim before storing it. A user statement or explicit confirmation
can be `user_stated_fact`; a retained proposal, note, or source can support a
`source_record` and a linked `source_derived_fact`; an interpretation belongs as
a reviewable `agent_inference`; and a comparison or recommendation is a linked
`derived_synthesis`. A source does not verify a claim merely because it exists.

Keep these distinctions explicit in the record body when they matter:

- an idea is not an adopted project;
- a candidate is not an active initiative;
- an opportunity is not an engagement;
- a proposal is not a commitment;
- a discussion is not an agreement;
- organizational access is not employment;
- a public role label is not contractual authority;
- a collaborator is not automatically a partner;
- a contribution is not ownership;
- a prototype is not a shipped product;
- project activity is not repository activity;
- personal dogfooding is not external adoption;
- one person's feedback is not validated demand;
- interest is not purchase intent;
- a stated outcome is not a measured outcome;
- course or resource exposure is not demonstrated knowledge;
- a recommendation is not a decision; and
- a decision is not an executed commitment.

When evidence is absent, write **unknown** or leave the claim unresolved rather
than selecting the most plausible interpretation. Never infer business
viability, product-market fit, partner status, employment, compensation,
equity, ownership, authority, contractual obligations, revenue, adoption, user
demand, project success, collaborator intent, collaborator reliability, or
future commitment. Do not derive sensitive characteristics about collaborators
or organizations. Preserve contradictory accounts, failed experiments, poor
outcomes, abandoned initiatives, and superseded approaches as history.

## Freshness and current state

Use the shared freshness mechanism. Keep `stale_after: null` by default. A
narrow current-state claim may receive a freshness deadline when being outdated
could materially change future reasoning, such as whether an opportunity is
open, the actionable current project state, an active external commitment,
current collaborator involvement, decision-relevant adoption, a time-sensitive
commercial proposal, or an assumption explicitly dependent on current
circumstances. Historical state, completed work, pauses, abandonment, and
less volatile decisions should not receive artificial expiration.

A stale claim needs freshness confirmation; it is not automatically false.
Queries should label stale or dynamically untracked current state and ask one
bounded question when it is decisive. Do not rewrite history to match the
current plan or renew freshness merely because a page was read.

## Ingest and update

Route meaningful initiative context from natural language, even when the user
does not name Ventures. Examples include: “I am building X”; “we decided to
pause X because ...”; “MyContext Systems proposed collaborating on ...”; “I
rejected this project because ...”; “I am dogfooding X”; “three people are now
actually using it”; “we changed the scope”; “I may turn this experiment into
...”; and “I committed to sending them a prototype.” Apply the normal durability
threshold: do not create a page for every passing idea, coding task,
repository mention, meeting, vague maybe, or company/person name.

1. After deciding Ventures / Projects is the likely owner, choose an explicit
   Ventures scope and useful anchors, then use SelfContext's bounded read-only
   `prepare_context.py` packet for compatibility, selected navigation, recent
   continuity, and ranked candidate metadata. Read the returned full initiative
   pages and linked evidence before creating another record, including aliases
   and prior lifecycle states; the helper does not infer ownership or load
   unrelated verticals.
2. Separate what the user said, what a source records, what another person
   proposed or reported, what was observed, what is inferred, and what remains
   unknown. Preserve useful provenance.
3. Update the smallest coherent venture record. Represent a new milestone,
   decision, outcome, scope change, pause, abandonment, completion, or
   supersession as dated evolution rather than destructive rewriting.
4. Link Career, Learning, Relationships, Writing, Core, and Sources only when
   their owned evidence helps explain the initiative. Route new facts to their
   real owner instead of copying them into Ventures.
5. For a meaningful mutation in an existing current vault, prepare the
   semantic initiative bytes and explicitly request `ventures` activation when
   first use requires it, then invoke the ordinary commit boundary. It stages
   exactly the requested control companions, managed catalog, and log, validates
   them together, owns backups/rollback, and returns one receipt. A schema 0.2
   first use records exactly `ventures@1`, creates only the area and index, and
   adds the root link. Missing or uninitialized bootstrap remains with
   [Initialization](initialization.md); a schema 0.1 vault upgrades first and
   receives no legacy Ventures activation. Read-only work never creates or
   enables Ventures.

## Query and cross-vertical routing

Targeted retrieval starts with the Ventures index and relevant records, then
checks provenance, status, assertion kind, freshness, review state, and history.
Combine verticals when the question needs them, but preserve ownership:

| Question | Primary route |
| --- | --- |
| What projects or initiatives are active? | Ventures |
| What opportunities am I considering? | Ventures |
| Where did initiative X leave off? | Ventures |
| What did we decide about X? | Ventures for an initiative-specific decision |
| What commitments are open for X? | Ventures |
| What evidence supports adoption or an outcome? | Ventures plus Sources as needed |
| What did X demonstrate professionally? | Career |
| What did I learn while building X? | Learning |
| How do I know collaborator X? | Relationships |
| What projects do I generally prefer? | Core when it is a durable cross-domain preference |
| How should I prioritize X versus Y? | Ventures/Core and other relevant evidence, then Derived or an Advisor |
| What should I publicly say about X? | Ventures evidence plus Writing and/or Career reasoning |
| What source supports this claim? | Sources and provenance |

A read-only question about an absent available vertical in a current vault
treats it as empty. It does not create `ventures/`, an index, a marker, a
placeholder page, or a backup. A query against schema 0.1 first reports the
upgrade requirement rather than altering or semantically operating on that
legacy state. Query-derived advice remains
`derived_synthesis` only when the shared persistence rules and explicit user
intent justify retention; it never silently becomes a fact or commitment.

## Advisor boundary and privacy

`ventures-advisor` performs reasoning after SelfContext retrieval. It may
compare opportunities, examine trade-offs, interpret dogfooding or adoption
evidence, surface unknowns, maintain continuity around a collaboration, and
recommend next steps. It must not claim viability or demand without evidence,
assume proposals became engagements, infer partner status, ownership, equity,
authority, deadlines, motives, reliability, or future commitments, or persist
its own recommendation as factual Ventures evidence. A recommendation remains
ephemeral unless the user explicitly asks to retain a linked derived synthesis
under the shared persistence rules.

Reject credentials, tokens, secrets, API keys, authentication material,
complete private workspace dumps, wholesale communication histories, and
unnecessary third-party information as Ventures context. Keep the project record
about the user's initiative and minimum necessary collaborator context, not a
surveillance archive or autonomous business system.

## Career compatibility

Career contract `career@1` remains semantically valid. Its project language is
read as the professional view of participation: what the work demonstrates,
its impact, scope, leadership, technical evidence, stories, and relevance to
professional goals. Ventures owns the initiative lifecycle itself. This is a
boundary clarification and cross-linking rule, not a material removal from
Career's v1 contract, so Career is not bumped to v2. Existing Career project
pages remain readable and in place; no page is moved or rewritten automatically.
An ambiguous page remains a review decision.

## Contract migrations

Version 1 has no prior Ventures contract migration. When a future version
changes Ventures' ownership or meaning, document the historical-upgrade
question before advertising it: where earlier project lifecycle evidence may be
stranded in Career or another area, what can be safely moved, split, or linked,
and what remains ambiguous. `upgrade vault latest` may apply only a complete
documented safe path; it does not replace this procedure, move ambiguous Career
pages, or invent initiative outcomes, authority, adoption, or commitments.
 An older applied Ventures contract is a migration source, not a permanent
runtime mode. A future contract must identify affected evidence, safe structural
changes, semantic review requirements, and forbidden automatic changes. It must
not move Career pages, split ambiguous ownership, invent outcomes, promote
recommendations, change verification, or migrate a user's private vault merely
because Ventures became available.
