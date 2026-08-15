# SelfContext Roadmap

This roadmap describes intended experiments, not promises. A change is ready
when its behavior is validated and documented; Git records the change history.

## Current Foundation

The current system provides:

- a portable Markdown vault with YAML frontmatter and standard links;
- schema 0.1 compatibility plus an explicit schema 0.2 maintenance path with selective vertical contracts;
- deterministic ordinary/deep lint, managed index catalogs, and disposable local lexical search;
- first-run initialization and orientation of existing vaults;
- natural-language ingest, query, review, and lint workflows;
- shared provenance, lifecycle, freshness, review, and epistemic boundaries;
- local provisional/final ZIP backups with retention of the latest ten archives;
- Obsidian compatibility and multi-session continuity; and
- separate Career, Learning, Writing, Relationships, Media / Taste, and
  Ventures / Projects verticals with replaceable Advisor Packs.

The verticals add no competing memory format, custom runtime, universal
confidence taxonomy, numeric profile model, or automatic promotion of generated
output into facts. Learning treats sources as evidence about the person's
knowledge; Relationships treats third-party information as bounded relationship
context; and Media / Taste treats consumption as evidence only when it helps
explain the user's reaction.

## Current Vertical Work

Each vertical has its own scope and experiment surface while reusing the shared
SelfContext lifecycle:

| Vertical | Current behavior | Next useful experiment |
| --- | --- | --- |
| Career | Evidence-backed roles, projects, skills, goals, and professional reasoning | Dogfood the workflows with real career information while keeping the vault local |
| Learning | Evidence-backed knowledge states, gaps, corrections, prerequisites, and progression using shared Markdown lifecycle | Exercise synthetic and real workflows for demonstrated, partial, corrected, and unchanged knowledge without profile bloat |
| Writing | Evidence-aware source comparison, selective profile updates, and writing reasoning | Use different authored modes and check whether the profile becomes more accurate without merely becoming larger |
| Relationships | Sparse user-centered relationship pages, meaningful shared history, commitments, open loops, privacy-aware provenance, and dated evolution | Exercise retention, redaction, reported statements, stale commitments, and pre-interaction retrieval with synthetic data |
| Media / Taste | Individual work reactions, conservative taste patterns, exceptions, cross-media evidence, and dated evolution | Exercise recommendation explanations, abandoned or revisited works, contradictory reactions, and no-update outcomes |
| Ventures / Projects | Initiative records for project and opportunity lifecycle, decisions, commitments, milestones, evidence, outcomes, dogfooding, adoption, and evolution | Exercise selective activation, stale opportunity state, proposal versus commitment, adoption evidence, abandoned history, and cross-vertical ownership |

## Shared constraints for implemented verticals

Every vertical must satisfy the same boundaries:

- **Distinct ownership:** a vertical owns one kind of evidence and reasoning
  workflow. Generic preferences, values, personality, goals, communication
  style, decision style, habits, and other cross-domain personal facts remain
  in `core/` unless a narrower domain scope is explicit.
- **Shared contract:** use the existing Markdown, YAML frontmatter, standard
  relative-link, provenance, freshness, review, and lifecycle conventions. Do
  not introduce a parallel epistemic model, confidence database, taxonomy, or
  storage format.
- **Epistemic discipline:** keep user-stated or user-confirmed facts,
  source-derived facts, agent inferences, and derived syntheses visibly
  distinct. Sources are evidence; durable context is what those sources reveal.
  Inferences remain reviewable, and derived analyses or advice do not silently
  become facts.
- **Independent usefulness:** no vertical may require another vertical to
  function. Cross-vertical use is an optional retrieval relationship through
  SelfContext, not a runtime or schema dependency.
- **Core boundary:** `core/` may later derive stable cross-domain patterns from
  vertical evidence, but vertical facts should not be copied into `core/` just
  to make retrieval easier.
- **Time and episodes:** time belongs in evidence and metadata rather than a
  generic timeline vertical. Domain-specific pages may preserve dated change
  where it explains continuity. The pattern `context -> alternatives ->
  decision -> reasoning -> outcome -> reflection` may be recorded where useful;
  Decision/Episodes should not become a fourth vertical.
