# Query and Derived Material

For a large or ambiguous vault, use the index first and then the disposable
local lexical helper:

```bash
python3 .agents/skills/self-context/scripts/search_vault.py "task words" vault
```

`search_vault.py` is read-only, dependency-free, and builds no permanent
index. It ranks exact ID/title/alias matches first, then title/alias tokens,
descriptions/tags, headings, and body matches. It excludes deep-review reports
and noncanonical state by default and returns bounded snippets plus metadata.
Search is only a retrieval aid: inspect provenance, freshness, status, and
source links before answering. A vertical filter and explicit source,
archived, and superseded inclusion flags are available.

Use this procedure for retrieval, comparison, synthesis, or evidence gathering.

## Targeted Retrieval

Start with `SCHEMA.md`, `index.md`, recent log entries, enabled vertical
indexes, and the smallest relevant linked pages. Managed catalog blocks are
compiled navigation, not evidence; inspect the linked durable page and its
provenance before relying on an entry. If a catalog is missing, drifted, or has
invalid marker structure, treat it as an unreliable navigation aid and run
`sync_indexes.py --check` as a read-only diagnostic. Do not manually edit
managed entries. `sync_indexes.py --write` belongs only inside an authorized
mutation workflow. For schema 0.2, an absent available vertical is empty; a
read-only query must not create its area or contract marker. Schema 0.1 is
likewise preserved during read-only retrieval. Use local lexical search only
when the index is ambiguous or the vault is large. Do not scan the entire vault
for a narrow question unless orientation shows that the relevant path is
unclear.

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

For Writing retrieval, include the relevant mode, audience, language, dates,
authorship, and evidence state. Generated drafts and derived style analyses are
not independent evidence of the user's communication. A Writing query may
report that no meaningful profile update was needed; retrieval and analysis do
not require a new durable page.

For Learning retrieval, read the relevant `learning/` concepts and linked
sources, then include the qualitative knowledge state, scope, dated evidence,
gaps, corrections, and prerequisite relationships. Distinguish exposure from
understanding or demonstrated application. Use reviewable Learning observations
as uncertainty, not settled knowledge. An explanation based on known concepts is
still derived output and does not update the Learning profile automatically.

For Relationships retrieval, read only the relevant relationship pages, shared
history, commitments, open loops, and linked source records. Keep reported
statements, user observations, source-derived facts, and agent inferences
separate. Do not expose unrelated third-party information or infer sensitive
characteristics. Context before an interaction is a focused derived answer, not
a complete person dossier.

For Media / Taste retrieval, read individual work reactions, supporting pattern
pages, exceptions, and dated evidence. Consumption is not preference, and
external metadata, copied reviews, and generated reactions are not personal
evidence. Explain recommendations through matches and conflicts in the user's
actual reactions; keep the recommendation derived and do not update taste or
`core/` automatically.

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

### Pre-write checks

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

Before creating the derived page, updating its index, or appending any
operation log for the query, create the pre-write backup described in [Vault
Backups](backups.md).

## Task context packets

When the user asks for a task context packet, return only the smallest relevant
material: the task objective, directly supported personal context, relevant
examples, constraints and explicit preferences, stale/provisional/contradictory
context, unknowns, evidence paths, and important exclusions. Keep relationship
and other sensitive context out unless directly relevant. The packet is derived
output, not evidence, and remains ephemeral unless the user explicitly asks to
retain a reusable packet under `derived/` through the normal persistence and
backup rules.

## Log and Response

Log a substantial query or a meaningful evidence retrieval, but not every
trivial lookup. Report whether a derived page was created, which evidence was
used, and what remains unknown or needs user confirmation. If no page was
created, briefly state that the answer did not meet the reusable-synthesis
threshold.
