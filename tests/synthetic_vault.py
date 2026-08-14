"""Fictional medium-vault fixtures shared by deep-maintenance integration tests.

The builder intentionally models the portable filesystem contract rather than
inventing a second vault implementation.  Every caller supplies a temporary
project root; no fixture reads or writes the repository's ignored ``vault/``.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import sync_indexes  # type: ignore  # noqa: E402


CATALOG_START = "<!-- selfcontext:catalog:start -->"
CATALOG_END = "<!-- selfcontext:catalog:end -->"
SENSITIVE_BODY_MARKER = "SYNTHETIC_PRIVATE_BODY_MARKER_7f3b1"

# Relationships is deliberately enabled so packet tests can prove that an
# unrelated enabled vertical is excluded.  Media and Ventures remain available
# but disabled until an explicit-adoption test enables one of them.
ENABLED_VERTICALS = ("career", "learning", "writing", "relationships")
DISABLED_VERTICALS = ("media", "ventures")

VERTICAL_DESCRIPTIONS = {
    "career": "Fictional career evidence and delivery examples.",
    "learning": "Fictional evidence-backed knowledge states.",
    "writing": "Fictional communication and revision context.",
    "relationships": "Fictional intentional relationship continuity.",
    "media": "Fictional reactions and taste context.",
    "ventures": "Fictional initiative lifecycle and project evidence.",
}


_PAGE_DEFAULTS = {
    "description": "Fictional durable page for integration tests.",
    "tags": ("synthetic",),
    "status": "active",
    "generated": "2026-08-12",
    "verified": "null",
    "sources": (),
    "assertion_kind": "user_stated_fact",
    "stale_after": "null",
}


def _yaml_string(value: str) -> str:
    """Return a simple YAML scalar for the fixture's controlled strings."""

    if any(character in value for character in (":", "#", "{", "}", "[", "]")):
        return '"' + value.replace('"', '\\"') + '"'
    return value


def page_text(
    *,
    page_type: str = "concept",
    title: str,
    description: str | None = None,
    aliases: Iterable[str] = (),
    tags: Iterable[str] = ("synthetic",),
    status: str = "active",
    generated: str = "2026-08-12",
    verified: str = "null",
    sources: Iterable[str] = (),
    assertion_kind: str = "user_stated_fact",
    stale_after: str = "null",
    superseded_by: str | None = None,
    extra_fields: Mapping[str, str] | None = None,
    body: str = "Fictional synthetic page body.\n",
) -> str:
    """Render a complete, deterministic durable page."""

    aliases = tuple(aliases)
    tags = tuple(tags)
    sources = tuple(sources)
    lines = ["---", f"type: {page_type}", f"title: {_yaml_string(title)}"]
    if aliases:
        lines.append("aliases:")
        lines.extend(f"  - {_yaml_string(alias)}" for alias in aliases)
    lines.extend(
        [
            f"description: {_yaml_string(description or _PAGE_DEFAULTS['description'])}",
            "tags:",
        ]
    )
    lines.extend(f"  - {_yaml_string(tag)}" for tag in tags)
    lines.extend(
        [
            f"status: {status}",
            f"generated: {generated}",
            f"verified: {verified}",
            "sources:",
        ]
    )
    lines.extend(f"  - {_yaml_string(source)}" for source in sources)
    if not sources:
        lines[-1] = "sources: []"
    lines.extend(
        [
            f"assertion_kind: {assertion_kind}",
            f"stale_after: {stale_after}",
        ]
    )
    if superseded_by:
        lines.append(f"superseded_by: {superseded_by}")
    for key, value in (extra_fields or {}).items():
        lines.append(f"{key}: {_yaml_string(value)}")
    lines.extend(["---", "", body.rstrip("\n"), ""])
    return "\n".join(lines)


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def write_page(vault: Path, relative: str, **kwargs: object) -> Path:
    path = vault / relative
    _write(path, page_text(**kwargs))
    return path


def _schema_text(schema_version: str, enabled: Sequence[str]) -> str:
    if schema_version == "0.1":
        return (
            "# Synthetic Legacy Schema\n\n"
            "schema_version: 0.1\n\n"
            "This fictional vault keeps legacy schema text until explicit migration.\n"
        )
    contracts = "\n".join(f"  - {identifier}@1" for identifier in enabled)
    return (
        "# Synthetic Current Schema\n\n"
        "schema_version: 0.2\n"
        "vertical_contracts:\n"
        f"{contracts}\n\n"
        "This fictional vault records only intentionally enabled contracts.\n"
    )


