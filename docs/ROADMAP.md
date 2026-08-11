# SelfContext Roadmap

This roadmap describes intended experiments, not promises. A change is ready
when its behavior is validated and documented; Git records the change history.

## Current Foundation

The current system provides:

- a portable Markdown vault with YAML frontmatter and standard links;
- first-run initialization and orientation of existing vaults;
- natural-language ingest, query, review, and lint workflows;
- shared provenance, lifecycle, freshness, and epistemic boundaries;
- local pre-write ZIP backups with retention of the latest three archives;
- Obsidian compatibility and multi-session continuity; and
- separate Career and Writing verticals with replaceable Advisor Packs.

## Current Vertical Work

Each vertical has its own scope and experiment surface while reusing the shared
SelfContext lifecycle:

| Vertical | Current behavior | Next useful experiment |
| --- | --- | --- |
| Career | Evidence-backed roles, projects, skills, goals, and professional reasoning | Dogfood the workflows with real career information while keeping the vault local |
| Writing | Evidence-aware source comparison, selective profile updates, and writing reasoning | Use different authored modes and check whether the profile becomes more accurate without merely becoming larger |

Neither vertical adds a competing memory format, custom runtime, universal
taxonomy, or automatic promotion of generated output into facts.

## Planned Future Verticals

The following verticals are planned future work, not implementations. This
roadmap records enough ownership and architectural direction for separate
implementation agents to work independently. It intentionally does not define
detailed schemas, create vault areas, or add procedures, agents, or pipelines.

### Shared constraints for all three verticals

Each planned vertical must satisfy the same boundaries as the existing Career
and Writing verticals:

- **Distinct ownership:** a vertical must own a distinct kind of evidence and
  reasoning workflow. Generic preferences, values, personality, goals,
  communication style, decision style, habits, and other cross-domain personal
  facts remain in `core/` unless a future decision establishes a narrower
  domain-specific scope.
- **Shared contract:** use the existing Markdown, YAML frontmatter, standard
  relative-link, provenance, freshness, review, and lifecycle conventions. Do
  not introduce a parallel epistemic model, confidence database, taxonomy, or
  storage format.
- **Epistemic discipline:** keep user-stated or user-confirmed facts,
  source-derived facts, agent inferences, and derived syntheses visibly
  distinct. Sources are evidence; the durable context is what those sources
  reveal. Inferences remain reviewable, and derived analyses or advice do not
  silently become facts.
- **Independent usefulness:** no planned vertical may require another vertical
  to function. Cross-vertical use is an optional retrieval relationship through
  SelfContext, not a runtime or schema dependency. A source may support claims
  in more than one domain, but each durable claim must have one clear owner.
- **Core boundary:** `core/` may later derive stable cross-domain patterns from
  vertical evidence, but vertical facts should not be copied into `core/` just
  to make retrieval easier. Advisor Packs, when justified, reason over
  retrieved context and do not own storage or provenance.
- **Time and episodes:** time belongs in evidence and metadata rather than a
  generic timeline vertical. The pattern `context -> alternatives -> decision
  -> reasoning -> outcome -> reflection` may be recorded as a domain-specific
  episode where useful; Decision/Episodes should not become a fourth vertical.
- **Implementation restraint:** the implementation agent should define a
  separate area and index, procedure, or Advisor Pack only when the workflow
  requires it, then update the vertical catalog and relevant documentation.
  It should add no schema or infrastructure that the roadmap does not require,
  and should validate boundaries with fictional or synthetic data.

### Learning

**Purpose:** What the person understands and how that understanding evolves.

**Why it deserves a vertical:** Learning has an evidence and reasoning workflow
that is different from keeping notes or recording a goal. It compares evidence
across time to represent an evolving knowledge state: what is demonstrated,
partial, uncertain, missing, corrected, or connected to prerequisites. That
state can improve future explanations and questions without pretending to be a
complete inventory of everything the person has read or studied.

**Owns:**

- topics, concepts, and mental models that are explicitly or evidentially
  relevant to the person's understanding;
- demonstrated or partially demonstrated knowledge, known gaps, questions,
  misconceptions, and corrected misconceptions;
- learning experiences, exercises, and projects when they provide evidence of
  understanding rather than merely an activity record;
- useful resources as provenance for what was learned and why it mattered;
- prerequisite relationships and dated evidence of progression.

**Does not own:**

- a generic notes, bookmarks, reading-list, course, certificate, or
  book-summary repository;
- every resource the person encountered, or a claim that consuming a resource
  proves understanding;
- generic goals, habits, preferences, or values owned by `core/`;
- career history, professional impact, or role evidence owned by Career;
- authored communication patterns owned by Writing; or
- media consumption and taste evidence owned by Media / Taste.

**Representative use cases:**

- identify what evidence supports explaining a concept and where the remaining
  gaps are;
- connect a new exercise or project to concepts it demonstrates, while
  preserving the project's Career ownership when it is also professional work;
