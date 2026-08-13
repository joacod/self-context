import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
SCRIPT = SCRIPTS / "migrate_vault.py"
LINT = SCRIPTS / "lint_vault.py"
SYNC = SCRIPTS / "sync_indexes.py"


PAGE = """---
type: concept
id: synthetic-career-page
title: Synthetic Career Page
description: Synthetic durable career evidence.
tags:
  - synthetic
status: active
generated: 2026-08-12
verified: null
sources: []
assertion_kind: user_stated_fact
stale_after: null
---

Synthetic personal page body.
"""


class MigrateVaultTests(unittest.TestCase):
    def migration_module(self):
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        return importlib.import_module("migrate_vault")

    def make_legacy(
        self,
        root: Path,
        *,
        career: bool = True,
        career_index: bool = True,
        career_root_link: bool = True,
        career_page: bool = False,
        custom_area: str = "custom-archive",
    ) -> Path:
        vault = root / "vault"
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory).mkdir(parents=True)
        if career:
            (vault / "career").mkdir()
        if custom_area:
            (vault / custom_area).mkdir()

        (vault / "SCHEMA.md").write_text(
            "# Legacy\n\nschema_version: 0.1\n", encoding="utf-8"
        )
        links = [
            "SCHEMA.md",
            "- [Core](core/index.md)",
            "- [Review](review/index.md)",
            "- [Sources](sources/index.md)",
            "- [Derived](derived/index.md)",
        ]
        if career and career_root_link:
            links.append("- [Career](career/index.md)")
        (vault / "index.md").write_text(
            "# Legacy\n\n" + "\n".join(links) + "\n", encoding="utf-8"
        )
        (vault / "log.md").write_text("# Log\n", encoding="utf-8")
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory / "index.md").write_text(
                f"# {directory}\n", encoding="utf-8"
            )
        if career and career_index:
            (vault / "career" / "index.md").write_text(
                "# Career\n", encoding="utf-8"
            )
        if career and career_page:
            (vault / "career" / "evidence.md").write_text(PAGE, encoding="utf-8")
        if custom_area:
            (vault / custom_area / "historical.md").write_text(
                "custom page that must remain untouched\n", encoding="utf-8"
            )
        return vault

    def run_migration(self, vault: Path, mode: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), mode, "--format", "json", str(vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_lint(self, vault: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(LINT), *args, str(vault)],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )

    def run_sync(self, vault: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SYNC), "--check", "--format", "json", str(vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def file_bytes(self, vault: Path) -> dict[str, bytes]:
        return {
            path.relative_to(vault).as_posix(): path.read_bytes()
            for path in vault.rglob("*")
            if path.is_file()
        }

    def backup_files(self, root: Path) -> list[Path]:
        return sorted((root / "backups").glob("vault-*.zip")) if (root / "backups").exists() else []

    def test_check_is_read_only_reports_plan_and_custom_area(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            before = self.file_bytes(vault)
            result = self.run_migration(vault, "--check")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["from_schema"], "0.1")
            self.assertEqual(report["to_schema"], "0.2")
            self.assertTrue(report["source_snapshot_id"])
            self.assertIn("career", report["inferred_enabled_verticals"])
            self.assertIn("career@1", report["enabled_vertical_contracts"])
            self.assertIn("SCHEMA.md", report["files_to_modify"])
            self.assertIn("log.md", report["files_to_modify"])
            self.assertIn("career/index.md", report["catalog_blocks_to_add_or_synchronize"])
            self.assertTrue(any(item["path"] == "custom-archive/" for item in report["findings"]))
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_well_formed_migration_creates_one_backup_and_exact_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            result = self.run_migration(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "success")
            self.assertIn("schema_version: 0.2", (vault / "SCHEMA.md").read_text())
            self.assertIn("- career@1", (vault / "SCHEMA.md").read_text())
            self.assertEqual(len(self.backup_files(root)), 1)
            self.assertTrue(Path(report["backup"]).is_file())
            self.assertIn("migrate_schema_0_1_to_0_2", (vault / "log.md").read_text())
            self.assertTrue((vault / "custom-archive" / "historical.md").is_file())

    def test_inferred_vertical_with_existing_index_is_not_created_again(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_legacy(Path(temporary))
            plan = self.migration_module().plan_migration(vault)
            self.assertEqual(plan["enabled_vertical_contracts"], ["career@1"])
            self.assertEqual(plan["missing_vertical_indexes"], [])
            self.assertNotIn("career/index.md", plan["files_to_create"])

    def test_missing_vertical_index_is_control_metadata_with_marker_and_no_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_index=False, career_page=True)
            result = self.run_migration(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            index = vault / "career" / "index.md"
            self.assertTrue(index.is_file())
            text = index.read_text(encoding="utf-8")
            self.assertIn("# Career Context", text)
            self.assertIn("<!-- selfcontext:catalog:start -->", text)
            self.assertIn("<!-- selfcontext:catalog:end -->", text)
            self.assertNotIn("placeholder", text.casefold())
            self.assertEqual(
                sorted((vault / "career").glob("*.md")),
                sorted([vault / "career" / "index.md", vault / "career" / "evidence.md"]),
            )
            deep = self.run_lint(vault, "--deep", "--format", "json")
            self.assertEqual(deep.returncode, 0, deep.stdout + deep.stderr)

    def test_missing_root_link_is_added_for_inferred_vertical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_legacy(Path(temporary), career_root_link=False)
            result = self.run_migration(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            root_text = (vault / "index.md").read_text(encoding="utf-8")
            self.assertIn("[Career context](career/index.md)", root_text)

    def test_custom_area_and_personal_page_bytes_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_page=True)
            before_page = (vault / "career" / "evidence.md").read_bytes()
            before_custom = (vault / "custom-archive" / "historical.md").read_bytes()
            result = self.run_migration(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(before_page, (vault / "career" / "evidence.md").read_bytes())
            self.assertEqual(before_custom, (vault / "custom-archive" / "historical.md").read_bytes())
            report = json.loads(result.stdout)
            self.assertIn("career/evidence.md", report["personal_pages_preserved"])
            self.assertIn("custom-archive", report["custom_areas_preserved"])

    def test_ambiguous_known_looking_area_remains_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career=False, custom_area="career-notes")
            before = self.file_bytes(vault)
            result = self.run_migration(vault, "--write")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertTrue(report["ambiguous_vertical_findings"])
            self.assertFalse(report["write_ready"])
            self.assertNotIn("career@1", report["enabled_vertical_contracts"])
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_source_snapshot_drift_stops_before_backup(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            plan = module.plan_migration(vault)
            (vault / "log.md").write_text("# changed before write\n", encoding="utf-8")
            with mock.patch.object(module, "plan_migration", return_value=plan):
                result = module.apply_migration(vault)
            self.assertTrue(any(item["classification"] == "snapshot-drift" for item in result["findings"]))
            self.assertEqual(self.backup_files(root), [])
            self.assertEqual((vault / "log.md").read_text(), "# changed before write\n")

    def test_proposed_state_validation_failure_causes_zero_active_writes(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            before = self.file_bytes(vault)
            with mock.patch.object(
                module,
                "_validate_proposed_state",
                return_value={"ok": False, "errors": [{"path": "SCHEMA.md", "message": "injected proposed failure"}]},
            ):
                result = module.apply_migration(vault)
            self.assertNotEqual(result.get("status"), "success")
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_backup_failure_causes_zero_active_writes(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            before = self.file_bytes(vault)
            with mock.patch.object(
                module.backup_vault,
                "create_backup",
                side_effect=module.backup_vault.BackupError("injected backup failure"),
            ):
                result = module.apply_migration(vault)
            self.assertTrue(any(item["classification"] == "backup" for item in result["findings"]))
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_replacement_failure_rolls_back_every_touched_file_and_temp_files(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_index=False, career_page=True)
            before = self.file_bytes(vault)
            original_replace = module.os.replace
            calls = {"count": 0}

            def fail_second(source: str | Path, destination: str | Path) -> None:
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("injected replacement failure")
                original_replace(source, destination)

            original_replace_planned = module._replace_planned_files

            def with_injected_failure(path: Path, updates: dict[str, bytes]) -> dict:
                with mock.patch.object(module.os, "replace", side_effect=fail_second):
                    return original_replace_planned(path, updates)

            with mock.patch.object(module, "_replace_planned_files", side_effect=with_injected_failure):
                result = module.apply_migration(vault)
            self.assertNotEqual(result["status"], "success")
            self.assertEqual(result["rollback"]["status"], "rolled-back")
            self.assertEqual(before, self.file_bytes(vault))
            self.assertFalse(any("migrate-" in path.name for path in vault.rglob(".*")))
            self.assertEqual(len(self.backup_files(root)), 1)

    def test_post_write_validation_failure_rolls_back_new_files_and_changes(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_index=False, career_page=True)
            before = self.file_bytes(vault)
            with mock.patch.object(
                module,
                "_validate_active_state",
                return_value={"ok": False, "errors": [{"path": "SCHEMA.md", "message": "injected lint failure"}]},
            ):
                result = module.apply_migration(vault)
            self.assertNotEqual(result["status"], "success")
            self.assertEqual(result["rollback"]["status"], "rolled-back")
            self.assertEqual(before, self.file_bytes(vault))
            self.assertFalse((vault / "career" / "index.md").exists())
            self.assertFalse(any("migrate-" in path.name for path in vault.rglob(".*")))
            self.assertEqual(len(self.backup_files(root)), 1)

    def test_result_passes_ordinary_deep_lint_and_catalog_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_page=True)
            result = self.run_migration(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            ordinary = self.run_lint(vault)
            deep = self.run_lint(vault, "--deep", "--format", "json")
            sync = self.run_sync(vault)
            self.assertEqual(ordinary.returncode, 0, ordinary.stdout + ordinary.stderr)
            self.assertEqual(deep.returncode, 0, deep.stdout + deep.stderr)
            self.assertEqual(sync.returncode, 0, sync.stdout + sync.stderr)
            self.assertIn("schema_version: 0.2", (vault / "SCHEMA.md").read_text())
            self.assertIn("career@1", json.loads(deep.stdout)["applied_vertical_contracts"])

    def test_dry_run_predicts_write_set_and_second_migration_is_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_index=False, career_page=True)
            check = self.run_migration(vault, "--check")
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            plan = json.loads(check.stdout)
            self.assertEqual(self.backup_files(root), [])
            before = self.file_bytes(vault)
            write = self.run_migration(vault, "--write")
            self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
            report = json.loads(write.stdout)
            self.assertEqual(set(report["changed"]), set(plan["would_change"]))
            self.assertNotEqual(before, self.file_bytes(vault))
            backup_count = len(self.backup_files(root))
            second = self.run_migration(vault, "--write")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            second_report = json.loads(second.stdout)
            self.assertEqual(second_report["status"], "already-migrated")
            self.assertEqual(len(self.backup_files(root)), backup_count)

    def test_migration_log_is_not_duplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            (vault / "log.md").write_text(
                "# Log\n\n- operation: migrate_schema_0_1_to_0_2\n", encoding="utf-8"
            )
            result = self.run_migration(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                (vault / "log.md").read_text().count("- operation: migrate_schema_0_1_to_0_2"),
                1,
            )


if __name__ == "__main__":
    unittest.main()