- **Implementation restraint:** add a separate area and index, procedure, or
  Advisor Pack only when the workflow needs it. Do not add infrastructure or
  fixed directories merely to make an empty vault look complete.
- **Privacy:** operational fixtures, docs, tests, and evaluations use fictional
  or abstract data only. Personal vault content remains ignored and local.

## Relationships

**Purpose:** Who matters to the user and the shared context between them.

**Owns:**

- how the user knows a person or group, within the scope the user chooses to
  preserve;
- shared history, meaningful conversations, interactions, important events,
  commitments, and unresolved threads;
- shared interests and plans when they are evidenced rather than assumed; and
- dated changes in the relationship and the user's explicitly recorded
  observations.

**Does not own:**

- a contacts database, CRM, address book, ranking, social graph, or task
  system;
- every email, chat, calendar event, social profile, or incidental mention;
- unrelated facts about third parties that do not help explain the user's
  relationship with them;
- professional achievements, career relevance, or mentoring evidence owned by
  Career; or
- initiative lifecycle, project decisions, or project-specific commitments
  owned by Ventures / Projects; or
- inferred medical, mental-health, sexual, religious, political, ethnic,
  criminal, financial, personality, motivational, or psychological attributes
  about third parties.

The vertical stores sparse pages under `relationships/` and uses shared
frontmatter. A page may describe the relationship to the user, shared context,
meaningful interactions, commitments and open loops, evidence boundaries, and
dated evolution. It does not require a fixed person schema or relationship
strength score. A raw interaction is retained only when it has future value; a
compact fact is preferred to a transcript. The user's direct statement, a
reported statement, a source, and an agent inference remain distinguishable.

Relationships can link Career, Ventures / Projects, Writing, Learning, and
Media / Taste pages when those pages explain part of a shared relationship, but
it does not copy their claims. Writing may use relationship context for a
message while owning the generated draft. Explicit deletion, redaction, archive, and retention choices
are honored, and removed third-party detail is not silently recreated from old
sources.

## Media / Taste

**Purpose:** What the user responds to and the evidence behind those tastes.

**Owns:**

- reactions to books, films, television, music, games, podcasts, comics, and
  other cultural works the user actually experienced;
- reasons for liking, disliking, abandoning, revisiting, or making an exception
  for a work;
- recurring and competing taste patterns involving themes, aesthetics,
  mechanics, storytelling, creators, genres, or cross-media similarities; and
- dated evolution of taste, including meaningful exceptions to an apparent
  preference.

**Does not own:**

- a favorites list, rating database, watchlist, library, collection, or
  consumption tracker without reflective evidence;
- plot summaries, copied reviews, complete external metadata, or generated
  reactions treated as personal taste evidence;
- what the person learned from a work, which belongs to Learning;
- shared viewing or recommendation exchanges when the relationship context is
  the durable evidence, which belongs to Relationships; or
- identity, ideology, politics, religion, sexuality, health, personality,
  morality, intelligence, or other sensitive characteristics inferred from
  cultural consumption.

The vertical stores sparse work pages under `media/`; it does not require a
separate directory for every medium. Individual works are primary evidence.
Consumption does not imply liking, and a single work does not establish an
inferred broad pattern unless the user explicitly states the preference.
Otherwise patterns need multiple independently meaningful reactions, links to
the supporting works, clear scope, and visible exceptions or uncertainty.
Qualitative states such as candidate or established remain readable body
content rather than numeric confidence. Recommendations remain derived and
explainable from both matches and conflicts.

External identifiers may help disambiguate a work when the user supplies them,
but no service, scraper, provider integration, or complete media catalog is
canonical or required. Taste evidence can link to Learning, Relationships,
Writing, Career, Ventures / Projects, or `core/` without duplicating their
ownership.

## Ventures / Projects

**Purpose:** Preserve continuity for meaningful initiatives without becoming a
task manager, CRM, repository inventory, or generic business system.

**Owns:**

- initiative purpose, origin, readable lifecycle, current state, user role, and
  evidenced authority;
- project decisions, trade-offs, commitments, milestones, outcomes, and dated
  evolution;