- record a question, misconception, or correction without silently presenting
  an agent's interpretation as established knowledge; and
- compare dated evidence to show progression, changed mental models, or a
  prerequisite that needs attention.

**Relationship to `core/`:** `core/` may contain broad goals or constraints that
shape learning, but the evolving knowledge state belongs in Learning. Core may
later derive a cross-domain pattern from Learning evidence; Learning should not
copy that synthesis back as a concept-level fact.

**Relationship to existing and planned verticals:** Career can provide work,
project, or public-artifact evidence from which Learning derives what was
understood, but Career remains the owner of employment and professional
outcomes. Writing may use Learning context to explain a subject, while Writing
continues to own communication evidence. Media may provide a consumed resource
or cultural work that prompted learning, but Learning owns what the person
learned and Media / Taste owns the response to the work. No one of these
relationships is a prerequisite for Learning.

**Likely future implementation-agent responsibilities:** establish the
vertical's evidence boundary and navigation; define how a source, exercise, or
project can support a knowledge claim without equating exposure with mastery;
compare new evidence with existing concepts, gaps, and contradictions; preserve
progression and uncertainty; and create synthetic evaluations for demonstrated,
partial, corrected, and unchanged knowledge. Add a Learning Advisor only if
future reasoning needs cannot be expressed by the shared SelfContext workflow.

**Questions intentionally left for the implementation agent:**

- What is the smallest useful concept granularity, and when should related
  concepts remain a single page?
- What evidence is sufficient to call understanding demonstrated or partial,
  especially when the evidence is an agent interpretation?
- How should prerequisites and changes in a mental model be represented without
  turning the vault into a knowledge graph or confidence database?
- When should a resource remain only a source record, and when does what was
  learned justify durable context?
- How should forgetting, stale knowledge, unfinished learning, and repeated
  evidence affect review without creating a generic timeline?

### Relationships

**Purpose:** Who matters to the person and the shared context between them.

**Why it deserves a vertical:** Relationship context has a distinct,
privacy-sensitive workflow centered on intentionally preserved interactions and
shared history. It is useful for continuity and respectful future interaction,
not for ranking people or building a complete social graph.

**Owns:**

- who someone is in relation to the user, within the scope the user chooses to
  preserve;
- shared history, meaningful conversations, interactions, important events,
  and commitments;
- shared interests when they are evidenced rather than assumed;
- unresolved threads and useful context for a future interaction; and
- dated changes in the relationship and the user's explicitly recorded
  observations.

**Does not own:**

- a traditional contacts database, sales CRM, social graph, address book, or
  task/reminder system;
- facts about third parties that the user did not intentionally provide or
  preserve;
- inferred sensitive characteristics, diagnoses, political beliefs,
  psychological profiles, motivations, or other speculative attributes about
  third parties;
- the user's general values, preferences, boundaries, or communication style
  owned by `core/`; or
- career achievements, mentoring evidence, or professional networking history
  when those claims belong to Career.

**Representative use cases:**

- orient before a conversation using intentionally retained shared history and
  relevant unresolved threads;
- remember a meaningful commitment or follow-up without turning the vertical
  into a task manager;
- preserve an important event or conversation and how the relationship changed;
  and
- distinguish the user's observation from what another person explicitly said
  or what a source documents, so future context can be corrected or removed.

**Relationship to `core/`:** `core/` may hold the user's general relationship
values, boundaries, or interaction preferences. Relationship-specific facts,
observations, and shared history remain in Relationships. Core must not become a
shadow directory of third parties merely because a pattern could be useful
across contexts.

**Relationship to existing and planned verticals:** Career may own professional
contacts as evidence of roles, mentoring, or networking, while Relationships
may preserve the shared human context only when it has a distinct relationship
purpose; the implementation must avoid duplicate pages. Writing may retrieve
relationship context to help draft a message, but a draft is not relationship
evidence. Learning and Media / Taste may contribute an evidenced shared interest
or event, while Relationships owns the interaction and its meaning. Each
vertical remains useful without the others.

**Likely future implementation-agent responsibilities:** define conservative
identity and relationship-scope handling; distinguish explicit user-provided
context, the user's observations, and unsupported inference; preserve
provenance, dates, corrections, and deletion/retention intent; make sensitive
content easy to review; and test that retrieval does not invent or expose
third-party attributes. Any future relationship-specific reasoning must remain
subordinate to the user's stated context and privacy choices.

**Questions intentionally left for the implementation agent:**

- How should people, groups, and changing relationship scopes be linked without
  becoming a general-purpose social graph?
- What retention, deletion, and redaction controls are needed for sensitive or
  obsolete relationship context?
- How should direct messages, private recollections, and user observations be
  classified and linked to provenance?
- Should commitments be represented as relationship context, linked to an
  external task workflow, or both without creating a task system?
- What is the smallest useful representation for relationship evolution and
  multi-person interactions?

### Media / Taste

