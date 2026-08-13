import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
SYNC = SCRIPTS / "sync_indexes.py"
LINT = SCRIPTS / "lint_vault.py"


PAGE = """---
type: concept
title: {title}
description: {description}
tags:
  - synthetic
status: active
generated: 2026-08-12
verified: null
sources: []
assertion_kind: user_stated_fact
stale_after: null
---

Synthetic body.
"""


class SyncIndexesTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Path:
        vault = root / "vault"
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory).mkdir(parents=True)
        (vault / "SCHEMA.md").write_text("# Schema\n\nschema_version: 0.1\n", encoding="utf-8")
        (vault / "log.md").write_text("# Log\n", encoding="utf-8")
        (vault / "index.md").write_text(
            "# Root\n\nManual navigation survives.\n"
            "- [Core](core/index.md)\n- [Review](review/index.md)\n"
            "- [Sources](sources/index.md)\n- [Derived](derived/index.md)\n",
            encoding="utf-8",
        )
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory / "index.md").write_text(f"# {directory}\n", encoding="utf-8")
        return vault

    def run_sync(self, vault: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SYNC), *args, str(vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_write_is_idempotent_and_preserves_manual_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            (vault / "core" / "one.md").write_text(
                PAGE.format(title="Synthetic One", description="First synthetic page."), encoding="utf-8"
            )
            (vault / "core" / "two.md").write_text(
                PAGE.format(title="Synthetic Two", description="Second synthetic page."), encoding="utf-8"
            )
            first = self.run_sync(vault, "--write", "--format", "json")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            before = (vault / "core" / "index.md").read_text(encoding="utf-8")
            self.assertIn("# core", before)
            self.assertIn("Synthetic One", before)
            second = self.run_sync(vault, "--write", "--format", "json")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(before, (vault / "core" / "index.md").read_text(encoding="utf-8"))
            check = self.run_sync(vault, "--check", "--format", "json")
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_check_detects_drift_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            (vault / "core" / "one.md").write_text(
                PAGE.format(title="Synthetic One", description="First synthetic page."), encoding="utf-8"
            )
            self.assertEqual(self.run_sync(vault, "--write").returncode, 0)
            index = vault / "core" / "index.md"
            before = index.read_bytes()
            index.write_bytes(before.replace(b"Synthetic One", b"Changed One"))
            result = self.run_sync(vault, "--check", "--format", "json")
            report = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(report["status"], "drifted")
            self.assertTrue(any(item["classification"] == "catalog-sync" for item in report["findings"]))
            after_check = index.read_bytes()
            self.assertNotEqual(before, after_check)
            self.assertEqual(after_check, before.replace(b"Synthetic One", b"Changed One"))

    def test_manual_prefix_and_suffix_survive_byte_for_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            (vault / "core" / "one.md").write_text(
                PAGE.format(title="Synthetic One", description="First synthetic page."), encoding="utf-8"
            )
            index = vault / "core" / "index.md"
            prefix = "# core\n\n<!-- manual prefix comment -->\nManual navigation.\n\n"
            suffix = "\n\n## Manual follow-up\nKeep this text exactly.\n"
            index.write_text(
                prefix
                + "<!-- selfcontext:catalog:start -->\n"
                + "- [Old](old.md) — old entry `active`\n"
                + "<!-- selfcontext:catalog:end -->"
                + suffix,
                encoding="utf-8",
            )
            result = self.run_sync(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated = index.read_text(encoding="utf-8")
            self.assertTrue(updated.startswith(prefix))
            self.assertTrue(updated.endswith(suffix))
            self.assertIn("Synthetic One", updated)
            self.assertNotIn("[Old]", updated)

    def test_crlf_newline_style_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            index = vault / "core" / "index.md"
            index.write_bytes(b"# core\r\n\r\nManual CRLF text.\r\n")
            (vault / "core" / "one.md").write_text(
                PAGE.format(title="Synthetic One", description="First synthetic page."), encoding="utf-8"
            )
            result = self.run_sync(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated = index.read_bytes()
            self.assertIn(b"\r\n", updated)
            self.assertNotIn(b"\n", updated.replace(b"\r\n", b""))
            self.assertEqual(self.run_sync(vault, "--write").returncode, 0)
            self.assertEqual(updated, index.read_bytes())

    def test_markdown_special_characters_unicode_and_encoded_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            title = "Title [with] \\\\ backtick ` and   Unicode ☃"
            description = "Description [with] \\\\ backtick ` and\t repeated   whitespace"
            page_path = vault / "core" / "space (one) [two]\\\\☃.md"
            page_path.write_text(PAGE.format(title=title, description=description), encoding="utf-8")
            result = self.run_sync(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            index_text = (vault / "core" / "index.md").read_text(encoding="utf-8")
            self.assertIn("%20", index_text)
            self.assertIn("%28", index_text)
            self.assertIn("%29", index_text)
            self.assertIn("%5B", index_text)
            self.assertIn("%5D", index_text)
            self.assertIn("%5C", index_text)
            self.assertIn("%E2%98%83", index_text)
            self.assertIn(r"\[with\]", index_text)
            sys.path.insert(0, str(SCRIPTS))
            import vault_utils

            links = list(vault_utils.iter_markdown_links(index_text))
            self.assertEqual(len(links), 1)
            self.assertTrue((vault / "core" / vault_utils.unquote(links[0])).is_file())
            entries = __import__("sync_indexes").managed_entries(index_text)
            self.assertEqual(entries[0]["title"], " ".join(title.split()))
            self.assertEqual(entries[0]["description"], "Description [with] \\\\ backtick ` and repeated whitespace")

    def test_marker_structure_is_rejected_without_guessing(self) -> None:
        malformed = {
            "duplicate": (
                "<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:end -->\n"
                "<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:end -->\n"
            ),
            "unmatched-start": "<!-- selfcontext:catalog:start -->\n",
            "unmatched-end": "<!-- selfcontext:catalog:end -->\n",
            "reversed": (
                "<!-- selfcontext:catalog:end -->\n"
                "<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:end -->\n"
            ),
            "nested": (
                "<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:end -->\n"
                "<!-- selfcontext:catalog:end -->\n"
            ),
        }
        for name, block in malformed.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                vault = self.make_vault(Path(temporary))
                index = vault / "core" / "index.md"
                index.write_text("# core\n" + block, encoding="utf-8")
                before = {path: path.read_bytes() for path in vault.rglob("index.md")}
                result = self.run_sync(vault, "--check", "--format", "json")
                report = json.loads(result.stdout)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(report["status"], "invalid-marker-structure")
                self.assertTrue(any(item["classification"] == "catalog-marker-structure" for item in report["findings"]))
                self.assertEqual(before[index], index.read_bytes())

    def test_invalid_marker_in_one_index_causes_zero_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            (vault / "core" / "one.md").write_text(
                PAGE.format(title="Synthetic One", description="First synthetic page."), encoding="utf-8"
            )
            invalid = vault / "review" / "index.md"
            invalid.write_text(
                "# review\n<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:end -->\n"
                "<!-- selfcontext:catalog:end -->\n",
                encoding="utf-8",
            )
            before = {path: path.read_bytes() for path in vault.rglob("index.md")}
            result = self.run_sync(vault, "--write", "--format", "json")
            report = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(report["changed"], [])
            self.assertEqual(before, {path: path.read_bytes() for path in vault.rglob("index.md")})

    def test_temporary_files_are_cleaned_and_replaced_indexes_roll_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            (vault / "core" / "one.md").write_text(
                PAGE.format(title="Synthetic One", description="First synthetic page."), encoding="utf-8"
            )
            before = {path: path.read_bytes() for path in vault.rglob("index.md")}
            sys.path.insert(0, str(SCRIPTS))
            import sync_indexes

            with mock.patch.object(
                sync_indexes.os,
                "replace",
                side_effect=[None, OSError("synthetic replacement failure"), None],
            ):
                report = sync_indexes.synchronize(vault, write=True)
            self.assertTrue(any(item["classification"] == "catalog-write" for item in report["findings"]))
            self.assertEqual(report["changed"], [])
            self.assertEqual(before, {path: path.read_bytes() for path in vault.rglob("index.md")})
            self.assertEqual(list(vault.rglob(".*.sync-*")), [])

    def test_deterministic_ordering_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            for filename, title in (("z.md", "Zeta"), ("a.md", "Alpha"), ("middle.md", "Alpha")):
                (vault / "core" / filename).write_text(
                    PAGE.format(title=title, description=f"Description for {title}."), encoding="utf-8"
                )
            first = self.run_sync(vault, "--write")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            before = (vault / "core" / "index.md").read_bytes()
            second = self.run_sync(vault, "--write")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(before, (vault / "core" / "index.md").read_bytes())
            lines = [line for line in (vault / "core" / "index.md").read_text().splitlines() if line.startswith("- [")]
            self.assertEqual(lines[0].split("]", 1)[0], "- [Alpha")
            self.assertEqual(lines[-1].split("]", 1)[0], "- [Zeta")

    def test_dead_generated_entry_is_removed_only_inside_managed_block(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            index = vault / "core" / "index.md"
            index.write_text(
                "# core\n\nManual [dead link](missing.md)\n\n"
                "<!-- selfcontext:catalog:start -->\n"
                "- [Dead](dead.md) — old generated entry `active`\n"
                "<!-- selfcontext:catalog:end -->\n",
                encoding="utf-8",
            )
            result = self.run_sync(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated = index.read_text(encoding="utf-8")
            self.assertIn("Manual [dead link](missing.md)", updated)
            self.assertNotIn("[Dead]", updated)

    def test_missing_description_is_a_finding_and_not_invented(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            (vault / "core" / "missing.md").write_text(
                PAGE.format(title="Synthetic", description=""), encoding="utf-8"
            )
            result = self.run_sync(vault, "--check", "--format", "json")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("existing non-empty description", result.stdout)
            lint = subprocess.run(
                [sys.executable, str(LINT), "--format", "json", str(vault)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(lint.returncode, 0)
            self.assertIn("description", lint.stdout)


if __name__ == "__main__":
    unittest.main()
