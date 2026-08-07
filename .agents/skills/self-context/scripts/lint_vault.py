#!/usr/bin/env python3
"""Deterministic structural lint for a SelfContext v0.1 vault."""

from __future__ import annotations

import argparse
import datetime as date
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote


REQUIRED_ROOT_FILES = ("SCHEMA.md", "index.md", "log.md")
REQUIRED_FIELDS = (
    "type",
    "title",
    "description",
    "tags",
    "status",
    "generated",
    "verified",
    "sources",
    "assertion_kind",
    "stale_after",
)
REQUIRED_NON_NULL_FIELDS = {
    "type",
    "title",
    "description",
    "status",
    "generated",
    "assertion_kind",
}
ALLOWED_TYPES = {"concept", "observation", "source", "synthesis"}
ALLOWED_STATUSES = {"active", "draft", "review", "archived", "superseded"}
ALLOWED_ASSERTIONS = {
    "user_stated_fact",
    "source_derived_fact",
    "agent_inference",
    "derived_synthesis",
    "source_record",
    "mixed",
}
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
SCHEMA_VERSION_PATTERN = re.compile(r"^\s*schema_version:\s*([0-9]+)\.([0-9]+)\s*$", re.MULTILINE)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        return [parse_scalar(item) for item in value[1:-1].split(",") if item.strip()]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == "null"


