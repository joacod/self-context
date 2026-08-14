import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Mapping
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

    def run_migration(
        self,
        vault: Path,
        mode: str,
        target: str | None = None,
    ) -> subprocess.CompletedProcess:
        command = [sys.executable, str(SCRIPT), mode, "--format", "json"]
        if target is not None:
            command.extend(["--target", target])
        command.append(str(vault))
        return subprocess.run(
            command,
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

    def make_current(self, root: Path) -> Path:
        vault = self.make_legacy(root)
        (vault / "SCHEMA.md").write_text(
            "# Synthetic Current Schema\n\nschema_version: 0.2\n"
            "vertical_contracts:\n  - career@1\n",
            encoding="utf-8",
        )
        return vault

    def make_multi_step_registry(self, module):
        def test_only_planner(stage: Path) -> dict:
            before = module._canonical_bytes(stage)
            updated = before["SCHEMA.md"].replace(
                b"schema_version: 0.2", b"schema_version: test-only-0.3"
            )
            proposed = dict(before)
            proposed["SCHEMA.md"] = updated
            return {
                "status": "planned",
                "write_ready": True,
                "findings": [],
                "_planned_updates": {"SCHEMA.md": updated},
                "_proposed_bytes": proposed,
            }

        def validate(stage: Path) -> dict:
            ok = b"schema_version: test-only-0.3" in (stage / "SCHEMA.md").read_bytes()
            return {
                "ok": ok,
                "snapshot_id": module.snapshot_id(stage),
                "errors": [] if ok else [{"path": "SCHEMA.md", "message": "test schema missing"}],
            }

        def active_validate(stage: Path, plan: dict) -> dict:
            return validate(stage)

        registry = module.MigrationRegistry(
            "test-only-0.3",
            (
                module.MigrationEdge("0.1", "0.2", module._plan_0_1_to_0_2),
                module.MigrationEdge(
                    "0.2",
                    "test-only-0.3",
                    test_only_planner,
                    validator=validate,
                    active_validator=active_validate,
                ),
            ),
        )
        return registry

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

    def test_explicit_target_0_2_and_omitted_target_default_to_latest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            explicit = self.run_migration(vault, "--check", target="0.2")
            self.assertEqual(explicit.returncode, 0, explicit.stdout + explicit.stderr)
            explicit_report = json.loads(explicit.stdout)
            self.assertEqual(explicit_report["current_schema"], "0.1")
            self.assertEqual(explicit_report["target_schema"], "0.2")
            self.assertEqual(explicit_report["migration_path"], ["0.1", "0.2"])
            self.assertEqual(explicit_report["migration_edges"][0]["label"], "0.1->0.2")
            self.assertEqual(explicit_report["latest_supported_schema"], "0.2")

            omitted = self.run_migration(vault, "--check")
            self.assertEqual(omitted.returncode, 0, omitted.stdout + omitted.stderr)
            omitted_report = json.loads(omitted.stdout)
            self.assertEqual(omitted_report["target_schema"], "0.2")
            self.assertEqual(omitted_report["migration_path"], ["0.1", "0.2"])
            self.assertEqual(self.backup_files(root), [])

    def test_already_latest_is_a_no_op_without_backup_or_file_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_current(root)
            before = self.file_bytes(vault)
            result = self.run_migration(vault, "--write", target="latest")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "already-migrated")
            self.assertFalse(report["migration_needed"])
            self.assertTrue(report["already_current"])
            self.assertEqual(report["migration_path"], ["0.2"])
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_migration_helper_owns_exactly_one_backup(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            with mock.patch.object(
                module.backup_vault,
                "create_backup",
                wraps=module.backup_vault.create_backup,
            ) as create_backup:
                result = module.apply_migration(vault, target="latest")
            self.assertEqual(result["status"], "success")
            self.assertEqual(create_backup.call_count, 1)
            self.assertEqual(len(self.backup_files(root)), 1)

    def test_malformed_schema_blocks_before_backup_or_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            (vault / "SCHEMA.md").write_text(
                "# Broken\n\nschema_version: 0.1\nschema_version: 0.1\n",
                encoding="utf-8",
            )
            before = self.file_bytes(vault)
            result = self.run_migration(vault, "--write")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["write_ready"])
            self.assertTrue(any(item["classification"] == "schema" for item in report["findings"]))
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_future_schema_blocks_before_backup_or_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            (vault / "SCHEMA.md").write_text(
                "# Future\n\nschema_version: 0.3\n", encoding="utf-8"
            )
            before = self.file_bytes(vault)
            result = self.run_migration(vault, "--write")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertTrue(any(item["classification"] == "future-schema" for item in report["findings"]))
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_unsupported_target_blocks_before_backup_or_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            before = self.file_bytes(vault)
            result = self.run_migration(vault, "--write", target="0.3")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertTrue(any(item["classification"] == "unsupported-target" for item in report["findings"]))
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_missing_path_blocks_with_an_injected_registry(self) -> None:
        module = self.migration_module()
        noop = lambda stage: {"status": "planned", "write_ready": True, "findings": [], "_proposed_bytes": module._canonical_bytes(stage)}
        registry = module.MigrationRegistry(
            "test-only-0.3",
            (module.MigrationEdge("0.2", "test-only-0.3", noop),),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            before = self.file_bytes(vault)
            result = module.apply_migration(vault, target="test-only-0.3", registry=registry)
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any(item["classification"] == "missing-path" for item in result["findings"]))
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_duplicate_edge_fails_registry_validation(self) -> None:
        module = self.migration_module()
        noop = lambda stage: {}
        registry = module.MigrationRegistry(
            "0.2",
            (
                module.MigrationEdge("0.1", "0.2", noop, name="first"),
                module.MigrationEdge("0.1", "0.2", noop, name="duplicate"),
            ),
        )
        findings = registry.validation_findings()
        self.assertTrue(any(item.get("code") == "duplicate-edge" for item in findings))
        self.assertTrue(registry.validate())

    def test_cyclic_edge_graph_fails_registry_validation(self) -> None:
        module = self.migration_module()
        noop = lambda stage: {}
        registry = module.MigrationRegistry(
            "0.2",
            (
                module.MigrationEdge("0.1", "0.2", noop),
                module.MigrationEdge("0.2", "0.1", noop),
            ),
        )
        findings = registry.validation_findings()
        self.assertTrue(any(item.get("code") == "cycle" for item in findings))
        with self.assertRaises(module.MigrationRegistryError) as error:
            registry.resolve_path("0.1", "0.2")
        self.assertEqual(error.exception.code, "invalid-registry")

    def test_registry_path_selection_is_deterministic(self) -> None:
        module = self.migration_module()
        noop = lambda stage: {}
        edges = (
            module.MigrationEdge("0.1", "0.4", noop),
            module.MigrationEdge("0.4", "test-only-0.3", noop),
            module.MigrationEdge("0.1", "0.3", noop),
            module.MigrationEdge("0.3", "test-only-0.3", noop),
        )
        first = module.MigrationRegistry("test-only-0.3", edges)
        second = module.MigrationRegistry("test-only-0.3", tuple(reversed(edges)))
        first_path = [edge.label for edge in first.resolve_path("0.1", "latest")]
        second_path = [edge.label for edge in second.resolve_path("0.1", "test-only-0.3")]
        self.assertEqual(first_path, ["0.1->0.3", "0.3->test-only-0.3"])
        self.assertEqual(first_path, second_path)

    def test_multi_step_registry_plans_final_state_and_uses_one_transaction(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_page=True)
            before_page = (vault / "career" / "evidence.md").read_bytes()
            before_custom = (vault / "custom-archive" / "historical.md").read_bytes()
            registry = self.make_multi_step_registry(module)
            original_replace = module._replace_planned_files

            def assert_final_transaction(path: Path, updates: Mapping[str, bytes]) -> dict:
                self.assertEqual(
                    (path / "SCHEMA.md").read_text(encoding="utf-8").splitlines()[2],
                    "schema_version: 0.1",
                )
                self.assertNotIn(b"test-only-0.3", (path / "SCHEMA.md").read_bytes())
                return original_replace(path, updates)

            with mock.patch.object(module, "_replace_planned_files", side_effect=assert_final_transaction) as replace:
                result = module.apply_migration(
                    vault, target="test-only-0.3", registry=registry
                )
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["migration_path"], ["0.1", "0.2", "test-only-0.3"])
            self.assertEqual(result["migration_path_applied"], result["migration_path"])
            self.assertEqual(replace.call_count, 1)
            self.assertEqual(len(self.backup_files(root)), 1)
            self.assertIn(b"schema_version: test-only-0.3", (vault / "SCHEMA.md").read_bytes())
            self.assertEqual(before_page, (vault / "career" / "evidence.md").read_bytes())
            self.assertEqual(before_custom, (vault / "custom-archive" / "historical.md").read_bytes())

    def test_multi_step_staged_final_validation_failure_writes_nothing(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root)
            before = self.file_bytes(vault)
            registry = self.make_multi_step_registry(module)
            registry.edges[-1].validator = lambda stage: {
                "ok": False,
                "errors": [{"path": "SCHEMA.md", "message": "injected final-state failure"}],
            }
            result = module.apply_migration(
                vault, target="test-only-0.3", registry=registry
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(self.backup_files(root), [])

    def test_multi_step_replacement_failure_rolls_back_complete_chain(self) -> None:
        module = self.migration_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_legacy(root, career_page=True)
            before = self.file_bytes(vault)
            registry = self.make_multi_step_registry(module)
            original_replace = module.os.replace
            calls = {"count": 0}

            def fail_second(source: str | Path, destination: str | Path) -> None:
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("injected multi-step replacement failure")
                original_replace(source, destination)

            original_replace_planned = module._replace_planned_files

            def with_injected_failure(path: Path, updates: Mapping[str, bytes]) -> dict:
                with mock.patch.object(module.os, "replace", side_effect=fail_second):
                    return original_replace_planned(path, updates)

            with mock.patch.object(
                module, "_replace_planned_files", side_effect=with_injected_failure
            ):
                result = module.apply_migration(
                    vault, target="test-only-0.3", registry=registry
                )
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["rollback"]["status"], "rolled-back")
            self.assertEqual(before, self.file_bytes(vault))
            self.assertEqual(len(self.backup_files(root)), 1)
            self.assertFalse(any("migrate-" in path.name for path in vault.rglob(".*")))


if __name__ == "__main__":
    unittest.main()