def _root_index(enabled: Sequence[str]) -> str:
    links = [
        "- [Schema](SCHEMA.md)",
        "- [Operation log](log.md)",
        "- [Core](core/index.md)",
        "- [Review](review/index.md)",
        "- [Sources](sources/index.md)",
        "- [Derived](derived/index.md)",
    ]
    links.extend(
        f"- [{identifier.title()} context]({identifier}/index.md)"
        for identifier in enabled
    )
    return (
        "# Synthetic Medium Vault\n\n"
        "Manual root navigation that must survive generated catalog refreshes.\n\n"
        + "\n".join(links)
        + "\n\n"
        + CATALOG_START
        + "\n"
        + CATALOG_END
        + "\n"
    )


def _category_index(identifier: str) -> str:
    return (
        f"# {identifier.title()} Context\n\n"
        f"Manual {identifier} category text remains outside the managed block.\n\n"
        f"{CATALOG_START}\n{CATALOG_END}\n"
    )


def _write_base_controls(vault: Path, schema_version: str, enabled: Sequence[str]) -> None:
    _write(vault / "SCHEMA.md", _schema_text(schema_version, enabled))
    _write(vault / "index.md", _root_index(enabled))
    _write(
        vault / "log.md",
        "# Synthetic Operation Log\n\n"
        "This fixture log is fictional and intentionally starts without maintenance entries.\n",
    )
    for area in ("core", "review", "sources", "derived", *enabled):
        _write(vault / area / "index.md", _category_index(area))


