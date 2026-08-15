import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LINT_SCRIPT = REPOSITORY_ROOT / ".agents/skills/self-context/scripts/lint_vault.py"


class RelationshipsMediaVerticalTests(unittest.TestCase):
    def make_vault(
        self, root: Path, include_relationships_link: bool = True, include_media_link: bool = True
    ) -> Path:
        vault = root / "vault"
        for directory in (
            "core",
            "career",
            "relationships",
            "media",
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
            "  - relationships@1\n"
            "  - media@1\n",
            encoding="utf-8",
        )
        root_links = [
            "SCHEMA.md",
            "core/index.md",
            "career/index.md",
            "relationships/index.md" if include_relationships_link else "",
            "media/index.md" if include_media_link else "",
            "review/index.md",
            "sources/index.md",
            "derived/index.md",
            "log.md",
        ]
        (vault / "index.md").write_text(
            "# SelfContext Vault\n\n"
            + "\n".join(link for link in root_links if link)
            + "\n",
            encoding="utf-8",
        )
        (vault / "log.md").write_text("# Operation Log\n", encoding="utf-8")
        for index in (
            "core/index.md",
            "career/index.md",
            "relationships/index.md",
            "media/index.md",
            "review/index.md",
            "sources/index.md",
            "derived/index.md",
        ):
            (vault / index).write_text(f"# {index}\n", encoding="utf-8")

        (vault / "sources/alice-note.md").write_text(
            """---
type: source
title: Synthetic Alice recollection
description: Fictional relationship recollection supporting a scoped shared-context claim.
tags:
  - relationships
status: active
generated: 2026-08-11
verified: null
sources: []
assertion_kind: source_record
stale_after: null
---

Alice told John about a future move, and the two exchanged a film recommendation.
""",
            encoding="utf-8",
        )
        (vault / "relationships/relationship-with-alice.md").write_text(
            """---
type: concept
title: Relationship with Alice
description: Fictional shared relationship context for a synthetic test.
tags:
  - relationships
  - shared-history
status: active
generated: 2026-08-11
verified: null
sources:
  - ../sources/alice-note.md
assertion_kind: source_derived_fact
stale_after: null
---

## Relationship to me

John and Alice worked together and remain friends.

## Shared context

They exchange science-fiction recommendations.

## Commitments and open loops

No active commitment is recorded.

## Evidence and boundaries

The move is a reported statement from the fictional recollection, not an independently verified fact.
""",
            encoding="utf-8",
        )
        (vault / "sources/film-reaction.md").write_text(
            """---
type: source
title: Synthetic film reaction
description: Fictional user reaction to a cultural work.
tags:
  - media
  - film
status: active
generated: 2026-08-11
verified: null
sources: []
assertion_kind: source_record
stale_after: null
---

John liked the atmosphere and ambiguous identity themes in the fictional film.
""",
            encoding="utf-8",
        )
        (vault / "media/atmospheric-film.md").write_text(
            """---
type: concept
title: Synthetic atmospheric film reaction
description: Fictional personal reaction to one film used as Media evidence.
tags:
  - media
  - film
status: active
generated: 2026-08-11
verified: null
sources:
  - ../sources/film-reaction.md
assertion_kind: user_stated_fact
stale_after: null
---

## Work

- medium: film
- creator: fictional creator

## Experience

- state: consumed

## Reaction

John liked the atmosphere and ambiguous identity themes, but disliked the slow opening.

## Evidence

- [Synthetic film reaction](../sources/film-reaction.md)
""",
            encoding="utf-8",
        )
        (vault / "media/exploration-game.md").write_text(
            """---
type: concept
title: Synthetic exploration game reaction
description: Fictional personal reaction to a second work used as Media evidence.
tags:
  - media
  - game
status: active
generated: 2026-08-11
verified: null
sources: []
assertion_kind: user_stated_fact
stale_after: null
---

## Reaction

John liked exploring an atmospheric fictional world through environmental storytelling.
""",
            encoding="utf-8",
        )
        (vault / "media/atmospheric-pattern.md").write_text(
            """---
type: observation
title: Synthetic atmospheric speculative pattern
description: Fictional reviewable pattern supported by individual work reactions.
tags:
  - media
  - taste
status: review
generated: 2026-08-11
verified: null
sources:
  - atmospheric-film.md
  - exploration-game.md
assertion_kind: agent_inference
stale_after: null
---

## Pattern

The fictional evidence may support a scoped interest in atmospheric speculative works.

## Evidence

- [Synthetic atmospheric film](atmospheric-film.md)
- [Synthetic exploration game](exploration-game.md)

## Exceptions

None recorded.
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

    def test_linter_accepts_relationships_and_media_pages(self) -> None:
        with TemporaryDirectory() as temporary:
            result = self.lint(self.make_vault(Path(temporary)))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("broken link", result.stdout)
            self.assertNotIn("does not mention relationships/index.md", result.stdout)
            self.assertNotIn("does not mention media/index.md", result.stdout)
            self.assertIn("atmospheric-pattern.md: observation or inference is unverified", result.stdout)

    def test_linter_checks_new_vertical_navigation_when_areas_exist(self) -> None:
        with TemporaryDirectory() as temporary:
            result = self.lint(
                self.make_vault(
                    Path(temporary),
                    include_relationships_link=False,
                    include_media_link=False,
                )
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("index.md does not mention relationships/index.md", result.stdout)
            self.assertIn("index.md does not mention media/index.md", result.stdout)

    def test_new_advisor_skill_evals_are_parseable(self) -> None:
        for skill_name in ("relationships-advisor", "media-advisor"):
            skill_dir = REPOSITORY_ROOT / ".agents/skills" / skill_name
            with self.subTest(skill_name=skill_name):
                metadata = json.loads((skill_dir / "evals/evals.json").read_text())
                triggers = json.loads((skill_dir / "evals/trigger-evals.json").read_text())
                self.assertEqual(metadata["skill_name"], skill_name)
                self.assertGreaterEqual(len(metadata["evals"]), 10)
                self.assertGreaterEqual(len(triggers), 20)
                self.assertTrue((skill_dir / "SKILL.md").read_text().startswith("---\n"))


if __name__ == "__main__":
    unittest.main()
