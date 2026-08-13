---
vertical_id: media
contract_version: 1
vault_area: media
advisor_skill: media-advisor
---

# Media / Taste Vertical Procedure

The Media / Taste vertical preserves evidence-backed context about what the
user responds to and why. It is not a media database, favorites list,
watchlist, collection manager, ratings service, or external catalog. The durable
asset is the user's reaction and the evidence behind a pattern, not complete
metadata about every cultural work encountered.

## Scope and ownership

Media / Taste owns:

- intentional, meaningful reactions to books, films, television, games, music,
  albums, artists, podcasts, comics, and other cultural works;
- whether a work was consumed, is being consumed, was abandoned, revisited, or
  otherwise experienced, when that state helps interpret the reaction;
- reasons for liking, disliking, mixed reactions, memorable aspects, emotional
  response, mechanics, themes, style, pacing, creators, or comparisons when the
  user actually provides them;
- recurring or competing taste patterns supported by individual works;
- exceptions to an apparent preference and dated changes in taste; and
- explainable evidence for future recommendation reasoning.

Media / Taste does not own:

- every play, view, click, article, video, song, or social-media mention;
- plot summaries, copied reviews, complete external metadata, or a provider's
  catalog;
- a rating database or consumption tracker without reflective personal
  context;
- what the person learned from a work, which belongs to Learning;
- shared viewing or recommendation exchanges when the durable evidence is the
  relationship, which belongs to Relationships; or
- writing style, career achievements, beliefs, ideology, personality,
  identity, or other personal attributes inferred from cultural consumption.

A work can support more than one vertical, but each durable claim has one clear
owner. Link to Learning, Relationships, Writing, Career, or `core/` when their
owned context is relevant; do not copy it into Media / Taste.

## Storage and page choices

- `media/index.md` is the navigation page for durable works and taste
  observations.
- A meaningful work reaction normally lives in a compact page directly under
  `media/`, such as `blade-runner-2049.md`. Use a `works/` or `patterns/`
  subdirectory only when an actual collection makes navigation clearer. There
  is no required taxonomy for books versus films versus games.
- A work page is usually a shared-schema `concept` page. Its body may contain
  `## Work`, `## Experience`, `## Reaction`, `## Comparisons`, and `## Evidence`
  sections, but empty or irrelevant sections should be omitted.
- A recurring inferred pattern is normally a shared-schema `observation` with
  `assertion_kind: agent_inference`, `status: review`, and `verified: null` until
  the user resolves it. An explicit user preference can be stored at its named
  scope as `user_stated_fact`; it still should not be broadened to every medium.
- Retained raw recollections or supplied captures remain shared `source_record`
  pages under `sources/`. A generated recommendation or cross-work comparison
  belongs under `derived/` only when persistence earns its maintenance cost.

Do not add rating scales, confidence fields, external-provider IDs, or media
schemas to frontmatter. Optional identifiers such as an ISBN or MusicBrainz ID
may appear in the body when the user supplies one and it helps disambiguate a
work, but external services are never required and metadata should stay sparse.

## Individual work evidence

Individual works are the primary evidence for taste. Record only what the user
actually experienced or intentionally supplied:

```markdown
## Work

- medium: film
- creator: fictional creator, if useful
- identifier: optional user-supplied identifier

## Experience

- state: consumed | currently consuming | abandoned | revisited
- experienced: approximate date or period, when known

## Reaction

What the user liked, disliked, noticed, remembered, or would recommend. A
rating belongs here only if the user uses ratings and it helps future context.

## Comparisons

Explicit comparisons with another work or creator.

## Evidence

Links to a supplied recollection, source record, or related owned context.
```

Finishing a work does not imply liking it. Starting it does not imply a
meaningful interest. An abandoned work may be useful when the user explains
why; otherwise it can remain unrecorded. Do not copy an external review or
invent a reaction from a work's reputation, genre, plot, or metadata. An
AI-generated reaction is derived output, not user evidence.

## Taste pattern evidence

A pattern must explain why the works support it and where it does not apply.
Use body sections such as `## Pattern`, `## Evidence`, `## Scope`, `## Exceptions`,
and `## Evolution`. Keep labels like candidate, emerging, established, or
explicit preference in readable content; they are not a second confidence
model.

Conservative evidence rules:

- One work can support a durable pattern only when the user explicitly states
  the preference or reaction as such. An agent should not generalize from one
  reaction.
- An inferred recurring pattern normally needs reactions to multiple
  independently meaningful works or clearly distinct contexts. Repeated
  metadata, repeated plot descriptions, or multiple agent summaries of one
  work are not independent evidence.
- Consumption is evidence that the work was encountered, not evidence that the
  user liked it or prefers its characteristics.
- A pattern remains scoped to the medium, genre, context, time, or exception
  shown by its evidence. Do not turn “usually” into “always.”
- Repeated evidence can reinforce an existing page and add links without
  automatically verifying it or changing its qualitative state. The user's
  explicit confirmation has a different epistemic role.

