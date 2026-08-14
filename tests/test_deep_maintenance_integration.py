from __future__ import annotations

import datetime as date
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
for import_path in (TESTS, SCRIPTS):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import backup_vault  # type: ignore  # noqa: E402
import lint_vault  # type: ignore  # noqa: E402
import migrate_vault  # type: ignore  # noqa: E402
import search_vault  # type: ignore  # noqa: E402
import sync_indexes  # type: ignore  # noqa: E402
import vault_utils  # type: ignore  # noqa: E402
from synthetic_vault import (  # noqa: E402
    CATALOG_START,
    DISABLED_VERTICALS,
    ENABLED_VERTICALS,
    SENSITIVE_BODY_MARKER,
    backup_paths,
    build_synthetic_vault,
    canonical_page_snapshot,
    copy_project,
    managed_index_paths,
    packet_from_results,
    tree_snapshot,
)


LINT = SCRIPTS / "lint_vault.py"
MIGRATE = SCRIPTS / "migrate_vault.py"
SEARCH = SCRIPTS / "search_vault.py"
SYNC = SCRIPTS / "sync_indexes.py"


class DeepMaintenanceIntegrationTests(unittest.TestCase):
    """Exercise the complete maintenance lifecycle against fictional vaults.

    Deep review, vertical adoption, deep update, and task packets are skill
    procedures rather than production CLI commands in this repository.  Their
    tests therefore use the existing deterministic lint/search/catalog seams
    and a small in-memory procedure harness; no new runtime is introduced.
    """

    def run_script(
        self, script: Path, *arguments: str, timeout: int = 30
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

    def assert_success(self, result: subprocess.CompletedProcess[str], label: str) -> None:
        # Do not include command output in assertion messages: a future fixture
        # change must not accidentally echo page bodies into test logs.
        self.assertEqual(result.returncode, 0, label)

    def assert_read_only(self, project_root: Path, operation: object, label: str) -> object:
        before = tree_snapshot(project_root)
        result = operation()  # type: ignore[operator]
        after = tree_snapshot(project_root)
        self.assertEqual(before, after, label)
        return result

    def assess_vertical(self, vault: Path, identifier: str) -> dict[str, object]:
        """Read-only adoption assessment from the canonical catalog/schema."""

        catalog = vault_utils.load_vertical_catalog()
        records = {
            str(record["id"]): record
            for record in vault_utils.catalog_records(catalog)
        }
        schema = vault_utils.parse_schema(vault)
        enabled = {
            str(entry.get("id"))
            for entry in schema.get("contract_entries", [])
            if entry.get("id")
        }
        record = records[identifier]
        return {
            "available": identifier in records,
            "enabled": identifier in enabled,
            "vault_area": record["vault_area"],
            "index_path": record["index_path"],
            "recommended": identifier not in enabled and identifier == "media",
        }

    def deep_review_without_retention(self, vault: Path) -> dict[str, object]:
        """Run the documented deep-review preflight without retaining output."""

        inventory = lint_vault.deep_lint_vault(vault, date.date(2026, 8, 12))
        return {
            "snapshot_id": inventory["snapshot_id"],
            "finding_count": len(inventory["findings"]),
            "retained": False,
            "report_path": None,
            "page_bodies_retained": False,
        }

    def task_packet_without_retention(self, vault: Path) -> dict[str, object]:
        """Compose a metadata-only packet in memory from relevant search seams."""

        career = search_vault.search_vault(
            vault, "Harbor Launch", vertical="career"
        )
        writing = search_vault.search_vault(
            vault, "Explanation Pattern", vertical="writing"
        )
        # A packet keeps the smallest relevant hit per requested vertical;
        # historical duplicates remain searchable but are not pulled in when
        # they are not needed for this task.
        results = [career["results"][0], writing["results"][0]]
        return packet_from_results(
            results,
            requested_verticals=("career", "writing"),
            excluded_verticals=("relationships",),
            retained=False,
        )

    def adopt_vertical_with_explicit_authorization(
        self, project_root: Path, vault: Path, identifier: str
    ) -> Path:
        """Model the documented, explicitly authorized adoption boundary.

        The production skill has no adoption CLI.  This test-only harness
        applies exactly the documented control-file contract, validates it,
        then creates the normal post-write backup through the existing helper.
        """

        catalog = vault_utils.load_vertical_catalog()
        record = next(
            item
            for item in vault_utils.catalog_records(catalog)
            if item["id"] == identifier
        )
        schema_path = vault / "SCHEMA.md"
        schema = schema_path.read_text(encoding="utf-8")
        marker = "vertical_contracts:\n"
        self.assertIn(marker, schema)
        contract = f"  - {identifier}@{record['contract_version']}\n"
        self.assertNotIn(contract, schema)
        schema = schema.replace(marker, marker + contract, 1)
        schema_path.write_text(schema, encoding="utf-8")

        area = vault / str(record["vault_area"])
        area.mkdir()
        index = area / "index.md"
        index.write_text(
            f"# {record['display_name']} Context\n\n"
            f"{record['ownership']}\n\n"
            "<!-- selfcontext:catalog:start -->\n"
            "<!-- selfcontext:catalog:end -->\n",
            encoding="utf-8",
        )
        root_index = vault / "index.md"
        root_text = root_index.read_text(encoding="utf-8")
        root_text += f"- [{record['display_name']} context]({record['index_path']})\n"
        root_index.write_text(root_text, encoding="utf-8")
        sync_result = sync_indexes.synchronize(vault, write=True)
        self.assertFalse(
            any(item.get("severity") == "error" for item in sync_result["findings"])
        )
        backup_path, _ = backup_vault.create_backup(vault)
        self.assertTrue(Path(backup_path).is_file())
        return area

    def test_read_only_operations_preserve_complete_synthetic_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "current"
            vault = build_synthetic_vault(project, schema_version="0.2")
            before_schema = (vault / "SCHEMA.md").read_bytes()
            before_log = (vault / "log.md").read_bytes()

            ordinary = self.assert_read_only(
                project,
                lambda: self.run_script(LINT, str(vault)),
                "ordinary lint changed the synthetic project",
            )
            self.assert_success(ordinary, "ordinary lint failed on the valid fixture")

            deep_text = self.assert_read_only(
                project,
                lambda: self.run_script(LINT, "--deep", "--format", "text", str(vault)),
                "deep lint text changed the synthetic project",
            )
            self.assert_success(deep_text, "deep lint text failed on the valid fixture")
            self.assertNotIn(SENSITIVE_BODY_MARKER, deep_text.stdout)

            deep_json = self.assert_read_only(
                project,
                lambda: self.run_script(LINT, "--deep", "--format", "json", str(vault)),
                "deep lint JSON changed the synthetic project",
            )
            self.assert_success(deep_json, "deep lint JSON failed on the valid fixture")
            deep_report = json.loads(deep_json.stdout)
            self.assertTrue(deep_report["snapshot_id"])
            self.assertFalse(
                any(item["path"].startswith("custom-notes/") for item in deep_report["pages"])
            )
            self.assertNotIn(SENSITIVE_BODY_MARKER, deep_json.stdout)

            index_check = self.assert_read_only(
                project,
                lambda: self.run_script(
                    SYNC, "--check", "--format", "json", str(vault)
                ),
                "catalog check changed the synthetic project",
            )
            self.assert_success(index_check, "catalog check failed on the valid fixture")
            self.assertEqual(json.loads(index_check.stdout)["changed"], [])

            lexical = self.assert_read_only(
                project,
                lambda: self.run_script(
                    SEARCH, "Harbor Launch", str(vault), "--format", "json"
                ),
                "lexical search changed the synthetic project",
            )
            self.assert_success(lexical, "lexical search failed on the valid fixture")
            lexical_report = json.loads(lexical.stdout)
            self.assertEqual(lexical_report["results"][0]["path"], "career/harbor-launch.md")
            self.assertNotIn(SENSITIVE_BODY_MARKER, lexical.stdout)
            marker_search = self.run_script(
                SEARCH, SENSITIVE_BODY_MARKER, str(vault), "--format", "json"
            )
            self.assert_success(marker_search, "marker retrieval unexpectedly failed")
            self.assertEqual(json.loads(marker_search.stdout)["results"], [])

            legacy_project = Path(temporary) / "legacy"
            legacy_vault = build_synthetic_vault(legacy_project, schema_version="0.1")
            dry_run = self.assert_read_only(
                legacy_project,
                lambda: self.run_script(
                    MIGRATE, "--check", "--format", "json", str(legacy_vault)
                ),
                "migration dry-run changed the synthetic project",
            )
            self.assert_success(dry_run, "migration dry-run failed")
            self.assertEqual(json.loads(dry_run.stdout)["from_schema"], "0.1")
            self.assertEqual(backup_paths(legacy_project), [])

            assessment = self.assert_read_only(
                project,
                lambda: self.assess_vertical(vault, "media"),
                "vertical adoption assessment changed the synthetic project",
            )
            self.assertEqual(assessment["available"], True)
            self.assertEqual(assessment["enabled"], False)
            self.assertEqual(assessment["recommended"], True)

            review = self.assert_read_only(
                project,
                lambda: self.deep_review_without_retention(vault),
                "no-retention deep review changed the synthetic project",
            )
            self.assertEqual(review["retained"], False)
            self.assertIsNone(review["report_path"])
            self.assertFalse((vault / "review" / "deep-reviews").exists())

            packet = self.assert_read_only(
                project,
                lambda: self.task_packet_without_retention(vault),
                "ephemeral task packet changed the synthetic project",
            )
            self.assertEqual(packet["retained"], False)
            self.assertTrue(packet["derived"])
            self.assertEqual(
                set(packet["evidence_paths"]),
                {"career/harbor-launch.md", "writing/explanation-pattern.md"},
            )
            self.assertIn("Excluded unrelated relationships context.", packet["important_exclusions"])
            self.assertNotIn(SENSITIVE_BODY_MARKER, json.dumps(packet))

            self.assertEqual(before_schema, (vault / "SCHEMA.md").read_bytes())
            self.assertEqual(before_log, (vault / "log.md").read_bytes())
            self.assertEqual(backup_paths(project), [])
            for vertical in DISABLED_VERTICALS:
                self.assertFalse((vault / vertical).exists())
            self.assertFalse((vault / "review" / "deep-reviews").exists())

    def test_migration_copy_creates_one_backup_and_interoperates_after_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_project = root / "source"
            build_synthetic_vault(
                source_project,
                schema_version="0.1",
                missing_indexes=("writing",),
            )
            # Remove one legacy root link so migration must restore the
            # control navigation as well as the missing category index.
            source_root = source_project / "vault" / "index.md"
            source_root.write_text(
                source_root.read_text(encoding="utf-8").replace(
                    "- [Relationships context](relationships/index.md)\n", ""
                ),
                encoding="utf-8",
            )
            copied_project = root / "migration-copy"
            vault = copy_project(source_project, copied_project)
            before_pages = canonical_page_snapshot(vault)
            custom_before = (vault / "custom-notes" / "field-log.md").read_bytes()

            result = self.run_script(MIGRATE, "--write", "--format", "json", str(vault))
            self.assert_success(result, "schema migration failed on the medium fixture")
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "success")
            backups = backup_paths(copied_project)
            self.assertEqual(len(backups), 1)
            self.assertTrue(report["backup"])

            # The archive must contain the final state, demonstrating that
            # backup creation followed schema/index/log replacement.
            with zipfile.ZipFile(backups[0]) as archive:
                self.assertIn("SCHEMA.md", archive.namelist())
                self.assertIn(b"schema_version: 0.2", archive.read("SCHEMA.md"))
                self.assertIn("writing/index.md", archive.namelist())
                self.assertIn(b"migrate_schema_0_1_to_0_2", archive.read("log.md"))

            schema = (vault / "SCHEMA.md").read_text(encoding="utf-8")
            self.assertIn("schema_version: 0.2", schema)
            for identifier in ENABLED_VERTICALS:
                self.assertIn(f"- {identifier}@1", schema)
            self.assertTrue((vault / "writing" / "index.md").is_file())
            root_text = (vault / "index.md").read_text(encoding="utf-8")
            self.assertIn("writing/index.md", root_text)
            self.assertIn(CATALOG_START, (vault / "writing" / "index.md").read_text())
            self.assertIn("Harbor Launch", (vault / "career" / "index.md").read_text())

            self.assertEqual(before_pages, canonical_page_snapshot(vault))
            self.assertEqual(custom_before, (vault / "custom-notes" / "field-log.md").read_bytes())
            review_page = (vault / "review" / "maintenance-candidate.md").read_text(encoding="utf-8")
            self.assertIn("status: review", review_page)
            self.assertIn("assertion_kind: agent_inference", review_page)
            self.assertIn("verified: null", review_page)
            self.assertIn("migrate_schema_0_1_to_0_2", (vault / "log.md").read_text())

            ordinary = self.run_script(LINT, str(vault))
            deep = self.run_script(LINT, "--deep", "--format", "json", str(vault))
            sync = self.run_script(SYNC, "--check", "--format", "json", str(vault))
            self.assert_success(ordinary, "ordinary lint failed after migration")
            self.assert_success(deep, "deep lint failed after migration")
            self.assert_success(sync, "catalog check failed after migration")

            search = self.run_script(
                SEARCH, "Harbor Launch", str(vault), "--format", "json"
            )
            self.assert_success(search, "search failed after migration")
            self.assertEqual(json.loads(search.stdout)["results"][0]["path"], "career/harbor-launch.md")
            packet = self.task_packet_without_retention(vault)
            self.assertEqual(packet["retained"], False)
            self.assertEqual(
                set(packet["evidence_paths"]),
                {"career/harbor-launch.md", "writing/explanation-pattern.md"},
            )

    def test_bounded_catalog_refresh_is_backed_up_once_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            index = vault / "career" / "index.md"
            index.write_bytes(index.read_bytes().replace(b"Harbor Launch", b"Stale Launch", 1))
            before_pages = canonical_page_snapshot(vault)
            custom_before = (vault / "custom-notes" / "field-log.md").read_bytes()

            first = sync_indexes.synchronize(vault, write=True)
            self.assertEqual(first["changed"], ["career/index.md"])
            backup_path, _ = backup_vault.create_backup(vault)
            self.assertTrue(Path(backup_path).is_file())
            self.assertEqual(len(backup_paths(project)), 1)
            self.assertIn("Harbor Launch", index.read_text(encoding="utf-8"))
            self.assertEqual(canonical_page_snapshot(vault), before_pages)
            self.assertEqual(custom_before, (vault / "custom-notes" / "field-log.md").read_bytes())

            after_first_write = tree_snapshot(vault)
            second = sync_indexes.synchronize(vault, write=True)
            self.assertEqual(second["changed"], [])
            self.assertEqual(after_first_write, tree_snapshot(vault))
            self.assertEqual(len(backup_paths(project)), 1)
            self.assert_success(
                self.run_script(SYNC, "--check", "--format", "json", str(vault)),
                "catalog check failed after repeated write",
            )

    def test_explicit_media_adoption_is_selective_and_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.2")
            before_pages = canonical_page_snapshot(vault)
            custom_before = (vault / "custom-notes" / "field-log.md").read_bytes()
            self.assertFalse((vault / "media").exists())
            self.assertEqual(backup_paths(project), [])

            self.adopt_vertical_with_explicit_authorization(project, vault, "media")
            self.assertEqual(len(backup_paths(project)), 1)
            schema = (vault / "SCHEMA.md").read_text(encoding="utf-8")
            self.assertIn("- media@1", schema)
            self.assertTrue((vault / "media" / "index.md").is_file())
            self.assertIn("media/index.md", (vault / "index.md").read_text(encoding="utf-8"))
            self.assertEqual(before_pages, canonical_page_snapshot(vault))
            self.assertEqual(custom_before, (vault / "custom-notes" / "field-log.md").read_bytes())

            self.assert_success(
                self.run_script(LINT, str(vault)),
                "ordinary lint failed after explicit vertical adoption",
            )
            deep = self.run_script(LINT, "--deep", "--format", "json", str(vault))
            self.assert_success(deep, "deep lint failed after explicit vertical adoption")
            deep_report = json.loads(deep.stdout)
            self.assertEqual(deep_report["enabled_verticals"], sorted((*ENABLED_VERTICALS, "media")))
            self.assert_success(
                self.run_script(SYNC, "--check", "--format", "json", str(vault)),
                "catalog check failed after explicit vertical adoption",
            )

    def test_stale_migration_plan_stops_before_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.1")
            plan = migrate_vault.plan_migration(vault)
            (vault / "log.md").write_text("# changed after review\n", encoding="utf-8")
            with mock.patch.object(migrate_vault, "plan_migration", return_value=plan):
                result = migrate_vault.apply_migration(vault)
            self.assertEqual(result["status"], "stale-plan")
            self.assertTrue(any(item["classification"] == "snapshot-drift" for item in result["findings"]))
            self.assertEqual(backup_paths(project), [])
            self.assertEqual((vault / "SCHEMA.md").read_text().splitlines()[2], "schema_version: 0.1")

    def test_failed_medium_migration_rolls_back_active_bytes_before_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project, schema_version="0.1")
            before = tree_snapshot(vault)
            with mock.patch.object(
                migrate_vault,
                "_validate_active_state",
                return_value={
                    "ok": False,
                    "errors": [{"path": "SCHEMA.md", "message": "synthetic validation failure"}],
                },
            ):
                result = migrate_vault.apply_migration(vault)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["rollback"]["status"], "rolled-back")
            self.assertEqual(before, tree_snapshot(vault))
            self.assertEqual(len(backup_paths(project)), 0)
            self.assertFalse(any(path.name.startswith(".index.md.migrate-") for path in vault.rglob(".*")))

    def test_valid_and_invalid_fixture_lint_modes_are_both_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            valid_project = Path(temporary) / "valid"
            valid_vault = build_synthetic_vault(valid_project, schema_version="0.2")
            self.assert_success(self.run_script(LINT, str(valid_vault)), "valid ordinary lint failed")
            self.assert_success(
                self.run_script(LINT, "--deep", "--format", "text", str(valid_vault)),
                "valid deep text lint failed",
            )
            valid_json = self.run_script(LINT, "--deep", "--format", "json", str(valid_vault))
            self.assert_success(valid_json, "valid deep JSON lint failed")
            json.loads(valid_json.stdout)

            invalid_project = Path(temporary) / "invalid"
            invalid_vault = build_synthetic_vault(invalid_project, schema_version="0.2")
            invalid_page = invalid_vault / "core" / "decision-trail.md"
            invalid_page.write_text(
                invalid_page.read_text(encoding="utf-8").replace(
                    "description: A cross-domain preference linked to fictional evidence.",
                    "description:\n",
                    1,
                ),
                encoding="utf-8",
            )
            ordinary = self.run_script(LINT, str(invalid_vault))
            self.assertNotEqual(ordinary.returncode, 0)
            deep_json = self.run_script(LINT, "--deep", "--format", "json", str(invalid_vault))
            self.assertNotEqual(deep_json.returncode, 0)
            invalid_report = json.loads(deep_json.stdout)
            self.assertTrue(invalid_report["severity_counts"]["error"])

    def test_fixture_exposes_required_medium_vault_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary), schema_version="0.2")
            schema = (vault / "SCHEMA.md").read_text(encoding="utf-8")
            self.assertIn("schema_version: 0.2", schema)
            self.assertEqual(
                [line.strip()[2:] for line in schema.splitlines() if line.strip().startswith("-")],
                [f"{identifier}@1" for identifier in ENABLED_VERTICALS],
            )
            self.assertTrue(all((vault / identifier / "index.md").is_file() for identifier in ENABLED_VERTICALS))
            self.assertTrue(all(not (vault / identifier).exists() for identifier in DISABLED_VERTICALS))
            self.assertIn("Manual root navigation", (vault / "index.md").read_text())
            self.assertIn(CATALOG_START, (vault / "career" / "index.md").read_text())
            self.assertIn("aliases:", (vault / "career" / "harbor-launch.md").read_text())
            statuses = {
                "active": "career/harbor-launch.md",
                "archived": "career/archived-role.md",
                "review": "review/maintenance-candidate.md",
                "superseded": "career/superseded-launch.md",
            }
            for status, relative in statuses.items():
                self.assertIn(f"status: {status}", (vault / relative).read_text())
            self.assertTrue((vault / "sources" / "current-signal.md").is_file())
            derived = (vault / "derived" / "maintenance-brief.md").read_text()
            self.assertIn("../sources/current-signal.md", derived)
            self.assertTrue((vault / "custom-notes" / "field-log.md").is_file())
            self.assertIn(SENSITIVE_BODY_MARKER, (vault / "custom-notes" / "field-log.md").read_text())
            self.assertIn("../writing/explanation-pattern.md", (vault / "core" / "decision-trail.md").read_text())
            self.assertEqual(
                managed_index_paths(vault),
                sorted(
                    [
                        "core/index.md",
                        "derived/index.md",
                        "index.md",
                        "career/index.md",
                        "learning/index.md",
                        "writing/index.md",
                        "relationships/index.md",
                        "review/index.md",
                        "sources/index.md",
                    ]
                ),
            )


if __name__ == "__main__":
    unittest.main()