def parse_frontmatter(path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["missing YAML frontmatter"]

    closing = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if closing is None:
        return None, ["frontmatter has no closing ---"]

    values: Dict[str, Any] = {}
    list_key: Optional[str] = None
    errors: List[str] = []
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if line.startswith("  - ") and list_key:
            current = values.get(list_key)
            if current is None:
                current = []
                values[list_key] = current
            if not isinstance(current, list):
                errors.append(f"field {list_key!r} mixes scalar and list values")
                continue
            current.append(parse_scalar(line[4:]))
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            errors.append(f"malformed frontmatter line: {line!r}")
            list_key = None
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            errors.append("frontmatter contains an empty field name")
            list_key = None
            continue
        value = parse_scalar(raw_value)
        values[key] = value
        list_key = key if raw_value.strip() == "" else None

    return values, errors


def iter_markdown_links(text: str) -> Iterable[str]:
    in_fence = False
    visible_lines: List[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            visible_lines.append(line)
    for match in LINK_PATTERN.finditer("\n".join(visible_lines)):
        destination = match.group(1).strip()
        if not destination:
            continue
        if destination.startswith("<") and ">" in destination:
            destination = destination[1 : destination.index(">")]
        else:
            destination = destination.split()[0]
        yield destination


def is_external(destination: str) -> bool:
    return destination.startswith(("#", "//", "http://", "https://", "mailto:", "tel:"))


def relative_label(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def is_under_obsidian(path: Path, root: Path) -> bool:
    return ".obsidian" in path.relative_to(root).parts


def is_non_durable_page(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return relative in {Path("SCHEMA.md"), Path("log.md")} or path.name == "index.md"


def parse_iso_date(value: Any) -> Optional[date.date]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def lint_vault(root: Path, today: date.date) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    root = root.resolve()

    if not root.exists():
        return [f"vault does not exist: {root}"], []
    if not root.is_dir():
        return [f"vault path is not a directory: {root}"], []

    for required in REQUIRED_ROOT_FILES:
        if not (root / required).is_file():
            errors.append(f"missing required root file: {required}")

    schema = root / "SCHEMA.md"
    if schema.is_file():
        schema_match = SCHEMA_VERSION_PATTERN.search(schema.read_text(encoding="utf-8"))
        if not schema_match:
            warnings.append("SCHEMA.md does not declare a parseable schema_version")
        elif schema_match.groups() != ("0", "1"):
            warnings.append(
                "SCHEMA.md declares unsupported schema_version: "
                f"{schema_match.group(1)}.{schema_match.group(2)}"
            )

    markdown_files = sorted(
        path for path in root.rglob("*.md") if not is_under_obsidian(path, root)
    )
    titles: Dict[str, Path] = {}
    ids: Dict[str, Path] = {}

    for path in markdown_files:
        relative = relative_label(path, root)
        text = path.read_text(encoding="utf-8")

        if "[[" in text:
            errors.append(f"{relative}: canonical Markdown must not contain wikilinks")

        for destination in iter_markdown_links(text):
            if is_external(destination) or not destination:
                continue
            target_text = destination.split("#", 1)[0].split("?", 1)[0]
            if not target_text:
                continue
            target = (path.parent / unquote(target_text)).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(f"{relative}: link leaves vault: {destination}")
                continue
            if not target.is_file():
                errors.append(f"{relative}: broken link: {destination}")

        if is_non_durable_page(path, root):
            continue

        fields, frontmatter_errors = parse_frontmatter(path)
        for problem in frontmatter_errors:
            errors.append(f"{relative}: {problem}")
        if fields is None:
            continue

        for field in REQUIRED_FIELDS:
            if field not in fields or (field in REQUIRED_NON_NULL_FIELDS and is_empty(fields[field])):
                errors.append(f"{relative}: missing required field: {field}")

        page_type = fields.get("type")
        status = fields.get("status")
        assertion = fields.get("assertion_kind")
        if not isinstance(page_type, str) or page_type not in ALLOWED_TYPES:
            errors.append(f"{relative}: invalid type: {page_type!r}")
        if not isinstance(status, str) or status not in ALLOWED_STATUSES:
            errors.append(f"{relative}: invalid status: {status!r}")
        if not isinstance(assertion, str) or assertion not in ALLOWED_ASSERTIONS:
            errors.append(f"{relative}: invalid assertion_kind: {assertion!r}")

        title = fields.get("title")
        if isinstance(title, str) and title.strip():
            title_key = " ".join(title.lower().split())
            if title_key in titles:
                warnings.append(
                    f"{relative}: duplicate title also used by {relative_label(titles[title_key], root)}"
                )
            else:
                titles[title_key] = path

        page_id = fields.get("id")
        if isinstance(page_id, str) and page_id.strip():
            if page_id in ids:
                errors.append(
                    f"{relative}: duplicate id also used by {relative_label(ids[page_id], root)}"
                )
            else:
                ids[page_id] = path

        generated = fields.get("generated")
        if not is_empty(generated) and parse_iso_date(generated) is None:
            errors.append(f"{relative}: generated is not an ISO date or datetime")

        verified = fields.get("verified")
        if not is_empty(verified) and parse_iso_date(verified) is None:
            errors.append(f"{relative}: verified is not an ISO date or datetime")

        stale_after = fields.get("stale_after")
        if not is_empty(stale_after):
            stale_date = parse_iso_date(stale_after)
            if stale_date is None:
                errors.append(f"{relative}: stale_after is not an ISO date")
            elif stale_date < today:
                warnings.append(f"{relative}: stale_after has passed ({stale_after})")

        if assertion == "agent_inference" or page_type == "observation":
            if is_empty(fields.get("verified")):
                warnings.append(f"{relative}: observation or inference is unverified")
            if status != "review":
                warnings.append(f"{relative}: observation or inference should normally have status: review")

        if "description" in fields and not isinstance(fields.get("description"), str):
            errors.append(f"{relative}: description must be a YAML string")
        if "tags" in fields and not isinstance(fields.get("tags"), list):
            errors.append(f"{relative}: tags must be a YAML list (use [] when empty)")

        sources = as_list(fields.get("sources"))
        if isinstance(assertion, str) and assertion in {"source_derived_fact", "derived_synthesis"} and not sources:
            warnings.append(f"{relative}: {assertion} has no sources")
        for source in sources:
            if not isinstance(source, str) or is_external(source):
                continue
            source_path = (path.parent / unquote(source.split("#", 1)[0])).resolve()
            try:
                source_path.relative_to(root)
            except ValueError:
                errors.append(f"{relative}: source reference leaves vault: {source}")
                continue
            if not source_path.is_file():
                errors.append(f"{relative}: missing source reference: {source}")

    root_index = root / "index.md"
    if root_index.is_file():
        index_text = root_index.read_text(encoding="utf-8")
        for expected in ("SCHEMA.md", "core/index.md", "career/index.md", "review/index.md", "sources/index.md", "derived/index.md", "log.md"):
            if expected not in index_text:
                warnings.append(f"index.md does not mention {expected}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a SelfContext v0.1 vault")
    parser.add_argument("vault", nargs="?", default="vault", help="Path to the vault (default: ./vault)")
    parser.add_argument("--today", help="ISO date used for stale_after checks (default: today)")
    args = parser.parse_args()

    today = date.date.today()
    if args.today:
        try:
            today = date.date.fromisoformat(args.today)
        except ValueError:
            print(f"ERROR: invalid --today date: {args.today}", file=sys.stderr)
            return 1

    errors, warnings = lint_vault(Path(args.vault), today)
    for finding in errors:
        print(f"ERROR: {finding}")
    for finding in warnings:
        print(f"WARNING: {finding}")
    print(f"SelfContext lint: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
