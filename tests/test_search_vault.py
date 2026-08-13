import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
SEARCH = SCRIPTS / "search_vault.py"


PAGE = """---
type: {type}
title: {title}
aliases:
  - {alias}
description: {description}
tags:
  - synthetic
status: {status}
generated: 2026-08-12
verified: null
sources: []
assertion_kind: {assertion}
stale_after: null
---

## {heading}

{body}
"""


class SearchVaultTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Path:
        vault = root / "vault"
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory).mkdir(parents=True)
        (vault / "SCHEMA.md").write_text("# Schema\n\nschema_version: 0.1\n", encoding="utf-8")
        (vault / "index.md").write_text("# Root\n", encoding="utf-8")
        (vault / "log.md").write_text("# Log\n", encoding="utf-8")
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory / "index.md").write_text(f"# {directory}\n", encoding="utf-8")
        (vault / "core" / "title.md").write_text(
            PAGE.format(
                type="concept", title="Synthetic Queue", alias="queue alias",
                description="A page about an unrelated concept.", status="active",
                assertion="user_stated_fact", heading="Concept", body="body only",
            ), encoding="utf-8"
        )
        (vault / "core" / "body.md").write_text(
            PAGE.format(
                type="concept", title="Synthetic Concept", alias="other",
                description="Navigation page.", status="active",
                assertion="user_stated_fact", heading="Queue heading", body="queue in the body",
            ), encoding="utf-8"
        )
        (vault / "review" / "review.md").write_text(
            PAGE.format(
                type="observation", title="Review Queue", alias="review queue",
                description="A provisional queue observation.", status="review",
                assertion="agent_inference", heading="Review", body="queue review",
            ), encoding="utf-8"
        )
        (vault / "sources" / "source.md").write_text(
            PAGE.format(
                type="source", title="Synthetic Source", alias="source",
                description="Raw queue source.", status="active",
                assertion="source_record", heading="Source", body="queue source",
            ), encoding="utf-8"
        )
        return vault

    def run_search(self, vault: Path, query: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SEARCH), query, str(vault), *args, "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_ranking_prefers_title_then_heading_then_body_and_review_remains_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            result = self.run_search(vault, "queue")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            paths = [item["path"] for item in json.loads(result.stdout)["results"]]
            self.assertEqual(paths[:3], ["core/title.md", "review/review.md", "core/body.md"])

    def test_sources_archived_and_superseded_are_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            default = json.loads(self.run_search(vault, "queue").stdout)["results"]
            self.assertNotIn("sources/source.md", [item["path"] for item in default])
            included = json.loads(self.run_search(vault, "queue", "--include-sources").stdout)["results"]
            self.assertIn("sources/source.md", [item["path"] for item in included])

    def test_json_contains_bounded_metadata_not_page_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(Path(temporary))
            report = json.loads(self.run_search(vault, "queue").stdout)
            self.assertTrue(report["results"])
            self.assertNotIn("Synthetic text that should not be emitted", json.dumps(report))
            for item in report["results"]:
                self.assertEqual(set(item), {"path", "title", "description", "status", "assertion_kind", "matched_fields", "vertical", "snippet"})


if __name__ == "__main__":
    unittest.main()
