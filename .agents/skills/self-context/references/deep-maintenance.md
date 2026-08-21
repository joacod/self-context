# Deep Maintenance Protocol

Deep maintenance is an explicit operational mode for a medium or large private
Context Vault. It improves deterministic navigation and surfaces semantic
questions without turning SelfContext into a generic knowledge base. The
private `vault/` remains the source of truth; scripts are read-only or bounded,
deterministic helpers. The advanced `deep review vault`, `deep update vault`,
vertical-adoption, and contract procedures remain available directly; the
latest-first [upgrade procedure](upgrade.md) may delegate bounded phases to
this protocol without duplicating its machinery. Upgrade authorization covers
safe, documented, unambiguous changes in those delegated phases; it does not
silently approve a human semantic decision.

## Terms and authorization

- **Lint** is the ordinary fast structural validator for the current runtime.
  Its explicit migration-source mode can inspect schema 0.1 without treating
  it as current.
- **Deep lint** is a deterministic, broader inventory and integrity pass. It
  checks links, catalogs, reachability, ownership, metadata compatibility,
  freshness relationships, and control metadata. It does not decide whether a
  claim is true.
- **Review** is the ordinary targeted human/agent semantic review requested for
  a bounded issue, such as “review my current role.” It must not become a
  full-vault scan merely because the word “review” appears.
- **Deep review** is an explicit, read-only, full maintenance review. It needs
  no backup and does not mutate the vault, append to `log.md`, create a report,
  or create an operations backlog unless the user explicitly asks to retain
  the report.
- **Deep update** is explicitly mutating. It creates a pre-write recovery
  backup, may apply safe structural changes and explicitly approved semantic
  proposals after snapshot validation, validates the final state, and creates a
  second post-write backup while retaining both. It does not silently migrate an
  old schema; an explicitly requested schema migration delegates to the
  canonical [Migration procedure](migration.md), whose helper owns both
  migration snapshots.
- **Schema migration** is a separate deterministic format/control-file
  operation. Its read-only assessment and authorized write sequence are defined
  entirely in [Migration](migration.md); it never replaces deep review or
  semantic maintenance.

Read-only deep review is the default for “deep review my vault.” Natural
language such as “deep lint,” “deep review,” “deep update,” “adopt the Learning
vertical,” “assess whether my vault should adopt Media / Taste,” or “update my
Writing vertical contract” selects the matching procedure. Ordinary targeted
review remains targeted. Direct deep lint/review/update requires the latest
schema and current applied contracts for ordinary operation; an older schema or
stale contract is reported and routed to `upgrade vault latest` rather than
handled through a legacy branch.

The canonical short forms are:

- `deep review vault`: run the full read-only maintenance review and return its
  bounded plan without a backup or active-vault mutation.
- `deep update vault`: authorize the bounded update after a review plan has been
  examined and approved. Apply safe structural changes and only semantic
  proposals explicitly approved by the user; if no approved plan is available,
  stop and request a reviewed, approved plan before mutating.

Run `deep review vault` before `deep update vault`. The update shorthand is an
authorization for the existing deep-update procedure, not permission to invent
facts, approve semantic proposals implicitly, or rerun schema migration.

Never treat model confidence as verification. Deep maintenance never resolves
contradictions, changes goals or preferences, promotes inferences, deletes or
redacts context, infers sensitive third-party information, or enables a
vertical solely because it is available.

## Available, enabled, and applied contracts

The repository catalog lists **available verticals**: verticals implemented by
this repository and their current contract versions, including Ventures /
Projects. A private vault has an **enabled vertical** in schema 0.2 only when
`SCHEMA.md` records one applied `vertical@version` entry and its area, index,
and root link are present. The
**applied contract version** is the exact version recorded by that vault.
Schema 0.1 has no contract markers; existing vertical areas are legacy
structure, not silently converted contracts. Availability never implies
adoption.

Compare an applied version with the catalog's available version as follows:

- equal: structurally valid and current; no update finding;
- older: a recognized upgrade source; inspect its documented migration, but
  block ordinary current semantic operation until `upgrade vault latest`
  applies a complete safe path;
- newer: error because the current repository cannot safely interpret a future
  contract and must not downgrade or guess.

Unknown vertical IDs, invalid/unknown versions, and duplicate applied entries
for one vertical ID are errors. Preserve their raw values for reporting rather
than deleting or coercing them. Duplicate detection is by ID, so both
`writing@1` plus `writing@1` and `writing@1` plus `writing@2` are invalid. An
available but disabled vertical is not a missing-contract finding.