A useful pattern page might say:

> The user often responds to atmospheric speculative works with ambiguous
> identity themes. Evidence includes three described works across film and
> games. The user usually dislikes grind-heavy progression; one exploration
> game is a recorded exception because its worldbuilding mattered more.

That is more useful than a list of genres or a personality claim. If the
pattern is uncertain, keep it reviewable and show the evidence that would
support or contradict it.

## Exceptions and taste evolution

Exceptions are first-class context when they help future recommendations. Keep
the general pattern, the exceptional work, and the reason for the exception
separate. Do not average the exception away or rewrite the general pattern to
fit one outlier.

Use dated evidence entries to represent change, for example “used to avoid
slow-paced films, then began enjoying them in 2025 in stories with strong
atmosphere.” Preserve the earlier reaction and its scope. A newer work is not
automatically more authoritative; it may reflect a different medium, mood,
context, or genuine evolution. Mark an old pattern superseded only when the
user or strong dated evidence clearly establishes that it no longer applies.
There is no separate timeline system.

## External metadata and privacy

Keep external facts to the minimum needed to identify the work. Do not make
ISBN, IMDb, TMDb, Spotify, MusicBrainz, or other identifiers mandatory; do not
add integrations, scraping, or network services for this vertical. Metadata
that can be fetched elsewhere should not crowd out the user's reaction.

Cultural consumption can be sensitive. Do not infer political beliefs,
religion, sexuality, ethnicity, medical or mental-health characteristics,
identity, morality, intelligence, or personality from the user's media history.
If the user explicitly supplies a sensitive connection and genuinely asks to
retain it for a narrow personal purpose, preserve only the stated context and
keep the claim easy to review or delete. A recommendation must never reveal or
invent a sensitive attribute as its explanation.

## Media / Taste ingest and update

After the normal SelfContext orientation and before a mutation:

1. Identify the work, medium, user's actual experience, and the personal
   reaction or reason it has future value. Do not create a record for every
   consumption event.
2. Separate user-stated reaction, retained source material, external metadata,
   agent interpretation, and generated recommendation.
3. Search `media/index.md` and related work or pattern pages before creating a
   new page. Update an existing work page when identity and reaction scope
   match; do not make duplicate pages for title variants.
4. Store the smallest useful work evidence. Preserve an abandoned, revisited,
   or mixed reaction only when the user explains why it matters.
5. Compare candidate patterns with existing evidence. A single non-explicit
   reaction is not enough; independent works and distinct contexts matter more
   than counting sources. Preserve contradictions and exceptions rather than
   flattening them.
6. Represent dated change as evolution and keep older evidence when it explains
   the change. Do not delete an old preference merely because a new work differs.
7. Update `media/index.md`, relevant review navigation, and `log.md` when a
   durable page or review observation changes. Keep Learning, Relationships,
   Writing, Career, and `core/` unchanged unless a claim clearly belongs there.
8. Apply the shared backup, confirmation, and freshness rules. A source or
   generated recommendation does not verify a taste claim.

A meaningful operation may result in **No meaningful Media / Taste update** when
the item was incidental, only supplied external metadata, repeated existing
evidence without useful provenance, or did not contain a personal reaction.
That is a successful noise-prevention outcome.

## Media / Taste queries and recommendations

For “why did I like this?” retrieve the work's own reaction, linked patterns,
exceptions, and relevant dates. For “would I like this?” compare the candidate
with several evidenced reactions, state both matches and conflicts, and label
the conclusion as a derived recommendation. Do not claim certainty from a genre,
creator, rating, or one superficially similar work.

For cross-media queries, link the individual work pages and explain the shared
feature that the evidence supports. A recommendation, comparison, or taste
summary remains ephemeral unless the user asks to retain it or it has clear
future continuity value. A persisted result is `derived_synthesis`, linked to
work and pattern evidence, and cannot update a taste pattern automatically.

## Example boundaries

Good durable context:

> The user liked *Disco Elysium* for exploration through dialogue, ambiguous
> identity, and worldbuilding. They disliked the amount of combat in another
> game. These are reactions to individual works, not a global personality
> profile.

> An inferred pattern about atmospheric speculative worlds links three distinct
> work pages and records one exception where the user preferred a fast-paced
> film for its visual design.

Not durable by default:

> The user finished a film, therefore they liked it.

> The user listens to political music, therefore they hold the artist's beliefs.

> A complete IMDb record or every Spotify play with no personal reaction.

After a Media / Taste operation, report the works or observations changed, the
reaction evidence and links retained, pattern support or exceptions, unresolved
review items, and whether `core/` and `derived/` were intentionally unchanged.

## Contract migrations

Version 1 has no prior migrations. Future versions must identify affected Media
/ Taste evidence, safe structural changes, semantic review requirements, and
forbidden automatic changes. A contract update never infers sensitive identity
or personality, turns consumption into preference, removes an exception, or
promotes generated reactions into evidence automatically.
