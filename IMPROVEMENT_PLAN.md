# SelfContext performance and semantic improvement handoff

Status: Pass 1 implemented and validated; Pass 2 not started.

Prepared on 2026-10-03 against commit
`e5991fdbe5aba0ef4d0e4264f988bf99477c8c73`.

## Purpose and execution boundary

Improve ingestion safety, performance, retrieval quality, and semantic
consistency while preserving a working, actively used SelfContext installation.
This is an implementation handoff requested by the user, not a new runtime
contract or an automatic maintenance backlog.

The analysis and this document do not authorize production-vault changes,
migration, commits, branches, pushes, PRs, external API calls, or deployment.
Follow the user's current authorization and [repository guidance](AGENTS.md).
Before a non-trivial implementation slice, explain its scope and obtain the
required confirmation. Implement the approved slice, report it, and do not
automatically start the next one without authorization.

The user subsequently authorized splitting this plan into two passes and
implementing Pass 1 immediately. That authorization covers the project changes
listed below; Pass 2 and production-vault migration remain unstarted.

Reinspect the current code and worktree before acting: this document records a
specific baseline, and later work may have resolved or changed these findings.
Mark a step complete only with its implementation and validation evidence.
Record completion concisely here when maintaining this handoff is in scope.

## Non-negotiable constraints

- Work from the repository root. Preserve unexpected worktree changes.
- Keep Markdown, YAML frontmatter, and relative Markdown links canonical.
  Python owns deterministic mechanics; the model and skills own semantics.
- Never use real vault content in tracked tests, examples, documentation,
  reports, or operational code. Use `John Doe` and `MyContext Systems` in
  fictional fixtures. This plan intentionally omits private vault measurements.
- Run mutation experiments only in temporary synthetic project roots, with
  their backups outside the production project. Do not benchmark production
  commits, alter the real vault, or clean up its backups.
- Read-only operations must remain free of vault, log, index, backup, marker,
  cache, and other persistent writes. Disabled verticals stay disabled.
- Preserve provenance, uncertainty, historical visibility, scoped verification,
  freshness, meaningful no-op behavior, and explicit activation decisions.
- Preserve path and symlink protections, runtime gates, backup lifecycles,
  validation, rollback, and structured receipts. Performance work must not
  silently weaken these guarantees.
- Avoid databases, embeddings, daemons, background indexing, dedicated runtime
  agents, or a new storage layer. No persistent cache is justified by this
  baseline. A later architectural proposal needs separate evidence and approval.
- Use `skill-creator` before materially modifying project skills. Keep their
  canonical files under `.agents/skills/`. Preserve useful repeated guardrails;
  do not shorten instructions through mechanical deduplication.
- Keep CI's single canonical gate, `python scripts/validate_repo.py`. Do not
  add duplicate checks, model API calls, or hardware-sensitive timing thresholds
  to CI. Do not update the public README for internal-only changes.

## Start here

Read [SelfContext](.agents/skills/self-context/SKILL.md) and the references for
the approved slice. This work is project maintenance, not ordinary vault use.

| Concern | Primary implementation or contract | Existing validation |
| --- | --- | --- |
| Preparation, navigation, evidence allocation | [prepare_context.py](.agents/skills/self-context/scripts/prepare_context.py), [Query](.agents/skills/self-context/references/query.md) | `tests/test_prepare_context.py`, `tests/test_retrieval_scope.py` |
| Ranking, scopes, source expansion | [search_vault.py](.agents/skills/self-context/scripts/search_vault.py), [vault_utils.py](.agents/skills/self-context/scripts/vault_utils.py) | `tests/test_search_vault.py`, `tests/test_retrieval_scope.py`, `tests/test_vault_utils.py` |
| Staging, preconditions, backups, rollback | [ordinary_commit.py](.agents/skills/self-context/scripts/ordinary_commit.py), [file_transaction.py](.agents/skills/self-context/scripts/file_transaction.py), [vault_state.py](.agents/skills/self-context/scripts/vault_state.py) | `tests/test_ordinary_commit.py`, `tests/test_backup_vault.py` |
| Managed catalogs | [sync_indexes.py](.agents/skills/self-context/scripts/sync_indexes.py) | `tests/test_sync_indexes.py` |
| Ingestion and retained outcomes | [Ingest](.agents/skills/self-context/references/ingest.md), [Checkpoint](.agents/skills/self-context/references/checkpoint.md), owning vertical procedures | SelfContext and advisor `evals/`, `tests/test_repository_consistency.py` |
| Schema and upgrades | [Vault schema](.agents/skills/self-context/references/vault-schema.md), [Upgrade](.agents/skills/self-context/references/upgrade.md), [Migration](.agents/skills/self-context/references/migration.md) | `tests/test_runtime_gate.py`, `tests/test_migration_registry.py`, `tests/test_migrate_vault.py`, `tests/test_upgrade_workflow.py` |
| Shared fictional fixtures | [synthetic_vault.py](tests/synthetic_vault.py) | Temporary project roots; never production data |

