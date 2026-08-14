# Deep Maintenance Protocol

Deep maintenance is an explicit operational mode for a medium or large private
Context Vault. It improves deterministic navigation and surfaces semantic
questions without turning SelfContext into a generic knowledge base. The
private `vault/` remains the source of truth; scripts are read-only or bounded,
deterministic helpers.

## Terms and authorization

- **Lint** is the ordinary fast structural validator. It is deterministic and
  backward-compatible with schema 0.1.
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
- **Deep update** is explicitly mutating. It may apply safe structural changes
  and explicitly approved semantic proposals only after snapshot validation,
  one pre-write backup, and bounded post-write validation. It does not silently
  migrate an old schema; an explicitly requested schema migration delegates to
  the canonical [Migration procedure](migration.md), whose helper owns the
  single migration backup.
- **Schema migration** is a separate deterministic format/control-file
  operation. Its read-only assessment and authorized write sequence are defined
  entirely in [Migration](migration.md); it never replaces deep review or
  semantic maintenance.

Read-only deep review is the default for “deep review my vault.” Natural
language such as “deep lint,” “deep review,” “deep update,” “adopt the Learning
vertical,” “assess whether my vault should adopt Media / Taste,” or “update my
Writing vertical contract” selects the matching procedure. Ordinary targeted
review remains targeted.

Never treat model confidence as verification. Deep maintenance never resolves
contradictions, changes goals or preferences, promotes inferences, deletes or
redacts context, infers sensitive third-party information, or enables a
vertical solely because it is available.

## Available, enabled, and applied contracts

The repository catalog lists **available verticals**: verticals implemented by
this repository and their current contract versions. A private vault has an
**enabled vertical** in schema 0.2 only when `SCHEMA.md` records one applied
`vertical@version` entry and its area, index, and root link are present. The
**applied contract version** is the exact version recorded by that vault.
Schema 0.1 has no contract markers; existing vertical areas are legacy
structure, not silently converted contracts. Availability never implies
adoption.

Compare an applied version with the catalog's available version as follows:

- equal: structurally valid and current; no update finding;
- older: structurally valid but emit an update-available warning; do not
  automatically migrate, and let deep review inspect documented migrations;
- newer: error because the current repository cannot safely interpret a future
  contract.

Unknown vertical IDs, invalid/unknown versions, and duplicate applied entries
for one vertical ID are errors. Preserve their raw values for reporting rather
than deleting or coercing them. Duplicate detection is by ID, so both
`writing@1` plus `writing@1` and `writing@1` plus `writing@2` are invalid. An
available but disabled vertical is not a missing-contract finding.

The catalog is `.agents/skills/self-context/references/verticals.json`; its
paths are canonical relative to the installed project skill. It currently
lists Career, Learning, Writing, Relationships, and Media / Taste. Detailed
rules stay in each procedure, whose small contract header must match its
catalog record. An available but absent vertical is empty for read-only
retrieval and does not cause file creation.

## Deep review phases

### A. Preflight

Orient from `SCHEMA.md`, the root index, recent log entries, and enabled
vertical indexes. Run ordinary lint, then deep lint in JSON mode. Record the
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

Use a small representative set of questions from meaningful recent log
entries, the deep-review request, and enabled indexes. Evaluate evidence
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
2. Create one pre-write backup and report/retain its path.
3. Apply safe structural changes first, then explicitly approved semantic
   proposals. Leave human decisions unresolved. Use a default maximum of 25
   personal durable pages per batch unless the user explicitly requests a full
   deterministic migration; control files do not count.
4. Synchronize managed indexes and rerun ordinary lint, deep lint, and affected
   retrieval probes. Stop further mutation on failed post-write validation and
   identify the pre-write backup.
5. Append one concise deep-update entry to `log.md` and update the retained
   report. State changed, intentionally unchanged, and deferred files.

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
index, exact available contract marker, and root link. For schema 0.2 first use,
ordinary mutation follows the same rule: create only the required vertical,
record its exact available contract, add the root link, and continue the
original operation after one normal pre-write backup. For schema 0.1 first use,
create only the legacy area/index/root link and preserve schema text without a
contract marker or implicit migration. Unrecognized or malformed schema state
stays conservative and does not guess.

It identifies clearly owned existing pages; it moves pages only when ownership
is unambiguous and links can be updated; it leaves ambiguous pages in place as
review findings; and it never creates placeholder personal pages or copies
facts.

A contract update applies only documented vertical-contract migrations after
the currently recorded version. It preserves historical evidence, verification,
provenance, and no-change migrations. A new contract never justifies invented
context. This is not a schema migration; use [Migration](migration.md) for
versioned vault-format changes.

## Task context packets

A task context packet is ephemeral derived output unless continuity rules and
an explicit retention request justify storing it under `derived/`. It contains
only the smallest relevant material:

- task objective;
- directly supported personal context;
- relevant examples;
- constraints and explicit preferences;
- stale, provisional, or contradictory context;
- unknowns;
- evidence paths; and
- important exclusions.

Do not expose unrelated relationship or other sensitive context merely because
it exists. A packet is not evidence and does not change the owning vertical.
For retained packets, use `type: synthesis`,
`assertion_kind: derived_synthesis`, provenance links, and a clear derived
label.

## Stabilization validation handoff

The repeatable repository-level evidence for these boundaries is maintained in
[the Deep Maintenance Release Checklist](../../../../docs/DEEP_MAINTENANCE_RELEASE_CHECKLIST.md).
It uses fictional temporary vaults and copied mutation targets; it is a release
validation aid, not a new deep-maintenance runtime or a substitute for the
authorization rules above.
