#!/usr/bin/env python3
"""Plan and transactionally apply supported SelfContext schema migrations."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import backup_vault
    import lint_vault
    import sync_indexes
    from vault_utils import (
        canonical_files,
        catalog_records,
        infer_enabled_contracts,
        iter_markdown_links,
        link_target,
        load_vertical_catalog,
        parse_schema,
        relative_label,
        safe_read_bytes,
        safe_read_text,
        snapshot_id,
        validate_vertical_catalog,
    )
except ImportError:  # pragma: no cover - useful when imported as a package
    from . import backup_vault, lint_vault, sync_indexes  # type: ignore
    from .vault_utils import (  # type: ignore
        canonical_files,
        catalog_records,
        infer_enabled_contracts,
        iter_markdown_links,
        link_target,
        load_vertical_catalog,
        parse_schema,
        relative_label,
        safe_read_bytes,
        safe_read_text,
        snapshot_id,
        validate_vertical_catalog,
    )


SCHEMA_LINE = re.compile(
    r"^([ \t]*schema_version:[ \t]*)0\.1([ \t]*)$", re.MULTILINE
)
SCHEMA_SECTION_LINE = re.compile(
    r"^[ \t]*vertical_contracts:[^\r\n]*$", re.MULTILINE
)
MIGRATION_OPERATION = "migrate_schema_0_1_to_0_2"
LATEST_SUPPORTED_SCHEMA = "0.2"
ROOT_CONTROL_FILES = {"SCHEMA.md", "index.md", "log.md"}
NON_CANONICAL_ROOTS = {".obsidian", "backups", ".DS_Store"}
SCHEMA_VERSION_LINE = re.compile(
    r"^[ \t]*schema_version:[ \t]*([^\s#]+)[ \t]*(?:#.*)?$", re.MULTILINE
)


class MigrationRegistryError(ValueError):
    """A migration registry cannot safely resolve the requested path."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MigrationEdge:
    """One deterministic schema transition in a migration graph.

    ``planner`` is read-only and must return a staged proposed state using the
    same private byte-set keys as the built-in planner.  The optional validators
    let unit tests model future, not-yet-supported edges without declaring a
    production schema version or weakening the production validator.
    """

    def __init__(
        self,
        source: Any,
        target: Any,
        planner: Callable[[Path], Dict[str, Any]],
        *,
        validator: Optional[Callable[[Path], Dict[str, Any]]] = None,
        active_validator: Optional[Callable[[Path, Mapping[str, Any]], Dict[str, Any]]] = None,
        name: Optional[str] = None,
    ) -> None:
        self.source = _schema_label(source)
        self.target = _schema_label(target)
        self.planner = planner
        self.validator = validator
        self.active_validator = active_validator
        self.name = name or f"{self.source}->{self.target}"

    @property
    def label(self) -> str:
        return f"{self.source}->{self.target}"


def _schema_label(value: Any) -> str:
    if isinstance(value, tuple) and len(value) == 2:
        return f"{int(value[0])}.{int(value[1])}"
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"invalid schema label: {value!r}")


def _numeric_schema_label(value: str) -> Optional[Tuple[int, int]]:
    match = re.fullmatch(r"(\d+)\.(\d+)", value)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _is_future_schema(value: str, latest: str) -> bool:
    current_number = _numeric_schema_label(value)
    latest_number = _numeric_schema_label(latest)
    return bool(current_number and latest_number and current_number > latest_number)


class MigrationRegistry:
    """Dependency-free directed graph for supported schema migrations."""

    def __init__(self, latest: Any, edges: Iterable[MigrationEdge]) -> None:
        self.latest = _schema_label(latest)
        self.edges = tuple(edges)

    @property
    def latest_supported_schema(self) -> str:
        return self.latest

    @property
    def supported_versions(self) -> List[str]:
        return sorted(
            {self.latest, *(edge.source for edge in self.edges), *(edge.target for edge in self.edges)},
            key=lambda value: (_numeric_schema_label(value) is None, _numeric_schema_label(value) or (0, 0), value),
        )

    def validation_findings(self) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        seen: Dict[Tuple[str, str], str] = {}
        adjacency: Dict[str, List[MigrationEdge]] = {}
        nodes = {self.latest}
        for edge in self.edges:
            nodes.update((edge.source, edge.target))
            key = (edge.source, edge.target)
            if key in seen:
                findings.append(
                    _finding(
                        "error",
                        "",
                        f"duplicate migration edge {edge.label} ({seen[key]} and {edge.name})",
                        "migration-registry",
                        code="duplicate-edge",
                    )
                )
            else:
                seen[key] = edge.name
            if edge.source == edge.target:
                findings.append(
                    _finding(
                        "error",
                        "",
                        f"migration edge cannot point to itself: {edge.label}",
                        "migration-registry",
                        code="cycle",
                    )
                )
            adjacency.setdefault(edge.source, []).append(edge)

        for source in adjacency:
            adjacency[source].sort(key=lambda edge: (edge.target, edge.name))

        visit_state: Dict[str, int] = {}
        cycle_keys: set[Tuple[str, str]] = set()

        def visit(node: str) -> None:
            visit_state[node] = 1
            for edge in adjacency.get(node, []):
                state = visit_state.get(edge.target, 0)
                if state == 1:
                    cycle = (node, edge.target)
                    if cycle not in cycle_keys:
                        cycle_keys.add(cycle)
                        findings.append(
                            _finding(
                                "error",
                                "",
                                f"cyclic migration graph includes {edge.label}",
                                "migration-registry",
                                code="cycle",
                            )
                        )
                elif state == 0:
                    visit(edge.target)
            visit_state[node] = 2

        for node in sorted(nodes):
            if visit_state.get(node, 0) == 0:
                visit(node)

        if self.latest not in nodes:
            findings.append(
                _finding(
                    "error",
                    "",
                    f"latest supported schema is not represented: {self.latest}",
                    "migration-registry",
                    code="missing-latest",
                )
            )
        return findings

    def validate(self) -> List[str]:
        """Return deterministic human-readable registry validation errors."""

        return [str(item["message"]) for item in self.validation_findings()]

    def resolve_path(self, source: Any, target: Any) -> List[MigrationEdge]:
        source_label = _schema_label(source)
        target_label = self.latest if _schema_label(target) == "latest" else _schema_label(target)
        findings = self.validation_findings()
        if findings:
            raise MigrationRegistryError("invalid-registry", "; ".join(self.validate()))
        if target_label not in self.supported_versions:
            raise MigrationRegistryError(
                "unsupported-target",
                f"unsupported migration target schema: {target_label}",
            )
        if _is_future_schema(source_label, self.latest):
            raise MigrationRegistryError(
                "future-schema",
                f"vault declares future unsupported schema: {source_label}",
            )
        if source_label not in self.supported_versions:
            raise MigrationRegistryError(
                "missing-path",
                f"no migration path starts at schema {source_label}",
            )
        if source_label == target_label:
            return []

        adjacency: Dict[str, List[MigrationEdge]] = {}
        for edge in self.edges:
            adjacency.setdefault(edge.source, []).append(edge)
        for source_edges in adjacency.values():
            source_edges.sort(key=lambda edge: (edge.target, edge.name))

        queue: List[Tuple[str, List[MigrationEdge]]] = [(source_label, [])]
        visited = {source_label}
        while queue:
            node, path = queue.pop(0)
            for edge in adjacency.get(node, []):
                candidate = path + [edge]
                if edge.target == target_label:
                    return candidate
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append((edge.target, candidate))
        raise MigrationRegistryError(
            "missing-path",
            f"no complete migration path from schema {source_label} to {target_label}",
        )


def default_migration_registry() -> MigrationRegistry:
    """Return the production registry; test-only registries stay injectable."""

    return MigrationRegistry(
        LATEST_SUPPORTED_SCHEMA,
        (MigrationEdge("0.1", "0.2", _plan_0_1_to_0_2, name="schema-0.1-to-0.2"),),
    )


def _finding(
    severity: str,
    path: str,
    message: str,
    classification: str = "migration",
    **extra: Any,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "severity": severity,
        "classification": classification,
        "path": path,
        "message": message,
    }
    result.update(extra)
    return result


def _contract_strings(contracts: Iterable[Mapping[str, Any]]) -> List[str]:
    return [f"{item.get('id')}@{item.get('version')}" for item in contracts]