Also consult [architecture](docs/ARCHITECTURE.md) and
[skill maintenance](docs/SELF_CONTEXT_SKILL_MAINTENANCE.md) when changing policy
loading or behavior. The historical build plan is not the current task list.

## Baseline evidence and limits

The analysis ran `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_repo.py`:
224 tests passed, none skipped, in approximately 31.7 seconds. The worktree was
clean before this handoff was added. Runtime code and the production vault were
not changed.

### Synthetic timing baseline

The benchmark used `build_synthetic_vault()` plus additional Career pages.
Each added page had a distinct numbered title and a body containing 15 copies
of this fictional sentence pair:

> John Doe delivered release planning for MyContext Systems. Evidence includes
> careful technical decisions and team coordination.

Catalogs were synchronized before timing. Query preparation used Career scope,
anchors `delivery planning`, `technical decisions`, and `team coordination`,
and complete evidence. A commit appended a small fictional paragraph to one
page and supplied an ingestion log entry. Each run used a temporary project.

| Measurement | Fixture + 100 pages | Fixture + 500 pages |
| --- | ---: | ---: |
| Query preparation, median of 3 | 0.059 s | 0.264 s |
| Byte-equivalent proposal, single run | 0.384 s | 1.366 s |
| One-page commit, median of 3 | 0.657 s | 2.698 s |
| Serialized query packet, approximate | 26.3 KB | 26.3 KB |

These were warm-process measurements on the local machine using Python 3.13;
CI targets Python 3.12. They exclude model reasoning, model context loading,
CLI startup, and tool transport. They are observations, not performance targets.
The repeated-body workload is useful for reproducibility, not representative of
every vault. Add heterogeneous and large-source cases before generalizing.

Separate `cProfile` runs identified:

- Four calls to `sync_indexes.synchronize()` and 18 calls to
  `vault_utils.canonical_files()` during one successful update.
- Catalog synchronization, including nested work, consumed about 59% of the
  500-page profiled commit time. Nested cumulative times must not be summed.
- Navigation occupied about a quarter of profiled query preparation; selected
  indexes had all links resolved before output was sliced to the limit.
- The unchanged-proposal path still staged a copy and synchronized catalogs.

The exploratory scripts lived in temporary storage and are not deliverables.
Recreate maintained fixtures and measurements in Step 01 rather than depending
on another machine's temporary files.

### Findings already reproduced

| Finding | Reproduction and observed result | Interpretation |
| --- | --- | --- |
| Stale proposal can replace a newer edit | Read page A, change A independently, submit bytes based on the first read without `expected_snapshot`; commit succeeds and the independent addition is lost | Missing caller precondition, not proof that supplied snapshot checks fail |
| Coverage can lose to additive bonuses | Query 20 distinct terms; one page title contains 19, another page body contains all 20; the 95% match ranked first | Numerical weights do not enforce the documented coverage priority |
| Successor evidence can lose all slots | Three exact-anchor primary matches, one superseded and linked to a nonmatching successor; default three-page evidence allocation contains the primaries and omits the discovered successor | Discovery works; answer evidence needs another read |
| Accent mismatch | Page title `Gestión`, no other matching terms; query `gestion` returns no match | NFKC/casefold does not perform accent folding |
| Cross-language mismatch | Spanish leadership page; English `technical leadership` query does not retrieve it | Expected lexical limitation; interpretation must remain in the semantic layer |