- proposal, experiment, dogfooding, adoption, and opportunity evidence with its
  scope and provenance; and
- project-specific collaborator or organization context, assumptions, unknowns,
  pauses, abandonment, completion, and supersession.

**Does not own:**

- professional impact or career positioning, which belongs to Career;
- knowledge states or learning progression, which belongs to Learning;
- relationship history or a collaborator CRM, which belongs to Relationships;
- cross-domain preferences, which belong to `core/`; or
- credentials, wholesale workspace/message archives, unsupported business claims,
  or recommendations treated as project facts.

Initiative lifecycle is readable body content, separate from shared page status,
assertion kind, and freshness. An idea is not an active project; a proposal is
not an engagement or commitment; dogfooding and one person's feedback are not
validated adoption or demand; and a recommendation remains derived. Abandoned,
paused, failed, and superseded initiatives remain useful history.

## Overlap risks

The main risks are duplicated concepts rather than incompatible storage:

- Learning may overlap with Career's skills, education, and professional project
  evidence, or with Ventures / Projects' initiative records and Media / Taste's
  resources. Keep professional outcomes in Career, initiative lifecycle in
  Ventures, knowledge state in Learning, and cultural reactions in Media / Taste.
- Relationships may overlap with Career's mentoring and networking evidence or
  Ventures / Projects' collaborator context, as well as Writing's
  message-drafting context. Keep professional evidence in Career, project state
  in Ventures, shared relationship context in Relationships, and generated
  communication in Writing or `derived/` as appropriate.
- Media / Taste may overlap with `core/` preferences, Learning's resource
  evidence, and Relationships' shared interests. Keep the underlying reaction
  evidence in Media / Taste and derive broader patterns only when they earn a
  separate, provenance-linked home.
- Writing may use media or relationship context for an artifact, but it owns
  communication behavior and generated drafts are not evidence of either taste
  or relationship change.
- All verticals may reuse a source or link to a project, work, or event. Reuse
  provenance and links rather than copying the same claim into multiple owning
  areas.

## Deep Maintenance Protocol

The implemented maintenance path is deliberately explicit:

- ordinary lint remains the fast compatibility path;
- deep lint inventories deterministic structural, navigation, contract, and
  freshness relationships without deciding truth;
- deep review is read-only by default and targeted review remains ordinary;
- deep update is explicitly authorized, snapshot-checked, backed up once, and
  bounded to safe structural changes plus approved semantic proposals;
- available Career, Learning, Writing, Relationships, Media / Taste, and
  Ventures / Projects verticals are selectively enabled in schema 0.2, with
  schema-specific first use and explicit contract comparison; and
- managed catalogs and local lexical search are disposable navigation aids, not
  evidence or a second store.

A future contract version must document migrations in its owning procedure,
including affected evidence, safe structural changes, semantic review
requirements, and forbidden automatic changes. No background maintenance,
external enrichment, embeddings, database, MCP, sync layer, or custom runtime
is planned.

## Near-Term Experiments

- Guided Discovery for context coverage and gap analysis.
- Targeted questions that remain bounded rather than becoming an open-ended
  interview.
- Stronger stale-context review when freshness matters to an answer.
- Exercise Learning evidence capture and explanation workflows with synthetic
  scenarios before deciding whether more structure is justified.
- Exercise Relationships retention and deletion choices with synthetic people,
  reported statements, commitments, and privacy-sensitive near misses.
- Exercise Media / Taste recommendations against positive evidence, dislikes,
  exceptions, and taste evolution without growing a catalog.
- Exercise Ventures / Projects comparisons, stale opportunity state, proposal
  versus commitment, adoption evidence, and cross-vertical ownership with
  synthetic data.

## Later Possibilities

- Additional personal-context verticals.
- More Advisor Packs where domain-specific reasoning earns the maintenance cost.
- Optional harness adapters that load the canonical project skills.
- Optional disposable local search indexes if vault scale requires them.
- User-controlled off-device backup copies and sync.
- Selective disclosure.
- Stronger privacy and encryption workflows.
- Automated refresh of explicitly approved sources.

These possibilities must preserve the portable Markdown vault and must not
silently turn generated interpretation into user-confirmed fact.