def _newline_style(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _schema_with_contracts(text: str, contracts: Sequence[Mapping[str, Any]]) -> str:
    """Return schema text with only the version and contract section changed."""

    matches = list(SCHEMA_LINE.finditer(text))
    if len(matches) != 1:
        raise ValueError("SCHEMA.md must contain exactly one schema_version: 0.1")

    newline = _newline_style(text)
    updated = SCHEMA_LINE.sub(
        lambda match: f"{match.group(1)}0.2{match.group(2)}", text, count=1
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
            if re.match(r"^[ \t]*schema_version:[ \t]*0\.2", line)
        )
        lines[version_index + 1 : version_index + 1] = block

    result = "".join(lines)
    if not text.endswith(("\n", "\r")) and result.endswith(newline):
        result = result[: -len(newline)]
    return result


def _root_has_link(vault: Path, index_path: str, text: Optional[str] = None) -> bool:
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


def _area_has_meaningful_content(vault: Path, area: str) -> bool:
    area_root = vault / area
    if not area_root.is_dir():
        return False
    for path in canonical_files(vault):
        try:
            relative = path.relative_to(vault).as_posix()
        except ValueError:
            continue
        if not relative.startswith(f"{area}/") or relative == f"{area}/index.md":
            continue
        content, error = safe_read_bytes(path)
        if error is None and content and content.strip():
            return True
    return False


def _compact_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _looks_like_vertical_area(name: str, record: Mapping[str, Any]) -> bool:
    compact = _compact_name(name)
    identifier = _compact_name(str(record.get("id", "")))
    display = _compact_name(str(record.get("display_name", "")))
    if not compact or compact in {identifier, display}:
        return False
    return bool(
        identifier
        and (
            compact.startswith(identifier)
            or compact.endswith(identifier)
            or identifier in compact
        )
    )


def _vertical_analysis(
    vault: Path, schema: Mapping[str, Any], catalog: Mapping[str, Any]
) -> Dict[str, Any]:
    records = catalog_records(dict(catalog))
    by_id = {
        str(record.get("id")): record
        for record in records
        if isinstance(record, dict) and record.get("id") is not None
    }
    explicit = {str(item) for item in schema.get("legacy_enabled_verticals", [])}
    try:
        _, inference_source = infer_enabled_contracts(vault, dict(catalog))
    except (OSError, ValueError, KeyError):
        inference_source = "inferred-legacy"

    enabled: List[Dict[str, Any]] = []
    ambiguous: List[Dict[str, Any]] = []
    human_decisions: List[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        identifier = str(record.get("id"))
        area = record.get("vault_area")
        index = record.get("index_path")
        if not isinstance(area, str) or not isinstance(index, str):
            ambiguous.append(
                _finding(
                    "warning",
                    "SCHEMA.md",
                    f"vertical catalog record for {identifier} has unsafe area or index metadata",
                    "ambiguous-vertical",
                )
            )
            human_decisions.append(
                f"Resolve the catalog area/index for {identifier} before migration."
            )
            continue

        area_path = vault / area
        index_path = vault / index
        signals = {
            "explicit_legacy_marker": identifier in explicit,
            "existing_area": area_path.is_dir(),
            "existing_index": index_path.is_file(),
            "root_index_link": _root_has_link(vault, index),
            "meaningful_existing_content": _area_has_meaningful_content(vault, area),
        }
        if any(signals.values()):
            # The exact catalog area is itself legacy structural evidence. An
            # empty area is still safe to preserve and complete with control
            # metadata; content is an additional conservative signal, not a
            # requirement for recognizing the canonical area.
            enabled.append(
                {
                    "id": identifier,
                    "version": record.get("contract_version"),
                    "record": record,
                    "signals": signals,
                }
            )
        elif area_path.exists():
            ambiguous.append(
                _finding(
                    "warning",
                    f"{area}/",
                    "known vertical path is not a directory; preserved and not enabled",
                    "ambiguous-vertical",
                )
            )
            human_decisions.append(
                f"Resolve the non-directory {area} path before enabling {identifier}."
            )

    for identifier in sorted(explicit - set(by_id)):
        ambiguous.append(
            _finding(
                "warning",
                "SCHEMA.md",
                f"legacy enabled vertical is unavailable in the current catalog: {identifier}; preserved without a contract",
                "ambiguous-vertical",
            )
        )
        human_decisions.append(
            f"Resolve unavailable legacy vertical {identifier} before enabling it."
        )

    known_areas = {
        str(record.get("vault_area"))
        for record in records
        if isinstance(record, dict) and record.get("vault_area")
    }
    custom: List[Dict[str, Any]] = []
    if vault.is_dir():
        for child in sorted(vault.iterdir(), key=lambda path: path.name):
            if not child.is_dir() or child.name in NON_CANONICAL_ROOTS:
                continue
            if child.name in {"core", "review", "sources", "derived"}:
                continue
            if child.name in known_areas:
                continue
            matching = next(
                (
                    record
                    for record in records
                    if isinstance(record, dict)
                    and _looks_like_vertical_area(child.name, record)
                ),
                None,
            )
            if matching is not None:
                ambiguous.append(
                    _finding(
                        "warning",
                        child.name + "/",
                        "ambiguous known-looking area preserved and not declared as a known vertical",
                        "ambiguous-vertical",
                    )
                )
                human_decisions.append(
                    f"Resolve whether custom area {child.name}/ belongs to {matching.get('id')}; migration will not move it."
                )
            else:
                custom.append(
                    _finding(
                        "info",
                        child.name + "/",
                        "custom area preserved and excluded from vertical contracts and managed catalogs",
                        "custom-area",
                    )
                )

    return {
        "enabled": enabled,
        "inference_source": inference_source,
        "ambiguous": ambiguous,
        "custom": custom,
        "human_decisions": human_decisions,
    }


def _index_template(record: Mapping[str, Any]) -> str:
    display_name = str(record.get("display_name") or record.get("vault_area"))
    ownership = str(record.get("ownership") or f"{display_name} context.")
    start = getattr(sync_indexes, "CATALOG_START", "<!-- selfcontext:catalog:start -->")
    end = getattr(sync_indexes, "CATALOG_END", "<!-- selfcontext:catalog:end -->")
    return f"# {display_name} Context\n\n{ownership}\n\n{start}\n{end}\n"


def _root_with_links(
    vault: Path,
    contracts: Sequence[Mapping[str, Any]],
    catalog: Mapping[str, Any],
    text: str,
) -> Tuple[str, List[str]]:
    records = {
        str(record.get("id")): record
        for record in catalog_records(dict(catalog))
        if isinstance(record, dict)
    }
    additions: List[str] = []
    for contract in contracts:
        record = records.get(str(contract.get("id")))
        if record is None:
            continue
        index_path = record.get("index_path")
        if not isinstance(index_path, str) or _root_has_link(vault, index_path, text):
            continue
        additions.append(f"- [{record.get('display_name', record.get('id'))} context]({index_path})")
    if not additions:
        return text, []
    newline = _newline_style(text)
    separator = "" if text.endswith(("\n", "\r")) else newline
    return text + separator + newline.join(additions) + newline, [
        str(records[str(contract.get("id"))].get("index_path"))
        for contract in contracts
        if str(contract.get("id")) in records
        and str(records[str(contract.get("id"))].get("index_path"))
        in {
            line.split("](", 1)[1].rstrip(")")
            for line in additions
            if "](" in line
        }
    ]


def _append_log_entry(
    text: str, changed_paths: Sequence[str]
) -> Tuple[str, bool]:
    marker = f"- operation: {MIGRATION_OPERATION}"
    if marker in text:
        return text, False
    newline = _newline_style(text)
    separator = "" if text.endswith(("\n", "\r")) else newline
    lines = [
        f"{separator}{newline}## {dt.date.today().isoformat()} - schema migration{newline}",
        newline,
        f"- operation: {MIGRATION_OPERATION}{newline}",
        f"- summary: Migrated schema 0.1 to 0.2 using control metadata only.{newline}",
        f"- changed:{newline}",
    ]
    for path in sorted(set(changed_paths)):
        lines.append(f"  - [{path}]({path}){newline}")
    lines.extend(
        [
            f"- preserved: Personal pages and custom areas were preserved.{newline}",
            f"- follow_up: Review any reported ambiguous areas before assigning ownership.{newline}",
        ]
    )
    return text + "".join(lines), True


def _canonical_bytes(root: Path) -> Dict[str, bytes]:
    result: Dict[str, bytes] = {}
    for path in canonical_files(root):
        content, error = safe_read_bytes(path)
        if content is None:
            raise OSError(error or f"unable to read {path}")
        result[relative_label(path, root)] = content
    return result


def _known_areas(catalog: Mapping[str, Any]) -> set[str]:
    return {
        "core",
        "review",
        "sources",
        "derived",
        *{
            str(record.get("vault_area"))
            for record in catalog_records(dict(catalog))
            if isinstance(record, dict) and record.get("vault_area")
        },
    }


def _is_managed_control(label: str, catalog: Mapping[str, Any]) -> bool:
    if label in ROOT_CONTROL_FILES:
        return True
    parts = Path(label).parts
    return bool(parts) and parts[-1] == "index.md" and parts[0] in _known_areas(catalog)


def _diff_bytes(
    original: Mapping[str, bytes], proposed: Mapping[str, bytes]
) -> Tuple[List[str], List[str], List[str]]:
    created = sorted(set(proposed) - set(original))
    deleted = sorted(set(original) - set(proposed))
    modified = sorted(
        label
        for label in set(original).intersection(proposed)
        if original[label] != proposed[label]
    )
    return created, modified, deleted


def _custom_area_names(root: Path, catalog: Mapping[str, Any]) -> List[str]:
    known = _known_areas(catalog)
    if not root.is_dir():
        return []
    return sorted(
        child.name
        for child in root.iterdir()
        if child.is_dir()
        and child.name not in known
        and child.name not in NON_CANONICAL_ROOTS
    )


def _preservation_report(
    source: Mapping[str, bytes],
    current: Mapping[str, bytes],
    catalog: Mapping[str, Any],
    source_root: Path,
    current_root: Path,
) -> Dict[str, Any]:
    labels = sorted(set(source).union(current))
    personal_changed = [
        label
        for label in labels
        if not _is_managed_control(label, catalog) and source.get(label) != current.get(label)
    ]
    source_custom = _custom_area_names(source_root, catalog)
    current_custom = _custom_area_names(current_root, catalog)
    return {
        "ok": not personal_changed and source_custom == current_custom,
        "personal_files_changed": personal_changed,
        "custom_areas_before": source_custom,
        "custom_areas_after": current_custom,
        "custom_areas_preserved": source_custom == current_custom,
    }


def _schema_contract_validation(root: Path) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    try:
        schema = parse_schema(root)
        catalog = load_vertical_catalog()
    except (OSError, ValueError, KeyError) as error:
        return {
            "ok": False,
            "errors": [{"path": "SCHEMA.md", "message": str(error)}],
            "contracts": [],
        }

    for problem in validate_vertical_catalog():
        errors.append({"path": "references/verticals.json", "message": problem})
    if schema.get("error"):
        errors.append({"path": "SCHEMA.md", "message": str(schema["error"])})
    if schema.get("version") != (0, 2):
        errors.append({"path": "SCHEMA.md", "message": "resulting schema is not 0.2"})
    if not schema.get("contract_section_present"):
        errors.append({"path": "SCHEMA.md", "message": "schema 0.2 must declare vertical_contracts"})
    for problem in schema.get("contract_errors", []):
        errors.append({"path": "SCHEMA.md", "message": str(problem)})

    records = {
        str(record.get("id")): record
        for record in catalog_records(catalog)
        if isinstance(record, dict) and record.get("id") is not None
    }
    seen: set[str] = set()
    root_text, root_error = safe_read_text(root / "index.md")
    if root_error or root_text is None:
        errors.append({"path": "index.md", "message": root_error or "missing root index"})
        root_text = ""

    entries = schema.get("contract_entries", [])
    for entry in entries:
        identifier = entry.get("id")
        version = entry.get("version")
        raw = str(entry.get("raw") or f"{identifier}@{version}")
        if not isinstance(identifier, str) or not isinstance(version, int):
            continue
        if identifier in seen:
            errors.append({"path": "SCHEMA.md", "message": f"duplicate applied vertical contract: {raw}"})
        seen.add(identifier)
        record = records.get(identifier)
        if record is None:
            errors.append({"path": "SCHEMA.md", "message": f"applied vertical is not available: {raw}"})
            continue
        available = record.get("contract_version")
        if version != available:
            errors.append(
                {
                    "path": "SCHEMA.md",
                    "message": f"migration contract must use exact available version: {raw} (available {identifier}@{available})",
                }
            )
        area = record.get("vault_area")
        index = record.get("index_path")
        if not isinstance(area, str) or not (root / area).is_dir():
            errors.append({"path": f"{area or identifier}/", "message": "enabled vertical is missing its area"})
        if not isinstance(index, str) or not (root / index).is_file():
            errors.append({"path": str(index or identifier), "message": "enabled vertical is missing its index"})
        elif not _root_has_link(root, index, root_text):
            errors.append({"path": "index.md", "message": f"enabled vertical is missing its root index link: {index}"})

    for record in records.values():
        area = record.get("vault_area")
        if isinstance(area, str) and (root / area).is_dir() and str(record.get("id")) not in seen:
            errors.append(
                {
                    "path": "SCHEMA.md",
                    "message": f"known vertical area is present but not versioned: {area}/",
                }
            )

    return {
        "ok": not errors,
        "errors": errors,
        "contracts": _contract_strings(entries),
        "enabled_verticals": sorted(seen),
    }


def _validation_summary(root: Path) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    try:
        ordinary_errors, ordinary_warnings = lint_vault.lint_vault(root, dt.date.today())
        ordinary = {
            "ok": not ordinary_errors,
            "errors": list(ordinary_errors),
            "warnings": list(ordinary_warnings),
        }
    except Exception as error:  # pragma: no cover - defensive safety boundary
        ordinary = {"ok": False, "errors": [str(error)], "warnings": []}

    try:
        deep_report = lint_vault.deep_lint_vault(root, dt.date.today())
        deep_errors = [
            {
                "path": str(item.get("path", "")),
                "message": str(item.get("message", "")),
                "classification": str(item.get("classification", "deep-lint")),
            }
            for item in deep_report.get("findings", [])
            if item.get("severity") == "error"
        ]
        deep = {
            "ok": not deep_errors,
            "schema_version": deep_report.get("schema_version"),
            "snapshot_id": deep_report.get("snapshot_id"),
            "severity_counts": deep_report.get("severity_counts", {}),
            "errors": deep_errors,
        }
    except Exception as error:  # pragma: no cover - defensive safety boundary
        deep = {"ok": False, "errors": [{"path": "", "message": str(error)}]}

    try:
        sync = sync_indexes.synchronize(root, write=False)
        sync_errors = [
            {
                "path": str(item.get("path", "")),
                "message": str(item.get("message", "")),
                "classification": str(item.get("classification", "catalog")),
            }
            for item in sync.get("findings", [])
            if item.get("severity") == "error"
        ]
        catalog = {
            "ok": not sync_errors,
            "status": sync.get("status"),
            "changed": sync.get("changed", []),
            "errors": sync_errors,
        }
    except Exception as error:  # pragma: no cover - defensive safety boundary
        catalog = {"ok": False, "errors": [{"path": "", "message": str(error)}]}

    try:
        schema = _schema_contract_validation(root)
    except Exception as error:  # pragma: no cover - defensive safety boundary
        schema = {"ok": False, "errors": [{"path": "SCHEMA.md", "message": str(error)}]}
    errors.extend(
        {"path": "", "message": message}
        for message in ordinary.get("errors", [])
    )
    for section in (deep, catalog, schema):
        errors.extend(section.get("errors", []))
    return {
        "ok": bool(ordinary.get("ok"))
        and bool(deep.get("ok"))
        and bool(catalog.get("ok"))
        and bool(schema.get("ok")),
        "errors": errors,
        "ordinary": ordinary,
        "deep": deep,
        "catalog_sync": catalog,
        "schema_contract": schema,
    }


def _validate_proposed_state(root: Path) -> Dict[str, Any]:
    """Validate the staged bytes before the active vault can be touched."""

    return _validation_summary(root)


def _validate_active_state(root: Path, plan: Mapping[str, Any]) -> Dict[str, Any]:
    result = _validation_summary(root)
    source = plan.get("_source_bytes", {})
    try:
        current = _canonical_bytes(root)
        catalog = load_vertical_catalog()
        preservation = _preservation_report(
            source,
            current,
            catalog,
            Path(str(plan.get("_vault_path", root))),
            root,
        )
    except Exception as error:  # pragma: no cover - defensive safety boundary
        preservation = {
            "ok": False,
            "personal_files_changed": [],
            "custom_areas_preserved": False,
            "error": str(error),
        }
    result["preservation"] = preservation
    result["ok"] = bool(result.get("ok")) and bool(preservation.get("ok"))
    if not preservation.get("ok"):
        result.setdefault("errors", []).append(
            {
                "path": "",
                "message": "personal or custom content changed during migration",
            }
        )
    return result


def _stage_write(stage: Path, label: str, content: bytes) -> None:
    path = stage / label
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _plan_0_1_to_0_2(vault: Path) -> Dict[str, Any]:
    supplied = vault.expanduser()
    resolved_label = str(supplied.resolve()) if supplied.exists() else str(supplied)
    plan: Dict[str, Any] = {
        "vault": resolved_label,
        "_vault_path": str(supplied),
        "from_schema": None,
        "to_schema": None,
        "source_schema_version": None,
        "target_schema_version": "0.2",
        "source_schema": None,
        "target_schema": "0.2",
        "source_snapshot_id": "",
        "source_snapshot": "",
        "snapshot_id": "",
        "inference": None,
        "inferred_enabled_verticals": [],
        "inferred_verticals": [],
        "enabled_vertical_contracts": [],
        "ambiguous_vertical_findings": [],
        "ambiguous_findings": [],
        "custom_area_findings": [],
        "custom_findings": [],
        "schema_changes": [],
        "missing_vertical_indexes": [],
        "missing_indexes_to_create": [],
        "root_index_links_to_add": [],
        "root_links_to_add": [],
        "catalog_blocks_to_add_or_synchronize": [],
        "catalog_blocks": [],
        "catalog_block_changes": [],
        "files_to_modify": [],
        "files_modified": [],
        "files_to_create": [],
        "files_created": [],
        "files_intentionally_preserved": [],
        "files_preserved": [],
        "personal_pages_preserved": [],
        "custom_areas_preserved": [],
        "warnings": [],
        "human_decisions": [],
        "findings": [],
        "would_change": [],
        "modified": [],
        "created": [],
        "status": "blocked",
        "write_ready": False,
    }

    if supplied.is_symlink():
        plan["findings"].append(
            _finding("error", str(supplied), "vault path must not be a symlink", "vault")
        )
        return plan
    if not supplied.exists() or not supplied.is_dir():
        plan["findings"].append(
            _finding("error", str(supplied), "vault path must be an existing directory", "vault")
        )
        return plan

    try:
        source_snapshot = snapshot_id(supplied)
        source_bytes = _canonical_bytes(supplied)
    except (OSError, ValueError, RuntimeError) as error:
        plan["findings"].append(
            _finding("error", "", f"unable to snapshot source vault: {error}", "snapshot")
        )
        return plan
    plan["source_snapshot_id"] = source_snapshot
    plan["source_snapshot"] = source_snapshot
    plan["snapshot_id"] = source_snapshot
    plan["_source_bytes"] = source_bytes

    schema = parse_schema(supplied)
    plan["from_schema"] = schema.get("version_text")
    plan["source_schema_version"] = schema.get("version_text")
    plan["source_schema"] = schema.get("version_text")
    plan["to_schema"] = "0.2" if schema.get("version") == (0, 1) else schema.get("version_text")
    if schema.get("error"):
        plan["findings"].append(
            _finding("error", "SCHEMA.md", str(schema["error"]), "schema")
        )
    if schema.get("version") == (0, 2):
        plan["status"] = "already-migrated"
        plan["findings"].append(
            _finding(
                "info",
                "SCHEMA.md",
                "vault already uses schema 0.2; migration is a no-op",
                "already-migrated",
            )
        )
        return plan
    if schema.get("version") != (0, 1):
        plan["findings"].append(
            _finding(
                "error",
                "SCHEMA.md",
                "only schema 0.1 can be migrated explicitly",
                "schema",
            )
        )
        return plan

    try:
        catalog = load_vertical_catalog()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        plan["findings"].append(
            _finding("error", "references/verticals.json", f"unable to load vertical catalog: {error}", "vertical-catalog")
        )
        return plan

    catalog_problems = validate_vertical_catalog()
    for problem in catalog_problems:
        plan["findings"].append(
            _finding("error", "references/verticals.json", problem, "vertical-catalog")
        )

    analysis = _vertical_analysis(supplied, schema, catalog)
    enabled = analysis["enabled"]
    plan["inference"] = analysis["inference_source"]
    plan["inferred_enabled_verticals"] = [item["id"] for item in enabled]
    plan["inferred_verticals"] = [
        {
            "id": item["id"],
            "version": item["version"],
            "signals": item["signals"],
        }
        for item in enabled
    ]
    plan["enabled_vertical_contracts"] = _contract_strings(enabled)
    plan["ambiguous_vertical_findings"] = analysis["ambiguous"]
    plan["ambiguous_findings"] = analysis["ambiguous"]
    plan["custom_area_findings"] = analysis["custom"]
    plan["custom_findings"] = analysis["custom"]
    plan["human_decisions"] = analysis["human_decisions"]
    plan["findings"].extend(analysis["ambiguous"])
    plan["findings"].extend(analysis["custom"])

    # Ambiguous known-looking or unavailable areas are never silently assigned
    # a contract. They remain untouched and require an explicit human decision.
    if analysis["ambiguous"]:
        for item in analysis["ambiguous"]:
            if item.get("classification") == "ambiguous-vertical":
                plan["findings"].append(
                    _finding(
                        "error",
                        str(item.get("path", "")),
                        "migration requires a human decision for this ambiguous area",
                        "migration-ambiguity",
                    )
                )

    root_text, root_error = safe_read_text(supplied / "index.md")
    schema_text, schema_error = safe_read_text(supplied / "SCHEMA.md")
    if root_error or root_text is None:
        plan["findings"].append(_finding("error", "index.md", root_error or "missing root index", "control-file"))
    if schema_error or schema_text is None:
        plan["findings"].append(_finding("error", "SCHEMA.md", schema_error or "missing schema", "control-file"))
    if not (supplied / "log.md").is_file():
        plan["findings"].append(_finding("error", "log.md", "missing required operation log", "control-file"))
    if any(item.get("severity") == "error" for item in plan["findings"]):
        plan["warnings"] = [item for item in plan["findings"] if item.get("severity") != "error"]
        return plan

    contracts = [
        {"id": item["id"], "version": int(item["version"])}
        for item in enabled
    ]
    try:
        schema_candidate = _schema_with_contracts(str(schema_text), contracts)
    except ValueError as error:
        plan["findings"].append(_finding("error", "SCHEMA.md", str(error), "schema"))
        return plan

    plan["schema_changes"] = [
        {
            "path": "SCHEMA.md",
            "from": "schema_version: 0.1 and legacy contract state",
            "to": "schema_version: 0.2 with exact enabled vertical@version entries",
            "contracts": _contract_strings(contracts),
        }
    ]

    with tempfile.TemporaryDirectory(prefix="selfcontext-migration-") as temporary:
        stage = Path(temporary) / "vault"
        try:
            shutil.copytree(supplied, stage, symlinks=True)
            _stage_write(stage, "SCHEMA.md", schema_candidate.encode("utf-8"))

            records = {
                str(record.get("id")): record
                for record in catalog_records(catalog)
                if isinstance(record, dict)
            }
            missing_indexes: List[str] = []
            for contract in contracts:
                record = records.get(str(contract["id"]))
                if record is None:
                    continue
                area = str(record.get("vault_area"))
                index = str(record.get("index_path"))
                area_path = stage / area
                index_path = stage / index
                if area_path.exists() and not area_path.is_dir():
                    plan["findings"].append(_finding("error", area + "/", "vertical area is not a directory", "vertical-contract"))
                    continue
                if index_path.exists() and not index_path.is_file():
                    plan["findings"].append(_finding("error", index, "vertical index path is not a file", "vertical-contract"))
                    continue
                if not index_path.is_file():
                    area_path.mkdir(parents=True, exist_ok=True)
                    _stage_write(stage, index, _index_template(record).encode("utf-8"))
                    missing_indexes.append(index)
            plan["missing_vertical_indexes"] = sorted(missing_indexes)
            plan["missing_indexes_to_create"] = list(plan["missing_vertical_indexes"])

            root_candidate, root_additions = _root_with_links(
                stage, contracts, catalog, str(root_text)
            )
            if root_candidate != root_text:
                _stage_write(stage, "index.md", root_candidate.encode("utf-8"))
            plan["root_index_links_to_add"] = sorted(root_additions)
            plan["root_links_to_add"] = list(plan["root_index_links_to_add"])

            sync_before = sync_indexes.synchronize(stage, write=False)
            sync_write = sync_indexes.synchronize(stage, write=True)
            sync_after = sync_indexes.synchronize(stage, write=False)
            plan["catalog_block_changes"] = [
                {
                    "path": str(item.get("path")),
                    "action": "add" if item.get("status") == "missing-catalog-block" else "synchronize",
                }
                for item in sync_write.get("index_states", [])
                if item.get("changed")
            ]
            plan["catalog_blocks_to_add_or_synchronize"] = [
                item["path"] for item in plan["catalog_block_changes"]
            ]
            plan["catalog_blocks"] = list(plan["catalog_blocks_to_add_or_synchronize"])

            before_log = _canonical_bytes(stage)
            log_text, log_error = safe_read_text(stage / "log.md")
            if log_error or log_text is None:
                plan["findings"].append(_finding("error", "log.md", log_error or "unable to read operation log", "control-file"))
            else:
                changed_for_log = [
                    label
                    for label in sorted(set(source_bytes).union(before_log))
                    if source_bytes.get(label) != before_log.get(label)
                ]
                log_candidate, log_added = _append_log_entry(log_text, changed_for_log)
                if log_added:
                    _stage_write(stage, "log.md", log_candidate.encode("utf-8"))
                    plan["log_entry"] = "planned"
                else:
                    plan["log_entry"] = "existing-preserved"

            proposed_bytes = _canonical_bytes(stage)
            created, modified, deleted = _diff_bytes(source_bytes, proposed_bytes)
            plan["created"] = created
            plan["modified"] = modified
            plan["files_to_create"] = created
            plan["files_created"] = list(created)
            plan["files_to_modify"] = modified
            plan["files_modified"] = list(modified)
            plan["would_change"] = sorted(set(created + modified))

            for label in deleted:
                plan["findings"].append(_finding("error", label, "migration would delete an existing file", "preservation"))
            for label in sorted(set(created + modified)):
                if not _is_managed_control(label, catalog):
                    plan["findings"].append(_finding("error", label, "migration would modify personal or custom content", "preservation"))

            preservation = _preservation_report(
                source_bytes, proposed_bytes, catalog, supplied, stage
            )
            if not preservation["ok"]:
                plan["findings"].append(_finding("error", "", "proposed migration does not preserve personal or custom content", "preservation"))

            validation = _validate_proposed_state(stage)
            plan["proposed_validation"] = validation
            plan["proposed_snapshot_id"] = str(
                validation.get("deep", {}).get("snapshot_id", "")
            )
            if not validation.get("ok"):
                for item in validation.get("errors", []):
                    plan["findings"].append(
                        _finding(
                            "error",
                            str(item.get("path", "")),
                            str(item.get("message", "proposed-state validation failed")),
                            "proposed-validation",
                        )
                    )

            # A plan is only predictive if the source remained unchanged while
            # the staging state was constructed.
            current_snapshot = snapshot_id(supplied)
            if current_snapshot != source_snapshot:
                plan["findings"].append(
                    _finding(
                        "error",
                        "",
                        "source vault changed while migration plan was being built; re-plan required",
                        "snapshot-drift",
                        planned_snapshot=source_snapshot,
                        current_snapshot=current_snapshot,
                    )
                )

            plan["_planned_updates"] = {
                label: proposed_bytes[label] for label in sorted(set(created + modified))
            }
            plan["_proposed_bytes"] = proposed_bytes
            plan["_stage_sync"] = {
                "before": sync_before,
                "write": sync_write,
                "after": sync_after,
            }
        except Exception as error:  # pragma: no cover - active writes remain blocked
            plan["findings"].append(
                _finding("error", "", f"could not construct proposed migration state: {error}", "proposed-state")
            )

    plan["files_intentionally_preserved"] = sorted(
        label
        for label in source_bytes
        if label not in set(plan.get("modified", []))
        and label not in set(plan.get("created", []))
    )
    plan["files_preserved"] = list(plan["files_intentionally_preserved"])
    plan["personal_pages_preserved"] = [
        label
        for label in plan["files_intentionally_preserved"]
        if not _is_managed_control(label, catalog)
    ]
    plan["custom_areas_preserved"] = _custom_area_names(supplied, catalog)
    plan["warnings"] = [
        item for item in plan["findings"] if item.get("severity") in {"warning", "info"}
    ]
    errors = [item for item in plan["findings"] if item.get("severity") == "error"]
    plan["write_ready"] = not errors and bool(plan.get("proposed_validation", {}).get("ok"))
    plan["status"] = "planned" if plan["write_ready"] else "blocked"
    return plan


def _empty_registry_plan(
    vault: Path, target: Any, registry: MigrationRegistry
) -> Dict[str, Any]:
    supplied = vault.expanduser()
    target_text = str(target if target is not None else "latest")
    resolved_target = registry.latest_supported_schema if target_text == "latest" else target_text
    return {
        "vault": str(supplied.resolve()) if supplied.exists() else str(supplied),
        "_vault_path": str(supplied),
        "from_schema": None,
        "to_schema": None,
        "current_schema": None,
        "source_schema_version": None,
        "source_schema": None,
        "target_schema_version": resolved_target,
        "target_schema": resolved_target,
        "requested_target": target_text,
        "latest_supported_schema": registry.latest_supported_schema,
        "supported_target_schemas": registry.supported_versions,
        "migration_path": [],
        "migration_edges": [],
        "source_snapshot_id": "",
        "source_snapshot": "",
        "snapshot_id": "",
        "proposed_snapshot_id": "",
        "proposed_final_snapshot_id": "",
        "proposed_final_snapshot": "",
        "inference": None,
        "inferred_enabled_verticals": [],
        "inferred_verticals": [],
        "enabled_vertical_contracts": [],
        "ambiguous_vertical_findings": [],
        "ambiguous_findings": [],
        "custom_area_findings": [],
        "custom_findings": [],
        "schema_changes": [],
        "missing_vertical_indexes": [],
        "missing_indexes_to_create": [],
        "root_index_links_to_add": [],
        "root_links_to_add": [],
        "catalog_blocks_to_add_or_synchronize": [],
        "catalog_blocks": [],
        "catalog_block_changes": [],
        "files_to_modify": [],
        "files_modified": [],
        "files_to_create": [],
        "files_created": [],
        "files_intentionally_preserved": [],
        "files_preserved": [],
        "personal_pages_preserved": [],
        "custom_areas_preserved": [],
        "warnings": [],
        "human_decisions": [],
        "findings": [],
        "blocking_findings": [],
        "would_change": [],
        "modified": [],
        "created": [],
        "migration_needed": False,
        "already_current": False,
        "registry_valid": False,
        "plan_valid": False,
        "status": "blocked",
        "write_ready": False,
    }


def _blocking_findings(result: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    return [
        item
        for item in result.get("findings", [])
        if isinstance(item, Mapping) and item.get("severity") == "error"
    ]


def _set_plan_summary(
    plan: Dict[str, Any],
    source: str,
    target: str,
    path: Sequence[MigrationEdge],
    registry: MigrationRegistry,
) -> Dict[str, Any]:
    path_labels = [source]
    path_labels.extend(edge.target for edge in path)
    plan["current_schema"] = source
    plan["from_schema"] = source
    plan["to_schema"] = target
    plan["source_schema_version"] = source
    plan["source_schema"] = source
    plan["target_schema"] = target
    plan["target_schema_version"] = target
    plan["migration_path"] = path_labels
    plan["migration_edges"] = [
        {"source": edge.source, "target": edge.target, "label": edge.label, "name": edge.name}
        for edge in path
    ]
    plan["latest_supported_schema"] = registry.latest_supported_schema
    plan["supported_target_schemas"] = registry.supported_versions
    plan["migration_needed"] = bool(path)
    plan["already_current"] = not path
    plan["blocking_findings"] = list(_blocking_findings(plan))
    plan["plan_valid"] = not plan["blocking_findings"] and (
        not path or bool(plan.get("proposed_validation", {}).get("ok"))
    )
    return plan


def _mark_blocked(plan: Dict[str, Any]) -> Dict[str, Any]:
    plan["blocking_findings"] = list(_blocking_findings(plan))
    plan["warnings"] = [
        item for item in plan.get("findings", [])
        if isinstance(item, Mapping) and item.get("severity") in {"warning", "info"}
    ]
    plan["write_ready"] = False
    plan["plan_valid"] = False
    plan["status"] = "blocked"
    return plan


def _no_op_plan(
    plan: Dict[str, Any],
    source: str,
    target: str,
    registry: MigrationRegistry,
    source_bytes: Mapping[str, bytes],
    vault: Path,
) -> Dict[str, Any]:
    _set_plan_summary(plan, source, target, [], registry)
    plan["already_current"] = True
    plan["migration_needed"] = False
    plan["plan_valid"] = True
    plan["status"] = "already-migrated"
    plan["write_ready"] = False
    plan["findings"].append(
        _finding(
            "info",
            "SCHEMA.md",
            f"vault already uses schema {target}; migration is a no-op",
            "already-current",
        )
    )
    plan["files_intentionally_preserved"] = sorted(source_bytes)
    plan["files_preserved"] = list(plan["files_intentionally_preserved"])
    try:
        catalog = load_vertical_catalog()
        plan["custom_areas_preserved"] = _custom_area_names(vault, catalog)
        plan["personal_pages_preserved"] = [
            label for label in source_bytes if not _is_managed_control(label, catalog)
        ]
    except Exception:
        # No-op reporting must not turn a valid read-only assessment into a
        # write or a second failure when the optional catalog is unavailable.
        pass
    plan["blocking_findings"] = []
    plan["warnings"] = list(plan["findings"])
    return plan


def _stage_apply_proposed_bytes(stage: Path, proposed: Mapping[str, bytes]) -> None:
    current = _canonical_bytes(stage)
    created, modified, deleted = _diff_bytes(current, proposed)
    if deleted:
        raise ValueError("migration edge would delete staged files: " + ", ".join(deleted))
    for label in sorted(set(created + modified)):
        path = stage / label
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise OSError(f"staged migration target is not a regular file: {path}")
        _stage_write(stage, label, proposed[label])


def _edge_proposed_bytes(stage: Path, result: Mapping[str, Any]) -> Dict[str, bytes]:
    proposed = result.get("_proposed_bytes")
    if isinstance(proposed, Mapping):
        return {str(label): bytes(content) for label, content in proposed.items()}
    updates = result.get("_planned_updates")
    if not isinstance(updates, Mapping):
        raise ValueError("migration edge did not return a complete proposed byte set")
    proposed_bytes = _canonical_bytes(stage)
    for label, content in updates.items():
        proposed_bytes[str(label)] = bytes(content)
    return proposed_bytes


def _chain_plan(
    vault: Path,
    plan: Dict[str, Any],
    source: str,
    target: str,
    path: Sequence[MigrationEdge],
    source_bytes: Mapping[str, bytes],
    registry: MigrationRegistry,
) -> Dict[str, Any]:
    edge_summaries: List[Dict[str, Any]] = []
    plan["_source_bytes"] = dict(source_bytes)
    plan["_vault_path"] = str(vault)
    findings: List[Dict[str, Any]] = list(plan.get("findings", []))
    final_validator: Optional[Callable[[Path], Dict[str, Any]]] = None
    active_validator: Optional[Callable[[Path, Mapping[str, Any]], Dict[str, Any]]] = None

    with tempfile.TemporaryDirectory(prefix="selfcontext-migration-chain-") as temporary:
        stage = Path(temporary) / "vault"
        try:
            shutil.copytree(vault, stage, symlinks=True)
            for edge in path:
                step = edge.planner(stage)
                if not isinstance(step, Mapping):
                    raise ValueError(f"migration edge {edge.label} returned no plan")
                step_findings = [
                    dict(item)
                    for item in step.get("findings", [])
                    if isinstance(item, Mapping)
                ]
                findings.extend(step_findings)
                for field in (
                    "inference",
                    "inferred_enabled_verticals",
                    "inferred_verticals",
                    "enabled_vertical_contracts",
                    "ambiguous_vertical_findings",
                    "ambiguous_findings",
                    "custom_area_findings",
                    "custom_findings",
                    "human_decisions",
                    "schema_changes",
                    "missing_vertical_indexes",
                    "missing_indexes_to_create",
                    "root_index_links_to_add",
                    "root_links_to_add",
                    "catalog_blocks_to_add_or_synchronize",
                    "catalog_blocks",
                    "catalog_block_changes",
                ):
                    if field in step:
                        plan[field] = step[field]
                edge_summaries.append(
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "label": edge.label,
                        "name": edge.name,
                        "status": step.get("status"),
                        "write_ready": bool(step.get("write_ready")),
                        "files_to_create": list(step.get("files_to_create", [])),
                        "files_to_modify": list(step.get("files_to_modify", [])),
                    }
                )
                if _blocking_findings(step) or not step.get("write_ready"):
                    if not _blocking_findings(step):
                        findings.append(
                            _finding(
                                "error",
                                "",
                                f"migration edge {edge.label} is not write-ready",
                                "migration-edge",
                            )
                        )
                    plan["findings"] = findings
                    plan["edge_plans"] = edge_summaries
                    return _mark_blocked(plan)
                _stage_apply_proposed_bytes(stage, _edge_proposed_bytes(stage, step))
                final_validator = edge.validator
                active_validator = edge.active_validator

            proposed_bytes = _canonical_bytes(stage)
            created, modified, deleted = _diff_bytes(source_bytes, proposed_bytes)
            for label in deleted:
                findings.append(
                    _finding("error", label, "migration would delete an existing file", "preservation")
                )

            catalog = load_vertical_catalog()
            for label in sorted(set(created + modified)):
                if not _is_managed_control(label, catalog):
                    findings.append(
                        _finding(
                            "error",
                            label,
                            "migration would modify personal or custom content",
                            "preservation",
                        )
                    )
            preservation = _preservation_report(
                source_bytes, proposed_bytes, catalog, vault, stage
            )
            if not preservation["ok"]:
                findings.append(
                    _finding(
                        "error",
                        "",
                        "proposed migration does not preserve personal or custom content",
                        "preservation",
                    )
                )

            validator = final_validator or _validate_proposed_state
            validation = validator(stage)
            plan["proposed_validation"] = validation
            if not validation.get("ok"):
                for item in validation.get("errors", []):
                    findings.append(
                        _finding(
                            "error",
                            str(item.get("path", "")),
                            str(item.get("message", "proposed-state validation failed")),
                            "proposed-validation",
                        )
                    )

            if snapshot_id(vault) != plan.get("source_snapshot_id"):
                findings.append(
                    _finding(
                        "error",
                        "",
                        "source vault changed while migration plan was being built; re-plan required",
                        "snapshot-drift",
                        planned_snapshot=plan.get("source_snapshot_id"),
                        current_snapshot=snapshot_id(vault),
                    )
                )

            final_snapshot = snapshot_id(stage)
            plan["proposed_snapshot_id"] = final_snapshot
            plan["proposed_final_snapshot_id"] = final_snapshot
            plan["proposed_final_snapshot"] = final_snapshot
            plan["_planned_updates"] = {
                label: proposed_bytes[label] for label in sorted(set(created + modified))
            }
            plan["_proposed_bytes"] = proposed_bytes
            plan["preservation"] = preservation
            plan["created"] = created
            plan["modified"] = modified
            plan["files_to_create"] = created
            plan["files_created"] = list(created)
            plan["files_to_modify"] = modified
            plan["files_modified"] = list(modified)
            plan["would_change"] = sorted(set(created + modified))
            plan["files_intentionally_preserved"] = sorted(
                label for label in source_bytes if label not in set(created + modified)
            )
            plan["files_preserved"] = list(plan["files_intentionally_preserved"])
            plan["personal_pages_preserved"] = [
                label
                for label in plan["files_intentionally_preserved"]
                if not _is_managed_control(label, catalog)
            ]
            plan["custom_areas_preserved"] = _custom_area_names(vault, catalog)
        except Exception as error:
            findings.append(
                _finding(
                    "error",
                    "",
                    f"could not construct proposed migration state: {error}",
                    "proposed-state",
                )
            )

    plan["findings"] = findings
    plan["edge_plans"] = edge_summaries
    plan["_active_validator"] = active_validator or _validate_active_state
    plan["warnings"] = [
        item for item in findings if item.get("severity") in {"warning", "info"}
    ]
    errors = [item for item in findings if item.get("severity") == "error"]
    plan["write_ready"] = not errors and bool(plan.get("proposed_validation", {}).get("ok"))
    plan["status"] = "planned" if plan["write_ready"] else "blocked"
    plan["plan_valid"] = plan["write_ready"]
    plan["blocking_findings"] = list(_blocking_findings(plan))
    _set_plan_summary(plan, source, target, path, registry)
    plan["plan_valid"] = plan["write_ready"]
    return plan


def plan_migration(
    vault: Path,
    target: Any = "latest",
    registry: Optional[MigrationRegistry] = None,
) -> Dict[str, Any]:
    """Build a complete read-only plan from the detected schema to ``target``."""

    supplied = vault.expanduser()
    migration_registry = registry or default_migration_registry()
    plan = _empty_registry_plan(supplied, target, migration_registry)
    registry_findings = migration_registry.validation_findings()
    plan["registry_validation"] = registry_findings
    plan["registry_valid"] = not registry_findings
    plan["findings"].extend(registry_findings)
    if registry_findings:
        return _mark_blocked(plan)

    if supplied.is_symlink():
        plan["findings"].append(
            _finding("error", str(supplied), "vault path must not be a symlink", "vault")
        )
        return _mark_blocked(plan)
    if not supplied.exists() or not supplied.is_dir():
        plan["findings"].append(
            _finding("error", str(supplied), "vault path must be an existing directory", "vault")
        )
        return _mark_blocked(plan)

    try:
        source_snapshot = snapshot_id(supplied)
        source_bytes = _canonical_bytes(supplied)
    except (OSError, ValueError, RuntimeError) as error:
        plan["findings"].append(
            _finding("error", "", f"unable to snapshot source vault: {error}", "snapshot")
        )
        return _mark_blocked(plan)
    plan["source_snapshot_id"] = source_snapshot
    plan["source_snapshot"] = source_snapshot
    plan["snapshot_id"] = source_snapshot
    plan["_source_bytes"] = source_bytes

    schema = parse_schema(supplied)
    plan["from_schema"] = schema.get("version_text")
    plan["current_schema"] = schema.get("version_text")
    plan["source_schema_version"] = schema.get("version_text")
    plan["source_schema"] = schema.get("version_text")
    schema_lines = list(SCHEMA_VERSION_LINE.finditer(str(schema.get("text", ""))))
    if schema.get("error"):
        plan["findings"].append(_finding("error", "SCHEMA.md", str(schema["error"]), "schema"))
    if len(schema_lines) != 1:
        plan["findings"].append(
            _finding(
                "error",
                "SCHEMA.md",
                "SCHEMA.md must contain exactly one schema_version declaration",
                "schema",
            )
        )
    if schema.get("version") is None:
        plan["findings"].append(
            _finding("error", "SCHEMA.md", "unable to identify a supported schema version", "schema")
        )
    for error in schema.get("contract_errors", []):
        plan["findings"].append(_finding("error", "SCHEMA.md", str(error), "schema"))
    if schema.get("version") == (0, 2) and not schema.get("contract_section_present"):
        plan["findings"].append(
            _finding(
                "error",
                "SCHEMA.md",
                "schema 0.2 must declare vertical_contracts",
                "schema",
            )
        )
    if _blocking_findings(plan):
        return _mark_blocked(plan)

    if schema.get("version") == (0, 2):
        contract_validation = _schema_contract_validation(supplied)
        plan["current_schema_contract_validation"] = contract_validation
        for item in contract_validation.get("errors", []):
            plan["findings"].append(
                _finding(
                    "error",
                    str(item.get("path", "SCHEMA.md")),
                    str(item.get("message", "schema contract validation failed")),
                    "schema-contract",
                )
            )
        if _blocking_findings(plan):
            return _mark_blocked(plan)

    current = str(schema.get("version_text"))
    requested_target = str(target if target is not None else "latest").strip()
    target_label = migration_registry.latest_supported_schema if requested_target == "latest" else requested_target
    plan["requested_target"] = requested_target
    plan["target_schema"] = target_label
    plan["target_schema_version"] = target_label
    if not target_label:
        plan["findings"].append(
            _finding(
                "error",
                "SCHEMA.md",
                "migration target cannot be empty",
                "unsupported-target",
                code="unsupported-target",
            )
        )
        return _mark_blocked(plan)
    if _is_future_schema(current, migration_registry.latest_supported_schema):
        plan["findings"].append(
            _finding(
                "error",
                "SCHEMA.md",
                f"vault declares future unsupported schema: {current}",
                "future-schema",
                code="future-schema",
            )
        )
        return _mark_blocked(plan)
    try:
        path = migration_registry.resolve_path(current, target_label)
    except MigrationRegistryError as error:
        plan["findings"].append(
            _finding("error", "SCHEMA.md", error.message, error.code, code=error.code)
        )
        return _mark_blocked(plan)

    if not path:
        return _no_op_plan(plan, current, target_label, migration_registry, source_bytes, supplied)

    _set_plan_summary(plan, current, target_label, path, migration_registry)
    if len(path) == 1 and path[0].planner is _plan_0_1_to_0_2:
        result = path[0].planner(supplied)
        result["_source_bytes"] = source_bytes
        result["_vault_path"] = str(supplied)
        result["_active_validator"] = path[0].active_validator or _validate_active_state
        result["registry_validation"] = registry_findings
        result["registry_valid"] = True
        _set_plan_summary(result, current, target_label, path, migration_registry)
        result["proposed_final_snapshot_id"] = str(
            result.get("proposed_snapshot_id", "")
        )
        result["proposed_final_snapshot"] = result["proposed_final_snapshot_id"]
        result["migration_needed"] = True
        result["already_current"] = False
        result["blocking_findings"] = list(_blocking_findings(result))
        result["plan_valid"] = not result["blocking_findings"] and bool(
            result.get("proposed_validation", {}).get("ok")
        )
        return result
    return _chain_plan(
        supplied,
        plan,
        current,
        target_label,
        path,
        source_bytes,
        migration_registry,
    )


def _write_temp_sibling(path: Path, content: bytes, suffix: str = "") -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.migrate-",
        suffix=suffix,
        dir=str(path.parent),
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            mode = path.stat().st_mode & 0o777
            os.chmod(temporary, mode)
        except (OSError, NotImplementedError):
            pass
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


def _cleanup_temporary(paths: Iterable[Path]) -> List[str]:
    failures: List[str] = []
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as error:
            failures.append(f"{path}: {error}")
    return failures


def _ensure_parent(path: Path, vault: Path, created: List[Path]) -> None:
    missing: List[Path] = []
    current = path.parent
    while current != vault and not current.exists():
        missing.append(current)
        current = current.parent
    if current != vault and (current.is_symlink() or not current.is_dir()):
        raise OSError(f"migration parent is not a real directory: {current}")
    for directory in reversed(missing):
        directory.mkdir()
        created.append(directory)


def _verify_rollback(transaction: Mapping[str, Any]) -> List[str]:
    failures: List[str] = []
    originals: Mapping[Path, Optional[bytes]] = transaction.get("originals", {})
    for path, original in originals.items():
        try:
            if original is None:
                if path.exists() or path.is_symlink():
                    failures.append(f"{path}: newly created file remains")
            elif not path.is_file() or path.read_bytes() != original:
                failures.append(f"{path}: original bytes were not restored")
        except OSError as error:
            failures.append(f"{path}: unable to verify rollback: {error}")
    for directory in transaction.get("created_dirs", []):
        if directory.exists():
            failures.append(f"{directory}: newly created directory remains")
    return failures


def _rollback_transaction(transaction: Mapping[str, Any]) -> Dict[str, Any]:
    replaced = list(transaction.get("replaced", []))
    originals: Mapping[Path, Optional[bytes]] = transaction.get("originals", {})
    temporary: List[Path] = []
    failures: List[str] = []
    for path in reversed(replaced):
        original = originals.get(path)
        try:
            if original is None:
                path.unlink(missing_ok=True)
            else:
                rollback = _write_temp_sibling(path, original, suffix="-rollback")
                temporary.append(rollback)
                os.replace(rollback, path)
                temporary.remove(rollback)
        except Exception as error:
            failures.append(f"{path}: {error}")
    failures.extend(_cleanup_temporary(temporary))

    for directory in sorted(transaction.get("created_dirs", []), key=lambda item: len(item.parts), reverse=True):
        try:
            directory.rmdir()
        except FileNotFoundError:
            pass
        except OSError as error:
            failures.append(f"{directory}: {error}")
    failures.extend(_verify_rollback(transaction))
    return {
        "status": "rolled-back" if not failures else "rollback-failed",
        "ok": not failures,
        "failures": failures,
    }


def _replace_planned_files(vault: Path, updates: Mapping[str, bytes]) -> Dict[str, Any]:
    originals: Dict[Path, Optional[bytes]] = {}
    temporary: List[Path] = []
    temporary_by_path: Dict[Path, Path] = {}
    replaced: List[Path] = []
    created_dirs: List[Path] = []
    try:
        paths = {vault / label: content for label, content in updates.items()}
        ordered_paths = sorted(paths, key=lambda item: item.as_posix())
        for path in ordered_paths:
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise OSError(f"migration target is not a regular file: {path}")
            originals[path] = path.read_bytes() if path.exists() else None
            _ensure_parent(path, vault, created_dirs)
        for path in ordered_paths:
            temporary_path = _write_temp_sibling(path, paths[path])
            temporary.append(temporary_path)
            temporary_by_path[path] = temporary_path
        for path in ordered_paths:
            temporary_path = temporary_by_path[path]
            os.replace(temporary_path, path)
            temporary.remove(temporary_path)
            replaced.append(path)
        return {
            "ok": True,
            "replaced": replaced,
            "originals": originals,
            "created_dirs": created_dirs,
            "temporary": temporary,
        }
    except Exception as error:
        cleanup_failures = _cleanup_temporary(temporary)
        transaction = {
            "replaced": replaced,
            "originals": originals,
            "created_dirs": created_dirs,
        }
        rollback = _rollback_transaction(transaction)
        failures = [str(error)] + cleanup_failures + rollback.get("failures", [])
        return {
            "ok": False,
            "error": str(error),
            "replaced": replaced,
            "originals": originals,
            "created_dirs": created_dirs,
            "temporary": [],
            "rollback": rollback,
            "failures": failures,
        }


def _public_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): _public_value(item)
            for key, item in value.items()
            if not str(key).startswith("_")
        }
    if isinstance(value, (list, tuple)):
        return [_public_value(item) for item in value]
    return value


