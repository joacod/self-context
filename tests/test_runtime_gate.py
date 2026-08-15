from __future__ import annotations

import datetime as date
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
TESTS = ROOT / "tests"
import sys

for import_path in (SCRIPTS, TESTS):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import lint_vault  # type: ignore  # noqa: E402
import migrate_vault  # type: ignore  # noqa: E402
import search_vault  # type: ignore  # noqa: E402
import sync_indexes  # type: ignore  # noqa: E402
import vault_utils  # type: ignore  # noqa: E402
from synthetic_vault import backup_paths, build_synthetic_vault, tree_snapshot  # noqa: E402


class RuntimeGateTests(unittest.TestCase):
    def test_current_schema_and_contracts_allow_normal_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")

            compatibility = vault_utils.runtime_compatibility(vault)
            self.assertEqual(compatibility["state"], "current")
            self.assertTrue(compatibility["ok"])

            errors, _ = lint_vault.lint_vault(vault, date.date(2026, 8, 15))
            self.assertEqual(errors, [])
            search = search_vault.search_vault(vault, "Harbor Launch")
            self.assertEqual(search["findings"], [])
            self.assertEqual(search["results"][0]["path"], "career/harbor-launch.md")
            catalogs = sync_indexes.synchronize(vault, write=True)
            self.assertEqual(catalogs["changed"], [])
            self.assertEqual(backup_paths(project), [])

    def test_old_schema_is_a_readable_upgrade_source_but_blocks_current_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.1")
            before = tree_snapshot(project)

            compatibility = vault_utils.runtime_compatibility(vault)
            self.assertEqual(compatibility["state"], "older-supported-schema")
            self.assertTrue(compatibility["requires_upgrade"])
            self.assertIn("upgrade vault latest", compatibility["message"])

            errors, _ = lint_vault.lint_vault(vault, date.date(2026, 8, 15))
            self.assertTrue(any("Legacy SelfContext schema detected: 0.1" in error for error in errors))
            search = search_vault.search_vault(vault, "Harbor Launch")
            self.assertEqual(search["results"], [])
            self.assertIn("upgrade vault latest", search["findings"][0])
            catalogs = sync_indexes.synchronize(vault, write=True)
            self.assertEqual(catalogs["changed"], [])
            self.assertTrue(any(item["classification"] == "runtime-schema" for item in catalogs["findings"]))
            self.assertEqual(before, tree_snapshot(project))
            self.assertEqual(backup_paths(project), [])

    def test_upgrade_migrates_old_schema_before_current_runtime_continues(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.1")
            page_before = (vault / "career" / "harbor-launch.md").read_bytes()

            result = migrate_vault.apply_migration(vault, target="latest")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["migration_path"], ["0.1", "0.2"])
            self.assertEqual(vault_utils.runtime_compatibility(vault)["state"], "current")
            self.assertEqual((vault / "career" / "harbor-launch.md").read_bytes(), page_before)
            self.assertEqual(len(backup_paths(project)), 2)

            search = search_vault.search_vault(vault, "Harbor Launch")
            self.assertEqual(search["results"][0]["path"], "career/harbor-launch.md")
            errors, _ = lint_vault.lint_vault(vault, date.date(2026, 8, 15))
            self.assertEqual(errors, [])

    def test_future_and_malformed_schema_states_never_mutate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for schema_text, expected_state in (
                ("schema_version: 0.3\n", "future-schema"),
                ("schema_version: not-a-version\n", "malformed"),
            ):
                project = root / expected_state
                vault = build_synthetic_vault(project, schema_version="0.2")
                schema = vault / "SCHEMA.md"
                schema.write_text(f"# Synthetic Schema\n\n{schema_text}", encoding="utf-8")
                before = tree_snapshot(project)

                compatibility = vault_utils.runtime_compatibility(vault)
                self.assertEqual(compatibility["state"], expected_state)
                result = sync_indexes.synchronize(vault, write=True)
                self.assertEqual(result["changed"], [])
                self.assertEqual(before, tree_snapshot(project))
                self.assertEqual(backup_paths(project), [])

    def test_contract_currency_is_a_second_latest_first_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for contract, expected_state in (
                ("career@0", "older-contract"),
                ("career@2", "future-contract"),
                ("archive@1", "malformed-contract"),
            ):
                project = root / expected_state
                vault = build_synthetic_vault(project, schema_version="0.2")
                schema = vault / "SCHEMA.md"
                schema.write_text(
                    schema.read_text(encoding="utf-8").replace("career@1", contract, 1),
                    encoding="utf-8",
                )
                before = tree_snapshot(project)

                compatibility = vault_utils.runtime_compatibility(vault)
                self.assertEqual(compatibility["state"], expected_state)
                self.assertFalse(compatibility["ok"])
                result = sync_indexes.synchronize(vault, write=True)
                self.assertEqual(result["changed"], [])
                self.assertEqual(before, tree_snapshot(project))
                self.assertEqual(backup_paths(project), [])

    def test_migration_source_validation_can_inspect_old_schema_without_promising_runtime_support(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary), schema_version="0.1")
            errors, _ = lint_vault.lint_vault(
                vault, date.date(2026, 8, 15), allow_legacy_source=True
            )
            self.assertFalse(any("Legacy SelfContext schema detected: 0.1" in error for error in errors))
            self.assertEqual(
                vault_utils.runtime_compatibility(vault)["state"],
                "older-supported-schema",
            )


if __name__ == "__main__":
    unittest.main()