Instruction-loading improvements, improved counterevidence recall, simultaneous
writer safety, and a schema 0.3 design are proposals requiring evaluation, not
measured improvements or completed failure investigations.

## Implementation sequence

### Two-pass scope and status

The original step numbers below remain stable for traceability. Their detailed
checklists describe the full opportunities, including optional extensions.

| Pass | Included work | Status |
| --- | --- | --- |
| 1 | Step 01 regression/benchmark foundation; Step 02 required read-time snapshots; Step 03 bounded navigation; Step 05 consistent coverage-first ordering; Step 06 successor evidence allocation | Complete within the bounded scope below |
| 2 | Step 04 staged ingestion performance; Steps 07–10 vocabulary, instruction/payload efficiency, semantic workflows, and behavioral evaluation; Step 11 schema decision | Not started |

Pass 1 deliberately uses the existing whole-vault snapshot rather than adding a
per-page precondition API. It does not add writer locking, change backup
lifecycles, implement new multi-anchor fusion, include complete linked sources,
or migrate any vault. Those optional extensions require evidence and a scoped
decision in Pass 2. Step 01's larger heterogeneous/long-source and bilingual
evaluation workloads can grow with their owning Pass 2 changes.

Steps 01–10 initially target schema 0.2. Step 11 is a decision experiment, not a
commitment to migrate. Keep independently reviewable changes small.

### Pass 1 implementation receipt

- `prepare_context.py --for-update` captures a canonical snapshot before reading
  context and checks it afterward. Only an unchanged, current vault receives
  `controls.mutation_ready: true` and `controls.expected_snapshot`. Ordinary
  query preparation performs neither whole-vault snapshot scan.
- `ordinary_commit` now requires `expected_snapshot`, including for no-op
  proposals. Existing direct callers must supply the read-time token; omission
  is intentionally rejected before staging. Ingest, checkpoint, initialization,
  query persistence, and the shared skill describe the updated contract.
- Navigation resolves no more than the requested link budget per index and
  reports link/catalog truncation. Maintenance helpers remain exhaustive by
  default. Managed entry parsing uses one bounded lookahead for truncation.
- Direct search and multi-anchor merging share an explicit exact-tier,
  rational coverage, matched-count, secondary-score, and path ordering key.
  `rank_score` remains explanatory but is no longer a standalone sort key.
- Complete evidence prioritizes the furthest visible successor and its
  historical origin over unrelated candidates within the selected set.
  Existing primary successor matches are eligible too. Omitted pages distinguish
  page limits from byte limits; cycle, scope, and depth findings remain visible.
- [Context regression tests](tests/test_context_regressions.py) exercise these
  guarantees with fictional data. Existing ordinary-commit callers/tests now
  supply snapshots. The preparation CLI test covers `--for-update`.
- [Synthetic benchmark](scripts/benchmark_context.py) builds temporary fixtures
  and reports query, mutation-preparation, no-op, and commit timings separately:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/benchmark_context.py --pages 100 500 --repetitions 3
  ```

Validation on 2026-10-03:

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_repo.py`: **241 tests
  passed**, zero skipped, failures, or errors; all seven skill metadata files
  and tracked JSON passed. This includes 17 new context regression tests.
- `git diff --check`: passed. Changed Markdown references and fences were
  checked separately, excluding fictional links inside code examples.
- The optional Skill Creator `quick_validate.py` could not run in the host
  Python because PyYAML is absent; no dependency was installed. The repository's
  own skill-metadata validation passed.
- No production-vault writes, migration, branch creation, commit, push, or
  external API calls were performed. Runtime schema and vertical versions,
  backup lifecycles, the public README, and CI configuration remain unchanged.

Pass 1 benchmark medians on the same local Python 3.13 environment, three runs
per size, without profiling:

