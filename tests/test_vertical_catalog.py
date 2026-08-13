import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"


class VerticalCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import vault_utils

        cls.vault_utils = vault_utils

    def test_catalog_has_one_consistent_record_per_available_vertical(self) -> None:
        catalog = self.vault_utils.load_vertical_catalog()
        records = self.vault_utils.catalog_records(catalog)
        self.assertEqual(catalog["catalog_version"], 1)
        self.assertEqual(
            [record["id"] for record in records],
            ["career", "learning", "writing", "relationships", "media"],
        )
        self.assertEqual(self.vault_utils.validate_vertical_catalog(), [])

    def test_catalog_paths_and_advisor_packs_exist(self) -> None:
        catalog = self.vault_utils.load_vertical_catalog()
        skill_root = ROOT / ".agents/skills/self-context"
        for record in catalog["verticals"]:
            self.assertTrue((skill_root / record["procedure_path"]).is_file())
            self.assertTrue((ROOT / ".agents/skills" / record["advisor_pack"] / "SKILL.md").is_file())
            header = self.vault_utils.procedure_header(skill_root / record["procedure_path"])
            expected_header = {
                "vertical_id": record["id"],
                "contract_version": record["contract_version"],
                "vault_area": record["vault_area"],
                "advisor_skill": record["advisor_skill"],
            }
            for key, expected in expected_header.items():
                self.assertEqual(header[key], expected, (record["id"], key))

    def test_public_documentation_names_available_verticals_consistently(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8") + (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        for display_name in ("Career", "Learning", "Writing", "Relationships", "Media / Taste"):
            self.assertIn(display_name, text)

    def test_duplicate_catalog_records_are_rejected(self) -> None:
        catalog = self.vault_utils.load_vertical_catalog()
        catalog["verticals"].append(dict(catalog["verticals"][0]))
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "verticals.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            problems = self.vault_utils.validate_vertical_catalog(path)
            self.assertTrue(any("duplicate vertical id" in problem for problem in problems))
            self.assertTrue(any("duplicate vertical area" in problem for problem in problems))
            self.assertTrue(any("duplicate vertical index" in problem for problem in problems))
            self.assertTrue(any("duplicate vertical contract" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