def _write_fictional_pages(vault: Path) -> None:
    write_page(
        vault,
        "core/decision-trail.md",
        title="Decision Trail",
        description="A cross-domain preference linked to fictional evidence.",
        aliases=("decision notes",),
        sources=("../sources/decision-note.md",),
        body=(
            "## Scope\n\n"
            "A fictional preference for written decisions spans the work and learning examples.\n\n"
            "[Delivery example](../career/harbor-launch.md) and "
            "[Explanation pattern](../writing/explanation-pattern.md).\n"
        ),
    )
    write_page(
        vault,
        "core/contradictory-signal.md",
        page_type="observation",
        title="Contradictory Signal",
        description="A review candidate with two fictional notes that do not settle one answer.",
        status="review",
        assertion_kind="agent_inference",
        sources=("../sources/conflicting-notes.md",),
        body=(
            "## Review candidate\n\n"
            "One fictional note favors fast decisions; another favors written decisions.\n"
            "Human confirmation is still required.\n"
        ),
    )
    write_page(
        vault,
        "career/harbor-launch.md",
        title="Harbor Launch",
        description="A fictional delivery example with a cross-vertical learning link.",
        aliases=("harbor delivery", "launch example"),
        sources=("../sources/harbor-notes.md",),
        body=(
            "## Evidence\n\n"
            "A fictional team delivered a Harbor service migration with a documented rollout.\n\n"
            "[Learning model](../learning/event-model.md).\n"
        ),
    )
    write_page(
        vault,
        "career/archived-role.md",
        title="Archived Harbor Role",
        description="A historical fictional role retained for continuity.",
        status="archived",
        sources=("../sources/old-role-notes.md",),
        body="## Historical\n\nThis fictional role is archived, not current.\n",
    )
    write_page(
        vault,
        "career/superseded-launch.md",
        title="Superseded Launch Plan",
        description="An older fictional plan retained with an explicit successor.",
        status="superseded",
        sources=("../sources/old-role-notes.md",),
        superseded_by="harbor-launch.md",
        body="## History\n\nThe newer Harbor Launch page supersedes this fictional plan.\n",
    )
    write_page(
        vault,
        "learning/event-model.md",
        title="Event Model",
        description="A scoped fictional learning state supported by an exercise.",
        aliases=("event loop model",),
        sources=("../sources/learning-exercise.md",),
        body=(
            "## Demonstrated scope\n\n"
            "The fictional learner can explain the event model for the Harbor example.\n\n"
            "[Career evidence](../career/harbor-launch.md).\n"
        ),
    )
    write_page(
        vault,
        "learning/review-candidate.md",
        page_type="observation",
        title="Event Model Review Candidate",
        description="A fictional gap candidate that remains open for human review.",
        status="review",
        assertion_kind="agent_inference",
        sources=("../sources/conflicting-notes.md",),
        body="## Open question\n\nThe two fictional notes support different explanations; do not promote either one.\n",
    )
    write_page(
        vault,
        "writing/explanation-pattern.md",
        title="Explanation Pattern",
        description="A fictional communication pattern for technical explanations.",
        aliases=("concrete explanation",),
        sources=("../sources/essay-notes.md",),
        body=(
            "## Communication fit\n\n"
            "The fictional examples start with a concrete case before naming an abstraction.\n\n"
            "[Delivery context](../career/harbor-launch.md).\n"
        ),
    )
    write_page(
        vault,
        "relationships/fictional-collaboration.md",
        title="Fictional Collaboration Thread",
        description="Unrelated relationship context that a career packet must exclude.",
        aliases=("collaboration thread",),
        sources=("../sources/collaboration-note.md",),
        body=(
            "## Exclusion fixture\n\n"
            "This fictional relationship continuity is unrelated to the Harbor interview task.\n"
        ),
    )
    write_page(
        vault,
        "review/maintenance-candidate.md",
        page_type="observation",
        title="Maintenance Candidate",
        description="A deterministic candidate that still needs a human decision.",
        status="review",
        assertion_kind="agent_inference",
        sources=("../sources/conflicting-notes.md",),
        body="## Decision boundary\n\nNo inference or verification is promoted by deterministic maintenance.\n",
    )
    write_page(
        vault,
        "sources/harbor-notes.md",
        page_type="source",
        title="Harbor Notes Source",
        description="A fictional source record for the delivery example.",
        assertion_kind="source_record",
        body="## Source record\n\nFictional source notes for the Harbor example.\n",
    )
    write_page(
        vault,
        "sources/old-role-notes.md",
        page_type="source",
        title="Old Role Notes Source",
        description="A fictional historical source record.",
        generated="2025-01-01",
        assertion_kind="source_record",
        body="## Historical source\n\nFictional historical notes retained for migration tests.\n",
    )
    write_page(
        vault,
        "sources/learning-exercise.md",
        page_type="source",
        title="Learning Exercise Source",
        description="A fictional exercise source record.",
        assertion_kind="source_record",
        body="## Exercise\n\nFictional event-model exercise evidence.\n",
    )
    write_page(
        vault,
        "sources/essay-notes.md",
        page_type="source",
        title="Essay Notes Source",
        description="A fictional authored-writing source record.",
        assertion_kind="source_record",
        body="## Source\n\nFictional essay notes for the communication pattern.\n",
    )
    write_page(
        vault,
        "sources/decision-note.md",
        page_type="source",
        title="Decision Note Source",
        description="A fictional cross-domain decision source record.",
        assertion_kind="source_record",
        body="## Source\n\nFictional decision note.\n",
    )
    write_page(
        vault,
        "sources/conflicting-notes.md",
        page_type="source",
        title="Conflicting Notes Source",
        description="A fictional source containing a contradiction candidate.",
        assertion_kind="source_record",
        body="## Source\n\nFictional notes intentionally point in two directions.\n",
    )
    write_page(
        vault,
        "sources/collaboration-note.md",
        page_type="source",
        title="Collaboration Note Source",
        description="A fictional relationship source record.",
        assertion_kind="source_record",
        body="## Source\n\nFictional collaboration continuity note.\n",
    )
    # This source is newer than the linked derived synthesis.  The date is a
    # deterministic review signal, not proof that regeneration is required.
    write_page(
        vault,
        "sources/current-signal.md",
        page_type="source",
        title="Current Signal Source",
        description="A fictional source with a newer timestamp than a synthesis.",
        generated="2026-08-11",
        assertion_kind="source_record",
        body="## Source\n\nFictional current-state signal for freshness testing.\n",
    )
    write_page(
        vault,
        "derived/maintenance-brief.md",
        page_type="synthesis",
        title="Maintenance Brief",
        description="A fictional derived synthesis that needs a freshness review signal.",
        generated="2026-01-01",
        sources=("../sources/current-signal.md", "../career/harbor-launch.md"),
        assertion_kind="derived_synthesis",
        body=(
            "## Derived only\n\n"
            "This fictional brief is generated output, not personal evidence.\n"
        ),
    )
    write_page(
        vault,
        "derived/interview-packet-seed.md",
        page_type="synthesis",
        title="Interview Packet Seed",
        description="A fictional derived seed for an ephemeral task packet.",
        sources=("../career/harbor-launch.md", "../writing/explanation-pattern.md"),
        assertion_kind="derived_synthesis",
        body=(
            "## Derived packet seed\n\n"
            "This fictional packet seed remains derived and does not own facts.\n"
        ),
    )


