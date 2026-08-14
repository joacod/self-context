import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest import mock
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKUP_SCRIPT = REPOSITORY_ROOT / ".agents/skills/self-context/scripts/backup_vault.py"
LINT_SCRIPT = REPOSITORY_ROOT / ".agents/skills/self-context/scripts/lint_vault.py"


class BackupVaultTests(unittest.TestCase):
    def backup_module(self):
        spec = importlib.util.spec_from_file_location("backup_vault_under_test", BACKUP_SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_backup(self, vault: Path, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(BACKUP_SCRIPT), str(vault), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_backup_captures_current_state_in_project_root_and_excludes_legacy_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            vault = project_root / "vault"
            (vault / "career").mkdir(parents=True)
            (vault / "career" / "profile.md").write_bytes(
                b"before the operation\n"
            )
            # The helper is intentionally a current-state snapshot primitive;
            # callers invoke it after their mutation so the archive is current.
            (vault / "career" / "profile.md").write_bytes(
                b"after the operation\n"
            )
            (vault / "backups").mkdir()
            legacy_file = vault / "backups" / "notes.txt"
            legacy_file.write_text("leave this alone\n", encoding="utf-8")

            result = self.run_backup(vault)

            self.assertEqual(result.returncode, 0, result.stderr)
            backups = sorted((project_root / "backups").glob("vault-*.zip"))
            self.assertEqual(len(backups), 1)
            with zipfile.ZipFile(backups[0]) as archive:
                self.assertEqual(
                    archive.read("career/profile.md"), b"after the operation\n"
                )
                self.assertNotIn("backups/notes.txt", archive.namelist())
            self.assertTrue(legacy_file.is_file())
            self.assertFalse((vault / "backups" / backups[0].name).exists())

    def test_provisional_backup_is_discarded_after_final_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            vault.mkdir()
            page = vault / "page.md"
            page.write_bytes(b"before\n")

            provisional_result = self.run_backup(vault)
            self.assertEqual(provisional_result.returncode, 0, provisional_result.stderr)
            provisional = next((root / "backups").glob("vault-*.zip"))
            page.write_bytes(b"after\n")
            final_result = self.run_backup(vault)
            self.assertEqual(final_result.returncode, 0, final_result.stderr)
            final = next(path for path in (root / "backups").glob("vault-*.zip") if path != provisional)

            discarded = self.run_backup(vault, "--discard", str(provisional))

            self.assertEqual(discarded.returncode, 0, discarded.stderr)
            self.assertFalse(provisional.exists())
            self.assertEqual(list((root / "backups").glob("vault-*.zip")), [final])
            with zipfile.ZipFile(final) as archive:
                self.assertEqual(archive.read("page.md"), b"after\n")

    def test_retention_keeps_only_the_newest_ten_managed_backups(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            vault = project_root / "vault"
            vault.mkdir()
            (vault / "SCHEMA.md").write_text("synthetic vault\n", encoding="utf-8")
            backup_dir = project_root / "backups"
            backup_dir.mkdir()
            for timestamp in (
                "20000101T000000Z",
                "20000102T000000Z",
                "20000103T000000Z",
                "20000104T000000Z",
                "20000105T000000Z",
                "20000106T000000Z",
                "20000107T000000Z",
                "20000108T000000Z",
                "20000109T000000Z",
                "20000110T000000Z",
            ):
                (backup_dir / f"vault-{timestamp}.zip").write_bytes(b"old")
            unrelated_file = backup_dir / "keep.txt"
            unrelated_file.write_text("not managed\n", encoding="utf-8")

            result = self.run_backup(vault)

            self.assertEqual(result.returncode, 0, result.stderr)
            backups = sorted(backup_dir.glob("vault-*.zip"))
            self.assertEqual(len(backups), 10)
            self.assertFalse((backup_dir / "vault-20000101T000000Z.zip").exists())
            self.assertTrue((backup_dir / "vault-20000102T000000Z.zip").exists())
            self.assertTrue((backup_dir / "vault-20000110T000000Z.zip").exists())
            self.assertTrue(unrelated_file.is_file())

    def test_retention_failure_removes_new_archive(self) -> None:
        module = self.backup_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            vault.mkdir()
            (vault / "page.md").write_text("synthetic\n", encoding="utf-8")
            backup_dir = root / "backups"
            backup_dir.mkdir()
            old = backup_dir / "vault-20000101T000000Z.zip"
            old.write_bytes(b"old")
            for number in range(2, 11):
                (backup_dir / f"vault-200001{number:02d}T000000Z.zip").write_bytes(b"old")
            class FailingBackup:
                def unlink(self):
                    raise OSError("injected retention failure")

            managed = [FailingBackup(), *([old] * 10)]
            with mock.patch.object(module, "_managed_backups", return_value=managed):
                with self.assertRaises(module.BackupError):
                    module.create_backup(vault)

            self.assertFalse(any(path.name.startswith(".vault-backup-") for path in backup_dir.iterdir()))
            self.assertEqual(len(list(backup_dir.glob("vault-*.zip"))), 10)
            self.assertFalse(any(path.name.endswith("-01.zip") for path in backup_dir.glob("vault-*.zip")))

    def test_discard_removes_only_a_managed_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            vault.mkdir()
            (vault / "page.md").write_text("synthetic\n", encoding="utf-8")
            created = self.run_backup(vault)
            self.assertEqual(created.returncode, 0, created.stderr)
            managed = next((root / "backups").glob("vault-*.zip"))

            discarded = self.run_backup(vault, "--discard", str(managed))

            self.assertEqual(discarded.returncode, 0, discarded.stderr)
            self.assertFalse(managed.exists())
            outside = root / "outside.zip"
            outside.write_bytes(b"keep")
            rejected = self.run_backup(vault, "--discard", str(outside))
            self.assertNotEqual(rejected.returncode, 0)
            self.assertTrue(outside.exists())

    def test_missing_vault_blocks_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing_vault = Path(temporary) / "vault"

            result = self.run_backup(missing_vault)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("vault does not exist", result.stderr)

    def test_symlinked_vault_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_vault = root / "real-vault"
            real_vault.mkdir()
            link = root / "vault"
            try:
                link.symlink_to(real_vault, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks unavailable: {error}")
            result = self.run_backup(link)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)

    def test_symlinked_file_and_directory_inside_vault_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            vault.mkdir()
            outside = root / "outside.txt"
            outside.write_text("private external", encoding="utf-8")
            try:
                (vault / "linked.txt").symlink_to(outside)
                (vault / "linked-dir").symlink_to(root, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks unavailable: {error}")
            result = self.run_backup(vault)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)
            self.assertEqual(list((root / "backups").glob("vault-*.zip")), [])

    def test_zip_is_verified_and_permissions_are_restrictive_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            vault.mkdir()
            (vault / "page.md").write_text("synthetic", encoding="utf-8")
            result = self.run_backup(vault)
            self.assertEqual(result.returncode, 0, result.stderr)
            destination = next((root / "backups").glob("vault-*.zip"))
            with zipfile.ZipFile(destination) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(archive.read("page.md"), b"synthetic")
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE((root / "backups").stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)

    def test_failed_backup_leaves_no_partial_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            vault.mkdir()
            # A dangling link is a deterministic failure and must not leave a
            # temporary or final managed archive behind.
            try:
                (vault / "dangling").symlink_to(root / "missing")
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks unavailable: {error}")
            result = self.run_backup(vault)
            self.assertNotEqual(result.returncode, 0)
            backup_dir = root / "backups"
            self.assertFalse(any(path.name.startswith(".vault-backup-") for path in backup_dir.iterdir()))
            self.assertEqual(list(backup_dir.glob("vault-*.zip")), [])

    def test_linter_does_not_scan_project_root_backup_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            vault = project_root / "vault"
            vault.mkdir()
            for filename in ("SCHEMA.md", "index.md", "log.md"):
                (vault / filename).write_text("# synthetic\n", encoding="utf-8")
            (project_root / "backups").mkdir()
            (project_root / "backups" / "not-a-page.md").write_text(
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
            self.assertNotIn("writing/index.md", result.stdout)

    def test_linter_checks_writing_navigation_when_writing_area_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            (vault / "writing").mkdir(parents=True)
            for filename in ("SCHEMA.md", "index.md", "log.md"):
                (vault / filename).write_text("# synthetic\n", encoding="utf-8")
            (vault / "core").mkdir()
            (vault / "career").mkdir()
            (vault / "review").mkdir()
            (vault / "sources").mkdir()
            (vault / "derived").mkdir()
            (vault / "writing" / "index.md").write_text(
                "# Writing Context\n", encoding="utf-8"
            )
            (vault / "index.md").write_text(
                "\n".join(
                    (
                        "# SelfContext Vault",
                        "SCHEMA.md",
                        "core/index.md",
                        "career/index.md",
                        "review/index.md",
                        "sources/index.md",
                        "derived/index.md",
                        "log.md",
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(LINT_SCRIPT), str(vault)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("index.md does not mention writing/index.md", result.stdout)

    def test_linter_validates_writing_artifact_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            sources = vault / "sources"
            sources.mkdir(parents=True)
            for filename in ("SCHEMA.md", "index.md", "log.md"):
                (vault / filename).write_text("# synthetic\n", encoding="utf-8")
            source = sources / "writing-source.md"
            source.write_text(
                """---
type: source
title: Synthetic writing source
description: Fictional writing source.
tags:
  - writing
status: active
generated: 2026-08-10
verified: null
sources: []
assertion_kind: source_record
stale_after: null
---

# Source
""",
                encoding="utf-8",
            )

            invalid = subprocess.run(
                [sys.executable, str(LINT_SCRIPT), str(vault)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("requires writing_evidence_role", invalid.stdout)

            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "stale_after: null\n",
                    "stale_after: null\n"
                    "writing_evidence_role: [primary]\n"
                    "authorship: user\n"
                    "ai_involvement: none\n",
                ),
                encoding="utf-8",
            )
            malformed = subprocess.run(
                [sys.executable, str(LINT_SCRIPT), str(vault)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(malformed.returncode, 0)
            self.assertNotIn("Traceback", malformed.stderr)

            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "writing_evidence_role: [primary]\n",
                    "writing_evidence_role: primary\n",
                ),
                encoding="utf-8",
            )
            valid = subprocess.run(
                [sys.executable, str(LINT_SCRIPT), str(vault)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)


if __name__ == "__main__":
    unittest.main()