| Measurement | Fixture + 100 pages | Fixture + 500 pages |
| --- | ---: | ---: |
| Read-only query preparation | 0.043 s | 0.185 s |
| Mutation preparation including snapshot scans | 0.064 s | 0.273 s |
| No-op commit, preparation excluded | 0.288 s | 1.328 s |
| One-page commit, preparation excluded | 0.707 s | 2.829 s |

Query timings improved relative to the earlier observational baseline; this is
not a controlled end-to-end model latency claim. The stronger deterministic
result is that requesting three navigation links from a 200-link index resolves
exactly three targets, while full maintenance still enumerates all 200. Commit
performance is broadly unchanged and remains Pass 2 work. Mutation preparation
now pays an explicit safety cost that ordinary queries avoid. Packet size was
about 26.9 KB, including new truncation metadata; payload reduction is deferred.

### Step 01 — Establish repeatable regression and measurement fixtures

**Outcome:** subsequent changes have observable correctness and cost baselines.

- Reuse the temporary fixture builder; add controlled workloads for small and
  larger scopes, many index links, long source pages, multiple anchors, and
  unrelated vertical growth.
- Reproduce the five findings above. Add failing-behavior tests alongside their
  fixes; do not leave the canonical repository gate deliberately failing.
- Measure file reads, page parses, link resolutions, traversal, output bytes,
  query/commit latency, and no-op side effects. Keep optional timing/profile
  tooling separate from deterministic test assertions.
- Record environment, repetitions, fixture size, and whether profiling was
  enabled. Do not compare profiled times with unprofiled times as a speedup.
- Preserve existing coverage for one corpus per preparation, fresh state across
  separate preparations, scoped traversal, and lazy linked-source loading.

**Acceptance:** fixtures read no production data; repeated runs are reproducible;
the canonical gate passes; cost counters can explain future improvements.

### Step 02 — Carry read-time preconditions through ingestion

**Outcome:** an agent cannot silently overwrite changes made since its evidence
was read merely because the commit helper captured a later source snapshot.

Relevant symbols: `commit_mutation()`, `_validate_proposal()`,
`snapshot_id()`, and preparation evidence `content_hash`.

- First design the read-to-proposal boundary explicitly. Capturing a snapshot
  only immediately before commit does not protect an earlier read. If using
  the existing whole-vault snapshot, associate it with the planning read and
  detect drift across that read before submission.
- Establish consistent use of the existing `expected_snapshot` mechanism in
  ordinary ingestion and persistence. Decide whether enforcement belongs in
  the API, orchestration, or both; inventory direct callers and tests before
  changing the optional API contract.
- Evaluate expected per-page hashes and expected absence as a later bounded
  API improvement if whole-vault snapshot cost or unrelated edits are material.
  Include pages whose contents informed the proposal, not just write targets.
  A hash is a byte identity check, not semantic confirmation.
- Do not silently retry a rejected proposal. Re-read changed evidence and
  rebuild the semantic proposal before trying again.
- Keep existing detection of changes during staging and around backup creation.
  Do not claim full simultaneous-writer or process-crash safety from optimistic
  preconditions. Writer serialization and crash recovery need separate design
  and failure tests if pursued.

**Acceptance:** the stale-read reproduction rejects without active writes,
backups, or log churn at the precondition boundary; matching preconditions
succeed; stale creates reject; existing staging drift and rollback tests pass.
Document whole-vault false conflicts or any other remaining limitations.

### Step 03 — Bound navigation work before resolving links

**Outcome:** a 20-entry query navigation budget does not resolve every link in a
large index.

- Inspect `_navigation_record()`, `markdown_link_records()`, and
  `sync_indexes.managed_entries()`.
- Add bounded iteration or an equivalent narrow query path. Apply the budget
  before expensive filesystem resolution. Reading index text may still be
  necessary; distinguish bytes scanned from targets resolved.
- Preserve complete enumeration for lint and maintenance. Do not globally
  truncate a helper whose other consumers expect exhaustive results.
