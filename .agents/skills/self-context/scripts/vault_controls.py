#!/usr/bin/env python3
"""Shared current-schema control-file planning helpers.

These helpers render only deterministic control/layout companions.  Semantic
ownership, vertical selection, and migration decisions remain with callers.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    import sync_indexes
    from vault_utils import (
        iter_markdown_links,
        link_target,
        relative_label,
        safe_read_text,
    )
except ImportError:  # pragma: no cover - package-style import fallback
    from . import sync_indexes  # type: ignore
    from .vault_utils import (  # type: ignore
        iter_markdown_links,
        link_target,
        relative_label,
        safe_read_text,
    )


SCHEMA_VERSION_LINE = re.compile(
    r"^([ \t]*schema_version:[ \t]*)[^\s#]+([ \t]*(?:#.*)?)$", re.MULTILINE
)
SCHEMA_SECTION_LINE = re.compile(r"^[ \t]*vertical_contracts:[^\r\n]*$", re.MULTILINE)


def _newline_style(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def schema_with_contracts(
    text: str,
    contracts: Sequence[Mapping[str, Any]],
    *,
    schema_version: str = "0.2",
) -> str:
    """Render a schema version and exact applied contract list in place.

    The surrounding schema prose is preserved.  Callers must make the
    semantic decision about which contracts belong in ``contracts``.
    """

    matches = list(SCHEMA_VERSION_LINE.finditer(text))
    if len(matches) != 1:
        raise ValueError("SCHEMA.md must contain exactly one schema_version declaration")

    newline = _newline_style(text)
    match = matches[0]
    updated = (
        text[: match.start()]
        + f"{match.group(1)}{schema_version}{match.group(2)}"
        + text[match.end() :]
    )
    lines = updated.splitlines(keepends=True)
    section_indices = [
        index
        for index, line in enumerate(lines)
        if SCHEMA_SECTION_LINE.match(line.rstrip("\r\n"))
    ]
    if len(section_indices) > 1:
        raise ValueError("SCHEMA.md contains duplicate vertical_contracts sections")

    block = [f"vertical_contracts:{newline}"]
    block.extend(
        f"  - {contract['id']}@{contract['version']}{newline}"
        for contract in contracts
    )

    if section_indices:
        start = section_indices[0]
        end = start + 1
        while end < len(lines):
            stripped = lines[end].strip()
            if not stripped:
                end += 1
                continue
            if lines[end].startswith((" ", "\t")) and stripped.startswith("-"):
                end += 1
                continue
            break
        lines[start:end] = block
    else:
        version_index = next(
            index
            for index, line in enumerate(lines)
            if re.match(r"^[ \t]*schema_version:[ \t]*" + re.escape(schema_version), line)
        )
        lines[version_index + 1 : version_index + 1] = block

    result = "".join(lines)
    if not text.endswith(("\n", "\r")) and result.endswith(newline):
        result = result[: -len(newline)]
    return result


def root_has_link(vault: Path, index_path: str, text: Optional[str] = None) -> bool:
    """Return whether the root index contains a link to ``index_path``."""

    root_index = vault / "index.md"
    if text is None:
        text, error = safe_read_text(root_index)
        if error or text is None:
            return False
    for destination in iter_markdown_links(text):
        try:
            target = link_target(root_index, destination, vault)
            if target is not None and relative_label(target, vault) == index_path:
                return True
        except (OSError, RuntimeError, ValueError):
            continue
    return False


def vertical_index_template(record: Mapping[str, Any]) -> str:
    """Render the control index shape for one catalog record."""

    display_name = str(record.get("display_name") or record.get("vault_area"))
    ownership = str(record.get("ownership") or f"{display_name} context.")
    start = getattr(sync_indexes, "CATALOG_START", "<!-- selfcontext:catalog:start -->")
    end = getattr(sync_indexes, "CATALOG_END", "<!-- selfcontext:catalog:end -->")
    return f"# {display_name} Context\n\n{ownership}\n\n{start}\n{end}\n"


def root_with_links(
    vault: Path,
    contracts: Sequence[Mapping[str, Any]],
    catalog: Mapping[str, Any],
    text: str,
) -> Tuple[str, List[str]]:
    """Add only the explicitly supplied vertical root links."""

    records = {
        str(record.get("id")): record
        for record in catalog.get("verticals", [])
        if isinstance(record, dict)
    }
    additions: List[Tuple[str, str]] = []
    for contract in contracts:
        identifier = str(contract.get("id"))
        record = records.get(identifier)
        if record is None:
            continue
        index_path = record.get("index_path")
        if not isinstance(index_path, str) or root_has_link(vault, index_path, text):
            continue
        additions.append(
            (index_path, f"- [{record.get('display_name', identifier)} context]({index_path})")
        )
    if not additions:
        return text, []

    newline = _newline_style(text)
    separator = "" if text.endswith(("\n", "\r")) else newline
    result = text + separator + newline.join(line for _, line in additions) + newline
    return result, [index_path for index_path, _ in additions]
