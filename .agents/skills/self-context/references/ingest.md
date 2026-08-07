# Ingest and Update Workflow

Use this procedure when the user supplies new information, a source document,
a recollection, or a correction to existing context.

## 1. Understand the Input

Identify what the user actually stated, what a supplied source says, and what
is still unknown. Do not fill gaps. Decide whether the material is:

- a direct user statement or confirmation;
- a source record to preserve;
- a normalized source-derived fact;
- a correction or contradiction; or
- an agent observation that needs review rather than storage as fact.

For a resume, profile, or other meaningful document, preserve a Markdown source
record under `sources/` when practical. Keep the original wording or a faithful
text capture sufficient to explain later normalized claims. Do not create an
arbitrary binary document dump as the durable representation.

## 2. Orient and Find Related Concepts

Read the schema, root index, and recent log first. Search relevant category
indexes and pages for names, organizations, roles, dates, projects, skills, and
distinctive phrases from the new information. Follow links only as far as
needed to understand relationships.

Prefer an existing concept when the identity and subject match. A new page is
appropriate when it represents a distinct durable concept, not merely a new
sentence about an existing one.

## 3. Normalize Conservatively

Create or update the smallest coherent set of pages:

- Put broadly reusable context in `core/`.
- Put career-specific concepts in `career/`.
- Put retained source or recollection material in `sources/`.
- Put unresolved interpretations in `review/observations/` with
  `assertion_kind: agent_inference`, `status: review`, and `verified: null`.

Use frontmatter from [the schema](vault-schema.md). Preserve the appropriate
assertion kind and link every important normalized claim to its source record or
other evidence. When a source is ambiguous or conflicts with existing context,
preserve both sides, state the uncertainty, and create a review item instead of
choosing silently.

Do not infer a user's values, personality, motivation, or goal from a single
example. Evidence-oriented recurring patterns can be observations, not facts,
until the user confirms them.

## 4. Connect and Maintain Navigation

Add links that explain meaningful relationships, such as a role to its projects,
a project to its skills and stories, or a goal to supporting evidence. Update
the nearest category index and the root index when a new durable page is
created. Do not add links to nonexistent pages or link every page to every
related page.

## 5. Log and Report

Append a concise dated entry to `log.md` for meaningful ingests and updates.
Include the operation, summary, changed pages, source records, and unresolved
follow-up items. Do not copy an entire resume or personal narrative into the
log.

Tell the user what was created or updated, what evidence was retained, what
remains uncertain, and whether confirmation is needed. A correction should
preserve useful history and provenance; do not silently erase a conflicting
source.

## Corrections and Confirmation

When the user corrects a page:

1. Update the normalized claim to match the user's correction.
2. Set `verified` to the current date when the user is confirming the claim.
3. Preserve a source link or note the user confirmation in the body when useful.
4. If the old claim remains in a source record, do not edit the source to make
   it agree; explain the discrepancy or mark the old normalized page
   superseded.
5. Resolve or archive the associated observation only after the user's intent
   is clear, and log the change.
