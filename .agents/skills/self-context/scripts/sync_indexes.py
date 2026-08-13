#!/usr/bin/env python3
"""Synchronize SelfContext's managed Markdown catalog blocks.

The script is intentionally disposable: it compiles navigation from durable
page metadata and never becomes evidence. Text outside explicit marker blocks
is preserved byte-for-byte when possible. Writes are planned for the complete
set of managed indexes and committed only after every input has been checked.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

try:
    from vault_utils import (
        canonical_markdown_files,
        durable_page_records,
        link_target,
        nearest_index,
        relative_label,
        safe_read_bytes,
    )
except ImportError:  # pragma: no cover - useful when imported as a package
    from .vault_utils import (  # type: ignore
        canonical_markdown_files,
        durable_page_records,
        link_target,
        nearest_index,
        relative_label,
        safe_read_bytes,
    )


CATALOG_START = "<!-- selfcontext:catalog:start -->"
CATALOG_END = "<!-- selfcontext:catalog:end -->"

# The label parser accepts backslash-escaped Markdown punctuation. Generated
# paths percent-encode parentheses and whitespace, so a closing parenthesis is
# unambiguous at this seam.
ENTRY_LINK_PATTERN = re.compile(
    r"^- \[(?P<title>(?:\\.|[^\\\]])*)\]\((?P<path>[^)\r\n]*)\) — (?P<rest>.*)$"
)
STATUS_PATTERN = re.compile(r" (?P<delimiter>`+)(?P<status>.*?)(?P=delimiter)$")

_MARKDOWN_PUNCTUATION = set(r"\\`*_{}[]()#+-.!<>|&")


@dataclass(frozen=True)
class _MarkerEvent:
    kind: str
    line_start: int
    line_end: int


@dataclass
class _MarkerParse:
    events: List[_MarkerEvent]
    errors: List[str]
    block_span: Optional[Tuple[int, int]] = None
    missing: bool = False
    complete_blocks: int = 0
    max_depth: int = 0

    @property
    def valid(self) -> bool:
        return not self.errors and self.block_span is not None


def _marker_parse(text: str) -> _MarkerParse:
    """Parse marker lines without selecting an authoritative block on error."""

    events: List[_MarkerEvent] = []
    malformed: List[str] = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        stripped = line.strip()
        if stripped == CATALOG_START:
            events.append(_MarkerEvent("start", offset, offset + len(raw_line)))
        elif stripped == CATALOG_END:
            events.append(_MarkerEvent("end", offset, offset + len(raw_line)))
        else:
            for marker, name in ((CATALOG_START, "start"), (CATALOG_END, "end")):
                if marker in line:
                    malformed.append(f"{name} marker must appear on its own line")
        offset += len(raw_line)

    errors: List[str] = []
    if malformed:
        errors.extend(sorted(set(malformed)))

    starts = [event for event in events if event.kind == "start"]
    ends = [event for event in events if event.kind == "end"]
    if not events:
        # A line containing a marker with surrounding prose is malformed, not
        # a genuinely missing block.
        return _MarkerParse(events, errors, missing=not malformed)

    if len(starts) > 1:
        errors.append("duplicate start markers")
    if len(ends) > 1:
        errors.append("duplicate end markers")

    stack: List[_MarkerEvent] = []
    blocks: List[Tuple[_MarkerEvent, _MarkerEvent]] = []
    unmatched_ends: List[_MarkerEvent] = []
    max_depth = 0
    for event in events:
        if event.kind == "start":
            if stack:
                max_depth = max(max_depth, len(stack) + 1)
            stack.append(event)
            max_depth = max(max_depth, len(stack))
            continue
        if not stack:
            unmatched_ends.append(event)
            continue
        start = stack.pop()
        blocks.append((start, event))

    if stack:
        errors.append("unmatched start marker")
    if unmatched_ends:
        errors.append("unmatched end marker")

    first_start = starts[0] if starts else None
    if first_start is None or any(
        event.kind == "end" and event.line_start < first_start.line_start for event in events
    ):
        errors.append("end marker appears before start marker")

    if len(blocks) > 1:
        errors.append("more than one complete catalog block")
    if max_depth > 1:
        errors.append("nested or overlapping managed catalog blocks")

    errors = list(dict.fromkeys(errors))
    span: Optional[Tuple[int, int]] = None
    if not errors and len(starts) == 1 and len(ends) == 1 and len(blocks) == 1:
        start, end = blocks[0]
        span = (start.line_start, end.line_end)

    return _MarkerParse(
        events,
        errors,
        block_span=span,
        complete_blocks=len(blocks),
        max_depth=max_depth,
    )


def managed_block(text: str) -> Optional[str]:
    """Return the sole valid managed block, never an arbitrary partial block."""

    parsed = _marker_parse(text)
    if not parsed.valid or parsed.block_span is None:
        return None
    start, end = parsed.block_span
    return text[start:end]


def _unescape_markdown(value: str) -> str:
    punctuation = set(r"\\`*_{}[]()#+-.!<>|&")
    result: List[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        if character == "\\" and index + 1 < len(value) and value[index + 1] in punctuation:
            result.append(value[index + 1])
            index += 2
        else:
            result.append(character)
            index += 1
    return "".join(result)


def _parse_entry_line(line: str) -> Optional[Dict[str, str]]:
    match = ENTRY_LINK_PATTERN.match(line.strip())
    if not match:
        return None
    rest = match.group("rest")
    status_matches = list(STATUS_PATTERN.finditer(rest))
    if not status_matches:
        return None
    status_match = status_matches[-1]
    description = rest[: status_match.start()].rstrip()
    return {
        "title": _unescape_markdown(match.group("title")),
        "path": match.group("path"),
        "description": _unescape_markdown(description),
        "status": html.unescape(status_match.group("status")),
    }


def managed_entries(text: str) -> List[Dict[str, str]]:
    block = managed_block(text)
    if block is None:
        return []
    entries: List[Dict[str, str]] = []
    for line in block.splitlines():
        if line.strip() in {CATALOG_START, CATALOG_END}:
            continue
        entry = _parse_entry_line(line)
        if entry is not None:
            entries.append(entry)
    return entries


def _newline_style(text: str) -> str:
    counts = {
        "\r\n": text.count("\r\n"),
        "\n": text.count("\n") - text.count("\r\n"),
        "\r": text.count("\r") - text.count("\r\n"),
    }
    candidates = [(count, newline) for newline, count in counts.items() if count]
    return max(candidates, key=lambda item: (item[0], item[1] == "\r\n"))[1] if candidates else "\n"


def _replace_block(text: str, block: str, newline: Optional[str] = None) -> str:
    """Replace a valid block or append a missing block without touching prose."""

    parsed = _marker_parse(text)
    if parsed.valid and parsed.block_span is not None:
        start, end = parsed.block_span
        return text[:start] + block + text[end:]
    if parsed.errors:
        return text
    line_ending = newline or _newline_style(text)
    separator = "" if not text or text.endswith(("\r", "\n")) else line_ending
    return text + separator + block


def _format_block(entries: Iterable[str], newline: str = "\n", final_newline: bool = True) -> str:
    lines = [CATALOG_START]
    lines.extend(entries)
    lines.append(CATALOG_END)
    return newline.join(lines) + (newline if final_newline else "")


def _presentation_text(value: str) -> str:
    # split() handles line breaks, tabs, repeated spaces, and Unicode
    # whitespace without changing the underlying metadata used by lint.
    return " ".join(value.split())


def _escape_markdown_text(value: str) -> str:
    return "".join(
        ("\\" + character) if character in _MARKDOWN_PUNCTUATION else character
        for character in _presentation_text(value)
    )


def _render_status(value: str) -> str:
    # A code span cannot contain an unescaped backtick. HTML escaping preserves
    # the visible value while keeping the delimiter deterministic and simple.
    return html.escape(_presentation_text(value), quote=False).replace("`", "&#96;")


def _render_path(path: Path) -> str:
    # Markdown destinations are URI-like. Keep only path separators and the
    # unreserved filename characters; this safely handles spaces, parentheses,
    # brackets, backslashes, Unicode, ?, #, and percent signs.
    return quote(path.as_posix(), safe="/._~-")


def _format_entry(title: str, description: str, status: str, target: Path) -> str:
    return (
        f"- [{_escape_markdown_text(title)}]({_render_path(target)}) — "
        f"{_escape_markdown_text(description)} `{_render_status(status)}`"
    )


def _metadata_finding(
    path: str,
    message: str,
    owner: Optional[Path],
    vault: Path,
) -> Dict[str, Any]:
    finding: Dict[str, Any] = {
        "severity": "error",
        "classification": "page-metadata",
        "state": "metadata-preventing-safe-rendering",
        "path": path,
        "message": message,
    }
    if owner is not None:
        finding["owner_index"] = relative_label(owner, vault)
    return finding


def _known_areas() -> set[str]:
    try:
        import vault_utils

        catalog = vault_utils.load_vertical_catalog()
        return {"core", "review", "sources", "derived"} | {
            str(item.get("vault_area"))
            for item in vault_utils.catalog_records(catalog)
            if item.get("vault_area")
        }
    except (ImportError, OSError, ValueError, json.JSONDecodeError):
        return {"core", "review", "sources", "derived"}


def _page_entries(vault: Path) -> Tuple[Dict[Path, List[str]], List[Dict[str, Any]]]:
    by_index: Dict[Path, List[Tuple[Tuple[str, str, str], str]]] = {}
    findings: List[Dict[str, Any]] = []
    known_areas = _known_areas()
    for record in durable_page_records(vault):
        page_path_text = str(record["path"])
        page_parts = Path(page_path_text).parts
        if page_parts and (
            page_parts[0] == ".DS_Store"
            or (len(page_parts) > 1 and page_parts[0] not in known_areas)
        ):
            findings.append(
                {
                    "severity": "info",
                    "classification": "custom-area",
                    "path": page_path_text,
                    "message": "custom top-level page preserved and excluded from managed catalogs",
                }
            )
            continue

        page_path = vault / page_path_text
        owner = nearest_index(page_path, vault)
        if owner is None:
            findings.append(
                {
                    "severity": "error",
                    "classification": "nearest-index-ownership",
                    "state": "catalog-owner-mismatch",
                    "path": page_path_text,
                    "message": "durable page has no nearest ancestor index",
                }
            )
            continue

        fields = record.get("frontmatter")
        if not isinstance(fields, dict):
            findings.append(
                _metadata_finding(
                    page_path_text,
                    "durable page has no parseable frontmatter",
                    owner,
                    vault,
                )
            )
            continue
        if record.get("frontmatter_errors"):
            findings.append(
                _metadata_finding(
                    page_path_text,
                    "durable page frontmatter is structurally invalid; catalog rendering is blocked",
                    owner,
                    vault,
                )
            )
            continue

        title = fields.get("title")
        description = fields.get("description")
        status = fields.get("status")
        if not isinstance(title, str) or not title.strip():
            findings.append(
                _metadata_finding(
                    page_path_text,
                    "catalog entry needs a non-empty title",
                    owner,
                    vault,
                )
            )
            continue
        if not isinstance(description, str) or not description.strip():
            findings.append(
                _metadata_finding(
                    page_path_text,
                    "catalog entry needs an existing non-empty description",
                    owner,
                    vault,
                )
            )
            continue
        if not isinstance(status, str) or not status.strip():
            findings.append(
                _metadata_finding(
                    page_path_text,
                    "catalog entry needs an existing status",
                    owner,
                    vault,
                )
            )
            continue

        relative = Path(page_path_text)
        target = Path(
            posixpath.relpath(
                relative.as_posix(),
                start=owner.relative_to(vault).parent.as_posix() or ".",
            )
        )
        entry = _format_entry(title, description, status, target)
        sort_key = (
            _presentation_text(title).casefold(),
            _presentation_text(title),
            relative.as_posix(),
        )
        by_index.setdefault(owner, []).append((sort_key, entry))

    rendered: Dict[Path, List[str]] = {}
    for owner, entries in by_index.items():
        rendered[owner] = [entry for _, entry in sorted(entries, key=lambda item: item[0])]
    return rendered, findings


def _index_paths(vault: Path) -> List[Path]:
    known_areas = _known_areas()
    paths = []
    for path in canonical_markdown_files(vault):
        if path.name != "index.md":
            continue
        parts = path.relative_to(vault).parts
        if len(parts) == 1 or parts[0] in known_areas:
            paths.append(path)
    return sorted(paths)


def _read_index(path: Path) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    raw, error = safe_read_bytes(path)
    if raw is None:
        return None, None, error or "unable to read index"
    try:
        return raw, raw.decode("utf-8"), None
    except UnicodeDecodeError:
        return raw, None, "UnicodeDecodeError: file is not valid UTF-8"


def _owner_findings(
    index: Path,
    text: str,
    vault: Path,
    records_by_path: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    parsed = _marker_parse(text)
    if not parsed.valid:
        return []
    results: List[Dict[str, Any]] = []
    label = relative_label(index, vault)
    for entry in managed_entries(text):
        try:
            target = link_target(index, entry["path"], vault)
            if target is None:
                continue
            target_label = relative_label(target, vault)
        except (OSError, RuntimeError, ValueError):
            continue
        record = records_by_path.get(target_label)
        if record is None:
            continue
        owner = nearest_index(vault / target_label, vault)
        if owner is None or owner.resolve() == index.resolve():
            continue
        results.append(
            {
                "severity": "error",
                "classification": "catalog-owner-mismatch",
                "state": "catalog-owner-mismatch",
                "path": label,
                "entry_path": entry["path"],
                "owner_index": relative_label(owner, vault),
                "message": (
                    f"catalog entry points to a page owned by "
                    f"{relative_label(owner, vault)}"
                ),
            }
        )
    return results


def _write_temp(path: Path, content: bytes, suffix: str = "") -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.sync-",
        suffix=suffix,
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return temporary


def _atomic_replace(
    updates: Dict[Path, bytes],
    originals: Dict[Path, bytes],
    vault: Path,
) -> Tuple[bool, List[Dict[str, Any]], List[Path]]:
    """Replace all planned indexes and roll back replaced files on failure."""

    temporary_paths: Dict[Path, Path] = {}
    rollback_paths: List[Path] = []
    replaced: List[Path] = []
    failures: List[Dict[str, Any]] = []
    success = False
    try:
        for path, content in sorted(updates.items(), key=lambda item: item[0].as_posix()):
            temporary_paths[path] = _write_temp(path, content)
        for path in sorted(updates, key=lambda item: item.as_posix()):
            os.replace(temporary_paths[path], path)
            replaced.append(path)
        success = True
    except Exception as error:
        failures.append(
            {
                "severity": "error",
                "classification": "catalog-write",
                "state": "write-failed",
                "message": f"atomic catalog replacement failed: {error}",
            }
        )
        rollback_failures: List[str] = []
        for path in reversed(replaced):
            try:
                rollback = _write_temp(path, originals[path], suffix="-rollback")
                rollback_paths.append(rollback)
                os.replace(rollback, path)
            except Exception as rollback_error:
                rollback_failures.append(
                    f"{relative_label(path, vault)}: {rollback_error}"
                )
        if rollback_failures:
            failures.append(
                {
                    "severity": "error",
                    "classification": "catalog-rollback",
                    "state": "rollback-failed",
                    "message": "bounded rollback failed: " + "; ".join(rollback_failures),
                }
            )
    finally:
        for temporary in list(temporary_paths.values()) + rollback_paths:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                # The caller receives the replacement/rollback error. A
                # cleanup failure is reported separately rather than hidden.
                failures.append(
                    {
                        "severity": "error",
                        "classification": "catalog-cleanup",
                        "state": "temporary-cleanup-failed",
                        "path": relative_label(temporary, vault),
                        "message": "unable to remove temporary catalog file",
                    }
                )
    return success, failures, replaced


def _finding_has_error(findings: Iterable[Dict[str, Any]]) -> bool:
    return any(finding.get("severity") == "error" for finding in findings)


def _state_priority(states: Iterable[str]) -> List[str]:
    order = [
        "invalid-marker-structure",
        "catalog-owner-mismatch",
        "metadata-preventing-safe-rendering",
        "write-failed",
        "rollback-failed",
        "temporary-cleanup-failed",
        "utf8-error",
        "missing-catalog-block",
        "drifted",
        "synchronized",
    ]
    present = set(states)
    return [state for state in order if state in present]


def synchronize(vault: Path, write: bool = False) -> Dict[str, Any]:
    vault = vault.expanduser()
    if not vault.exists():
        return {
            "vault": str(vault),
            "status": "error",
            "changed": [],
            "findings": [
                {
                    "severity": "error",
                    "classification": "vault",
                    "state": "error",
                    "path": str(vault),
                    "message": "vault does not exist",
                }
            ],
            "write": write,
        }
    if vault.is_symlink() or not vault.is_dir():
        return {
            "vault": str(vault),
            "status": "error",
            "changed": [],
            "findings": [
                {
                    "severity": "error",
                    "classification": "vault",
                    "state": "error",
                    "path": str(vault),
                    "message": "vault path must be a real directory",
                }
            ],
            "write": write,
        }

    desired, findings = _page_entries(vault)
    indexes = _index_paths(vault)
    records_by_path = {
        str(record["path"]): record for record in durable_page_records(vault)
    }
    metadata_indexes = {
        str(finding["owner_index"])
        for finding in findings
        if finding.get("state") == "metadata-preventing-safe-rendering"
        and finding.get("owner_index")
    }

    plans: List[Dict[str, Any]] = []
    for index in indexes:
        label = relative_label(index, vault)
        raw, text, error = _read_index(index)
        if raw is None or text is None:
            findings.append(
                {
                    "severity": "error",
                    "classification": "utf8" if error and error.startswith("Unicode") else "filesystem",
                    "state": "utf8-error" if error and error.startswith("Unicode") else "error",
                    "path": label,
                    "message": error or "unable to read index",
                }
            )
            plans.append({"path": index, "label": label, "state": "utf8-error", "changed": False})
            continue

        parsed = _marker_parse(text)
        marker_errors = parsed.errors
        if marker_errors:
            for message in marker_errors:
                findings.append(
                    {
                        "severity": "error",
                        "classification": "catalog-marker-structure",
                        "state": "invalid-marker-structure",
                        "path": label,
                        "message": message,
                    }
                )
            plans.append(
                {
                    "path": index,
                    "label": label,
                    "state": "invalid-marker-structure",
                    "changed": False,
                    "expected_entries": len(desired.get(index, [])),
                    "actual_entries": 0,
                }
            )
            continue

        owner_findings = _owner_findings(index, text, vault, records_by_path)
        findings.extend(owner_findings)
        newline = _newline_style(text)
        entries = desired.get(index, [])
        if parsed.valid and parsed.block_span is not None:
            start, end = parsed.block_span
            current_block = text[start:end]
            expected_block = _format_block(
                entries,
                newline=newline,
                final_newline=current_block.endswith(("\r", "\n")),
            )
            candidate = text[:start] + expected_block + text[end:]
            state = "drifted" if candidate != text else "synchronized"
            actual_entries = len(managed_entries(text))
        else:
            expected_block = _format_block(entries, newline=newline)
            candidate = _replace_block(text, expected_block, newline=newline)
            state = "missing-catalog-block"
            actual_entries = 0
            findings.append(
                {
                    "severity": "error" if not write else "info",
                    "classification": "catalog-missing",
                    "state": "missing-catalog-block",
                    "path": label,
                    "message": "managed catalog block is missing",
                    "expected_entries": len(entries),
                    "actual_entries": 0,
                }
            )

        changed = candidate != text
        if parsed.valid and changed:
            findings.append(
                {
                    "severity": "error" if not write else "info",
                    "classification": "catalog-sync",
                    "state": "drifted",
                    "path": label,
                    "message": "managed catalog block is out of sync",
                    "expected_entries": len(entries),
                    "actual_entries": actual_entries,
                }
            )

        if owner_findings:
            state = "catalog-owner-mismatch"
        elif label in metadata_indexes:
            state = "metadata-preventing-safe-rendering"
        plans.append(
            {
                "path": index,
                "label": label,
                "state": state,
                "changed": changed,
                "original": raw,
                "candidate": candidate.encode("utf-8"),
                "expected_entries": len(entries),
                "actual_entries": actual_entries,
            }
        )

    changed: List[str] = []
    if write and not _finding_has_error(findings):
        updates = {
            plan["path"]: plan["candidate"]
            for plan in plans
            if plan.get("changed") and plan.get("candidate") is not None
        }
        originals = {
            plan["path"]: plan["original"]
            for plan in plans
            if plan.get("changed") and plan.get("original") is not None
        }
        if updates:
            success, write_findings, replaced = _atomic_replace(updates, originals, vault)
            findings.extend(write_findings)
            if success:
                changed = [
                    relative_label(path, vault)
                    for path in sorted(updates, key=lambda item: item.as_posix())
                ]
            elif replaced and any(
                item.get("classification") == "catalog-rollback"
                for item in write_findings
            ):
                # A failed rollback means the final filesystem state is
                # necessarily uncertain; report the touched paths rather than
                # claiming a clean all-or-nothing result. A successful bounded
                # rollback leaves changed empty.
                changed = [relative_label(path, vault) for path in replaced]

    states = [str(plan["state"]) for plan in plans]
    states.extend(
        str(finding["state"])
        for finding in findings
        if finding.get("state") in {
            "invalid-marker-structure",
            "catalog-owner-mismatch",
            "metadata-preventing-safe-rendering",
            "write-failed",
            "rollback-failed",
            "temporary-cleanup-failed",
            "missing-catalog-block",
            "drifted",
            "utf8-error",
        }
    )
    ordered_states = _state_priority(states)
    has_error = _finding_has_error(findings)
    if has_error:
        status = ordered_states[0] if ordered_states else "error"
    elif write:
        status = "synchronized"
    else:
        status = ordered_states[0] if ordered_states else "synchronized"

    index_states = [
        {
            "path": plan["label"],
            "status": plan["state"],
            "changed": bool(plan.get("changed")),
            "expected_entries": plan.get("expected_entries", 0),
            "actual_entries": plan.get("actual_entries", 0),
        }
        for plan in plans
    ]
    findings.sort(
        key=lambda finding: (
            str(finding.get("path", "")),
            str(finding.get("classification", "")),
            str(finding.get("message", "")),
        )
    )
    return {
        "vault": str(vault.resolve()),
        "status": status,
        "states": ordered_states,
        "changed": changed,
        "indexes": [relative_label(path, vault) for path in indexes],
        "index_states": index_states,
        "findings": findings,
        "write": write,
    }


def _print_text(result: Dict[str, Any]) -> None:
    for finding in result.get("findings", []):
        severity = str(finding.get("severity", "info")).upper()
        path = finding.get("path", "")
        state = finding.get("state")
        message = finding.get("message", "")
        detail = f"{state}: {message}" if state else str(message)
        print(f"{severity}: {path}: {detail}" if path else f"{severity}: {detail}")
    status = result.get("status", "synchronized")
    changed = result.get("changed", [])
    if changed:
        print("Synchronized catalogs: " + ", ".join(changed))
    elif status == "synchronized":
        print("SelfContext index catalogs: synchronized")
    else:
        print("SelfContext index catalogs: " + str(status))


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
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        _print_text(result)
    return 1 if _finding_has_error(result.get("findings", [])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