def build_synthetic_vault(
    project_root: Path,
    *,
    schema_version: str = "0.2",
    missing_indexes: Iterable[str] = (),
) -> Path:
    """Create a medium fictional vault under ``project_root/vault``.

    ``missing_indexes`` is used only for migration fixtures.  The area, pages,
    and root link remain present so migration can infer the vertical while
    creating the missing managed control index.
    """

    if schema_version not in {"0.1", "0.2"}:
        raise ValueError("synthetic schema_version must be 0.1 or 0.2")
    project_root.mkdir(parents=True, exist_ok=True)
    vault = project_root / "vault"
    vault.mkdir()
    missing = set(missing_indexes)
    _write(vault / "SCHEMA.md", _schema_text(schema_version, ENABLED_VERTICALS))
    _write(vault / "index.md", _root_index(ENABLED_VERTICALS))
    _write(
        vault / "log.md",
        "# Synthetic Operation Log\n\n"
        "This fixture log is fictional and intentionally starts without maintenance entries.\n",
    )
    for area in ("core", "review", "sources", "derived", *ENABLED_VERTICALS):
        if area in missing:
            continue
        _write(vault / area / "index.md", _category_index(area))
    _write_fictional_pages(vault)

    custom = vault / "custom-notes"
    _write(custom / "index.md", "# Custom Notes\n\nThis area is preserved but unmanaged.\n")
    _write(
        custom / "field-log.md",
        "# Fictional Field Log\n\n"
        f"{SENSITIVE_BODY_MARKER} is deliberately outside canonical retrieval.\n",
    )

    # Catalog generation is fixture setup, not part of the operation under
    # test.  It gives every valid variant stable managed blocks while keeping
    # manual text outside those blocks byte-for-byte visible.
    result = sync_indexes.synchronize(vault, write=True)
    if result.get("findings") and any(
        item.get("severity") == "error" for item in result["findings"]
    ):
        raise AssertionError("failed to build synthetic managed catalogs")
    if missing:
        # Without the owning index, setup would temporarily catalogue those
        # pages under the root.  Leave the legacy fixture's root block empty so
        # migration can create the index and then compile the correct catalog
        # in one proposed state.
        root_text = (vault / "index.md").read_text(encoding="utf-8")
        start = root_text.index(CATALOG_START)
        end = root_text.index(CATALOG_END, start) + len(CATALOG_END)
        root_text = root_text[:start] + CATALOG_START + "\n" + CATALOG_END + root_text[end:]
        (vault / "index.md").write_text(root_text, encoding="utf-8")
    return vault


def copy_project(source_project: Path, destination_project: Path) -> Path:
    """Copy a fixture project, returning the copied vault path."""

    shutil.copytree(source_project, destination_project)
    return destination_project / "vault"


def tree_snapshot(root: Path) -> dict[str, tuple[str, str]]:
    """Hash every file/symlink below ``root`` without exposing its content."""

    snapshot: dict[str, tuple[str, str]] = {}
    if not root.exists():
        return snapshot
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[relative] = ("symlink", os.readlink(path))
        elif path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[relative] = ("file", digest)
    return snapshot


def canonical_page_snapshot(vault: Path) -> dict[str, tuple[str, str]]:
    """Return a snapshot limited to durable page bodies for preservation checks."""

    snapshot = tree_snapshot(vault)
    return {
        path: value
        for path, value in snapshot.items()
        if path.endswith(".md")
        and path not in {"SCHEMA.md", "index.md", "log.md"}
        and not path.endswith("/index.md")
        and not path.startswith("custom-notes/")
    }


def backup_paths(project_root: Path) -> list[Path]:
    return sorted((project_root / "backups").glob("vault-*.zip")) if (project_root / "backups").exists() else []


def managed_index_paths(vault: Path) -> list[str]:
    known_areas = {"core", "review", "sources", "derived", *ENABLED_VERTICALS}
    return sorted(
        path.relative_to(vault).as_posix()
        for path in vault.rglob("index.md")
        if path.is_file()
        and (
            len(path.relative_to(vault).parts) == 1
            or path.relative_to(vault).parts[0] in known_areas
        )
    )


def packet_from_results(
    results: Sequence[Mapping[str, object]],
    *,
    requested_verticals: Sequence[str],
    excluded_verticals: Sequence[str],
    retained: bool = False,
) -> dict[str, object]:
    """Build a metadata-only packet-shaped result for procedure tests.

    SelfContext currently defines packets in the skill procedure rather than a
    production CLI.  This helper intentionally returns paths and bounded
    search metadata only; it never writes a derived page or promotes evidence.
    """

    return {
        "type": "task_context_packet",
        "derived": True,
        "retained": retained,
        "requested_verticals": list(requested_verticals),
        "excluded_verticals": list(excluded_verticals),
        "evidence_paths": [str(item["path"]) for item in results],
        "unknowns": ["Fictional current state requires human confirmation."],
        "important_exclusions": [
            f"Excluded unrelated {vertical} context." for vertical in excluded_verticals
        ],
    }
