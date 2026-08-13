import json
import subprocess
import sys
import tempfile
import unittest
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
    def make_vault(self, root: Path, *, schema: str = "0.1", career: bool = False) -> Path:
        vault = root / "vault"
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory).mkdir(parents=True)
        if career:
            (vault / "career").mkdir()
        contracts = ""
        if schema == "0.2" and career:
            contracts = "\nvertical_contracts:\n  - career@1\n"
        (vault / "SCHEMA.md").write_text(
            f"# Synthetic Schema\n\nschema_version: {schema}\n{contracts}",
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
        return vault

    def run_lint(self, vault: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(LINT), *args, str(vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_schema_01_remains_accepted_without_contract_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            result = self.run_lint(vault)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("schema_version: 0.1", (vault / "SCHEMA.md").read_text())

    def test_schema_02_parses_selective_contracts_and_disabled_vertical_is_not_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2")
            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            self.assertEqual(report["enabled_vertical_contracts"], [])
            self.assertNotIn("missing its area", result.stdout)

    def test_enabled_vertical_missing_index_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.2", career=True)
            (vault / "career" / "index.md").unlink()
            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            self.assertTrue(any("missing its index" in item["message"] for item in report["findings"]))

    def test_custom_unknown_area_is_informational(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            (vault / "custom-notes").mkdir()
            result = self.run_lint(vault, "--deep", "--format", "json")
            report = json.loads(result.stdout)
            custom = [item for item in report["findings"] if item["classification"] == "custom-area"]
            self.assertEqual(len(custom), 1)
            self.assertEqual(custom[0]["severity"], "info")

    def test_malformed_utf8_is_a_controlled_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), schema="0.1")
            (vault / "broken.md").write_bytes(b"\xff\xfe")
            result = self.run_lint(vault, "--deep", "--format", "json")
            self.assertNotIn("Traceback", result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(any(item["classification"] == "utf8" for item in report["findings"]))

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
        self.assertEqual({record["id"] for record in records}, {"career", "learning", "writing", "relationships", "media"})


if __name__ == "__main__":
    unittest.main()
