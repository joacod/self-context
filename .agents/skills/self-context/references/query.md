# Query and Derived Material

Use this procedure for retrieval, comparison, synthesis, or evidence gathering.

## Targeted Retrieval

Start with `SCHEMA.md`, `index.md`, and recent log entries. Use category indexes,
frontmatter, filenames, targeted text search, and links to locate relevant
pages. Do not scan the entire vault for a narrow question unless orientation
shows that the relevant path is unclear.

Separate the result into:

- what the vault directly supports;
- what appears likely from several pieces of evidence;
- what is unknown, stale, contradictory, or unverified; and
- any conclusion or recommendation, which is derived rather than fact.

Never use an agent inference or derived advice as if it were independent source
evidence. If the vault is insufficient, say so and identify the missing context
instead of guessing.

## Verification and Freshness at Query Time

Treat verification and freshness as separate dimensions:

- An active page with `verified: null` is usable as source-derived or user-stated
  evidence when its status and provenance are appropriate, but describe it as
  unconfirmed rather than presenting it as explicitly verified.
- A page with `status: review` is provisional. Use it to identify a question or
  uncertainty, not as settled evidence for a confident answer. If it is decisive
  to the question, give the user the supported conditional answer and ask one
  bounded confirmation question rather than silently promoting it.
- A page past `stale_after` may remain useful historical evidence, but do not use
  it as current without labeling the freshness problem or asking the user.
- `stale_after: null` means there is no automated deadline. It does not prove
  that dynamic information is current; if currentness is decisive, identify the
  freshness as unknown and ask a bounded question.

When a user confirms that an expired current-state claim is still true, update
the page's `verified` date when the claim was explicitly confirmed and set
`stale_after` from the current date using the selected or default horizon. If
the user reports a change, follow the correction workflow and preserve the old
evidence rather than silently rewriting it. Reading or citing a page alone must
not renew either field.

If a user defers or leaves a review item unconfirmed, do not repeat the prompt in
unrelated answers. Surface it again during an explicit review or when it becomes
decisive to the requested answer.

## Persistence Decision

Use the smallest durable result that serves the request:

- A simple lookup, such as a previous employer or project name, returns an
  answer and may be logged without creating a page.
- A meaningful query can be logged when it informs continuity or exposes a
  review item.
- A substantial, reusable comparison or synthesis may become a page under
  `derived/`, with `type: synthesis`, `assertion_kind: derived_synthesis`, and
  links to the evidence it combines.

Do not save every answer. A derived page should earn its maintenance cost by
being likely to be reused, difficult to reconstruct, or important for later
review. It must not modify `core/` or `career/` facts merely because the
synthesis recommends something.

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

## Log and Response

Log a substantial query or a meaningful evidence retrieval, but not every
trivial lookup. Report whether a derived page was created, which evidence was
used, and what remains unknown or needs user confirmation. If no page was
created, briefly state that the answer did not meet the reusable-synthesis
threshold.
