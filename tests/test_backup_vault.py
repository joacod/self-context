import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKUP_SCRIPT = REPOSITORY_ROOT / ".agents/skills/self-context/scripts/backup_vault.py"
LINT_SCRIPT = REPOSITORY_ROOT / ".agents/skills/self-context/scripts/lint_vault.py"


class BackupVaultTests(unittest.TestCase):
    def run_backup(self, vault: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(BACKUP_SCRIPT), str(vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_backup_captures_state_and_excludes_backup_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            (vault / "career").mkdir(parents=True)
            (vault / "career" / "profile.md").write_text(
                "before the operation\n", encoding="utf-8"
            )
            (vault / "backups").mkdir()
            unrelated_file = vault / "backups" / "notes.txt"
            unrelated_file.write_text("leave this alone\n", encoding="utf-8")

            result = self.run_backup(vault)

            self.assertEqual(result.returncode, 0, result.stderr)
            backups = sorted((vault / "backups").glob("vault-*.zip"))
            self.assertEqual(len(backups), 1)
            with zipfile.ZipFile(backups[0]) as archive:
                self.assertEqual(
                    archive.read("career/profile.md"), b"before the operation\n"
                )
                self.assertNotIn("backups/notes.txt", archive.namelist())
            self.assertTrue(unrelated_file.is_file())

    def test_retention_keeps_only_the_newest_three_managed_backups(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            vault.mkdir()
            (vault / "SCHEMA.md").write_text("synthetic vault\n", encoding="utf-8")
            backup_dir = vault / "backups"
            backup_dir.mkdir()
            for timestamp in (
                "20000101T000000Z",
                "20000102T000000Z",
                "20000103T000000Z",
            ):
                (backup_dir / f"vault-{timestamp}.zip").write_bytes(b"old")
            unrelated_file = backup_dir / "keep.txt"
            unrelated_file.write_text("not managed\n", encoding="utf-8")

            result = self.run_backup(vault)

            self.assertEqual(result.returncode, 0, result.stderr)
            backups = sorted(backup_dir.glob("vault-*.zip"))
            self.assertEqual(len(backups), 3)
            self.assertFalse((backup_dir / "vault-20000101T000000Z.zip").exists())
            self.assertTrue((backup_dir / "vault-20000102T000000Z.zip").exists())
            self.assertTrue((backup_dir / "vault-20000103T000000Z.zip").exists())
            self.assertTrue(unrelated_file.is_file())

    def test_missing_vault_blocks_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing_vault = Path(temporary) / "vault"

            result = self.run_backup(missing_vault)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("vault does not exist", result.stderr)

    def test_linter_ignores_markdown_inside_backup_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            vault.mkdir()
            for filename in ("SCHEMA.md", "index.md", "log.md"):
                (vault / filename).write_text("# synthetic\n", encoding="utf-8")
            (vault / "backups").mkdir()
            (vault / "backups" / "not-a-page.md").write_text(
                "not durable context\n", encoding="utf-8"
            )

            result = subprocess.run(
                [sys.executable, str(LINT_SCRIPT), str(vault)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("backups/not-a-page.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
