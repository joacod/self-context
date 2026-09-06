# Deep Maintenance Release Checklist

Use this checklist from the repository root. All checks must use temporary
synthetic fixtures or copies of those fixtures. Do not access the ignored real
`vault/` for release validation.

## Repository gates

- [ ] Run the canonical dependency-free validation:
  `python3 scripts/validate_repo.py`. This includes Agent Skill metadata,
  tracked JSON validation, full unittest discovery and execution, and repository
  consistency checks; do not repeat them as separate release gates.
- [ ] Confirm the single Ubuntu Python 3.12 CI job remains green.

## Focused troubleshooting

These optional commands isolate failures or provide feedback while editing.
Their tests already run through the canonical gate:

| Behavior | Command |
| --- | --- |
| Read-only filesystem preservation, migration, catalog refresh, retrieval, backups, and rollback | `python3 -m unittest tests.test_deep_maintenance_integration` |
| Migration targets, dry-run/write behavior, no-ops, and failure recovery | `python3 -m unittest tests.test_migrate_vault` |
| Upgrade helper compatibility, preserved history, and validation of changed controls | `python3 -m unittest tests.test_upgrade_workflow` |
| Catalog idempotence and search ranking | `python3 -m unittest tests.test_sync_indexes tests.test_search_vault` |

## Skill behavior review

The Python tests exercise deterministic helpers. They do not prove that an
agent follows natural-language authorization, chooses the right vertical, or
orders upgrade phases correctly. Parsing eval JSON also does not execute an
eval.

When changing skill behavior, exercise the relevant synthetic cases in the
[SelfContext eval corpus](../.agents/skills/self-context/evals/evals.json):

- [ ] Confirm migration assessment stays read-only, authorized migration requires
  a write-ready plan, and other operations do not migrate implicitly.
- [ ] Confirm upgrade assesses and reorients before semantic decisions, adopts
  only justified verticals, and preserves ambiguity.
- [ ] Confirm deep review and task packets remain ephemeral unless retention is
  explicitly requested, and retained output remains derived.

## Final inspection

- [ ] Confirm no production schema 0.3 was introduced; test-only multi-step
  registry labels remain injectable unit-test fixtures only.
- [ ] Inspect the private-content boundary with `git diff --check` and
  `git diff --stat`; no real vault paths, titles, bodies, findings, or backup
  archives may appear in the tracked diff.
- [ ] Confirm generated reports and task packets remain derived output and do
  not become evidence.
- [ ] Run `git status --short` and confirm only intended tracked files are
  present; ignored `vault/`, `backups/`, and transient test state are absent
  from the deliverable.
