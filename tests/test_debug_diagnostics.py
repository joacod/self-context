from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
DEBUG_SCRIPT = SCRIPTS / "debug_diagnostics.py"
RECENT_LOG_SCRIPT = SCRIPTS / "recent_log.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import debug_diagnostics  # type: ignore  # noqa: E402


class DebugDiagnosticsTests(unittest.TestCase):
    def make_project(self, temporary: str) -> tuple[Path, Path, Path]:
        project = Path(temporary) / "synthetic-project"
        vault = project / "vault"
        backups = project / "backups"
        vault.mkdir(parents=True)
        backups.mkdir()
        return project, vault, backups

    def start_report(self, output: Path, project: Path) -> Path:
        return debug_diagnostics.start_session(
            output_dir=output,
            repository_root=project,
            harness="other",
        )

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

    def write_log(self, vault: Path, text: str) -> None:
        (vault / "log.md").write_text(
            "# Synthetic operation log\n\n"
            "## 2026-08-28 - query\n\n"
            "- operation: query\n"
            f"- summary: {text}\n"
            "- changed:\n"
            "  - [Synthetic](synthetic.md)\n",
            encoding="utf-8",
        )

    def run_debug(self, output: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment[debug_diagnostics.DEBUG_DIR_ENV] = str(output)
        return subprocess.run(
            [sys.executable, str(DEBUG_SCRIPT), *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_normal_script_session_does_not_create_diagnostics_or_change_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, vault, _ = self.make_project(temporary)
            sentinel = "SYNTHETIC_NORMAL_OUTPUT_SENTINEL"
            self.write_log(vault, sentinel)
            output = project.parent / "normal-downloads"
            before = self.snapshot(project)

            environment = os.environ.copy()
            environment[debug_diagnostics.DEBUG_DIR_ENV] = str(output)
            result = subprocess.run(
                [sys.executable, str(RECENT_LOG_SCRIPT), str(vault), "--entries", "1"],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn(sentinel, result.stdout)
            self.assertEqual(self.snapshot(project), before)
            self.assertFalse(output.exists())

    def test_configured_start_uses_prompt_independent_timestamped_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, _, _ = self.make_project(temporary)
            output = Path(temporary) / "SYNTHETIC_OUTPUT_PATH_SENTINEL"
            with mock.patch.dict(
                os.environ,
                {debug_diagnostics.DEBUG_DIR_ENV: str(output)},
                clear=False,
            ):
                first = debug_diagnostics.start_session(repository_root=project)
                second = debug_diagnostics.start_session(repository_root=project)

            pattern = r"^self-context-debug-\d{8}T\d{6}Z-[0-9a-f]{16}\.md$"
            self.assertRegex(first.name, pattern)
            self.assertRegex(second.name, pattern)
            self.assertNotEqual(first.name, second.name)
            self.assertEqual(first.parent, output.resolve())
            report_text = first.read_text(encoding="ascii")
            self.assertNotIn("SYNTHETIC_PROMPT_SENTINEL", report_text)
            self.assertNotIn("SYNTHETIC_OUTPUT_PATH_SENTINEL", report_text)

    def test_report_is_incremental_and_finish_appends_fixed_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, _, _ = self.make_project(temporary)
            report = self.start_report(Path(temporary) / "downloads", project)
            partial = report.read_bytes()
            self.assertIn("event: session-started", partial.decode())
            self.assertIn("status: partial", partial.decode())
            self.assertNotIn("session-completed", partial.decode())

            debug_diagnostics.append_event(
                report,
                {
                    "event": "retry-started",
                    "component": "harness",
                    "phase": "response",
                    "operation": "query",
                    "attempt": 2,
                    "retry_count": 1,
                },
                repository_root=project,
            )
            with_retry = report.read_bytes()
            self.assertTrue(with_retry.startswith(partial))
            self.assertIn("event: retry-started", with_retry.decode())

            debug_diagnostics.finish_session(
                report,
                status="complete",
                operation="query",
                duration_ms=12,
                validation_ok=True,
                rollback_ok=True,
                provisional_backup_ok=True,
                final_backup_ok=True,
                repository_root=project,
            )
            finished = report.read_bytes()
            self.assertTrue(finished.startswith(with_retry))
            self.assertIn("event: session-completed", finished.decode())
            self.assertIn("status: complete", finished.decode())

    def test_event_catalog_rejects_unknown_values_and_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, _, _ = self.make_project(temporary)
            report = self.start_report(Path(temporary) / "downloads", project)
            base = {
                "event": "unexpected-behavior",
                "component": "harness",
                "phase": "response",
                "operation": "query",
            }
            for field, value in (
                ("event", "not-an-event"),
                ("component", "personal-page"),
                ("phase", "free-form-phase"),
                ("operation", "career"),
                ("status", "not-a-status"),
            ):
                invalid = dict(base)
                invalid[field] = value
                with self.assertRaises(debug_diagnostics.DiagnosticError):
                    debug_diagnostics.append_event(
                        report, invalid, repository_root=project
                    )

            for field in (
                "message",
                "details",
                "notes",
                "summary",
                "prompt",
                "path",
                "command",
                "stdout",
                "stderr",
                "exception",
                "finding_message",
                "finding_path",
            ):
                invalid = dict(base)
                invalid[field] = "SYNTHETIC_FORBIDDEN_TEXT"
                with self.assertRaises(debug_diagnostics.DiagnosticError):
                    debug_diagnostics.append_event(
                        report, invalid, repository_root=project
                    )

            for invalid in (
                {**base, "attempt": 0},
                {**base, "exit_code": 2_147_483_648},
                {**base, "finding_counts": {"personal": 1}},
                {**base, "validation_ok": "true"},
            ):
                with self.assertRaises(debug_diagnostics.DiagnosticError):
                    debug_diagnostics.append_event(
                        report, invalid, repository_root=project
                    )

            text = report.read_text(encoding="ascii")
            self.assertNotIn("SYNTHETIC_FORBIDDEN_TEXT", text)
            self.assertNotIn("personal-page", text)

    def test_wrapped_script_keeps_output_and_exit_code_without_serializing_sensitive_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, vault, _ = self.make_project(temporary)
            output = Path(temporary) / "downloads"
            report = self.start_report(output, project)
            sentinel = "SYNTHETIC_VAULT_AND_STDOUT_SENTINEL"
            self.write_log(vault, sentinel)

            success = self.run_debug(
                output,
                "run",
                "--report",
                str(report),
                "--component",
                "recent-log",
                "--phase",
                "retrieval",
                "--operation",
                "query",
                "--",
                str(vault),
                "--entries",
                "1",
            )
            self.assertEqual(success.returncode, 0)
            self.assertIn(sentinel, success.stdout)
            report_text = report.read_text(encoding="ascii")
            self.assertIn("event: script-succeeded", report_text)
            self.assertNotIn(sentinel, report_text)
            self.assertNotIn(str(project), report_text)
            self.assertNotIn(str(vault), report_text)
            self.assertNotIn("synthetic.md", report_text)

            missing = project / "SYNTHETIC_ARG_AND_ERROR_PATH_SENTINEL"
            failure = self.run_debug(
                output,
                "run",
                "--report",
                str(report),
                "--component",
                "recent-log",
                "--phase",
                "retrieval",
                "--operation",
                "query",
                "--",
                str(missing),
                "--entries",
                "1",
            )
            self.assertEqual(failure.returncode, 1)
            self.assertIn("SYNTHETIC_ARG_AND_ERROR_PATH_SENTINEL", failure.stderr)
            report_text = report.read_text(encoding="ascii")
            self.assertIn("event: script-failed", report_text)
            self.assertNotIn("SYNTHETIC_ARG_AND_ERROR_PATH_SENTINEL", report_text)
            self.assertNotIn("SYNTHETIC_VAULT_AND_STDOUT_SENTINEL", report_text)

    def test_tool_exception_and_finding_data_never_serialize_messages_or_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, _, _ = self.make_project(temporary)
            report = self.start_report(Path(temporary) / "downloads", project)
            with mock.patch.object(
                debug_diagnostics.subprocess,
                "run",
                side_effect=OSError("SYNTHETIC_EXCEPTION_MESSAGE"),
            ):
                result = debug_diagnostics.run_wrapped(
                    report,
                    component="recent-log",
                    phase="retrieval",
                    operation="query",
                    repository_root=project,
                )
            self.assertEqual(result, 1)
            text = report.read_text(encoding="ascii")
            self.assertIn("event: tool-call-failed", text)
            for sentinel in (
                "SYNTHETIC_EXCEPTION_MESSAGE",
                "SYNTHETIC_FINDING_MESSAGE",
                "SYNTHETIC_FINDING_PATH",
                str(project),
            ):
                self.assertNotIn(sentinel, text)

    def test_output_targets_inside_repository_vault_or_backups_are_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project, vault, backups = self.make_project(temporary)
            marker = vault / "synthetic-marker.txt"
            marker.write_text("SYNTHETIC_VAULT_MARKER", encoding="utf-8")
            before = self.snapshot(project)
            for target in (project, vault, backups, project / "new-output"):
                with self.assertRaises(debug_diagnostics.DiagnosticError):
                    debug_diagnostics.start_session(
                        output_dir=target,
                        repository_root=project,
                    )
            with mock.patch.dict(
                os.environ,
                {debug_diagnostics.DEBUG_DIR_ENV: ""},
                clear=False,
            ):
                with self.assertRaises(debug_diagnostics.DiagnosticError):
                    debug_diagnostics.start_session(repository_root=project)
            self.assertEqual(self.snapshot(project), before)

    def test_reports_and_directories_use_owner_only_permissions_on_posix(self) -> None:
        if os.name != "posix":
            self.skipTest("owner-only permissions are platform-specific")
        with tempfile.TemporaryDirectory() as temporary:
            project, _, _ = self.make_project(temporary)
            output = Path(temporary) / "downloads"
            report = self.start_report(output, project)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(report.stat().st_mode), 0o600)

    def test_skill_documents_exact_prefix_and_safe_overlay_boundaries(self) -> None:
        skill = (ROOT / ".agents/skills/self-context/SKILL.md").read_text(
            encoding="utf-8"
        )
        reference = (
            ROOT / ".agents/skills/self-context/references/debug-diagnostics.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`--debug-mode `", skill)
        self.assertIn("remove that prefix", skill)
        self.assertIn("references/debug-diagnostics.md", skill)
        self.assertIn("safe operational metadata, not sanitized transcripts", reference)
        self.assertIn("never read the report back", reference)
        self.assertIn("not a third", reference)

    def test_skill_evals_cover_prefix_activation_removal_and_non_prefix(self) -> None:
        import json

        path = ROOT / ".agents/skills/self-context/evals/evals.json"
        cases = json.loads(path.read_text(encoding="utf-8"))["evals"]
        selected = {int(case["id"]): case for case in cases if int(case["id"]) >= 159}
        self.assertEqual(set(selected), {159, 160, 161})
        self.assertTrue(selected[159]["prompt"].startswith("--debug-mode "))
        self.assertTrue(selected[160]["prompt"].startswith("--debug-mode "))
        self.assertFalse(selected[161]["prompt"].startswith("--debug-mode "))
        combined = "\n".join(
            str(case["prompt"]) + "\n" + str(case["expected_output"])
            for case in selected.values()
        )
        self.assertIn("removed before", combined)
        self.assertIn("not a debug prefix", combined)


if __name__ == "__main__":
    unittest.main()
