import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
SYNC = SCRIPTS / "sync_indexes.py"


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


if __name__ == "__main__":
    unittest.main()