**Purpose:** What the person responds to and the evidence behind those tastes.

**Why it deserves a vertical:** Taste is best understood through reactions to
media the person actually consumed, not through a list of favorites or
ratings. A distinct workflow can compare reasons, themes, aesthetics, mechanics,
storytelling, creators, genres, similarities, exceptions, and changes over time
while preserving the individual work as evidence.

**Owns:**

- reactions to books, films, television, music, games, podcasts, and other
  cultural works the person actually consumed;
- reasons for liking, disliking, abandoning, revisiting, or making an exception
  for a work;
- recurring and competing taste patterns involving themes, aesthetics,
  mechanics, storytelling, creators, genres, or cross-media similarities; and
- dated evolution of taste, including meaningful exceptions to an apparent
  preference.

**Does not own:**

- a generic favorites list, ratings database, watchlist, library, collection,
  or consumption tracker without reflective evidence;
- summaries, reviews, or recommendations treated as personal taste evidence
  merely because an agent generated them;
- generic preferences in `core/` unless a stable cross-domain pattern is later
  deliberately derived from evidence;
- what the person learned from a work, which belongs to Learning; or
- writing style, audience, or career context merely because a work influenced a
  piece of Writing or professional work.

**Representative use cases:**

- explain why a recommendation fits the person's evidenced reactions rather
  than relying on a favorite-work list;
- identify a recurring aesthetic, storytelling, or game-mechanics pattern and
  show the works that support and complicate it;
- compare reactions across media and preserve an exception instead of averaging
  it away; and
- notice how taste changed over time without treating an old reaction as a
  current preference automatically.

**Relationship to `core/`:** Taste evidence remains in Media / Taste. `core/`
may eventually contain a stable, cross-domain preference derived from several
owned evidence pages, but it should not become a duplicate catalog of works or
reactions. A recommendation remains derived advice and cannot update core or
Media / Taste by itself.

**Relationship to existing and planned verticals:** Learning may use a book,
film, podcast, or other work as a source for what was learned, while Media /
Taste owns the reaction to that work. Writing may use taste context for a
creative or audience objective, but Writing owns authored communication
patterns. Career owns professional media work or public achievements, not the
user's cultural response to them. Relationships may record a shared interest
or viewing experience when the relationship context is the durable evidence;
Media / Taste owns the user's reaction and broader taste pattern. None of these
links creates a dependency.

**Likely future implementation-agent responsibilities:** distinguish actual
consumption and user reaction from metadata, summaries, and recommendations;
preserve enough work provenance without building a catalog; compare evidence
conservatively across media and time; retain contradictions and exceptions;
avoid inferring identity, ideology, psychology, or other sensitive attributes
from cultural consumption; and evaluate whether a no-pattern or no-update
result is the correct outcome. Add a Media / Taste Advisor only if a
future use case needs reasoning beyond retrieval and generic recommendation
writing.

**Questions intentionally left for the implementation agent:**

- How should works and creators be identified across media without making an
  external catalog or provider service canonical?
- What counts as meaningful reaction evidence, especially for unfinished,
  rewatched, replayed, or revisited works?
- How should genre and other descriptive labels remain useful without imposing a
  rigid universal taxonomy?
- What evidence threshold supports a recurring taste pattern, and how should
  exceptions, context, and evolution qualify it?
- Which cultural-consumption details require extra retention or privacy care,
  and how should recommendations remain visibly derived?

### Overlap risks to resolve during implementation

The main risks are duplicated concepts rather than incompatible storage:

- Learning may overlap with Career's skills, education, and project evidence or
  with Media / Taste's resources. Keep professional outcomes in Career, learning
  state in Learning, and cultural reactions in Media / Taste.
- Relationships may overlap with Career's mentoring and networking evidence or
  Writing's message-drafting context. Keep professional evidence in Career,
  shared relationship context in Relationships, and generated communication in
  Writing or `derived/` as appropriate.
- Media / Taste may overlap with `core/` preferences, Learning's resource
  evidence, and Relationships' shared interests. Keep the underlying reaction
  evidence in Media / Taste and derive broader patterns only when they earn a
  separate, provenance-linked home.
- All three may reuse a source or link to a project, work, or event. Reuse
  provenance and links rather than copying the same claim into multiple owning
  areas.

## Near-Term Experiments

- Guided Discovery for context coverage and gap analysis.
- Targeted questions that remain bounded rather than becoming an open-ended
  interview.
- Stronger stale-context review when freshness matters to an answer.

## Later Possibilities

- Additional personal-context verticals.
- More Advisor Packs.
- Optional harness adapters that load the canonical project skills.
- Optional disposable local search indexes if vault scale requires them.
- User-controlled off-device backup copies and sync.
- Selective disclosure.
- Stronger privacy and encryption workflows.
- Automated refresh of explicitly approved sources.

These possibilities must preserve the portable Markdown vault and must not silently turn generated interpretation into user-confirmed fact.
