# Deep Maintenance Release Checklist

Use this checklist from the repository root. All vault mutations in the smoke
steps must target temporary synthetic fixtures or copied temporary vaults; do
not use the ignored real `vault/` as a mutation target.

## Repository gates

- [ ] Run the canonical dependency-free validation:
  `python3 scripts/validate_repo.py` (including Agent Skill metadata budgets).
- [ ] Run direct unittest discovery:
  `python3 -m unittest discover -s tests -p 'test_*.py'`.
- [ ] Parse every tracked JSON file:
  `python3 scripts/validate_json.py`.
- [ ] Run the repository consistency checks:
  `python3 -m unittest tests.test_repository_consistency`.
- [ ] Confirm the supported CI matrix remains green on Ubuntu Python 3.10,
  Ubuntu Python 3.12, and Windows Python 3.12.

## Synthetic maintenance smoke tests

- [ ] Run the synthetic read-only smoke test and confirm complete byte/file
  preservation, no backup, no log append, no report, no vertical creation,
  no catalog write, and no schema change:
  `python3 -m unittest tests.test_deep_maintenance_integration.DeepMaintenanceIntegrationTests.test_read_only_operations_preserve_complete_synthetic_tree`.
- [ ] Run the copied-vault mutation smoke test and inspect its backup,
  migration, index, lint, search, and task-packet assertions:
  `python3 -m unittest tests.test_deep_maintenance_integration.DeepMaintenanceIntegrationTests.test_migration_copy_creates_recovery_and_final_backups`.
- [ ] Validate first-class migration dry-run and write behavior, including
  target `latest`, explicit `0.2`, helper-owned recovery and final backups,
  post-migration ordinary/deep lint, catalog check, no-op behavior, and rollback
  coverage.
- [ ] Exercise the natural-language migration procedure: assessment requests
  stop after the read-only plan, authorized requests continue only when the
  plan is write-ready, and deep review/deep lint/deep update/vertical-contract
  requests do not migrate implicitly.
- [ ] Run the latest-first upgrade orchestration contract tests and confirm a
  current synthetic vault is a no-op, schema work re-orients before adoption,
  selective vertical adoption preserves ambiguity, and future schema/contract
  states block before mutation:
  `python3 -m unittest tests.test_upgrade_workflow`.
- [ ] Run the catalog refresh/idempotence check and verify a repeated write
  produces no further changes.
- [ ] Run representative search-ranking fixtures and confirm unrelated custom
  content is excluded.
- [ ] Verify the mutation failure path restores or preserves the active copied
  vault and leaves exactly the expected backup.

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