The catalog is `.agents/skills/self-context/references/verticals.json`; its
paths are canonical relative to the installed project skill. It currently
lists Career, Learning, Writing, Relationships, Media / Taste, and Ventures /
Projects. Detailed rules stay in each procedure, whose small contract header
must match its catalog record. An available but absent vertical is empty for
read-only retrieval and does not cause file creation.

## Deep review phases

### A. Preflight

For this explicit broad maintenance operation, orient from `SCHEMA.md`, the
root index, the bounded recent-log view, and the enabled vertical indexes as
its preflight requires. Run ordinary lint, then deep lint in JSON mode. Record the
snapshot ID and detect schema and contract compatibility. A deep-review JSON
report is a compact inventory: it includes schema version, enabled contracts,
page metadata, link/index relationships, findings, and severity counts, but not
complete page bodies.

Each `pages` entry uses stable, metadata-only fields when valid: `path`, `id`,
`title`, `description`, `aliases`, `tags`, `type`, `assertion_kind`, `status`,
the existing lifecycle dates (`generated`, `verified`, `stale_after`, plus any
already-present valid `observed`, `reviewed`, or `updated` dates), `owner_index`,
`vertical`, `content_hash`, `outbound_links`, `inbound_links`, `sources`, and
`source_relationships`. `vertical` is the catalog vertical ID; it is `null` for
shared `core/`, `review/`, `sources/`, and `derived/` areas. Link arrays contain
normalized relative internal targets and are separate from frontmatter
provenance. `sources` preserves valid frontmatter references, while each
`source_relationships` record contains only `original`, `normalized_target`,
`internal`, `external`, `exists`, and `target_kind` (`source`, `derived`, or
another known page type). External existence is left `null`; no source is
labeled authoritative, decisive, true, or otherwise privileged unless durable
metadata explicitly stores that role.

Use this inventory as a deterministic map of evidence files, not as evidence by
itself. First sort and batch pages by `vertical`, `owner_index`, `status`,
assertion kind, tags, and path. Then use the findings and relationships to
choose a bounded semantic pass:

- **Page batching:** begin with the smallest relevant page set rather than
  opening every body. Tags and aliases improve selection, but they are
  retrieval metadata, not new personal claims.
- **Ownership triage:** use `vertical` and `owner_index` to identify the owning
  area and avoid duplicating a page across verticals.
- **Provenance triage:** inspect `source_relationships` and provenance findings
  to locate missing, broken, external, source, and derived pointers. A
  body/context link in `outbound_links` is not a frontmatter source.
- **Stale-source candidates:** use `derived-freshness` findings and their
  linked source path to select candidates for review. A newer timestamp is only
  a review signal; it does not prove material change, decisiveness, error, or
  mandatory regeneration.
- **Index and link triage:** use `inbound_links`, `outbound_links`,
  `index_relationships`, ownership findings, and reachability findings to focus
  navigation checks.

Open full pages, source records, and linked evidence only when this metadata and
the selected question show that their content is needed. Keep the batch bounded
and preserve the distinction between deterministic triggers and semantic
conclusions.

### B. Page-local semantic pass

Review bounded batches by owning vertical. Consider coherent subject and claim
scope, assertion kind, provenance, freshness, historical versus current
meaning, retrieval title/aliases/description/tags, ownership, third-party
privacy, generated feedback sources, and whether derived material remains
visibly derived.

### C. Vertical pass

For each enabled vertical inspect duplicates, competing canonical homes,
contradictions, exceptions, evolution and supersession, unsupported global
patterns, missing meaningful links, stale or unresolved high-impact context,
contract fit, and successful no-change cases.

### D. Cross-vertical pass

Inspect copied facts, stranded cross-domain context, candidate patterns that
must remain observations until confirmed, derived syntheses treated as evidence,
useful missing links, and ownership ambiguity. Do not create link
spam or duplicate evidence.

### E. Contract and adoption pass

For an older applied contract, read only the documented migrations between the
applied and available versions, identify affected evidence, and allow “no
affected evidence.” The update finding is informational until an explicitly
authorized contract update is planned; do not reinterpret an entire vertical
without a migration reason. A newer applied contract is not reviewable as a
safe current contract and remains an error. For a disabled available vertical,
report an adoption candidate only when existing evidence or repeated use cases
provide a concrete durable reason; “vertical not needed” is successful. Do not
create the area during assessment.

