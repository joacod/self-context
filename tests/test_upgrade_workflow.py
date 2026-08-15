from __future__ import annotations

import datetime as date
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
TESTS = ROOT / "tests"
for import_path in (SCRIPTS, TESTS):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import backup_vault  # type: ignore  # noqa: E402
import lint_vault  # type: ignore  # noqa: E402
import migrate_vault  # type: ignore  # noqa: E402
import sync_indexes  # type: ignore  # noqa: E402
import vault_utils  # type: ignore  # noqa: E402
from synthetic_vault import build_synthetic_vault, tree_snapshot  # noqa: E402


UPGRADE = ROOT / ".agents/skills/self-context/references/upgrade.md"
SKILL = ROOT / ".agents/skills/self-context/SKILL.md"


class UpgradeWorkflowTests(unittest.TestCase):
    """Exercise upgrade's observable seams without adding a second runtime.

    The user-facing operation is a skill procedure, while deterministic helpers
    remain the owners of schema, catalog, and validation behavior. These tests
    therefore compose those existing seams and assert the documented phase
    boundaries against fictional temporary vaults.
    """

    @staticmethod
    def backup_paths(project: Path) -> list[Path]:
        return sorted((project / "backups").glob("vault-*.zip")) if (project / "backups").exists() else []

    @staticmethod
    def assess(vault: Path) -> dict[str, object]:
        """Read-only Phase A assessment used by the procedure contract tests."""

        migration = migrate_vault.plan_migration(vault, target="latest")
        ordinary_errors, ordinary_warnings = lint_vault.lint_vault(
            vault, date.date(2026, 8, 15)
        )
        deep = lint_vault.deep_lint_vault(vault, date.date(2026, 8, 15))
        catalogs = sync_indexes.synchronize(vault, write=False)
        return {
            "migration": migration,
            "ordinary_errors": ordinary_errors,
            "ordinary_warnings": ordinary_warnings,
            "deep": deep,
            "catalogs": catalogs,
        }

    def test_current_vault_is_a_no_op_without_backup_or_file_churn(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            before = tree_snapshot(project)

            first = self.assess(vault)
            second = self.assess(vault)

            for result in (first, second):
                migration = result["migration"]
                self.assertTrue(migration["already_current"])
                self.assertFalse(migration["migration_needed"])
                self.assertEqual(result["ordinary_errors"], [])
                self.assertEqual(result["deep"]["severity_counts"]["error"], 0)
                self.assertEqual(result["catalogs"]["changed"], [])
            self.assertEqual(before, tree_snapshot(project))
            self.assertEqual(self.backup_paths(project), [])
            self.assertFalse((vault / "review" / "deep-reviews").exists())

    def test_schema_phase_uses_migration_then_reorients_active_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.1")
            before_page = (vault / "career" / "harbor-launch.md").read_bytes()
            phases: list[str] = []

            plan = migrate_vault.plan_migration(vault, target="latest")
            self.assertEqual(plan["migration_path"], ["0.1", "0.2"])
            phases.append("assess")
            result = migrate_vault.apply_migration(vault, target="latest")
            self.assertEqual(result["status"], "success")
            phases.append("schema")

            # This re-read is the seam that prevents pre-migration inventories
            # from being used for contract/adoption decisions.
            schema = vault_utils.parse_schema(vault)
            phases.append("reorient")
            self.assertEqual(schema["version"], (0, 2))
            self.assertEqual(
                migrate_vault.plan_migration(vault, target="latest")["already_current"],
                True,
            )
            phases.append("semantic-assessment")
            self.assertEqual(phases, ["assess", "schema", "reorient", "semantic-assessment"])
            self.assertEqual(before_page, (vault / "career" / "harbor-launch.md").read_bytes())
            self.assertEqual(len(self.backup_paths(project)), 2)

    def test_ambiguous_history_is_preserved_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            review_page = vault / "review" / "maintenance-candidate.md"
            before = review_page.read_bytes()

            assessment = self.assess(vault)

            self.assertEqual(before, review_page.read_bytes())
            self.assertTrue(
                any(
                    item.get("path") == "review/maintenance-candidate.md"
                    for item in assessment["deep"]["findings"]
                )
            )
            self.assertEqual(self.backup_paths(project), [])

    def test_older_contract_is_phase_c_work_without_schema_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            schema_path = vault / "SCHEMA.md"
            schema_path.write_text(
                schema_path.read_text(encoding="utf-8").replace("career@1", "career@0", 1),
                encoding="utf-8",
            )

            assessment = self.assess(vault)
            migration = assessment["migration"]
            contract_findings = [
                item
                for item in assessment["deep"]["findings"]
                if item["classification"] == "vertical-contract-update"
            ]
            self.assertTrue(migration["already_current"])
            self.assertTrue(contract_findings)
            self.assertEqual(self.backup_paths(project), [])
            self.assertIn("Phase C: update enabled contracts", UPGRADE.read_text(encoding="utf-8"))

    def test_relevant_historical_vertical_can_be_adopted_without_copying_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            lifecycle = vault / "career" / "harbor-lifecycle.md"
            lifecycle.write_text(
                "---\n"
                "type: concept\n"
                "title: Harbor Initiative Lifecycle\n"
                "description: Fictional project lifecycle evidence for upgrade tests.\n"
                "tags:\n"
                "  - synthetic\n"
                "status: active\n"
                "generated: 2026-08-15\n"
                "verified: null\n"
                "sources: []\n"
                "assertion_kind: user_stated_fact\n"
                "stale_after: null\n"
                "---\n\n"
                "## Initiative lifecycle\n\n"
                "A fictional experiment moved from proposal to a paused prototype.\n",
                encoding="utf-8",
            )
            sync_indexes.synchronize(vault, write=True)
            lifecycle_bytes = lifecycle.read_bytes()

            # This is a synthetic test of the existing deep-maintenance
            # adoption boundary, not a production detector. The upgrade
            # procedure delegates this decision to the owning contract.
            recovery, _ = backup_vault.create_backup(vault)
            schema_path = vault / "SCHEMA.md"
            schema = schema_path.read_text(encoding="utf-8")
            schema_path.write_text(
                schema.replace("vertical_contracts:\n", "vertical_contracts:\n  - ventures@1\n", 1),
                encoding="utf-8",
            )
            ventures = vault / "ventures"
            ventures.mkdir()
            record = next(
                item
                for item in vault_utils.catalog_records(vault_utils.load_vertical_catalog())
                if item["id"] == "ventures"
            )
            (ventures / "index.md").write_text(
                f"# {record['display_name']} Context\n\n{record['ownership']}\n\n"
                "<!-- selfcontext:catalog:start -->\n<!-- selfcontext:catalog:end -->\n",
                encoding="utf-8",
            )
            root_index = vault / "index.md"
            root_index.write_text(
                root_index.read_text(encoding="utf-8")
                + f"- [{record['display_name']} context]({record['index_path']})\n",
                encoding="utf-8",
            )
            moved = ventures / lifecycle.name
            lifecycle.rename(moved)
            synced = sync_indexes.synchronize(vault, write=True)
            self.assertFalse(
                any(item.get("severity") == "error" for item in synced["findings"]),
                synced,
            )
            ordinary_errors, _ = lint_vault.lint_vault(vault, date.date(2026, 8, 15))
            deep = lint_vault.deep_lint_vault(vault, date.date(2026, 8, 15))
            self.assertEqual(ordinary_errors, [])
            self.assertEqual(deep["severity_counts"]["error"], 0)
            final, _ = backup_vault.create_backup(vault)

            self.assertTrue(Path(recovery).is_file())
            self.assertTrue(Path(final).is_file())
            self.assertEqual(
                {path.resolve() for path in self.backup_paths(project)},
                {Path(recovery).resolve(), Path(final).resolve()},
            )
            self.assertEqual(lifecycle_bytes, moved.read_bytes())
            self.assertFalse(lifecycle.exists())
            self.assertTrue((vault / "career" / "harbor-launch.md").is_file())
            self.assertIn("ventures@1", schema_path.read_text(encoding="utf-8"))
            self.assertIn("ventures/index.md", root_index.read_text(encoding="utf-8"))

    def test_selective_adoption_contract_leaves_irrelevant_verticals_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            catalog = vault_utils.load_vertical_catalog()
            records = {
                str(record["id"]): record
                for record in vault_utils.catalog_records(catalog)
            }
            schema = vault_utils.parse_schema(vault)
            enabled = {str(entry["id"]) for entry in schema["contract_entries"]}

            self.assertIn("career", enabled)
            self.assertNotIn("media", enabled)
            self.assertNotIn("ventures", enabled)
            self.assertFalse((vault / "media").exists())
            self.assertFalse((vault / "ventures").exists())

            # A disabled area remains absent when there is no durable reason to
            # adopt it. The catalog supplies the candidate set; no detector is
            # added here or to the production skill.
            for identifier in ("media", "ventures"):
                self.assertIn(identifier, records)
                self.assertNotIn(identifier, enabled)
            self.assertEqual(self.backup_paths(project), [])

    def test_future_schema_or_contract_blocks_before_upgrade_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            before = tree_snapshot(project)

            schema_path = vault / "SCHEMA.md"
            schema_path.write_text(
                schema_path.read_text(encoding="utf-8").replace(
                    "schema_version: 0.2", "schema_version: 0.3", 1
                ),
                encoding="utf-8",
            )
            future_schema = migrate_vault.plan_migration(vault, target="latest")
            self.assertFalse(future_schema["plan_valid"])
            self.assertTrue(
                any(item["classification"] == "future-schema" for item in future_schema["findings"])
            )
            self.assertEqual(self.backup_paths(project), [])

            # Restore the supported schema, then exercise the separate future
            # contract blocker without allowing either operation to write.
            schema_path.write_text(
                schema_path.read_text(encoding="utf-8").replace(
                    "schema_version: 0.3", "schema_version: 0.2", 1
                ).replace("career@1", "career@2", 1),
                encoding="utf-8",
            )
            future_contract = migrate_vault.plan_migration(vault, target="latest")
            self.assertFalse(future_contract["plan_valid"])
            self.assertTrue(
                any(
                    item["classification"] == "schema-contract"
                    and "exact available version" in item["message"]
                    for item in future_contract["findings"]
                )
            )
            self.assertEqual(self.backup_paths(project), [])
            self.assertNotEqual(before, tree_snapshot(project))  # fixture mutation only

    def test_procedure_preserves_phase_order_safety_and_idempotence_contract(self) -> None:
        procedure = UPGRADE.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        headings = [
            "## Phase A: orient and assess",
            "## Phase B: resolve schema",
            "## Phase C: update enabled contracts",
            "## Phase D: assess and apply selective adoption",
            "## Phase E: bounded semantic maintenance",
            "## Phase F: synchronize and validate",
        ]
        positions = [procedure.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("re-orient", procedure.casefold())
        self.assertIn("Your vault is already current. No files changed.", procedure)
        self.assertIn("Do not create redundant orchestration backups", procedure)
        self.assertIn("human_decision", procedure)
        self.assertIn("upgrade vault latest", skill.casefold())
        self.assertIn("migrate vault latest", skill.casefold())
        self.assertIn("deep review vault", skill.casefold())
        self.assertIn("deep update vault", skill.casefold())


if __name__ == "__main__":
    unittest.main()
