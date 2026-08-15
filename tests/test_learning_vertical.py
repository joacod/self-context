import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LINT_SCRIPT = REPOSITORY_ROOT / ".agents/skills/self-context/scripts/lint_vault.py"


class LearningVerticalTests(unittest.TestCase):
    def make_vault(self, root: Path, include_learning_link: bool = True) -> Path:
        vault = root / "vault"
        for directory in (
            "core",
            "career",
            "learning",
            "review/observations",
            "sources",
            "derived",
        ):
            (vault / directory).mkdir(parents=True, exist_ok=True)

        (vault / "SCHEMA.md").write_text(
            "# SelfContext Vault Schema\n\n"
            "schema_version: 0.2\n"
            "vertical_contracts:\n"
            "  - career@1\n"
            "  - learning@1\n",
            encoding="utf-8",
        )
        root_links = [
            "SCHEMA.md",
            "core/index.md",
            "career/index.md",
            "learning/index.md" if include_learning_link else "",
            "review/index.md",
            "sources/index.md",
            "derived/index.md",
            "log.md",
        ]
        (vault / "index.md").write_text(
            "# SelfContext Vault\n\n" + "\n".join(link for link in root_links if link) + "\n",
            encoding="utf-8",
        )
        (vault / "log.md").write_text("# Operation Log\n", encoding="utf-8")
        for index in (
            "core/index.md",
            "career/index.md",
            "learning/index.md",
            "review/index.md",
            "sources/index.md",
            "derived/index.md",
        ):
            (vault / index).write_text(f"# {index}\n", encoding="utf-8")

        (vault / "sources/closure-exercise.md").write_text(
            """---
type: source
title: Synthetic closure exercise
description: Fictional exercise source supporting a scoped Learning claim.
tags:
  - learning
  - javascript
status: active
generated: 2026-03-05
verified: null
sources: []
assertion_kind: source_record
stale_after: null
---

The fictional exercise asks the learner to explain a callback that captures a variable.
""",
            encoding="utf-8",
        )
        (vault / "learning/lexical-closures.md").write_text(
            """---
type: concept
title: JavaScript lexical closures
description: Scoped understanding of lexical closures supported by a fictional exercise.
tags:
  - learning
  - javascript
  - closures
status: active
generated: 2026-03-05
verified: null
sources:
  - ../sources/closure-exercise.md
assertion_kind: source_derived_fact
stale_after: null
---

# JavaScript lexical closures

## Knowledge state

- state: demonstrated
- scope: Can explain captured variables in a callback and use the pattern in a small implementation.

## Boundary

The fictional evidence does not establish performance knowledge for large closure graphs.

## Evidence

- [Synthetic closure exercise](../sources/closure-exercise.md)

## Prerequisites and relationships

None recorded.
""",
            encoding="utf-8",
        )
        (vault / "review/observations/closure-gap.md").write_text(
            """---
type: observation
title: Synthetic closure performance gap
description: Fictional reviewable Learning observation about an unresolved boundary.
tags:
  - learning
  - review
status: review
generated: 2026-03-05
verified: null
sources:
  - ../../learning/lexical-closures.md
assertion_kind: agent_inference
stale_after: null
---

The fictional evidence may indicate an unresolved performance boundary.
""",
            encoding="utf-8",
        )
        return vault

    def lint(self, vault: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(LINT_SCRIPT), str(vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_linter_accepts_learning_pages_and_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.lint(self.make_vault(Path(temporary)))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("does not mention learning/index.md", result.stdout)
            self.assertIn("closure-gap.md: observation or inference is unverified", result.stdout)

    def test_linter_checks_learning_navigation_when_learning_area_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.lint(
                self.make_vault(Path(temporary), include_learning_link=False)
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("index.md does not mention learning/index.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
