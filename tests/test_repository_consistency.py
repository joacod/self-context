from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills/self-context"
CATALOG_PATH = SKILL_ROOT / "references/verticals.json"

# Keep this guard deliberately narrow: it protects the known legacy fixture
# aliases without prohibiting distinct people, works, or project names needed
# by relationship and media scenarios.
LEGACY_SYNTHETIC_PLACEHOLDER_PATTERNS = (
    ("Nia", re.compile(r"\bNia(?:\s+Vale|'s)?\b")),
    ("Cedar Cooperative", re.compile(r"\bCedar Cooperative\b")),
    ("generic company placeholder", re.compile(r"\bCompany [A-Z]\b")),
)

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
            (ROOT / "README.md", "### Context Areas"),
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

    def test_eval_structure_and_unique_ids(self) -> None:
        paths = sorted(ROOT.glob(".agents/skills/*/evals/*.json"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                parsed = json.loads(path.read_text(encoding="utf-8"))
                if path.name == "evals.json":
                    self.assertIsInstance(parsed, dict)
                    self.assertEqual(parsed["skill_name"], path.parents[1].name)
                    cases = parsed["evals"]
                    self.assertIsInstance(cases, list)
                    ids = [case["id"] for case in cases]
                    self.assertEqual(len(ids), len(set(ids)))
                    for case in cases:
                        self.assertIsInstance(case["prompt"], str)
                        self.assertIsInstance(case["expected_output"], str)
                        self.assertIsInstance(case["expectations"], list)
                else:
                    self.assertIsInstance(parsed, list)

    def test_synthetic_example_placeholders_follow_repository_convention(self) -> None:
        paths = sorted(ROOT.glob(".agents/skills/*/evals/*.json"))
        paths.extend(
            (
                ROOT / "docs/ARCHITECTURE.md",
                SKILL_ROOT / "references/ventures.md",
            )
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for label, pattern in LEGACY_SYNTHETIC_PLACEHOLDER_PATTERNS:
                self.assertIsNone(
                    pattern.search(text),
                    f"legacy synthetic placeholder {label!r} in {path.relative_to(ROOT)}",
                )

    def test_consistency_test_is_independent_of_a_real_vault(self) -> None:
        # This test does not open vault/; the actual ignored vault, when
        # present, is intentionally outside the consistency contract.
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertTrue(any(line.strip() == "/vault/" for line in gitignore.splitlines()))

    def test_duplicate_catalog_records_are_rejected(self) -> None:
        catalog = vault_utils.load_vertical_catalog()
        catalog["verticals"].append(dict(catalog["verticals"][0]))

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "verticals.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            problems = vault_utils.validate_vertical_catalog(path)
            self.assertTrue(any("duplicate vertical id" in problem for problem in problems))
            self.assertTrue(any("duplicate vertical area" in problem for problem in problems))
            self.assertTrue(any("duplicate vertical index" in problem for problem in problems))
            self.assertTrue(any("duplicate vertical contract" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
