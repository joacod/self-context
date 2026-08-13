#!/usr/bin/env python3
"""Synchronize SelfContext's managed Markdown catalog blocks.

The script is intentionally disposable: it compiles navigation from durable
page metadata and never becomes evidence.  Text outside explicit marker blocks
is preserved byte-for-byte when possible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from vault_utils import (
        canonical_markdown_files,
        durable_page_records,
        is_control_page,
        nearest_index,
        relative_label,
        safe_read_text,
    )
except ImportError:  # pragma: no cover - useful when imported as a package
    from .vault_utils import (  # type: ignore
        canonical_markdown_files,
        durable_page_records,
        is_control_page,
        nearest_index,
        relative_label,
        safe_read_text,
    )


CATALOG_START = "<!-- selfcontext:catalog:start -->"
CATALOG_END = "<!-- selfcontext:catalog:end -->"
BLOCK_PATTERN = re.compile(
    rf"(?ms)^[ \t]*{re.escape(CATALOG_START)}[ \t]*\n.*?^[ \t]*{re.escape(CATALOG_END)}[ \t]*(?:\n|$)"
)
ENTRY_PATTERN = re.compile(
    r"^- \[(?P<title>[^]]+)\]\((?P<path>[^)]+)\) — (?P<description>.*?) `(?P<status>[^`]+)`\s*$"
)


def managed_block(text: str) -> Optional[str]:
    match = BLOCK_PATTERN.search(text)
    return match.group(0) if match else None


def managed_entries(text: str) -> List[Dict[str, str]]:
    block = managed_block(text)
    if block is None:
        return []
    entries: List[Dict[str, str]] = []
    for line in block.splitlines():
        match = ENTRY_PATTERN.match(line.strip())
        if match:
            entries.append(match.groupdict())
    return entries


def _replace_block(text: str, block: str) -> str:
    match = BLOCK_PATTERN.search(text)
    if match:
        return text[: match.start()] + block + text[match.end() :]
    separator = "" if not text else ("" if text.endswith("\n") else "\n")
    if text and not text.endswith("\n"):
        separator = "\n"
    return text + separator + block


def _format_block(entries: Iterable[str]) -> str:
    lines = [CATALOG_START]
    lines.extend(entries)
    lines.append(CATALOG_END)
    return "\n".join(lines) + "\n"


def _page_entries(vault: Path) -> Tuple[Dict[Path, List[str]], List[Dict[str, str]]]:
    by_index: Dict[Path, List[str]] = {}
    findings: List[Dict[str, str]] = []
    try:
        import vault_utils
        catalog = vault_utils.load_vertical_catalog()
        known_areas = {"core", "review", "sources", "derived"} | {
            str(item.get("vault_area")) for item in vault_utils.catalog_records(catalog)
        }
    except (ImportError, OSError, ValueError, json.JSONDecodeError):
        known_areas = {"core", "review", "sources", "derived"}
    for record in durable_page_records(vault):
        page_parts = Path(record["path"]).parts
        if page_parts and (page_parts[0] == ".DS_Store" or (len(page_parts) > 1 and page_parts[0] not in known_areas)):
            findings.append(
                {
                    "severity": "info",
                    "classification": "custom-area",
                    "path": record["path"],
                    "message": "custom top-level page preserved and excluded from managed catalogs",
                }
            )
            continue
        page_path = vault / record["path"]
        owner = nearest_index(page_path, vault)
        if owner is None:
            findings.append(
                {
                    "severity": "error",
                    "classification": "nearest-index-ownership",
                    "path": record["path"],
                    "message": "durable page has no nearest ancestor index",
                }
            )
            continue
        fields = record.get("frontmatter")
        if not isinstance(fields, dict):
            findings.append(
                {
                    "severity": "error",
                    "classification": "page-metadata",
                    "path": record["path"],
                    "message": "durable page has no parseable frontmatter",
                }
            )
            continue
        title = fields.get("title")
        description = fields.get("description")
        status = fields.get("status")
        if not isinstance(title, str) or not title.strip():
            findings.append(
                {
                    "severity": "error",
                    "classification": "page-metadata",
                    "path": record["path"],
                    "message": "catalog entry needs a non-empty title",
                }
            )
            continue
        if not isinstance(description, str) or not description.strip():
            findings.append(
                {
                    "severity": "error",
                    "classification": "page-metadata",
                    "path": record["path"],
                    "message": "catalog entry needs an existing non-empty description",
                }
            )
            continue
        if not isinstance(status, str) or not status.strip():
            findings.append(
                {
                    "severity": "error",
                    "classification": "page-metadata",
                    "path": record["path"],
                    "message": "catalog entry needs an existing status",
                }
            )
            continue
        relative = Path(record["path"])
        import posixpath

        target = Path(
            posixpath.relpath(
                relative.as_posix(),
                start=owner.relative_to(vault).parent.as_posix() or ".",
            )
        )
        entry = f"- [{title}]({target.as_posix()}) — {description} `{status}`"
        by_index.setdefault(owner, []).append(entry)
    for entries in by_index.values():
        entries.sort(key=lambda line: (line.casefold(), line))
    return by_index, findings


def _index_paths(vault: Path) -> List[Path]:
    try:
        import vault_utils
        catalog = vault_utils.load_vertical_catalog()
        known_areas = {"core", "review", "sources", "derived"} | {
            str(item.get("vault_area")) for item in vault_utils.catalog_records(catalog)
        }
    except (ImportError, OSError, ValueError, json.JSONDecodeError):
        known_areas = {"core", "review", "sources", "derived"}
    paths = []
    for path in canonical_markdown_files(vault):
        if path.name != "index.md":
            continue
        parts = path.relative_to(vault).parts
        if len(parts) == 1 or parts[0] in known_areas:
            paths.append(path)
    return sorted(paths)


def synchronize(vault: Path, write: bool = False) -> Dict[str, Any]:
    vault = vault.expanduser()
    if not vault.exists():
        return {
            "vault": str(vault),
            "changed": [],
            "findings": [
                {
                    "severity": "error",
                    "classification": "vault",
                    "path": str(vault),
                    "message": "vault does not exist",
                }
            ],
        }
    if vault.is_symlink() or not vault.is_dir():
        return {
            "vault": str(vault),
            "changed": [],
            "findings": [
                {
                    "severity": "error",
                    "classification": "vault",
                    "path": str(vault),
                    "message": "vault path must be a real directory",
                }
            ],
        }

    desired, findings = _page_entries(vault)
    indexes = _index_paths(vault)
    # An existing managed block with no remaining pages is intentionally
    # replaced by an empty block so dead generated entries disappear on write.
    for index in indexes:
        text, error = safe_read_text(index)
        label = relative_label(index, vault)
        if text is None:
            findings.append(
                {
                    "severity": "error",
                    "classification": "utf8",
                    "path": label,
                    "message": error or "unable to read index",
                }
            )
            continue
        entries = desired.get(index, [])
        expected = _format_block(entries)
        actual = managed_block(text)
        current = actual if actual is not None else ""
        if current != expected:
            item = {
                "severity": "error" if not write else "info",
                "classification": "catalog-sync",
                "path": label,
                "message": "managed catalog block is out of sync",
                "expected_entries": str(len(entries)),
                "actual_entries": str(len(managed_entries(text))),
            }
            findings.append(item)
            if write:
                try:
                    index.write_text(_replace_block(text, expected), encoding="utf-8")
                except OSError as error:
                    findings.append(
                        {
                            "severity": "error",
                            "classification": "catalog-write",
                            "path": label,
                            "message": str(error),
                        }
                    )
    # Pages whose owner index was not itself present are already reported by
    # _page_entries.  Keep a compact changed list based on the post-operation
    # comparison rather than relying on filesystem metadata.
    changed: List[str] = []
    for index in indexes:
        text, _ = safe_read_text(index)
        if text is None:
            continue
        expected = _format_block(desired.get(index, []))
        if managed_block(text) == expected:
            # It is useful to report synchronized indexes only when the original
            # state differed; derive that from the finding list.
            if any(
                finding.get("path") == relative_label(index, vault)
                and finding.get("classification") == "catalog-sync"
                for finding in findings
            ):
                changed.append(relative_label(index, vault))
    if write:
        # A write is successful when no actual error remains.  Sync notices are
        # informational after applying the block.
        for finding in findings:
            if finding.get("classification") == "catalog-sync":
                finding["severity"] = "info"
    return {
        "vault": str(vault.resolve()),
        "changed": changed,
        "indexes": [relative_label(path, vault) for path in indexes],
        "findings": findings,
        "write": write,
    }


def _print_text(result: Dict[str, Any]) -> None:
    for finding in result.get("findings", []):
        severity = str(finding.get("severity", "info")).upper()
        path = finding.get("path", "")
        message = finding.get("message", "")
        print(f"{severity}: {path}: {message}" if path else f"{severity}: {message}")
    changed = result.get("changed", [])
    if changed:
        print("Synchronized catalogs: " + ", ".join(changed))
    if not result.get("findings"):
        print("SelfContext index catalogs: synchronized")


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronize managed SelfContext index catalogs")
    parser.add_argument("vault", nargs="?", default="vault")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="compare without writing")
    mode.add_argument("--write", action="store_true", help="write managed catalog blocks")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    result = synchronize(Path(args.vault), write=args.write)
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_text(result)
    has_error = any(f.get("severity") == "error" for f in result.get("findings", []))
    if args.write:
        return 1 if has_error else 0
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
