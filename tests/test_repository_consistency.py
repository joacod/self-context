from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills/self-context"
CATALOG_PATH = SKILL_ROOT / "references/verticals.json"

if str(ROOT / ".agents/skills/self-context/scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / ".agents/skills/self-context/scripts"))

import vault_utils  # type: ignore  # noqa: E402


class RepositoryConsistencyTests(unittest.TestCase):
    """Check stable machine-readable contracts without snapshotting prose."""

    @staticmethod
    def table_rows(path: Path, heading: str) -> list[list[str]]:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        start = lines.index(heading)
        heading_level = len(heading) - len(heading.lstrip("#"))
        rows: list[list[str]] = []
        for line in lines[start + 1 :]:
            heading_match = re.match(r"^(#+)\s+", line)
            if heading_match and len(heading_match.group(1)) <= heading_level:
                break
            if not line.lstrip().startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
                continue
            rows.append(cells)
        return rows

    @staticmethod
    def routing_rows() -> list[list[str]]:
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        section = text.split("Current vertical routing:", 1)[1].split(
            "- A future vertical", 1
        )[0]
        rows: list[list[str]] = []
        for line in section.splitlines():
            if line.lstrip().startswith("|"):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if cells and not all(set(cell) <= {"-", ":", " "} for cell in cells):
                    rows.append(cells)
        return rows

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = vault_utils.load_vertical_catalog(CATALOG_PATH)
        cls.records = vault_utils.catalog_records(cls.catalog)

    def test_catalog_paths_headers_and_advisor_packs_are_consistent(self) -> None:
        self.assertEqual(vault_utils.validate_vertical_catalog(CATALOG_PATH), [])
        self.assertTrue(self.records)
        ids = [str(record["id"]) for record in self.records]
        self.assertEqual(len(ids), len(set(ids)))
        for record in self.records:
            identifier = str(record["id"])
            area = str(record["vault_area"])
            index_path = str(record["index_path"])
            self.assertEqual(index_path, f"{area}/index.md", identifier)
            self.assertFalse(Path(index_path).is_absolute())
            self.assertTrue((SKILL_ROOT / index_path).parent == SKILL_ROOT / area)

            procedure = SKILL_ROOT / str(record["procedure_path"])
            self.assertTrue(procedure.is_file(), identifier)
            header = vault_utils.procedure_header(procedure)
            self.assertEqual(header["vertical_id"], record["id"], identifier)
            self.assertEqual(header["contract_version"], record["contract_version"], identifier)
            self.assertEqual(header["vault_area"], record["vault_area"], identifier)
            self.assertEqual(
                header["advisor_skill"],
                record.get("advisor_skill", record.get("advisor_pack")),
                identifier,
            )

            advisor_pack = record.get("advisor_pack")
            if advisor_pack is not None:
                self.assertTrue(
                    (ROOT / ".agents/skills" / str(advisor_pack) / "SKILL.md").is_file(),
                    identifier,
                )

    def test_intentionally_enumerated_vertical_tables_match_catalog(self) -> None:
        documentation_tables = (
            (ROOT / "README.md", "### Available Verticals"),
            (ROOT / "docs/ARCHITECTURE.md", "### Available Vertical Catalog"),
        )
        for path, heading in documentation_tables:
            rows = self.table_rows(path, heading)
            self.assertGreaterEqual(len(rows), len(self.records), path.as_posix())
            for record in self.records:
                display_name = str(record["display_name"])
                area = str(record["vault_area"])
                self.assertTrue(
                    any(
                        row
                        and row[0] == display_name
                        and any(area in cell for cell in row[1:])
                        for row in rows
                    ),
                    f"{path}: {display_name}",
                )

        routing = self.routing_rows()
        for record in self.records:
            self.assertTrue(
                any(row and row[0] == record["display_name"] for row in routing),
                str(record["id"]),
            )

    def test_validation_and_release_commands_are_documented(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = ROOT / "docs/DEEP_MAINTENANCE_RELEASE_CHECKLIST.md"
        self.assertIn("python3 scripts/validate_repo.py", readme)
        self.assertTrue(checklist.is_file())
        checklist_text = checklist.read_text(encoding="utf-8")
        self.assertIn("python3 scripts/validate_repo.py", checklist_text)

    def test_initialization_preserves_schema_compatibility_and_selective_activation(self) -> None:
        text = (SKILL_ROOT / "references/initialization.md").read_text(encoding="utf-8")
        normalized = " ".join(text.casefold().split())
        self.assertRegex(text, r"schema_version:\s*0\.2")
        self.assertRegex(text, r"vertical_contracts:")
        self.assertRegex(normalized, r"schema\s+0\.1")
        self.assertRegex(normalized, r"schema\s+0\.2")
        self.assertRegex(normalized, r"do not add contract\s+markers")
        self.assertRegex(normalized, r"explicit\s+migration\s+helper")
        self.assertRegex(normalized, r"does not enable unrelated available\s+verticals")
        self.assertRegex(
            normalized,
            r"never create or enable a vertical for a read-only query, assessment, lint, or\s+review\.",
        )

    def test_deep_maintenance_terminology_keeps_read_only_and_mutating_boundaries(self) -> None:
        text = (SKILL_ROOT / "references/deep-maintenance.md").read_text(encoding="utf-8")
        lowered = text.casefold()
        self.assertIn("deep review", lowered)
        self.assertIn("deep update", lowered)
        self.assertIn("read-only", lowered)
        self.assertIn("one pre-write backup", lowered)
        self.assertIn("snapshot", lowered)
        self.assertIn("human decisions", lowered)
        self.assertNotRegex(lowered, r"deep review[^.\n]{0,120}\b(?:writes|mutates|creates a backup)\b")
        self.assertNotRegex(lowered, r"deep update[^.\n]{0,120}\b(?:read-only|never writes)\b")

    def test_all_tracked_json_and_eval_files_parse(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "*.json"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        paths = [
            ROOT / Path(raw.decode())
            for raw in result.stdout.split(b"\0")
            if raw
        ]
        self.assertGreaterEqual(len(paths), 1)
        eval_paths = []
        for path in paths:
            with path.open(encoding="utf-8") as handle:
                parsed = json.load(handle)
            if "/evals/" in path.as_posix():
                eval_paths.append(path)
                if path.name == "evals.json":
                    self.assertIsInstance(parsed, dict)
                    cases = parsed.get("evals")
                    self.assertIsInstance(cases, list)
                    ids = [case.get("id") for case in cases]
                    self.assertEqual(len(ids), len(set(ids)), path.as_posix())
                else:
                    self.assertIsInstance(parsed, list)
        self.assertGreaterEqual(len(eval_paths), 2)

    def test_consistency_test_is_independent_of_a_real_vault(self) -> None:
        # This test does not open vault/; the actual ignored vault, when
        # present, is intentionally outside the consistency contract.
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertTrue(any(line.strip() == "/vault/" for line in gitignore.splitlines()))


if __name__ == "__main__":
    unittest.main()
