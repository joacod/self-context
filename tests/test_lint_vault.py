import datetime as date
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
LINT = SCRIPTS / "lint_vault.py"
SYNC = SCRIPTS / "sync_indexes.py"


PAGE = """---
type: concept
id: synthetic-{slug}
title: {title}
aliases:
  - {alias}
description: Synthetic durable page for tests.
tags:
  - synthetic
status: active
generated: 2026-08-12
verified: null
sources: []
assertion_kind: user_stated_fact
stale_after: null
---

## Evidence

Synthetic evidence for {title}.
"""


class LintVaultTests(unittest.TestCase):
    def make_vault(
        self,
        root: Path,
        *,
        schema: str = "0.2",
        career: bool = False,
        contracts: list[str] | None = None,
        custom_area: bool = False,
    ) -> Path:
        vault = root / "vault"
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory).mkdir(parents=True)
        if career:
            (vault / "career").mkdir()
        if custom_area:
            (vault / "archive").mkdir()
        if contracts is None:
            contracts = ["career@1"] if schema == "0.2" and career else []
        contract_text = ""
        if schema == "0.2":
            contract_text = "\nvertical_contracts:\n" + "".join(
                f"  - {entry}\n" for entry in contracts
            )
        (vault / "SCHEMA.md").write_text(
            f"# Synthetic Schema\n\nschema_version: {schema}\n{contract_text}",
            encoding="utf-8",
        )
        links = [
            "SCHEMA.md",
            "log.md",
            "- [Core](core/index.md)",
            "- [Review](review/index.md)",
            "- [Sources](sources/index.md)",
            "- [Derived](derived/index.md)",
        ]
        if career:
            links.append("- [Career](career/index.md)")
        (vault / "index.md").write_text("# Synthetic Vault\n\n" + "\n".join(links) + "\n", encoding="utf-8")
        (vault / "log.md").write_text("# Synthetic Log\n", encoding="utf-8")
        for index in ("core", "review", "sources", "derived"):
            (vault / index / "index.md").write_text(f"# {index.title()}\n", encoding="utf-8")
        if career:
            (vault / "career" / "index.md").write_text("# Career\n", encoding="utf-8")
        if schema == "0.2":
            sys.path.insert(0, str(SCRIPTS))
            import sync_indexes

            sync_indexes.synchronize(vault, write=True)
        return vault

    def contract_findings(self, vault: Path) -> list[dict]:
        report = json.loads(self.run_lint(vault, "--deep", "--format", "json").stdout)
        return [item for item in report["findings"] if item["classification"].startswith("vertical-contract")]

    def run_lint(self, vault: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(LINT), *args, str(vault)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def test_schema_01_current_runtime_requires_upgrade_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            before = (vault / "SCHEMA.md").read_text()
            result = self.run_lint(vault, "--format", "json")
            report = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(report["validation_mode"], "current-runtime")
            self.assertEqual(
                report["runtime_compatibility"]["state"],
                "older-supported-schema",
            )
            self.assertIn("Legacy SelfContext schema detected: 0.1", result.stdout)
            self.assertIn("Current runtime schema: 0.2", result.stdout)
            self.assertIn("upgrade vault latest", result.stdout)
            self.assertEqual(before, (vault / "SCHEMA.md").read_text())

    def test_schema_01_legacy_verticals_are_migration_source_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1", career=True)
            before = (vault / "SCHEMA.md").read_text()
            current = self.run_lint(vault, "--deep", "--format", "json")
            current_report = json.loads(current.stdout)
            source = self.run_lint(
                vault,
                "--migration-source",
                "--deep",
                "--format",
                "json",
            )
            report = json.loads(source.stdout)
            self.assertNotEqual(current.returncode, 0)
            self.assertTrue(
                any(item["classification"] == "runtime-schema" for item in current_report["findings"])
            )
            self.assertEqual(report["validation_mode"], "migration-source")
            self.assertEqual(report["runtime_compatibility"]["state"], "older-supported-schema")
            self.assertFalse(
                any(item["classification"] == "runtime-schema" for item in report["findings"])
            )
            self.assertEqual(report["enabled_vertical_contracts"], [])
            self.assertEqual(report["enabled_verticals"], [])
            self.assertEqual(report["applied_vertical_contracts"], [])
            self.assertEqual(report["legacy_inferred_verticals"], ["career"])
            self.assertIn("migration-source inspection only", self.run_lint(vault, "--migration-source").stdout)
            self.assertEqual(before, (vault / "SCHEMA.md").read_text())

    def test_schema_01_migration_source_validation_preserves_legacy_control_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            result = self.run_lint(vault, "--migration-source", "--format", "json")
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(report["validation_mode"], "migration-source")
            self.assertEqual(report["runtime_compatibility"]["schema_version"], "0.1")
            self.assertEqual(report["runtime_compatibility"]["latest_supported_schema"], "0.2")
            schema_text = (vault / "SCHEMA.md").read_text()
            self.assertIn("schema_version: 0.1", schema_text)
            self.assertNotIn("vertical_contracts:", schema_text)

    def test_schema_02_requires_an_explicit_empty_contract_section(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2")
            schema_path = vault / "SCHEMA.md"
            schema_path.write_text("# Synthetic Schema\n\nschema_version: 0.2\n", encoding="utf-8")
            findings = self.contract_findings(vault)
            self.assertTrue(any("must declare a vertical_contracts section" in item["message"] for item in findings))

    def test_schema_02_without_optional_verticals_remains_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2")
            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(report["enabled_vertical_contracts"], [])
            self.assertEqual(report["available_vertical_contracts"], [
                "career@1",
                "learning@1",
                "writing@1",
                "relationships@1",
                "media@1",
                "ventures@1",
            ])
            self.assertEqual(report["enabled_verticals"], [])
            self.assertEqual(report["applied_vertical_contracts"], [])
            self.assertEqual(report["legacy_inferred_verticals"], [])
            self.assertFalse(any(item["classification"] == "vertical-contract" for item in report["findings"]))

    def test_available_but_disabled_vertical_is_not_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2")
            report = json.loads(self.run_lint(vault, "--deep", "--format", "json").stdout)
            findings = self.contract_findings(vault)
            self.assertFalse(any("missing" in item["message"] for item in findings))
            self.assertEqual(report["enabled_verticals"], [])

    def test_enabled_vertical_with_matching_version_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True, contracts=["career@1"])
            report = json.loads(self.run_lint(vault, "--deep", "--format", "json").stdout)
            findings = self.contract_findings(vault)
            self.assertEqual(findings, [])
            self.assertEqual(report["enabled_verticals"], ["career"])
            self.assertEqual(report["applied_vertical_contracts"], ["career@1"])

    def test_older_applied_contract_requires_upgrade_but_is_inspectable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True, contracts=["career@0"])
            before = (vault / "SCHEMA.md").read_text()
            current = self.run_lint(vault, "--deep", "--format", "json")
            current_report = json.loads(current.stdout)
            source = self.run_lint(
                vault,
                "--migration-source",
                "--deep",
                "--format",
                "json",
            )
            report = json.loads(source.stdout)
            findings = [
                item
                for item in report["findings"]
                if item["classification"].startswith("vertical-contract")
            ]
            self.assertNotEqual(current.returncode, 0)
            self.assertEqual(
                current_report["runtime_compatibility"]["state"],
                "older-contract",
            )
            self.assertTrue(
                any(item["classification"] == "runtime-contract" for item in current_report["findings"])
            )
            self.assertTrue(any(item["classification"] == "vertical-contract-update" for item in findings))
            self.assertFalse(
                any(item["classification"] == "runtime-contract" for item in report["findings"])
            )
            self.assertEqual(report["enabled_verticals"], ["career"])
            self.assertEqual(report["applied_vertical_contracts"], ["career@0"])
            self.assertFalse(any(item["severity"] == "error" for item in findings))
            self.assertEqual(before, (vault / "SCHEMA.md").read_text())

    def test_future_applied_contract_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True, contracts=["career@2"])
            findings = self.contract_findings(vault)
            self.assertTrue(any(item["severity"] == "error" and "newer than available" in item["message"] for item in findings))

    def test_unknown_vertical_id_is_an_error_and_preserved_in_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", contracts=["archive@1"])
            findings = self.contract_findings(vault)
            self.assertTrue(any(item["severity"] == "error" and "archive@1" in item["message"] for item in findings))
            self.assertIn("archive@1", (vault / "SCHEMA.md").read_text())

    def test_invalid_contract_version_is_an_error_without_coercion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", contracts=["career@v1"])
            findings = self.contract_findings(vault)
            self.assertTrue(any(item["severity"] == "error" and "invalid contract version" in item["message"] for item in findings))
            self.assertIn("career@v1", (vault / "SCHEMA.md").read_text())

    def test_duplicate_identical_contract_entry_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True, contracts=["career@1", "career@1"])
            findings = self.contract_findings(vault)
            self.assertTrue(any(item["severity"] == "error" and "duplicate applied vertical contract" in item["message"] for item in findings))

    def test_duplicate_vertical_id_with_different_versions_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True, contracts=["career@0", "career@1"])
            findings = self.contract_findings(vault)
            self.assertTrue(any(item["severity"] == "error" and "duplicate applied vertical contract" in item["message"] for item in findings))

    def test_schema_02_malformed_schema_state_is_reported_conservatively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="not-a-version")
            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            self.assertTrue(any(item["classification"] == "schema" and "ambiguous" in item["message"] for item in report["findings"]))
            self.assertFalse(any(item["classification"] == "vertical-contract" for item in report["findings"]))

    def test_enabled_vertical_missing_area_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", contracts=["career@1"])
            findings = self.contract_findings(vault)
            self.assertTrue(any("missing its area" in item["message"] for item in findings))

    def test_enabled_vertical_missing_index_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True)
            (vault / "career" / "index.md").unlink()
            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            self.assertTrue(any("missing its index" in item["message"] for item in report["findings"]))

    def test_schema_02_known_vertical_area_without_contract_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True, contracts=[])
            findings = self.contract_findings(vault)
            self.assertTrue(any("present but not versioned" in item["message"] for item in findings))

    def test_custom_unknown_area_is_informational_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1", custom_area=True)
            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            custom = [item for item in report["findings"] if item["classification"] == "custom-area"]
            self.assertTrue(custom)
            self.assertTrue(all(item["severity"] == "info" for item in custom))
            self.assertTrue((vault / "archive").is_dir())

    def test_malformed_utf8_is_a_controlled_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            custom = vault / "custom-notes"
            custom.mkdir()
            broken = custom / "broken.md"
            broken.write_bytes(b"\xff\xfeunrelated-private-marker")
            healthy = vault / "core" / "healthy.md"
            healthy.write_text(
                PAGE.format(slug="healthy", title="Healthy Synthetic Page", alias="healthy alias"),
                encoding="utf-8",
            )

            result = self.run_lint(vault, "--deep", "--format", "json")
            self.assertNotIn("Traceback", result.stderr)
            report = json.loads(result.stdout)
            malformed = [
                item
                for item in report["findings"]
                if item["classification"] == "utf8" and item.get("path") == "custom-notes/broken.md"
            ]
            self.assertEqual(len(malformed), 1)
            self.assertNotIn("unrelated-private-marker", result.stdout)
            self.assertTrue(any(item.get("path") == "core/healthy.md" for item in report["pages"]))

            text_result = self.run_lint(vault, "--deep", "--format", "text")
            self.assertNotIn("Traceback", text_result.stderr)
            self.assertIn("custom-notes/broken.md", text_result.stdout)

    def test_custom_area_is_unmanaged_but_universal_link_safety_still_applies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            custom = vault / "custom-notes"
            custom.mkdir()
            (custom / "index.md").write_text(
                "# Custom index\n\n- [Self](index.md)\n", encoding="utf-8"
            )
            (custom / "plain.md").write_text(
                "# Custom notes\n\nNo SelfContext frontmatter is required here.\n",
                encoding="utf-8",
            )
            unsafe = custom / "unsafe.md"
            unsafe.write_text("# Custom link\n\n[Escape](../../outside.md)\n", encoding="utf-8")

            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            self.assertTrue(
                any(
                    item["classification"] == "custom-area"
                    and item.get("path") == "custom-notes/plain.md"
                    for item in report["findings"]
                )
            )
            self.assertTrue(
                any(
                    item["classification"] == "links"
                    and item.get("path") == "custom-notes/unsafe.md"
                    for item in report["findings"]
                )
            )
            self.assertFalse(any(item.get("path") == "custom-notes/plain.md" for item in report["pages"]))
            self.assertFalse(
                any(
                    item["classification"] == "root-reachability"
                    and item.get("path") == "custom-notes/index.md"
                    for item in report["findings"]
                )
            )
            managed_classes = {
                "frontmatter",
                "metadata",
                "root-reachability",
                "nearest-index-ownership",
                "catalog-sync",
                "vertical-contract",
            }
            self.assertFalse(
                any(
                    item.get("path", "").startswith("custom-notes/")
                    and item["classification"] in managed_classes
                    for item in report["findings"]
                )
            )

    def test_custom_area_symlink_is_reported_as_a_safety_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_vault(root, schema="0.1")
            custom = vault / "custom-notes"
            custom.mkdir()
            outside = root / "outside.md"
            outside.write_text("synthetic outside target\n", encoding="utf-8")
            linked = custom / "linked.md"
            try:
                linked.symlink_to(outside)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks unavailable: {error}")

            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            self.assertTrue(
                any(
                    item["classification"] == "symlink"
                    and item["severity"] == "error"
                    and item.get("path") == "custom-notes/linked.md"
                    for item in report["findings"]
                )
            )

    def test_unreadable_file_is_reported_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            custom = vault / "custom-notes"
            custom.mkdir()
            unreadable = custom / "unreadable.md"
            unreadable.write_text("synthetic unreadable content\n", encoding="utf-8")

            sys.path.insert(0, str(SCRIPTS))
            import lint_vault

            original_read = lint_vault.safe_read_text

            def fake_read(path: Path):
                if path == unreadable:
                    return None, "PermissionError: unable to read file"
                return original_read(path)

            with mock.patch.object(lint_vault, "safe_read_text", side_effect=fake_read):
                report = lint_vault.deep_lint_vault(vault, date.date(2026, 8, 12))

            self.assertTrue(
                any(
                    item["classification"] == "filesystem"
                    and item.get("path") == "custom-notes/unreadable.md"
                    for item in report["findings"]
                )
            )

    def test_json_omits_page_bodies_and_snapshot_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            page = vault / "core" / "concept.md"
            page.write_text(PAGE.format(slug="concept", title="Synthetic Concept", alias="concept alias"), encoding="utf-8")
            first = self.run_lint(vault, "--deep", "--format", "json")
            second = self.run_lint(vault, "--deep", "--format", "json")
            one, two = json.loads(first.stdout), json.loads(second.stdout)
            self.assertEqual(one["snapshot_id"], two["snapshot_id"])
            self.assertNotIn("body", one)
            page.write_text(page.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
            third = json.loads(self.run_lint(vault, "--deep", "--format", "json").stdout)
            self.assertNotEqual(one["snapshot_id"], third["snapshot_id"])

    def test_snapshot_ignores_noncanonical_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            first = json.loads(self.run_lint(vault, "--deep", "--format", "json").stdout)["snapshot_id"]
            (vault / ".obsidian").mkdir()
            (vault / ".obsidian" / "workspace.json").write_text("viewer", encoding="utf-8")
            second = json.loads(self.run_lint(vault, "--deep", "--format", "json").stdout)["snapshot_id"]
            self.assertEqual(first, second)

    def test_repository_catalog_is_valid(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import vault_utils

        self.assertEqual(vault_utils.validate_vertical_catalog(), [])
        records = vault_utils.catalog_records(vault_utils.load_vertical_catalog())
        self.assertEqual(
            {record["id"] for record in records},
            {"career", "learning", "writing", "relationships", "media", "ventures"},
        )


if __name__ == "__main__":
    unittest.main()
