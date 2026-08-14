from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from validate_skill_metadata import (  # type: ignore  # noqa: E402
    DESCRIPTION_MAX_CHARS,
    DESCRIPTION_WARNING_CHARS,
    parse_frontmatter,
    validate_skill_metadata,
    validate_skill_text,
)


class SkillMetadataTests(unittest.TestCase):
    def test_parser_folds_descriptions_and_plain_scalar_continuations(self) -> None:
        text = (
            "---\n"
            "name: example-skill\n"
            "description: >\n"
            "  First line\n"
            "  second line\n"
            "compatibility: Requires local access to the repository\n"
            "  and standard Markdown files.\n"
            "---\n"
        )

        metadata = parse_frontmatter(text)

        self.assertEqual(metadata["description"], "First line second line")
        self.assertEqual(
            metadata["compatibility"],
            "Requires local access to the repository and standard Markdown files.",
        )

    def test_recommended_budget_warns_before_hard_limit(self) -> None:
        description = "x" * (DESCRIPTION_WARNING_CHARS + 1)

        problems, warnings = validate_skill_text(
            "example/SKILL.md",
            f"---\nname: example\ndescription: {description}\n---\n",
        )

        self.assertEqual(problems, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn(str(DESCRIPTION_WARNING_CHARS), warnings[0])

    def test_description_hard_limit_is_enforced(self) -> None:
        description = "x" * (DESCRIPTION_MAX_CHARS + 1)

        problems, warnings = validate_skill_text(
            "example/SKILL.md",
            f"---\nname: example\ndescription: {description}\n---\n",
        )

        self.assertEqual(warnings, [])
        self.assertEqual(len(problems), 1)
        self.assertIn(str(DESCRIPTION_MAX_CHARS), problems[0])

    def test_all_tracked_project_skills_pass_metadata_validation(self) -> None:
        paths, problems, _warnings = validate_skill_metadata(ROOT)

        self.assertGreaterEqual(len(paths), 1)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
