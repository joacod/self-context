import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Iterable, Optional


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
SEARCH = SCRIPTS / "search_vault.py"


class SearchVaultTests(unittest.TestCase):
    def write_page(
        self,
        vault: Path,
        relative: str,
        *,
        title: str,
        description: str,
        body: str,
        aliases: Iterable[str] = (),
        identifier: Optional[str] = None,
        page_type: str = "concept",
        status: str = "active",
        assertion: str = "user_stated_fact",
        tags: Iterable[str] = ("synthetic",),
        superseded_by: Optional[str] = None,
    ) -> None:
        lines = ["---", f"type: {page_type}"]
        if identifier:
            lines.append(f"id: {identifier}")
        lines.extend([f"title: {title}", "aliases:"])
        lines.extend(f"  - {alias}" for alias in aliases)
        lines.extend(
            [
                f"description: {description}",
                "tags:",
            ]
        )
        lines.extend(f"  - {tag}" for tag in tags)
        lines.extend(
            [
                f"status: {status}",
                "generated: 2026-08-12",
                "verified: null",
                "sources: []",
                f"assertion_kind: {assertion}",
                "stale_after: null",
            ]
        )
        if superseded_by:
            lines.append(f"superseded_by: {superseded_by}")
        lines.extend(["---", "", body, ""])
        path = vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")

    def make_vault(self, root: Path) -> Path:
        vault = root / "vault"
        for directory in (
            "core",
            "career",
            "learning",
            "writing",
            "review",
            "sources",
            "derived",
        ):
            (vault / directory).mkdir(parents=True)
        (vault / "SCHEMA.md").write_text(
            "# Schema\n\nschema_version: 0.1\n", encoding="utf-8"
        )
        (vault / "index.md").write_text("# Root\n", encoding="utf-8")
        (vault / "log.md").write_text("# Log\n", encoding="utf-8")
        for directory in (
            "core",
            "career",
            "learning",
            "writing",
            "review",
            "sources",
            "derived",
        ):
            (vault / directory / "index.md").write_text(
                f"# {directory}\n", encoding="utf-8"
            )
        self.write_page(
            vault,
            "core/title.md",
            title="Synthetic Queue",
            aliases=("queue alias",),
            description="A page about an unrelated concept.",
            status="active",
            body="## Concept\n\nbody only",
        )
        self.write_page(
            vault,
            "core/body.md",
            title="Synthetic Concept",
            aliases=("other",),
            description="Navigation page.",
            status="active",
            body="## Queue heading\n\nqueue in the body",
        )
        self.write_page(
            vault,
            "review/review.md",
            title="Review Queue",
            aliases=("review queue",),
            description="A provisional queue observation.",
            status="review",
            assertion="agent_inference",
            page_type="observation",
            body="## Review\n\nqueue review",
        )
        self.write_page(
            vault,
            "sources/source.md",
            title="Synthetic Source",
            aliases=("source",),
            description="Raw queue source.",
            status="active",
            assertion="source_record",
            page_type="source",
            body="## Source\n\nqueue source",
        )
        return vault

    def make_lookup_vault(self, root: Path) -> Path:
        vault = self.make_vault(root)
        self.write_page(
            vault,
            "core/id.md",
            identifier="page-042",
            title="Stable Record",
            aliases=("record",),
            description="A stable identifier fixture.",
            body="## Identifier\n\nidentifier fixture",
        )
        self.write_page(
            vault,
            "core/one-word.md",
            title="Leadership",
            aliases=("lead",),
            description="A one-word title fixture.",
            body="## Lookup\n\nleadership fixture",
        )
        self.write_page(
            vault,
            "core/acronym.md",
            title="Frontend Engineering",
            aliases=("FE",),
            description="An acronym alias fixture.",
            body="## Lookup\n\nfrontend fixture",
        )
        self.write_page(
            vault,
            "core/unicode.md",
            title="Coffee",
            aliases=("Café",),
            description="A Unicode alias fixture.",
            body="## Lookup\n\nunicode fixture",
        )
        self.write_page(
            vault,
            "core/punctuation.md",
            title="C++ Notes",
            aliases=("plus notes",),
            description="A punctuation title fixture.",
            body="## Lookup\n\npunctuation fixture",
        )
        return vault

    def make_task_vault(self, root: Path) -> Path:
        vault = self.make_vault(root)
        self.write_page(
            vault,
            "career/frontend-leadership.md",
            title="Frontend Leadership Interview",
            aliases=("frontend leadership prep",),
            description=(
                "Prepare a frontend leadership interview with mentoring and delivery examples."
            ),
            body=(
                "## Interview\n\nPrepare frontend leadership interview examples for the task."
            ),
        )
        self.write_page(
            vault,
            "career/frontend-leadership-archived.md",
            title="Frontend Leadership Interview",
            aliases=("frontend leadership prep",),
            description="An archived duplicate of the interview context.",
            status="archived",
            body="## Historical\n\nOld frontend leadership interview context.",
        )
        self.write_page(
            vault,
            "career/leadership.md",
            title="Leadership",
            description="A single incidental title-token match.",
            body="## General\n\nA broad leadership note.",
        )
        self.write_page(
            vault,
            "writing/technical-project-explanation.md",
            title="Technical Project Explanation",
            aliases=("concise project explanation",),
            description=(
                "Write concise technical project explanations for a non-specialist audience."
            ),
            body=(
                "## Writing\n\nWrite a concise technical project explanation."
            ),
        )
        self.write_page(
            vault,
            "core/project.md",
            title="Project",
            description="A single incidental project-token match.",
            body="## General\n\nA project note.",
        )
        self.write_page(
            vault,
            "learning/distributed-systems-gaps.md",
            title="Distributed Systems Knowledge Gaps",
            description="Refresh distributed systems knowledge and identify gaps.",
            body="## Learning\n\nRefresh knowledge of distributed systems gaps.",
        )
        self.write_page(
            vault,
            "core/gaps.md",
            title="Gaps",
            description="A single incidental gaps-token match.",
            body="## General\n\nA gap note.",
        )
        self.write_page(
            vault,
            "career/cross-team-conflict.md",
            title="Cross-Team Conflict Resolution",
            description="Examples of cross-team conflict resolution from delivery work.",
            body="## Examples\n\nExamples of cross-team conflict resolution.",
        )
        self.write_page(
            vault,
            "core/conflict.md",
            title="Conflict",
            description="A single incidental conflict-token match.",
            body="## General\n\nA conflict note.",
        )
        self.write_page(
            vault,
            "career/past-role.md",
            title="Past Role Before Current Company",
            description="The role held before the current company.",
            body="## Career\n\nPast role before current company.",
        )
        self.write_page(
            vault,
            "career/past-role-superseded.md",
            title="Past Role Before Current Company",
            description="Historical role context retained for continuity.",
            status="superseded",
            superseded_by="past-role.md",
            body="## Historical\n\nPast role before current company.",
        )
        self.write_page(
            vault,
            "sources/frontend-source.md",
            title="Frontend Leadership Interview Source",
            description="Prepare frontend leadership interview source material.",
            page_type="source",
            assertion="source_record",
            body="## Source\n\nSource material for frontend leadership interview.",
        )
        self.write_page(
            vault,
            "review/deep-reviews/frontend-report.md",
            title="Frontend Leadership Interview Report",
            description="A deep-review report that must not be searchable.",
            body="## Report\n\nPrepare frontend leadership interview.",
        )
        self.write_page(
            vault,
            "core/tie-a.md",
            title="Deterministic Tie",
            description="Same deterministic tie fixture.",
            body="## Tie\n\nSame tie fixture.",
        )
        self.write_page(
            vault,
            "core/tie-b.md",
            title="Deterministic Tie",
            description="Same deterministic tie fixture.",
            body="## Tie\n\nSame tie fixture.",
        )
        return vault

    def run_search(
        self, vault: Path, query: str, *args: str
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SEARCH), query, str(vault), *args, "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

    def report(self, vault: Path, query: str, *args: str) -> dict:
        result = self.run_search(vault, query, *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_ranking_prefers_title_then_heading_then_body_and_review_remains_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            report = self.report(vault, "queue")
            paths = [item["path"] for item in report["results"]]
            self.assertEqual(paths[:3], ["core/title.md", "review/review.md", "core/body.md"])
            self.assertEqual(report["results"][0]["match_type"], "title_phrase")

    def test_sources_remain_opt_in_while_historical_pages_are_default_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            self.write_page(
                vault,
                "core/archived.md",
                title="Archived Queue",
                aliases=("old queue",),
                description="An archived queue page.",
                status="archived",
                body="## History\n\narchived queue",
            )
            self.write_page(
                vault,
                "core/superseded.md",
                title="Superseded Queue",
                aliases=("old queue",),
                description="A superseded queue page.",
                status="superseded",
                superseded_by="title.md",
                body="## History\n\nsuperseded queue",
            )
            default = self.report(vault, "queue")
            default_paths = [item["path"] for item in default["results"]]
            self.assertIn("core/archived.md", default_paths)
            self.assertIn("core/superseded.md", default_paths)
            self.assertLess(default_paths.index("core/title.md"), default_paths.index("core/archived.md"))
            self.assertLess(default_paths.index("core/title.md"), default_paths.index("core/superseded.md"))

            without_archived = self.report(vault, "queue", "--exclude-archived")
            self.assertNotIn(
                "core/archived.md",
                [item["path"] for item in without_archived["results"]],
            )
            without_superseded = self.report(vault, "queue", "--exclude-superseded")
            self.assertNotIn(
                "core/superseded.md",
                [item["path"] for item in without_superseded["results"]],
            )

            included_sources = self.report(vault, "queue", "--include-sources")
            self.assertIn(
                "sources/source.md",
                [item["path"] for item in included_sources["results"]],
            )

    def test_json_contains_bounded_metadata_and_deterministic_match_explanation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            report = self.report(vault, "queue")
            self.assertTrue(report["results"])
            self.assertNotIn("Synthetic text that should not be emitted", json.dumps(report))
            expected = {
                "path",
                "title",
                "description",
                "status",
                "assertion_kind",
                "matched_fields",
                "vertical",
                "snippet",
                "match_type",
                "query_term_coverage",
                "matched_term_count",
                "query_term_count",
                "phrase_fields",
                "rank_score",
            }
            for item in report["results"]:
                self.assertEqual(set(item), expected)
                self.assertIsInstance(item["rank_score"], int)
                self.assertGreaterEqual(item["query_term_coverage"], 0)
                self.assertLessEqual(item["query_term_coverage"], 1)

    def test_exact_and_concise_lookup_regressions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_lookup_vault(Path(temporary))

            cases = (
                ("page-042", "core/id.md", "exact_id"),
                ("Stable Record", "core/id.md", "exact_title"),
                ("record", "core/id.md", "exact_alias"),
                ("Leadership", "core/one-word.md", "exact_title"),
                ("fe", "core/acronym.md", "exact_alias"),
                ("CAFÉ", "core/unicode.md", "exact_alias"),
                ("C++ Notes", "core/punctuation.md", "exact_title"),
            )
            for query, expected_path, expected_match_type in cases:
                with self.subTest(query=query):
                    results = self.report(vault, query)["results"]
                    self.assertTrue(results)
                    self.assertEqual(results[0]["path"], expected_path)
                    self.assertEqual(results[0]["match_type"], expected_match_type)

    def test_task_queries_prioritize_coverage_over_incidental_title_tokens(self) -> None:
        queries = (
            ("prepare frontend leadership interview", "career/frontend-leadership.md"),
            ("write concise technical project explanation", "writing/technical-project-explanation.md"),
            ("refresh distributed systems knowledge gaps", "learning/distributed-systems-gaps.md"),
            ("examples of cross-team conflict resolution", "career/cross-team-conflict.md"),
            ("past role before current company", "career/past-role.md"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_task_vault(Path(temporary))
            for query, expected_path in queries:
                with self.subTest(query=query):
                    results = self.report(vault, query)["results"]
                    self.assertTrue(results)
                    self.assertEqual(results[0]["path"], expected_path)
                    self.assertGreaterEqual(results[0]["query_term_coverage"], 0.8)

            past_role_paths = [
                item["path"]
                for item in self.report(vault, "past role before current company")["results"]
            ]
            self.assertIn("career/past-role-superseded.md", past_role_paths)
            self.assertLess(
                past_role_paths.index("career/past-role.md"),
                past_role_paths.index("career/past-role-superseded.md"),
            )

            archived_duplicate_paths = [
                item["path"]
                for item in self.report(vault, "Frontend Leadership Interview")["results"]
            ]
            self.assertEqual(archived_duplicate_paths[:2], [
                "career/frontend-leadership.md",
                "career/frontend-leadership-archived.md",
            ])

    def test_source_vertical_and_deep_review_filters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_task_vault(Path(temporary))
            query = "prepare frontend leadership interview"
            default = self.report(vault, query)
            default_paths = [item["path"] for item in default["results"]]
            self.assertNotIn("sources/frontend-source.md", default_paths)
            self.assertNotIn("review/deep-reviews/frontend-report.md", default_paths)

            with_sources = self.report(vault, query, "--include-sources")
            source_paths = [item["path"] for item in with_sources["results"]]
            self.assertIn("sources/frontend-source.md", source_paths)
            self.assertLess(
                source_paths.index("career/frontend-leadership.md"),
                source_paths.index("sources/frontend-source.md"),
            )

            career = self.report(vault, "technical project explanation", "--vertical", "career")
            self.assertEqual(career["results"], [])
            writing = self.report(vault, "technical project explanation", "--vertical", "writing")
            self.assertEqual(writing["results"][0]["vertical"], "writing")
            self.assertEqual(
                writing["results"][0]["path"],
                "writing/technical-project-explanation.md",
            )

    def test_ties_are_path_stable_across_repeated_searches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_task_vault(Path(temporary))
            first = self.run_search(vault, "Deterministic Tie")
            second = self.run_search(vault, "Deterministic Tie")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            first_paths = [item["path"] for item in json.loads(first.stdout)["results"]]
            second_paths = [item["path"] for item in json.loads(second.stdout)["results"]]
            self.assertEqual(first_paths, second_paths)
            self.assertLess(first_paths.index("core/tie-a.md"), first_paths.index("core/tie-b.md"))

    def test_legacy_historical_flags_warn_on_stderr_without_corrupting_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_task_vault(Path(temporary))
            result = self.run_search(
                vault,
                "past role before current company",
                "--include-archived",
                "--include-superseded",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["results"])
            self.assertIn("deprecated", result.stderr)
            self.assertNotIn("deprecated", result.stdout)
            self.assertIn(
                "career/past-role-superseded.md",
                [item["path"] for item in report["results"]],
            )

    def test_cli_help_describes_default_historical_inclusion_and_exclusions(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SEARCH), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--exclude-archived", result.stdout)
        self.assertIn("--exclude-superseded", result.stdout)
        self.assertIn("Deprecated compatibility option", result.stdout)


if __name__ == "__main__":
    unittest.main()