### F. Retrieval-readiness pass

Use a small representative set of questions from meaningful recent-log
entries (and `search_log.py` when older history is explicitly relevant), the
deep-review request, and enabled indexes. Evaluate evidence
selection, irrelevant-area dominance, stale/provisional visibility, ownership,
aliases, descriptions, links, and catalog entries. Evaluate selection and
epistemic labels, not exact generated prose.

### G. Plan

Return stable finding IDs with severity, classification, affected files,
evidence/metadata trigger, recommended action, automation class, risk, and
status. Automation classes are `safe_structural`, `semantic_proposal`,
`human_decision`, and `no_change`. Keep successful no-change outcomes
visible. A full-vault review or retained report must not copy page bodies,
source transcripts, snippets, or generated task packets; retain only the bounded
metadata map, paths, findings, decisions, and links needed to explain the
review. `No meaningful update` remains a valid result when the selected
evidence does not change an owning page or decision.

## Retained reports

Create `vault/review/deep-reviews/` only when the user explicitly asks to
retain a deep review or a deep update is being performed. A report is portable
Markdown using existing synthesis metadata and contains a run ID, date, scope,
snapshot ID, schema/contract comparison, completed passes, finding counts,
detailed findings, proposed/applied changes, deferred human decisions, and
validation result. Keep it out of ordinary retrieval by default and avoid
unnecessary sensitive quotations. At most one report for a scope remains
active; older completed reports may be archived with links preserved. Reports
are maintenance artifacts, not personal evidence or a permanent operations
backlog.

## Deep update sequence

1. Rerun deep lint and compare the current snapshot with the reviewed snapshot.
   If it changed, re-evaluate affected findings instead of applying a stale plan.
2. Create one pre-write recovery backup and report/retain its path.
3. Apply safe structural changes first, then explicitly approved semantic
   proposals. Leave human decisions unresolved. Use a default maximum of 25
   personal durable pages per batch unless the user explicitly requests a full
   deterministic migration; control files do not count.
4. Synchronize managed indexes, append one concise deep-update entry to
   `log.md`, update the retained report, and rerun ordinary lint, deep lint, and
   affected retrieval probes. Stop further mutation on failed post-write
   validation.
5. After the final state validates, create one post-write backup, retain it
   alongside the recovery backup, and report both paths. If final backup
   creation fails, stop further writes and keep the recovery archive.
6. State changed, intentionally unchanged, and deferred files.

Safe structural changes include managed index refreshes, unambiguous catalog
entries/dead generated entries, explicitly authorized schema-control migration,
deterministic frontmatter formatting that preserves values, and an unambiguous
link repair supported by a stable ID or exact target. Never automatically set
`verified`, promote an inference, resolve a contradiction, change a goal or
preference, delete/redact context, merge ambiguous pages, infer sensitive
third-party details, or enable a vertical solely because it is available.

## Contract adoption and vertical-contract updates

Assessment is read-only. Adoption and contract updates are mutations and use
the deep-update snapshot/backup rules. Adoption adds only the requested area,
index, exact available contract marker, and root link in a current schema. A
schema 0.1 vault must be migrated/upgraded before any vertical activation; no
legacy area/index/root-link activation is performed. Unrecognized or malformed
schema state stays conservative and does not guess.

It identifies clearly owned existing pages; it moves pages only when ownership
is unambiguous and links can be updated; it leaves ambiguous pages in place as
review findings; and it never creates placeholder personal pages or copies
facts.

A contract update applies only documented vertical-contract migrations after
the currently recorded version. It preserves historical evidence, verification,
provenance, and no-change migrations. A new contract never justifies invented
context, and an older contract is not kept as a permanent alternate runtime
mode. This is not a schema migration; use [Migration](migration.md) for
versioned vault-format changes.

## Task context packets

Task context packets are a Query output, not a maintenance artifact. Follow the
canonical [Query task context packet procedure](query.md#task-context-packets)
for scope, ownership, privacy, ephemeral handling, and optional derived
persistence. Deep maintenance may inspect packet-related retrieval findings,
but it must not create a parallel packet format or storage lifecycle.

## Stabilization validation handoff

The repeatable repository-level evidence for these boundaries is maintained in
[the Deep Maintenance Release Checklist](../../../../docs/DEEP_MAINTENANCE_RELEASE_CHECKLIST.md).
It uses fictional temporary vaults and copied mutation targets; it is a release
validation aid, not a new deep-maintenance runtime or a substitute for the
authorization rules above.