- Preserve ordering, path safety, malformed-input handling, and useful manual
  navigation outside generated blocks. Expose truncation explicitly.

**Acceptance:** index growth beyond the limit does not increase resolved-target
count proportionally; zero limits perform no unnecessary resolution; existing
navigation semantics remain covered; full lint still sees links beyond the cap.

### Step 04 — Reuse staged ingestion data without weakening validation

**Outcome:** reduce repeated parsing and traversal in one commit.

- Profile `commit_mutation()`, `_validate_state()`, `canonical_bytes()`,
  `snapshot_id()`, and `synchronize(records=...)` before editing.
- Reuse parsed page records for the same immutable stage. Invalidate/rebuild
  affected records after semantic writes, activations, index changes, or log
  changes as appropriate. Do not reuse staged assumptions for independently
  mutable active files.
- Separate checks that establish different guarantees from repeated reads of
  identical state. Consolidate only the latter. Preserve independent active
  validation and the checks that detect concurrent drift.
- Consider earlier no-op detection only after defining behavior for catalog
  drift, activation, invalid controls, and malformed proposals. Matching supplied
  page bytes alone is not sufficient to prove the whole operation is a no-op.
- Inspect full-tree copying, including excluded viewer state, as a secondary
  candidate. Any copy-policy change must preserve custom content and filesystem
  safety; do not introduce hard links that allow stage writes to alter originals.

**Acceptance:** measured redundant parses/enumerations decrease; successful
receipts, resulting bytes, backups, index text, activation, and log behavior
remain correct; injected replacement, active-validation, and final-backup
failures still roll back. Retain fresh active-state reads where required.

### Step 05 — Make ranking priorities explicit

**Outcome:** documented priority rules cannot be accidentally overturned by
secondary bonuses.

- Inspect `_score_record()`, `_search_corpus()`, and
  `_merge_search_results()` together. Changing only the direct search sort while
  the merger still sorts by the old scalar would leave inconsistent behavior.
- Define exact ID/title/alias priority, then non-exact coverage, then secondary
  field/phrase/proximity preferences, status adjustments, and stable path ties.
  Use an explicit ordering key or another demonstrably invariant representation.
- Preserve explainable match metadata. Decide how `rank_score` remains useful
  without falsely claiming to be confidence or the sole ordering key.
- Reproduce the 20-term case with `alpha beta gamma delta epsilon zeta eta
  theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon`; put the
  first 19 in one title and all 20 in another page's body.
- Evaluate multi-anchor fusion separately. Alternative names are not independent
  evidence, while facets of a comparison may need coverage across distinct
  results. Do not introduce anchor-count bonuses without that distinction.

**Acceptance:** full coverage wins within the intended non-exact tier; exact
lookups, short queries, historical visibility, review visibility, source opt-in,
contextual filtering, and deterministic ties remain correct. Direct search and
prepared packets use compatible ordering and explanations.

### Step 06 — Allocate complete evidence to answer dependencies

**Outcome:** the first packet more often includes the evidence needed to answer
accurately, within explicit limits.

- Inspect `_select_complete_evidence()` and successor traversal. Reproduce with
  exact anchors `Uniqueanchor0`, `Uniqueanchor1`, and `Uniqueanchor2`; make the
  first page superseded with `superseded_by: new.md`. The successor must contain
  none of those anchors. Set result and evidence limits to three.
- Define a bounded allocation policy for relevant predecessor/successor pairs.
  Do not silently change match ordering or discard historical matches. Preserve
  chain, cycle, missing-target, scope, depth, and count explanations.
- Distinguish page-count exhaustion, byte-budget exhaustion, oversize pages,
  and unreadable pages. Metadata-only evidence is not a completed page read.
- Evaluate complete linked-source inclusion only when requested and relevant.
  Keep sources distinct from successors; do not turn provenance expansion into
  a source dump or assume that a source verifies a claim.
- Oversized evidence must remain explicitly omitted or explicitly partial under
  a separately designed contract. Never silently truncate a complete-page field.