def _error_findings(result: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    return [
        item
        for item in result.get("findings", [])
        if isinstance(item, Mapping) and item.get("severity") == "error"
    ]


def apply_migration(
    vault: Path,
    target: Any = "latest",
    registry: Optional[MigrationRegistry] = None,
) -> Dict[str, Any]:
    """Atomically apply, validate, and back up a migration's final state."""

    plan = plan_migration(vault, target=target, registry=registry)
    if not plan.get("migration_needed", plan.get("from_schema") == "0.1"):
        return plan
    if not plan.get("write_ready"):
        return plan

    supplied = Path(str(plan.get("_vault_path", vault))).expanduser()
    expected_snapshot = str(plan.get("source_snapshot_id", ""))
    try:
        current_snapshot = snapshot_id(supplied)
    except (OSError, ValueError, RuntimeError) as error:
        plan["findings"].append(_finding("error", "", f"unable to verify source snapshot: {error}", "snapshot-drift"))
        plan["status"] = "blocked"
        plan["write_ready"] = False
        return plan
    plan["current_snapshot_before_write"] = current_snapshot
    if current_snapshot != expected_snapshot:
        plan["findings"].append(
            _finding(
                "error",
                "",
                "source vault changed after planning; migration stopped and must be re-planned",
                "snapshot-drift",
                planned_snapshot=expected_snapshot,
                current_snapshot=current_snapshot,
            )
        )
        plan["status"] = "stale-plan"
        plan["write_ready"] = False
        return plan

    updates = plan.get("_planned_updates", {})
    if not isinstance(updates, Mapping):
        plan["findings"].append(_finding("error", "", "migration plan has no complete planned byte set", "plan"))
        plan["status"] = "failed"
        plan["write_ready"] = False
        return plan

    transaction = _replace_planned_files(supplied, updates)
    if not transaction.get("ok"):
        plan["findings"].append(
            _finding(
                "error",
                "",
                f"active-vault replacement failed: {transaction.get('error', 'unknown error')}",
                "migration-write",
            )
        )
        plan["rollback"] = transaction.get("rollback", {"status": "unknown", "ok": False})
        plan["status"] = "failed"
        plan["write_ready"] = False
        plan["changed"] = []
        return plan

    try:
        active_validator = plan.get("_active_validator")
        if callable(active_validator):
            post_validation = active_validator(supplied, plan)
        else:
            post_validation = _validate_active_state(supplied, plan)
    except Exception as error:  # pragma: no cover - rollback safety boundary
        post_validation = {
            "ok": False,
            "errors": [{"path": "", "message": str(error)}],
        }
    expected_final_snapshot = str(
        plan.get("proposed_final_snapshot_id")
        or plan.get("proposed_snapshot_id")
        or ""
    )
    actual_final_snapshot = str(
        post_validation.get("deep", {}).get("snapshot_id")
        or post_validation.get("snapshot_id")
        or snapshot_id(supplied)
    )
    if expected_final_snapshot and actual_final_snapshot != expected_final_snapshot:
        post_validation["ok"] = False
        post_validation.setdefault("errors", []).append(
            {
                "path": "",
                "message": "active vault bytes differ from the validated proposed state",
            }
        )
    plan["post_write_validation"] = post_validation
    if not post_validation.get("ok"):
        rollback = _rollback_transaction(transaction)
        plan["rollback"] = rollback
        plan["findings"].append(
            _finding(
                "error",
                "",
                "post-write validation failed; active-vault changes were rolled back",
                "post-write-validation",
            )
        )
        for item in post_validation.get("errors", []):
            plan["findings"].append(
                _finding(
                    "error",
                    str(item.get("path", "")),
                    str(item.get("message", "post-write validation failed")),
                    "post-write-validation",
                )
            )
        if not rollback.get("ok"):
            plan["findings"].append(
                _finding("error", "", "active-vault rollback did not complete; stop and recover from an existing backup", "rollback")
            )
        plan["status"] = "failed"
        plan["write_ready"] = False
        plan["changed"] = []
        return plan

    plan["post_write_snapshot_id"] = actual_final_snapshot
    try:
        backup_path, removed = backup_vault.create_backup(supplied)
        backup_path = Path(backup_path)
        if not backup_path.is_file():
            raise backup_vault.BackupError(
                f"backup helper returned a path that does not exist: {backup_path}"
            )
    except Exception as error:
        rollback = _rollback_transaction(transaction)
        plan["rollback"] = rollback
        plan["findings"].append(
            _finding("error", "backups/", f"post-write backup failed: {error}", "backup")
        )
        if not rollback.get("ok"):
            plan["findings"].append(
                _finding("error", "", "active-vault rollback did not complete; stop and recover from the existing backup set", "rollback")
            )
        plan["status"] = "failed"
        plan["write_ready"] = False
        plan["changed"] = []
        return plan

    plan["backup"] = str(backup_path)
    plan["removed_backups"] = [str(path) for path in removed]
    plan["backup_snapshot_id"] = actual_final_snapshot
    plan["rollback"] = {"status": "not-needed", "ok": True}
    plan["changed"] = sorted(updates)
    plan["applied_changed"] = sorted(updates)
    plan["migration_path_applied"] = list(plan.get("migration_path", []))
    plan["migration_completed"] = True
    plan["status"] = "success"
    plan["write_ready"] = False
    plan["blocking_findings"] = list(_blocking_findings(plan))
    return plan


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan or explicitly migrate a SelfContext vault to a supported target schema"
    )
    parser.add_argument("vault", nargs="?", default="vault")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only migration plan")
    mode.add_argument("--write", action="store_true", help="apply the migration and create one final-state backup")
    parser.add_argument(
        "--target",
        default="latest",
        help="supported target schema label, or latest (default: latest)",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    result = (
        apply_migration(Path(args.vault), target=args.target)
        if args.write
        else plan_migration(Path(args.vault), target=args.target)
    )
    public = _public_value(result)
    if args.format == "json":
        print(json.dumps(public, indent=2, sort_keys=True))
    else:
        for item in public.get("findings", []):
            prefix = str(item.get("severity", "info")).upper()
            location = f"{item.get('path')}: " if item.get("path") else ""
            print(f"{prefix}: {location}{item.get('message', '')}")
        if public.get("backup"):
            print(f"Backup: {public['backup']}")
        if public.get("changed"):
            print("Changed: " + ", ".join(public["changed"]))
        elif public.get("status") == "already-migrated":
            print(
                "No migration changes needed; vault already uses "
                + str(public.get("target_schema", "the requested schema"))
            )
        elif public.get("status") == "planned":
            print("Migration plan is valid; no active-vault writes performed")
    return 1 if _error_findings(public) else 0


if __name__ == "__main__":
    raise SystemExit(main())
