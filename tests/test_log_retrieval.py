from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
RECENT = SCRIPTS / "recent_log.py"
SEARCH = SCRIPTS / "search_log.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import log_utils  # type: ignore  # noqa: E402


class LogRetrievalTests(unittest.TestCase):
    def make_vault(self, root: Path, entries: list[str] | None = None) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        vault = root / "vault"
        vault.mkdir()
        (vault / "SCHEMA.md").write_text(
            "# Synthetic Schema\n\nschema_version: 0.2\nvertical_contracts:\n",
            encoding="utf-8",
        )
        (vault / "index.md").write_text("# Synthetic Vault\n", encoding="utf-8")
        self.write_log(vault, entries or [])
        return vault

    @staticmethod
    def write_log(vault: Path, entries: list[str]) -> None:
        text = "# Synthetic Operation Log\n\n"
        if entries:
            text += "\n\n".join(entries) + "\n"
        (vault / "log.md").write_text(text, encoding="utf-8")

    @staticmethod
    def entry(number: int, *, terms: str = "routine maintenance", body: str = "") -> str:
        detail = body or f"- summary: Synthetic operation {number}."
        return (
            f"## 2026-08-{number:02d} - operation-{number}\n"
            f"\n- operation: operation-{number}\n"
            f"- summary: {terms}.\n"
            f"- changed:\n  - [synthetic page](pages/{number}.md)\n"
            f"\n### Details\n\n{detail}"
        )

    def run_recent(self, vault: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RECENT), str(vault), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_search(
        self, vault: Path, query: str, *args: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SEARCH), query, str(vault), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_recent_returns_newest_requested_complete_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(
                Path(temporary),
                [self.entry(number) for number in range(1, 6)],
            )
            result = self.run_recent(vault, "--entries", "2")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("operation-4", result.stdout)
            self.assertIn("operation-5", result.stdout)
            self.assertNotIn("operation-3", result.stdout)
            self.assertIn("[synthetic page](pages/4.md)", result.stdout)
            self.assertIn("### Details", result.stdout)
            self.assertNotIn("## 2026-08-03", result.stdout)

    def test_recent_default_bound_does_not_include_historical_tail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            entries = [self.entry(number) for number in range(1, 31)]
            vault = self.make_vault(Path(temporary), entries)
            result = self.run_recent(vault)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("- operation: operation-"), 10)
            self.assertNotIn("operation-1", result.stdout)
            self.assertIn("operation-30", result.stdout)
            self.assertLess(len(result.stdout), len((vault / "log.md").read_text()))

    def test_recent_handles_fewer_entries_and_empty_log(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = self.make_vault(root, [self.entry(1), self.entry(2)])
            fewer = self.run_recent(vault, "--entries", "10")
            self.assertEqual(fewer.returncode, 0, fewer.stderr)
            self.assertEqual(fewer.stdout.count("- operation: operation-"), 2)

            empty = self.make_vault(root / "empty", [])
            result = self.run_recent(empty, "--entries", "10")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "No operation log entries")

    def test_recent_missing_log_uses_clean_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), [])
            (vault / "log.md").unlink()
            result = self.run_recent(vault)
            self.assertEqual(result.returncode, 1)
            self.assertIn("ERROR: missing required operation log", result.stderr)

    def test_recent_tail_reader_preserves_entry_boundary_across_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(
                Path(temporary),
                [
                    self.entry(1, body="old-entry-marker"),
                    self.entry(2, body="x" * 400),
                    self.entry(3, body="new-entry-marker"),
                ],
            )
            with patch.object(log_utils, "TAIL_CHUNK_SIZE", 64):
                entries = log_utils.read_recent_entries(vault / "log.md", limit=1)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].operation, "operation-3")
            self.assertIn("new-entry-marker", entries[0].text)
            self.assertNotIn("old-entry-marker", entries[0].text)

    def test_historical_search_finds_recent_term_and_returns_complete_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(
                Path(temporary),
                [
                    self.entry(1, terms="routine maintenance"),
                    self.entry(2, terms="migration ventures", body="- follow_up: inspect changed files"),
                    self.entry(3, terms="routine maintenance"),
                ],
            )
            result = self.run_search(vault, "migration ventures", "--limit", "5")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("## 2026-08-02 - operation-2", result.stdout)
            self.assertIn("- follow_up: inspect changed files", result.stdout)
            self.assertNotIn("## 2026-08-01", result.stdout)
            self.assertNotIn("## 2026-08-03", result.stdout)

    def test_historical_search_finds_far_back_match_in_large_log(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            entries = [self.entry(number % 28 + 1) for number in range(300)]
            entries[4] = self.entry(5, terms="legacy migration ventures", body="- changed: old-index.md")
            vault = self.make_vault(Path(temporary), entries)
            result = self.run_search(vault, "legacy migration", "--limit", "1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("old-index.md", result.stdout)
            self.assertIn("## 2026-08-05 - operation-5", result.stdout)
            self.assertLess(
                sum(line.startswith("## ") for line in result.stdout.splitlines()),
                2,
            )

    def test_historical_search_respects_limit_and_ranks_stronger_matches_first(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(
                Path(temporary),
                [
                    self.entry(1, terms="migration ventures", body="exact phrase match"),
                    self.entry(2, terms="migration only", body="weaker match"),
                    self.entry(3, terms="migration ventures", body="another exact phrase match"),
                ],
            )
            result = self.run_search(vault, "migration ventures", "--limit", "2", "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(len(report["matches"]), 2)
            self.assertEqual(
                [item["operation"] for item in report["matches"]],
                ["operation-3", "operation-1"],
            )
            self.assertEqual(report["matches"][0]["query_term_coverage"], 1.0)
            self.assertNotIn("operation-2", json.dumps(report))

    def test_historical_search_returns_clean_empty_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), [self.entry(1)])
            result = self.run_search(vault, "does-not-exist", "--limit", "3")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "No matching operation log entries")

    def test_search_is_read_only_and_json_exposes_date_and_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary), [self.entry(1, terms="migration ventures")])
            before = (vault / "log.md").read_bytes()
            result = self.run_search(vault, "migration", "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["matches"][0]["date"], "2026-08-01")
            self.assertEqual(report["matches"][0]["operation"], "operation-1")
            self.assertEqual((vault / "log.md").read_bytes(), before)
            self.assertEqual(
                sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*")),
                ["SCHEMA.md", "index.md", "log.md"],
            )


if __name__ == "__main__":
    unittest.main()
