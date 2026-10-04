# Retaining Query Results

Read [Query](query.md) first. Load this procedure only when persistence is
explicitly requested. An ordinary answer remains ephemeral.

## Persistence Decision

Use the smallest durable result that serves the request:

- A simple lookup, such as a previous employer or project name, returns an
  answer without mutating the vault by default.
- A read-only Query or contextual-thinking answer does not append an
  operational-log entry by default. If the user explicitly asks to retain a
  query log entry, treat that separate log write as an ordinary mutation and
  follow the normal backup/validation lifecycle.
- A substantial, reusable comparison or synthesis may become a page under
  `derived/`, with `type: synthesis`, `assertion_kind: derived_synthesis`, and
  links to the evidence it combines, but only after explicit retention or a
  separate authorized persistence operation.

### Continuity signals

Persistence is based on durable value, not only on importance or length. Treat
one or more of these as a reason to evaluate a small derived page:

- the user explicitly asks to remember, retain, save, or reuse the result;
- the user says the result would help with a similar future question;
- the answer captures a non-obvious decision, recommendation, or tradeoff that
  will be expensive to reconstruct;
- the answer combines several existing pages into a reusable synthesis; or
- the query exposes a meaningful review item, unresolved conflict, or missing
  evidence that should remain visible.

An explicit retention request is a continuity signal, not permission to promote
an interpretation into a fact. A positive reaction without a future-use signal
does not require persistence.

### Persistence checks

Before creating or updating a derived page, perform a lightweight semantic
check:

1. **Classify the result.** Separate retrieved facts, source material,
   observations, recommendations, and unknowns. Persist advice as
   `derived_synthesis`; route newly supplied factual context through ingest
   instead of hiding it in advice.
2. **Check for an existing home.** Search the relevant indexes and linked pages
   for an existing concept or synthesis. Update the smallest matching page
   rather than creating a duplicate.
3. **Check ownership.** Keep domain facts and goals in their owning vertical,
   cross-domain facts in `core/`, and reusable conclusions in `derived/`. A
   synthesis may link several areas without copying their facts into another
   owner.
4. **Check conflicts.** Compare the conclusion with active goals, facts,
   review items, and relevant derived pages. Preserve factual contradictions and
   surface them as uncertainty or review. A recommendation can remain
   conditional when it explores an option that differs from a current goal; do
   not rewrite the goal merely because the advice is useful.
5. **Check freshness.** If current metrics, role state, goals, or other dynamic
   context materially affects reuse, record a review horizon or explain the
   freshness limitation. Do not silently rely on stale decisive evidence.

If the result has no stable reuse value, no explicit future-use signal, and no
meaningful review value, keep it ephemeral. Do not create a page merely because
several queries were asked or because the answer sounds helpful.

Do not save every answer. A derived page should earn its maintenance cost by
being likely to be reused, difficult to reconstruct, explicitly requested for
future continuity, or important for later review. It must not modify `core/` or
vertical facts merely because the synthesis recommends something.

The number of queries is not the persistence threshold. Several simple lookups
may leave `derived/` unchanged, while one substantial reusable analysis may
justify a page. Do not create a synthesis only to make the folder appear
current.

## Derived Page Shape

When persistence is justified, use a stable descriptive filename and frontmatter
like this:

```yaml
---
type: synthesis
title: Evidence for technical leadership scope
description: Reusable synthesis of leadership evidence across several roles.
tags:
  - leadership
status: active
generated: 2026-08-07
verified: null
sources:
  - ../career/roles/example-role.md
  - ../career/projects/example-project.md
assertion_kind: derived_synthesis
stale_after: 2027-02-07
---
```

The body should state the question, summarize evidence with links, identify
uncertainty and freshness, and label conclusions as derived. If the result is
advice, label recommendations as recommendations. Never phrase a recommendation
as a newly confirmed goal.

For a persisted query result in an existing current vault, prepare the
mutation context with `--for-update` before preparing the smallest derived-page
bytes. Require `controls.mutation_ready: true` and pass
`controls.expected_snapshot` unchanged as the required proposal
`expected_snapshot`. If previous read-only evidence informed the result,
revalidate that evidence under this snapshot before planning the write. On drift,
reread and reconsider the proposal, not just the token. Invoke the ordinary
commit boundary with the
semantic log metadata. The helper stages the page, managed index, and log,
validates them together, owns the provisional/final backup lifecycle and
rollback, and returns one receipt. A true persistence no-op creates no backup
or log entry. If the vault is missing or uninitialized, use the existing
initialization procedure; ordinary commit does not bootstrap it. Schema
migration and deep maintenance remain separate high-level workflows.
