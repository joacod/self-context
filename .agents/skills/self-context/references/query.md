# Query and Derived Material

## Contents

- [Deep-lint inventory versus search output](#deep-lint-inventory-versus-search-output)
- [Contextual thinking as a Query mode](#contextual-thinking-as-a-query-mode)
- [Optional Context Receipts](#optional-context-receipts)
- [Targeted Retrieval](#targeted-retrieval)
- [Verification and Freshness at Query Time](#verification-and-freshness-at-query-time)
- [Persistence Decision](#persistence-decision)
- [Derived Page Shape](query-persistence.md#derived-page-shape)
- [Task context packets](#task-context-packets)
- [Log and Response](#log-and-response)

This is the mandatory retrieval and evidence contract for Query. Load the linked
optional modes or persistence procedure only when the request needs them; do not
read every Query reference for a factual lookup.

Keep index-first retrieval as the primary workflow. After choosing the
smallest explicit scope and useful search anchors, use the bounded preparation
boundary rather than coordinating schema, index, continuity, and search reads
separately:

```bash
python3 .agents/skills/self-context/scripts/prepare_context.py \
  vault --scope core --scope ventures --anchor "task words" \
  --recent-limit 3 --result-limit 5 --navigation-limit 5 --include-evidence
```

The read-only helper composes the current runtime gate, selected navigation,
`recent_log.py` continuity, and existing `search_vault.py` ranking. It does not
infer an owner, load every enabled vertical, initialize a missing vault, or run
deep lint. The default packet is metadata-only. Ordinary factual Query must
pass `--include-evidence` so ranked canonical pages can be answered from this
first response. See [Targeted Retrieval](#targeted-retrieval) for how complete
evidence satisfies a page read, when a separate read is still required, and
the evidence-section limits. Add `--contextual` when the question is
contextual reasoning rather than a simple lookup.

Do not read the complete `log.md` or run historical search automatically. When
an older operation may matter, use the bounded historical helper explicitly:

```bash
python3 .agents/skills/self-context/scripts/search_log.py \
  "migration ventures" vault --limit 10
```

`search_vault.py` is read-only, dependency-free, builds no permanent index, and
never replaces the Markdown vault. Its deterministic priorities are exact stable
ID, exact normalized title, exact normalized alias, and then non-exact matches.
For non-exact queries, unique query-term coverage is the
primary signal; matched-term count, field importance (title/alias, description/
tags, headings, body), phrase matches, term proximity, status, page type, and
assertion kind refine the ordering. Path is the final tie-breaker. A one-token
title match should not outrank a page covering nearly all task terms merely
because the token is in a prominent field.

JSON results include matched fields, bounded snippets, a match type, query-term
coverage, phrase fields, a deterministic `rank_score`, and `superseded_by` when
that explicit successor field is present. Exact-match tier, exact term-coverage
ratio, and matched-term count precede the scalar score in both direct search
and multi-anchor merging. `rank_score` refines that ordering; it is not a
standalone sort key, confidence, truth, or verification. Archived and superseded
pages are
included by default with lower ranking. Use `--exclude-archived` or
`--exclude-superseded` to omit them. The accepted `--include-archived` and
`--include-superseded` options are deprecated compatibility aliases for one
cycle and will be removed in a future release; they do not change the default
inclusion behavior. Sources remain opt-in via `--include-sources`.

After ranked matches are selected, `prepare_context.py` follows explicit
`superseded_by` links from selected superseded pages. The successor does not
need to match the query. Historical matches stay in `matches`; replacements
appear in `related_replacements` with the originating page, relationship, and
chain. Follow at most three replacement edges and six related pages by default.
Unresolved links and stopping reasons such as a missing target, invalid
reference, cycle, out-of-scope path, or exhausted limit appear in
`unresolved_replacements`. Do not treat a newer timestamp as a replacement, do
not infer successors from similar titles, and do not mix successor
relationships into `linked_sources`.

Search is only a retrieval aid: inspect provenance, freshness, assertion kind,
review state, contradictions, source links, and available replacement evidence
before answering. Deep-review reports and noncanonical state remain excluded.

### Contextual retrieval scope rules

Contextual Query should make scope explicit before lexical search whenever the
question supplies enough information to do so:

1. Start with the most likely canonical owner: `core/` for goals, values,
   preferences, and recurring constraints; or the named vertical for a domain
   question.
2. Add another owner only when it can materially change the answer. Keep the
   initial set small and record the reason for each cross-vertical expansion.
3. Treat `derived/` as optional analysis, not a default context layer. Include a
   derived synthesis only when canonical pages are insufficient or the user
   asks for reusable prior analysis.
4. Keep `sources/` opt-in. When provenance, freshness, or verification matters,
   expand the selected canonical pages' linked source records rather than
   searching every source in the vault.
5. Exclude unrelated verticals even when common words match. A scoped result
   may be empty; do not fill it with lexical near-matches.

The disposable helper makes these rules inspectable with repeatable
`--scope PATH` options, `--contextual`, and `--expand-linked-sources`. A
contextual search ignores multi-term matches below 50% query-term coverage and
prefers canonical pages over derived syntheses unless `--include-derived` is
explicit and `derived` is included in the requested scope. Linked-source expansion reserves at most three result slots by
default, so provenance cannot turn a targeted query into a source dump. These
are conservative retrieval aids, not confidence or truth scores.

For modern Query semantics, treat the runtime state returned by
`prepare_context.py` as the shared latest-first compatibility gate. Continue
normally only when the packet reports a current schema with current applied
contracts. An old recognized schema or stale applied contract must not receive
a native modern query answer or silently upgrade; return a concise `upgrade
vault latest` direction. Limited read-only orientation and migration planning
may inspect control state and selected old pages solely to explain or perform
the upgrade. Future, malformed, and unversioned state is a
compatibility/recovery blocker.

## Deep-lint inventory versus search output

Deep-lint JSON is a deterministic maintenance inventory, not a second evidence
store. Use its compact page metadata to batch pages, compare ownership, select
provenance and stale-source candidates, and triage index/link relationships
before opening full files. Its `tags` and aliases are selection aids only; they
do not establish a personal claim. `outbound_links` and `inbound_links` are
ordinary internal navigation, while `source_relationships` is reserved for
frontmatter `sources` and remains a provenance pointer without authority or
truth scoring. A newer linked timestamp is a review candidate, not an automatic
rewrite instruction.

Search output may include a strictly bounded snippet to help answer a targeted
query. Do not copy those snippets, complete bodies, source transcripts, or task
packets into deep-lint JSON or a retained deep-review report. The inventory
points to evidence files; it does not replace reading the relevant page when
content is needed.

Use this procedure for retrieval, comparison, synthesis, or evidence gathering.

## Contextual thinking as a Query mode

For brainstorming, comparisons, advice, or challenges, load
[contextual thinking](query-modes.md#contextual-thinking-as-a-query-mode).
Retrieve evidence, frame supported context and unknowns, explore options,
challenge them against relevant counterevidence, and conclude conditionally.
Generated ideas and recommendations remain ephemeral unless retention is
explicitly requested. Simple lookups do not need this extended flow.

## Optional Context Receipts

When the user asks for the basis, sources, freshness, or persistence behind an
answer, load [context receipts](query-modes.md#optional-context-receipts). Do not
load that presentation guide or produce a full receipt for every lookup.

## Targeted Retrieval

### Bounded vocabulary recovery

Search remains lexical. Accent folding is a fallback (`accent_folded: true`),
not an exact identity match; equal-coverage strict matches rank ahead of folded
ones. Original text, IDs, aliases, and collision checks remain unchanged.
If evidence is insufficient, make at most one reformulation pass with up to two
useful alternate names, paraphrases, or translations. Preserve the original
scope unless another owner can materially change the answer. Do not persist
generated aliases or expand every vertical to compensate for a miss. A missing
match is a retrieval gap, not evidence that a personal fact is false.

### Packet budget

`--packet-byte-limit` defaults to 32768 bytes (minimum 1024) of compact UTF-8 JSON;
the CLI emits that representation. `controls.packet_omissions` counts removed
items by section. Navigation and recent continuity are reduced before evidence;
pages are omitted whole with an omission reason, never silently sliced. If
omission details themselves cannot fit, their removal is also counted in
`packet_omissions`.
Treat any omissions as incomplete coverage and fetch only what the answer needs.
If required runtime findings or unresolved replacement qualifications cannot
fit, the packet blocks entirely with `packet-budget-exceeded`; retry with a
narrower scope or an explicit larger budget. A blocked packet never supplies a
usable mutation token. The existing evidence budget is a separate inner limit.

For normal Query retrieval, first declare the smallest likely owner and any
material cross-vertical expansion, then call the preparation boundary with
those explicit scopes, anchors, and `--include-evidence`. The packet supplies
current runtime state, selected root/manual indexes, bounded continuity,
ranked candidate metadata, optional linked-source candidates, related
replacement pages from explicit `superseded_by` links, unresolved replacement
reasons, and complete original contents for a bounded set of ranked canonical
pages and related replacements. It is a retrieval aid, not a
semantic Query engine.

Complete content in `evidence` includes frontmatter, epistemic metadata
(`status`, `sources`, assertion kind, and freshness fields), a `content_hash`
of the original page bytes, and `complete: true`. That content satisfies
reading that page; do not reopen it unnecessarily. `--evidence-page-limit`
(default 3) and `--evidence-byte-limit` (default 24576) bound only the
evidence section, including its metadata, using compact UTF-8 JSON accounting.
This inner budget does not cap the whole packet or measure model tokens;
the separate packet budget above caps total serialized output. Among the first `--evidence-page-limit` ranked
matches, explicit successor/predecessor evidence receives slots before unrelated
matches. The furthest visible successor is considered first, then its historical
origin and intervening pages. This also applies when a successor is already a
primary match. Match ranking itself is unchanged. Remaining related replacements
share the budget. A furthest discovered successor is not necessarily current:
inspect unresolved traversal limits or edges before answering. Pages are
never silently truncated. Selected candidates that are not included remain in
the ranked `matches` or `related_replacements` lists and appear in
`evidence_omitted` when considered, with a reason such as `page too large`,
`page limit exhausted`, or `aggregate budget exhausted`. An oversized top
candidate is not covered by a
lower-ranked page. Metadata-only related replacements have not been fully
read. Preserve targeted reads when required evidence is omitted, insufficient,
or needs freshness confirmation. Keep facts, inferences, historical material,
and sources distinct. A content hash identifies the returned version; it does
not establish that a later write is safe.

Start from the packet's selected navigation and inspect only the primary owner
index and linked pages that the request makes relevant. Navigation resolves at
most the requested link limit per index; `links_truncated` and
`managed_entries_truncated` identify incomplete navigation. Maintenance checks
remain exhaustive. Add another enabled
vertical only when it can materially change the answer; cross-vertical
questions may pass multiple relevant scopes, while unrelated enabled verticals
stay out of context. The root index and targeted search remain current
navigation; do not maintain or load a growing Recent Additions page/list.
Managed catalog blocks are compiled navigation, not evidence; inspect the
linked durable page and its provenance before relying on an entry. If a
catalog is missing, drifted, or has invalid marker structure, treat it as an
unreliable navigation aid and run `sync_indexes.py --check` as a read-only
diagnostic. Do not manually edit managed entries. `sync_indexes.py --write`
belongs only inside an authorized current-model mutation workflow. For schema
0.2, an absent available vertical is empty; a read-only query must not create
its area or contract marker. A schema 0.1 query is limited to
orientation/diagnosis and must direct the user to upgrade rather than promise
current retrieval semantics. Use `search_log.py` only for an explicit
historical question; normal Query does not search full log history
automatically. Explicit broad review or deep-maintenance procedures may use
their documented broader inventory when required.

Separate the result into:

- what the vault directly supports;
- what appears likely from several pieces of evidence;
- what is unknown, stale, contradictory, or unverified; and
- any conclusion or recommendation, which is derived rather than fact.

Never use an agent inference or derived advice as if it were independent source
evidence. If the vault is insufficient, say so and identify the missing context
instead of guessing.

## Vertical-specific retrieval

When a query depends on a vertical, use its procedure for detailed evidence
semantics and its Advisor Pack's local guides for personalized reasoning and
output. Keep claims with their owning pages; cross-vertical retrieval links
owners rather than copying facts.

| Vertical | Retrieval guardrail and canonical procedure |
| --- | --- |
| Career | Retrieve relevant professional evidence, scope, outcomes, goals, and gaps; see [Career](career.md). |
| Writing | Include mode, audience, language, dates, authorship, and evidence state; generated drafts are not independent evidence. See [Writing](writing.md). |
| Learning | Include qualitative knowledge state, scope, dates, gaps, corrections, and prerequisites; exposure is not understanding and explanations remain derived. See [Learning](learning.md). |
| Relationships | Retrieve only relevant shared history, commitments, open loops, and sources; keep reported statements and inferences separate and do not produce a person dossier. See [Relationships](relationships.md). |
| Media / Taste | Retrieve actual work reactions, patterns, exceptions, and dates; consumption is not preference and recommendations remain derived. See [Media / Taste](media-taste.md). |
| Ventures / Projects | Retrieve lifecycle, current state, decisions, commitments, milestones, outcomes, adoption evidence, evolution, and unknowns; keep initiative claims distinct from Career, Learning, Relationships, Writing, and `core/`. See [Ventures / Projects](ventures.md). |

For any vertical, inspect the returned page's assertion kind, status,
provenance, freshness, review state, and available replacement evidence before
treating it as current evidence. If the vertical procedure says the evidence is
insufficient or a no-op is appropriate, preserve that result rather than
manufacturing a claim.

## Verification and Freshness at Query Time

Treat verification and freshness as separate dimensions:

- A current-state answer must inspect available `related_replacements` before
  relying on a `status: superseded` claim. Keep the historical match visible
  and use the explicit successor when the question is about the current
  decision or preference. A historical question may use the superseded page;
  make its temporal status clear rather than presenting it as current.
- An explicit successor is recorded replacement context, not automatically
  verified truth. If `unresolved_replacements` shows a missing target, cycle,
  invalid reference, scope restriction, or exhausted limit, keep the current
  state visibly uncertain instead of implying that the latest retrieved page
  is the replacement.
- An active page with `verified: null` is usable as source-derived or user-stated
  evidence when its status and provenance are appropriate, but describe it as
  unconfirmed rather than presenting it as explicitly verified.
- A page with `status: review` is provisional. Use it to identify a question or
  uncertainty, not as settled evidence for a confident answer. If it is decisive
  to the question, give the user the supported conditional answer and ask one
  bounded confirmation question rather than silently promoting it.
- A page past `stale_after` may remain useful historical evidence, but do not use
  it as current without labeling the freshness problem or asking the user.
- `stale_after: null` means there is no automatic stale horizon. It does not
  prove that dynamic information is current. Report the page's generated date
  and any dated source/evidence coverage separately; if currentness is
  decisive, identify it as unknown and ask a bounded question.

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

Only when the user explicitly asks to retain a result, load
[Query persistence](query-persistence.md). Check ownership, existing homes,
provenance, conflicts, and freshness; retain recommendations as derived
syntheses. Revalidate earlier evidence under a mutation snapshot before writing.
Read-only Query never appends logs or creates durable artifacts.

## Task context packets

For a requested task packet, load [task context packets](query-modes.md#task-context-packets).
Return the smallest relevant evidence, constraints, unknowns, and exclusions.
A packet is ephemeral derived output unless explicitly retained.

## Log and Response

Read-only Query and contextual thinking do not log by default. Report the
relevant evidence, scope, coverage/as-of dates, assertion kinds, freshness and
uncertainty, and say that no durable or operational-log change was made. If the
user explicitly authorizes a separate operation-log entry, report it as that
mutation rather than implying a page was created. If no page was created, say
whether the answer remained ephemeral or whether a durable candidate was
identified but not applied.