**Acceptance:** successor evidence is available under the selected policy or
has an accurate explicit omission; evidence limits hold; no unrelated expansion
occurs; unchanged read-only and path-safety guarantees pass. Evaluate historical
questions as well as current-state questions before choosing a default policy.

### Step 07 — Improve bounded vocabulary recovery

**Outcome:** reduce avoidable misses from accents, alternate names, and language
differences while retaining transparent lexical mechanics.

- Keep strict identity and alias matching distinct from accent-folded lexical
  fallback. Do not change global normalization used for identity collisions,
  deduplication, or schema checks without auditing those consumers.
- Test `Gestión` versus `gestion`, already accented queries, and distinct names
  that collapse under folding. Preserve original text and expose match behavior.
- In the Query procedure, evaluate a bounded retry with useful aliases,
  paraphrases, or translations when initial evidence is insufficient. Ownership
  and cross-language interpretation stay with the model.
- Do not automatically persist generated aliases, add a multilingual NLP
  dependency, or search every vertical after a miss.

**Acceptance:** accent fallback improves the fixture without breaking exact
identity ordering; bilingual behavior evals improve or expose honest gaps;
retry counts and scope remain bounded; a no-match result never implies that
the underlying personal fact is false.

### Step 08 — Reduce unnecessary instruction and packet loading

**Outcome:** ordinary lookups load fewer irrelevant instructions and repeated
metadata without losing guardrails.

- At baseline, `query.md` has approximately 4,842 words covering retrieval,
  contextual reasoning, receipts, persistence, and task packets. Measure actual
  loaded instructions/tool output before assuming all of it is always loaded.
- Use the skill-creator workflow to consider progressive loading: a compact
  mandatory query contract with detailed modes loaded at their decision points.
  Keep links valid and trigger/routing behavior intact across advisor packs.
- Retain immediately relevant provenance, freshness, contradiction, compatibility,
  scope, and read-only rules. Do not replace those with vague pointers.
- Evaluate duplicate metadata across navigation, matches, and full evidence.
  Preserve consumer-required fields and content identity. An overall packet
  budget must report exclusions and preserve runtime blockers and evidence
  qualification; the current evidence byte budget is not a whole-packet cap.
- Measure serialized bytes or explicitly labeled token estimates, tool rounds,
  and answer support. Fewer words alone is not an acceptance criterion.

**Acceptance:** routine lookup payload decreases on fixed cases; advanced modes
remain discoverable; no unsupported facts, silent omissions, writes, or routing
regressions appear in behavioral evaluations.

### Step 09 — Strengthen semantic ingestion and counterevidence retrieval

**Outcome:** more consistent corrections, re-ingestion, partial confirmation,
and advice grounded in relevant qualifications.

- Refine the owning procedures rather than inventing another lifecycle. During
  ingestion, compare what is new, repeated, corrected, narrowed, or superseded;
  what evidence supports it; and which confirmed scope remains applicable.
- Keep that comparison transient. Do not create an automatic reasoning log,
  change ledger, context summary, or improvement queue.
- Prefer useful sections and precise source links for coherent larger pages.
  Split only where independent confirmation, freshness, or subject identity
  warrants it. Do not mandate one page per statement.
- Preserve sources and exceptions. Repeated input must not reset review,
  verification, assertion kind, or freshness, or create duplicate source pages
  merely because wording changed.
- For contextual decisions where qualifications could change the conclusion,
  evaluate one bounded counterevidence pass through relevant explicit links or
  a justified review/owner scope. Never load every review item by default.
- Keep a proposal distinct from a commitment, exposure from demonstrated
  knowledge, reported statements from confirmation, and recommendations from
  personal facts. Follow each vertical's existing procedure.

**Acceptance:** synthetic behavioral cases demonstrate correct owner selection,
no-op handling, partial-confirmation scope, preserved competing evidence, and
useful counterevidence. Added procedure text must address an observed behavior
gap rather than repeat rules that already work.

### Step 10 — Add repeatable semantic evaluation outside the fast gate

**Outcome:** distinguish mechanically valid operations from correct agent use.

