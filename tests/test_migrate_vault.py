import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/self-context/scripts/migrate_vault.py"


class MigrateVaultTests(unittest.TestCase):
    def make_legacy(self, root: Path) -> Path:
        vault = root / "vault"
        for directory in ("core", "career", "review", "sources", "derived", "custom-archive"):
            (vault / directory).mkdir(parents=True)
        (vault / "SCHEMA.md").write_text("# Legacy\n\nschema_version: 0.1\n", encoding="utf-8")
        (vault / "index.md").write_text(
            "# Legacy\n\n- [Core](core/index.md)\n- [Career](career/index.md)\n"
            "- [Review](review/index.md)\n- [Sources](sources/index.md)\n- [Derived](derived/index.md)\n",
            encoding="utf-8",
        )
        (vault / "log.md").write_text("# Log\n", encoding="utf-8")
        for directory in ("core", "career", "review", "sources", "derived"):
            (vault / directory / "index.md").write_text(f"# {directory}\n", encoding="utf-8")
        (vault / "custom-archive" / "historical.md").write_text("custom page\n", encoding="utf-8")
        return vault

    def run_migration(self, vault: Path, mode: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), mode, "--format", "json", str(vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_check_is_read_only_and_reports_custom_area(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_legacy(Path(temporary))
            before = (vault / "SCHEMA.md").read_text(encoding="utf-8")
            result = self.run_migration(vault, "--check")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["from_schema"], "0.1")
            self.assertIn("career@1", report["enabled_vertical_contracts"])
            self.assertTrue(any(item["path"] == "custom-archive/" for item in report["findings"]))
            self.assertEqual(before, (vault / "SCHEMA.md").read_text(encoding="utf-8"))
            self.assertFalse((Path(temporary) / "backups").exists())

    def test_write_backs_up_and_preserves_pages_and_custom_areas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_legacy(Path(temporary))
            result = self.run_migration(vault, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["from_schema"], "0.1")
            self.assertIn("schema_version: 0.2", (vault / "SCHEMA.md").read_text(encoding="utf-8"))
            self.assertIn("career@1", (vault / "SCHEMA.md").read_text(encoding="utf-8"))
            self.assertTrue((vault / "custom-archive" / "historical.md").is_file())
            self.assertTrue(report["backup"])
            self.assertEqual(len(list((Path(temporary) / "backups").glob("vault-*.zip"))), 1)


if __name__ == "__main__":
    unittest.main()
