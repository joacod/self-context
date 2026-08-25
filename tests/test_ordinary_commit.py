from __future__ import annotations

import datetime as date
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
TESTS = ROOT / "tests"
for import_path in (SCRIPTS, TESTS):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import lint_vault  # type: ignore  # noqa: E402
import ordinary_commit  # type: ignore  # noqa: E402
import vault_utils  # type: ignore  # noqa: E402
from synthetic_vault import (  # type: ignore  # noqa: E402
    backup_paths,
    build_synthetic_vault,
    tree_snapshot,
)


PAGE = """---
type: concept
title: Synthetic Ordinary Page
description: A fictional page for ordinary commit tests.
tags:
  - synthetic
status: active
generated: 2026-08-24
verified: null
sources: []
assertion_kind: user_stated_fact
stale_after: null
---

Synthetic ordinary mutation body.
"""

VENTURE_PAGE = """---
type: concept
title: Synthetic Venture
description: A fictional venture for activation tests.
tags:
  - synthetic
status: active
generated: 2026-08-24
verified: null
sources: []
assertion_kind: user_stated_fact
stale_after: null
---

Synthetic venture body.
"""


class OrdinaryCommitTests(unittest.TestCase):
    def proposal(
        self,
        *,
        writes: dict[str, str | bytes] | None = None,
        activations: list[str] | None = None,
        paths: list[str] | None = None,
        summary: str = "Applied a synthetic ordinary mutation",
        operation: str = "ingest",
        expected_snapshot: str | None = None,
    ) -> dict:
        return {
            "expected_snapshot": expected_snapshot,
            "writes": writes or {},
            "activations": activations or [],
            "log": {
                "operation": operation,
                "summary": summary,
                "paths": paths or sorted((writes or {}).keys()),
            },
        }

    def test_current_compatible_vault_create_succeeds_with_one_final_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(writes={"career/ordinary-page.md": PAGE}),
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["state"], "committed")
            self.assertTrue((vault / "career/ordinary-page.md").is_file())
            self.assertIn("career/index.md", result["modified"])
            self.assertIn("career/ordinary-page.md", result["created"])
            self.assertTrue(result["provisional_discarded"])
            self.assertTrue(Path(result["final_backup"]).is_file())
            self.assertEqual(len(backup_paths(project)), 1)

    def test_update_page_is_committed_and_logged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            page = vault / "career" / "harbor-launch.md"
            updated = page.read_text(encoding="utf-8") + "\nAdditional fictional evidence.\n"
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(
                    writes={"career/harbor-launch.md": updated},
                    paths=["career/harbor-launch.md"],
                    summary="Updated one synthetic page",
                ),
            )

            self.assertEqual(result["status"], "success")
            self.assertIn("career/harbor-launch.md", result["modified"])
            self.assertIn("Updated one synthetic page", (vault / "log.md").read_text())
            self.assertIn("Additional fictional evidence", page.read_text())

    def test_semantic_noop_creates_no_backup_or_log_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            page = vault / "career" / "harbor-launch.md"
            before_tree = tree_snapshot(vault)
            before_log = (vault / "log.md").read_bytes()
            result = ordinary_commit.commit_mutation(
                vault,
                {"writes": {"career/harbor-launch.md": page.read_bytes()}},
            )

            self.assertEqual(result["status"], "noop")
            self.assertEqual(result["state"], "no-op")
            self.assertEqual(result["changed"], [])
            self.assertEqual(tree_snapshot(vault), before_tree)
            self.assertEqual((vault / "log.md").read_bytes(), before_log)
            self.assertEqual(backup_paths(project), [])

    def test_managed_index_is_in_same_active_write_set_and_final_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            captured: dict[str, bytes] = {}
            real_replace = ordinary_commit.file_transaction.replace_planned_files

            def capture(path: Path, updates: dict[str, bytes]) -> dict:
                captured.update(updates)
                return real_replace(path, updates)

            with mock.patch.object(
                ordinary_commit.file_transaction,
                "replace_planned_files",
                side_effect=capture,
            ):
                result = ordinary_commit.commit_mutation(
                    vault,
                    self.proposal(writes={"career/ordinary-page.md": PAGE}),
                )

            self.assertEqual(result["status"], "success")
            self.assertIn("career/ordinary-page.md", captured)
            self.assertIn("career/index.md", captured)
            self.assertIn("log.md", captured)
            with zipfile.ZipFile(result["final_backup"]) as archive:
                self.assertIn("career/ordinary-page.md", archive.namelist())
                self.assertIn(b"Synthetic Ordinary Page", archive.read("career/index.md"))
                self.assertIn(b"ingest", archive.read("log.md"))

    def test_manual_index_text_and_custom_area_survive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            index = vault / "career" / "index.md"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "<!-- selfcontext:catalog:start -->",
                    "Manual prefix that must remain.\n\n<!-- selfcontext:catalog:start -->",
                )
                + "\nManual suffix that must remain.\n",
                encoding="utf-8",
            )
            custom = vault / "custom-notes" / "field-log.md"
            custom_before = custom.read_bytes()
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(writes={"career/ordinary-page.md": PAGE}),
            )

            self.assertEqual(result["status"], "success")
            updated_index = index.read_text(encoding="utf-8")
            self.assertIn("Manual prefix that must remain.", updated_index)
            self.assertIn("Manual suffix that must remain.", updated_index)
            self.assertEqual(custom.read_bytes(), custom_before)

    def test_operation_log_escapes_special_canonical_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            label = "career/space [one].md"
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(
                    writes={label: PAGE},
                    paths=[label],
                    summary="Stored a path with Markdown punctuation",
                ),
            )

            self.assertEqual(result["status"], "success")
            log = (vault / "log.md").read_text(encoding="utf-8")
            self.assertIn(r"career/space \[one\].md", log)
            self.assertIn("career/space%20%5Bone%5D.md", log)
            errors, _ = lint_vault.lint_vault(vault, date.date.today())
            self.assertEqual(errors, [])

    def test_explicit_one_vertical_activation_uses_exact_catalog_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(
                    writes={"ventures/example.md": VENTURE_PAGE},
                    activations=["ventures"],
                    paths=["ventures/example.md"],
                    summary="Activated the synthetic ventures area",
                ),
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["activations"], ["ventures"])
            schema = (vault / "SCHEMA.md").read_text(encoding="utf-8")
            catalog = vault_utils.load_vertical_catalog()
            version = next(
                record["contract_version"]
                for record in catalog["verticals"]
                if record["id"] == "ventures"
            )
            self.assertIn(f"- ventures@{version}", schema)
            self.assertTrue((vault / "ventures" / "index.md").is_file())
            self.assertIn("ventures/index.md", (vault / "index.md").read_text())
            self.assertIn("Synthetic Venture", (vault / "ventures" / "index.md").read_text())
            self.assertFalse((vault / "media").exists())

    def test_activation_is_never_inferred_from_a_semantic_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            before = tree_snapshot(vault)
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(
                    writes={"media/inferred.md": PAGE},
                    paths=["media/inferred.md"],
                ),
            )

            self.assertNotEqual(result["status"], "success")
            self.assertEqual(result["activations"], [])
            self.assertEqual(backup_paths(project), [])
            self.assertEqual(tree_snapshot(vault), before)
            self.assertFalse((vault / "media").exists())

    def test_old_future_and_malformed_runtime_states_block_without_side_effects(self) -> None:
        variants = ("old", "future", "malformed")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for variant in variants:
                with self.subTest(variant=variant):
                    project = root / variant
                    vault = build_synthetic_vault(
                        project, schema_version="0.1" if variant == "old" else "0.2"
                    )
                    schema = vault / "SCHEMA.md"
                    if variant == "future":
                        schema.write_text("# Future\n\nschema_version: 0.3\n", encoding="utf-8")
                    elif variant == "malformed":
                        schema.write_text("# Broken\n\nschema_version: not-a-version\n", encoding="utf-8")
                    before = tree_snapshot(vault)
                    result = ordinary_commit.commit_mutation(
                        vault,
                        self.proposal(writes={"career/ordinary-page.md": PAGE}),
                    )

                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(backup_paths(project), [])
                    self.assertEqual(tree_snapshot(vault), before)
                    self.assertTrue(result["findings"])

    def test_missing_and_empty_vaults_report_initialization_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = root / "missing-vault"
            result = ordinary_commit.commit_mutation(
                missing,
                self.proposal(writes={"core/new.md": PAGE}),
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["state"], "initialization-required")
            self.assertFalse(missing.exists())
            self.assertFalse((root / "backups").exists())

            empty = root / "empty-vault"
            empty.mkdir()
            result = ordinary_commit.commit_mutation(
                empty,
                self.proposal(writes={"core/new.md": PAGE}),
            )
            self.assertEqual(result["state"], "initialization-required")
            self.assertEqual(list(empty.iterdir()), [])

    def test_absolute_traversal_and_out_of_vault_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            outside = project / "outside.md"
            for label in (str(outside), "../outside.md", "core/../../outside.md"):
                with self.subTest(label=label):
                    result = ordinary_commit.commit_mutation(
                        vault,
                        self.proposal(writes={label: PAGE}, paths=[label]),
                    )
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(result["state"], "input-invalid")
                    self.assertFalse(outside.exists())
                    self.assertEqual(backup_paths(project), [])

    def test_symlink_traversal_and_nonregular_targets_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            outside = project / "outside"
            outside.mkdir()
            (vault / "linked").symlink_to(outside, target_is_directory=True)
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(writes={"linked/new.md": PAGE}, paths=["linked/new.md"]),
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(backup_paths(project), [])

            target = vault / "core" / "directory-target.md"
            target.mkdir()
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(writes={"core/directory-target.md": PAGE}),
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["state"], "input-invalid")
            self.assertTrue(target.is_dir())

    def test_unsupported_deletion_is_explicitly_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            result = ordinary_commit.commit_mutation(
                vault,
                {
                    "deletes": ["career/harbor-launch.md"],
                    "log": {
                        "operation": "review",
                        "summary": "Delete attempt",
                        "paths": ["career/harbor-launch.md"],
                    },
                },
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["state"], "input-invalid")
            self.assertTrue(any(item["classification"] == "unsupported-deletion" for item in result["findings"]))
            self.assertEqual(backup_paths(project), [])

    def test_expected_snapshot_mismatch_blocks_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            before = tree_snapshot(vault)
            result = ordinary_commit.commit_mutation(
                vault,
                self.proposal(
                    writes={"career/ordinary-page.md": PAGE},
                    expected_snapshot="not-the-current-snapshot",
                ),
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["state"], "snapshot-mismatch")
            self.assertEqual(backup_paths(project), [])
            self.assertEqual(tree_snapshot(vault), before)

    def test_source_change_during_staging_blocks_before_active_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            real_sync = ordinary_commit.sync_indexes.synchronize
            changed = {"value": False}

            def mutate_active_after_stage(path: Path, write: bool = False) -> dict:
                result = real_sync(path, write=write)
                if write and path.resolve() != vault.resolve() and not changed["value"]:
                    (vault / "log.md").write_text("# changed outside staging\n", encoding="utf-8")
                    changed["value"] = True
                return result

            with mock.patch.object(
                ordinary_commit.sync_indexes,
                "synchronize",
                side_effect=mutate_active_after_stage,
            ):
                result = ordinary_commit.commit_mutation(
                    vault,
                    self.proposal(writes={"career/ordinary-page.md": PAGE}),
                )

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["state"], "snapshot-drift")
            self.assertEqual(backup_paths(project), [])
            self.assertFalse((vault / "career" / "ordinary-page.md").exists())

    def test_proposed_validation_failure_has_zero_active_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            before = tree_snapshot(vault)
            real_validate = ordinary_commit._validate_state

            def fail_stage(path: Path) -> dict:
                if path.resolve() != vault.resolve():
                    return {"ok": False, "ordinary": {"errors": [{"path": "career/ordinary-page.md", "message": "synthetic proposed failure"}]}}
                return real_validate(path)

            with mock.patch.object(ordinary_commit, "_validate_state", side_effect=fail_stage):
                result = ordinary_commit.commit_mutation(
                    vault,
                    self.proposal(writes={"career/ordinary-page.md": PAGE}),
                )

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["state"], "proposed-validation")
            self.assertEqual(backup_paths(project), [])
            self.assertEqual(tree_snapshot(vault), before)

    def test_replacement_failure_rolls_back_and_retains_provisional_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            before = tree_snapshot(vault)
            real_replace = ordinary_commit.file_transaction.os.replace
            calls = {"count": 0}

            def fail_second(source: str | Path, destination: str | Path) -> None:
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("synthetic replacement failure")
                real_replace(source, destination)

            real_transaction = ordinary_commit.file_transaction.replace_planned_files

            def replace_with_injected_failure(path: Path, updates: dict[str, bytes]) -> dict:
                with mock.patch.object(
                    ordinary_commit.file_transaction.os,
                    "replace",
                    side_effect=fail_second,
                ):
                    return real_transaction(path, updates)

            with mock.patch.object(
                ordinary_commit.file_transaction,
                "replace_planned_files",
                side_effect=replace_with_injected_failure,
            ):
                result = ordinary_commit.commit_mutation(
                    vault,
                    self.proposal(writes={"career/ordinary-page.md": PAGE}),
                )

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["state"], "active-replacement")
            self.assertEqual(result["rollback"]["status"], "rolled-back")
            self.assertEqual(tree_snapshot(vault), before)
            self.assertEqual(len(backup_paths(project)), 1)
            self.assertFalse(any("transaction-" in path.name for path in vault.rglob(".*")))

    def test_active_validation_failure_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            before = tree_snapshot(vault)
            real_validate = ordinary_commit._validate_state

            def fail_active(path: Path) -> dict:
                if path.resolve() == vault.resolve():
                    return {"ok": False, "ordinary": {"errors": [{"path": "", "message": "synthetic active failure"}]}}
                return real_validate(path)

            with mock.patch.object(ordinary_commit, "_validate_state", side_effect=fail_active):
                result = ordinary_commit.commit_mutation(
                    vault,
                    self.proposal(writes={"career/ordinary-page.md": PAGE}),
                )

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["state"], "active-validation")
            self.assertEqual(result["rollback"]["status"], "rolled-back")
            self.assertEqual(tree_snapshot(vault), before)
            self.assertEqual(len(backup_paths(project)), 1)

    def test_final_backup_failure_rolls_back_and_retains_provisional(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            before = tree_snapshot(vault)
            real_backup = ordinary_commit.backup_vault.create_backup
            calls = {"count": 0}

            def first_backup_then_fail(path: Path):
                calls["count"] += 1
                if calls["count"] == 1:
                    return real_backup(path)
                raise ordinary_commit.backup_vault.BackupError("synthetic final backup failure")

            with mock.patch.object(
                ordinary_commit.backup_vault,
                "create_backup",
                side_effect=first_backup_then_fail,
            ):
                result = ordinary_commit.commit_mutation(
                    vault,
                    self.proposal(writes={"career/ordinary-page.md": PAGE}),
                )

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["state"], "final-backup")
            self.assertEqual(result["rollback"]["status"], "rolled-back")
            self.assertEqual(tree_snapshot(vault), before)
            self.assertTrue(Path(result["provisional_backup"]).is_file())
            self.assertEqual(len(backup_paths(project)), 1)

    def test_rollback_verification_failure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            with mock.patch.object(
                ordinary_commit.file_transaction,
                "rollback_transaction",
                return_value={
                    "status": "rollback-failed",
                    "ok": False,
                    "failures": ["synthetic rollback failure"],
                },
            ):
                with mock.patch.object(
                    ordinary_commit,
                    "_validate_state",
                    side_effect=[
                        {"ok": True},
                        {"ok": False, "ordinary": {"errors": [{"path": "", "message": "active failure"}]}},
                    ],
                ):
                    result = ordinary_commit.commit_mutation(
                        vault,
                        self.proposal(writes={"career/ordinary-page.md": PAGE}),
                    )

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["rollback"]["status"], "rollback-failed")
            self.assertTrue(any(item["classification"] == "rollback" for item in result["findings"]))
            self.assertEqual(len(backup_paths(project)), 1)

    def test_provisional_discard_failure_keeps_valid_committed_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            with mock.patch.object(
                ordinary_commit.backup_vault,
                "discard_backup",
                side_effect=ordinary_commit.backup_vault.BackupError("synthetic cleanup failure"),
            ):
                result = ordinary_commit.commit_mutation(
                    vault,
                    self.proposal(writes={"career/ordinary-page.md": PAGE}),
                )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["state"], "committed")
            self.assertFalse(result["provisional_discarded"])
            self.assertTrue((vault / "career" / "ordinary-page.md").is_file())
            self.assertTrue(Path(result["final_backup"]).is_file())
            self.assertEqual(len(backup_paths(project)), 2)
            self.assertTrue(any(item["classification"] == "backup-cleanup" for item in result["findings"]))

    def test_cli_returns_machine_readable_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = build_synthetic_vault(project)
            proposal = json.dumps(self.proposal(writes={"career/ordinary-page.md": PAGE}))
            result = __import__("subprocess").run(
                [sys.executable, str(SCRIPTS / "ordinary_commit.py"), str(vault), "--proposal", proposal],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "success")
            self.assertNotIn("Synthetic ordinary mutation body", result.stdout)


if __name__ == "__main__":
    unittest.main()