- Existing eval JSON contains prompts and expectations; the canonical validator
  checks structure and repository consistency, not full model execution of those
  scenarios. Do not report parsed evals as passed behavioral evaluations.
- Maintain a small fictional case set covering exact/paraphrased/bilingual
  retrieval, successors, stale decisive context, corrections, contradiction,
  partial confirmation, repeated ingestion, and checkpoint rejection of
  assistant-generated suggestions.
- Define expected evidence paths, forbidden claims/writes, permissible changes,
  and valid no-op outcomes. Allow multiple semantically correct phrasings.
- Measure evidence recall within the result budget, answer support, unnecessary
  reads, duplicate creation, metadata preservation, and unintended writes.
- Use disposable vaults and before/after byte comparisons. Record model,
  harness, version/settings, repetitions, and qualitative adjudication limits.
- External model/API execution requires authorization. This evaluation workflow
  must not become a SelfContext runtime, mandatory service, or automatic CI API
  dependency. Deterministic fixture checks can remain in the canonical gate.

**Acceptance:** another agent can rerun the specified cases and distinguish
mechanical checks, model observations, and human review. Establish these cases
early enough to evaluate Steps 07–09, even if the complete runner lands later.

### Step 11 — Decide whether schema 0.3 earns its migration cost

**Outcome:** an evidence-backed design decision, which may be to stay on 0.2.

The promising areas are temporal validity and scoped confirmation/provenance.
Current shared metadata is page-scoped. Existing prose, sections, optional
metadata, and separate coherent pages may already solve many cases.

- Compare 0.2 representations with fictional cases involving a historical role
  and current availability, two separately confirmed claims on one page, and
  partial supersession. Evaluate retrieval accuracy and authoring burden.
- Consider explicit observation/validity dates, named-section provenance or
  confirmation, and partial supersession only where a demonstrated gap remains.
  No field names, required metadata, or schema change are approved by this plan.
- Keep event/validity time distinct from ingestion, generation, verification,
  and review deadlines. Unknown dates remain unknown; generated timestamps do
  not establish when something became true.
- Avoid a universal claim ledger, relationship graph, mandatory empty metadata,
  or bulk page splitting. Keep Markdown directly useful without a tool.
- If warranted, propose an architecture decision and exact migration contract
  before implementation. Separate deterministic structural migration from
  ambiguous semantic transformations that need review.

**Migration acceptance if separately approved:** preserve all original evidence
and custom content; never infer missing validity dates, extend verification,
resolve contradictions, or silently split meaning. Implement registry edge,
target validation, staged application, recovery and final backups, rollback,
idempotence, and future-version rejection through existing machinery. Test
0.1-to-latest and 0.2-to-latest paths as applicable, malformed states, and injected
failures. Refer to the existing migration lifecycle rather than ordinary-commit
cleanup rules where their backup retention differs.

Because the runtime is latest-first, do not switch `LATEST_SUPPORTED_SCHEMA`
until the complete migration and contract path is available and validated.
Obtain explicit authorization before applying any migration to the user's vault.

## Validation and handoff protocol for each implemented slice

Use focused tests while editing. For example, from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_ordinary_commit.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_prepare_context.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_search_vault.py'
```

Select the commands relevant to the change; do not run all three mechanically.
Before declaring a slice complete, run the canonical gate and inspect the diff:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_repo.py
git diff --check
git status --short
```

The validation count may grow from the recorded 224. Passing structural tests
does not establish model behavior, live acceptance, simultaneous-writer safety,
or migration correctness beyond the exercised cases.

Every implementation handoff should report:

1. Approved step and actual scope, with changed files and intentional exclusions.
2. Behavior before/after and the reproduced case it addresses.
3. Focused tests, canonical validation, and performance/behavior measurements.
4. Preserved safety guarantees, unresolved risks, and untested behavior.
5. Any compatibility, contract, or migration implications.
6. The next incomplete step, without silently starting it.

The next implementation work is Pass 2, beginning with Step 04 after the user
authorizes that pass. Preserve the separation between improving the project and
modifying the user's durable personal context throughout.
